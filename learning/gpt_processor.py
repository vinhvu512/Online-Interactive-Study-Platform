import os
import base64
import re
import requests
import openai
from moviepy.editor import AudioFileClip, ImageSequenceClip, concatenate_videoclips
from pathlib import Path
from PIL import Image
import numpy as np
import fitz  # PyMuPDF
import natsort
from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletionMessage


class GPTProcessor2:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.openai_client = OpenAI(api_key=openai_api_key)

    def images_from_folder(self, folder_path):
        """Reads all images from a folder and sorts them."""
        image_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if
                       file.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return natsort.natsorted(image_files)

    def encode_image(self, image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def create_base64_image_content(self, filenames):
        image_content = []
        for filename in filenames:
            base64_image = self.encode_image(filename)
            ext = os.path.splitext(filename)[1].lower()
            mime = "image/png" if ext == ".png" else "image/jpeg"
            image_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime};base64,{base64_image}",
                    "detail": "high",
                },
            })
        return image_content

    def process_response(self, json_response):
        if json_response.get("error"):
            raise ValueError(f"OpenAI API error: {json_response['error']}")
        choices = json_response.get("choices") or []
        if not choices:
            raise ValueError("OpenAI API returned no choices")
        content = (choices[0].get("message") or {}).get("content") or ""
        slides = re.split(r'(#slide\d+#)', content)[1:]

        slide_dict = {}
        for i in range(0, len(slides), 2):
            if i + 1 >= len(slides):
                break
            tag = slides[i]
            nums = re.findall(r'\d+', tag)
            if not nums:
                continue
            slide_number = int(nums[0])
            slide_text = slides[i + 1].strip()
            slide_dict[slide_number] = slide_text

        return slide_dict

    def send_batch_request(
        self,
        image_files,
        start_slide,
        previous_response_text="",
        is_first_batch=True,
        strict=False,
    ):
        """Sends a batch of image files to the API and returns the response."""
        image_content = self.create_base64_image_content(image_files)

        slide_tags = [f"#slide{start_slide + i}#" for i in range(len(image_files))]
        tags_joined = ", ".join(slide_tags)
        end_slide = start_slide + len(image_files) - 1

        base_instructions = (
            f"These are images of presentation slides (pages {start_slide}–{end_slide}). "
            "Describe visible text, diagrams, and bullet points and write engaging professor-style lecture narration. "
            f"You MUST output exactly {len(image_files)} sections. Each section MUST start with one of these tags on its own line: {tags_joined}. "
            "After each tag, write the narration for that slide only. "
            "Do not add a title, preamble, apology, or refusal—your first characters must be the first required tag. "
            "Do not use any other #slideN# tags."
        )
        if strict:
            base_instructions += (
                f" RETRY: Your previous answer did not use the required tags. "
                f"Start now with exactly #slide{start_slide}# then narration, then #slide{start_slide + 1}#, and so on."
            )

        if is_first_batch:
            prompt_text = f"{previous_response_text}\n\n{base_instructions}"
        else:
            prompt_text = (
                f"{previous_response_text}\n\n"
                f"{base_instructions} "
                "Continue the lecture in the same tone; do not greet the audience."
            )

        text_content = {
            "type": "text",
            "text": prompt_text,
        }

        system_text = (
            "You are an educational assistant that narrates presentation slides for video generation. "
            "The images are instructional slide decks (not private photos). "
            "You always follow the user's delimiter format exactly so downstream code can parse your output."
        )

        messages = [
            {"role": "system", "content": system_text},
            {
                "role": "user",
                "content": [
                    text_content,
                    *image_content,
                ],
            },
        ]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_api_key}",
        }

        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "max_tokens": 4096,
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=300,
        )
        data = response.json()
        if response.status_code >= 400:
            raise ValueError(f"OpenAI HTTP {response.status_code}: {data}")
        print("Response JSON:", data)
        return data

    def process_pdf_to_descriptions(self, pdf_path, output_folder):
        image_folder = os.path.join(output_folder, 'images')
        image_files = self.pdf_to_images(pdf_path, image_folder)
        batch_size = 10
        start_slide = 1
        all_descriptions = {}
        previous_response_text = ""
        is_first_batch = True

        for i in range(0, len(image_files), batch_size):
            batch_files = image_files[i:i + batch_size]
            expected_keys = set(range(start_slide, start_slide + len(batch_files)))

            response = self.send_batch_request(
                batch_files, start_slide, previous_response_text, is_first_batch
            )
            slide_dict = self.process_response(response)
            if expected_keys - set(slide_dict.keys()):
                response = self.send_batch_request(
                    batch_files,
                    start_slide,
                    previous_response_text,
                    is_first_batch,
                    strict=True,
                )
                slide_dict = self.process_response(response)

            missing = expected_keys - set(slide_dict.keys())
            if missing:
                raise ValueError(
                    f"Vision model did not return narration for slides {sorted(missing)}. "
                    f"Got tags for slides {sorted(slide_dict.keys())}. "
                    "Check API key, model access, or try a smaller PDF batch."
                )

            previous_response_text = response["choices"][0]["message"]["content"]
            is_first_batch = False

            all_descriptions.update(slide_dict)
            start_slide += batch_size

        descriptions = [all_descriptions[key] for key in sorted(all_descriptions.keys())]
        if len(descriptions) != len(image_files):
            raise ValueError(
                f"Expected {len(image_files)} slide narrations, got {len(descriptions)}. "
                "Vision parsing failed partway through the PDF."
            )
        descriptions_file = os.path.join(output_folder, "descriptions.txt")
        self.save_descriptions(descriptions, descriptions_file)
        return descriptions_file, image_files

    def process_with_openai(self, descriptions_file, output_file):
        full_content = self.read_file(descriptions_file)
        total_slides = len(re.findall(r'#slide\d+#', full_content))

        # Dynamically determine batch sizes
        batch_sizes = []
        remaining_slides = total_slides
        while remaining_slides > 0:
            batch_size = min(10, remaining_slides)
            batch_sizes.append(batch_size)
            remaining_slides -= batch_size

        start = 1
        for i, batch_size in enumerate(batch_sizes, 1):
            end = min(start + batch_size - 1, total_slides)
            print(f"Processing batch {i} (slides {start}-{end})")

            processed_batch = self.process_batch(self.openai_client, full_content, start, end, total_slides)

            print("Type of processed_batch:", type(processed_batch))
            print("Content of processed_batch:", processed_batch)

            # Extract the text content from the TextBlock object
            if isinstance(processed_batch, ChatCompletionMessage) and len(processed_batch) > 0 and hasattr(processed_batch, '__str__'):
                processed_batch = processed_batch.content
            elif not isinstance(processed_batch, str):
                processed_batch = str(processed_batch)

            print("Type of processed_batch after conversion:", type(processed_batch))
            print("Content of processed_batch after conversion:", processed_batch)

            full_content = self.replace_batch(full_content, processed_batch, start, end)

            start = end + 1

        self.write_file(output_file, full_content)
        return output_file

    def create_video_from_context(self, final_context_file, image_files, output_folder):
        with open(final_context_file, 'r', encoding='utf-8') as f:
            final_context = f.read()

        slide_descriptions = self.extract_slide_descriptions(final_context)

        audio_folder = os.path.join(output_folder, 'audio')
        audio_files = self.text_to_speech_with_openai(slide_descriptions, audio_folder)
        video_path = os.path.join(output_folder, "final_video.mp4")

        durations = self.create_video(image_files, audio_files, video_path)
        return video_path, slide_descriptions, durations

    def pdf_to_images(self, pdf_path, output_folder):
        """Converts a PDF into high-resolution images."""
        pdf_document = fitz.open(pdf_path)
        num_pages = pdf_document.page_count

        os.makedirs(output_folder, exist_ok=True)

        image_paths = []
        for page_num in range(num_pages):
            page = pdf_document.load_page(page_num)
            zoom = 2  # Increase this value for higher resolution
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            image_path = os.path.join(output_folder, f"slide_{page_num + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)
        return image_paths

    def text_to_speech_with_openai(self, descriptions, output_dir="audio_files"):
        """Converts text descriptions to speech using OpenAI TTS."""
        os.makedirs(output_dir, exist_ok=True)
        audio_files = []

        for i, description in enumerate(descriptions):
            speech_file_path = Path(output_dir) / f"slide_{i + 1}.mp3"
            response = openai.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=description
            )
            with open(speech_file_path, "wb") as f:
                f.write(response.content)
            audio_files.append(str(speech_file_path))
        return audio_files

    def create_video(self, image_files, audio_files, output_file, fps=24):
        clips = []
        durations = []  # Save the duration for each slide
        for image_file, audio_file in zip(image_files, audio_files):
            audio = AudioFileClip(audio_file)
            duration = audio.duration
            durations.append(duration)
            img = Image.open(image_file)
            img = img.resize((1280, 720), Image.LANCZOS)  # Resize image to 720p
            img_array = np.array(img)
            img_clip = ImageSequenceClip([img_array], durations=[duration])
            img_clip = img_clip.set_audio(audio)
            img_clip = img_clip.set_fps(fps)  # Set the fps for each image clip
            clips.append(img_clip)

        if clips:
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps)
        else:
            raise RuntimeError(
                "No video clips to concatenate: no audio was produced for slides "
                f"(images={len(image_files)}, audio={len(audio_files)}). "
                "Usually the vision step returned no #slideN# narration."
            )

        return durations

    def save_descriptions(self, descriptions, file_path):
        """Saves the descriptions to a text file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('full_content = """\n')
            for i, desc in enumerate(descriptions, 1):
                f.write(f"#slide{i}#\n{desc}\n\n")
            f.write('"""')

    def read_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content.strip('full_content = """').strip('"""')

    def write_file(self, file_path, content):
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('full_content = """\n' + content + '\n"""')

    def create_prompt(self, batch_content, start, end, total_slides):
        prompt = f"""{batch_content}
Please read the content of these slides carefully and assume the role of a knowledgeable and engaging professor delivering a comprehensive and captivating lecture. Your goal is to deeply understand the meaning and context of each slide, explaining them in a manner that is both thorough and engaging. Rather than merely reading the existing text, provide insightful and detailed explanations, ensuring smooth and natural transitions between the content.
Create seamless and logical transitions that connect each slide to the overall theme of the lecture. Use phrases like, "This concept will be further explored in upcoming slides," or "Keep this idea in mind, as it will be crucial later on," to link different sections and maintain coherence throughout the lecture. Additionally, incorporate natural lecturer comments and anecdotes to make the lecture feel more authentic, relatable, and engaging.
You'll smoothly transition from the concepts covered in slides 1-{start - 1} to the advanced topics in slides {start}-{total_slides}. As you know from the first ten slides, [summarize key points from slides 1-{start - 1}], it's essential to build upon these foundations to fully grasp the ideas presented in the subsequent slides.
To recap, we've discussed [briefly mention a few key points from slides 1-{start - 1}]. Building on this, you will now explore how [mention the new concepts in slides {start}-{total_slides}] expand and improve your understanding of [content in slides 1-{start - 1}]. Additionally, as highlighted earlier, [mention another key point from slides 1-{start - 1}], which serves as a critical link to the upcoming sections.
By connecting these concepts, you'll gain a comprehensive understanding of the subject matter. This approach ensures that you can seamlessly integrate the knowledge from the initial slides with the more advanced topics to follow.
Now, let's delve into the details from slide {start} to slide {end}.
Please read the content of these slides carefully and assume the role of a knowledgeable and engaging professor delivering a comprehensive and captivating lecture. Your goal is to deeply understand the meaning and context of each slide, explaining them in a manner that is both thorough and engaging. Rather than merely reading the existing text, provide insightful and detailed explanations, ensuring smooth and natural transitions between the content.
Create seamless and logical transitions that connect each slide to the overall theme of the lecture. Use some phrases to link different sections and maintain coherence throughout the lecture. Additionally, incorporate natural lecturer comments and anecdotes to make the lecture feel more authentic, relatable, and engaging.
You'll smoothly transition from the concepts covered in slides 1-{start - 1} to the advanced topics in slides {start}-{total_slides}. As you know from the first ten slides, [summarize key points from slides 1-{start - 1}], it's essential to build upon these foundations to fully grasp the ideas presented in the subsequent slides.
To recap, we've discussed [briefly mention a few key points from slides 1-{start - 1}]. Building on this, you will now explore how [mention the new concepts in slides {start}-{total_slides}] expand and improve your understanding of [content in slides 1-{start - 1}]. Additionally, as highlighted earlier, [mention another key point from slides 1 to {start - 1}], which serves as a critical link to the upcoming sections.
By connecting these concepts, you'll gain a comprehensive understanding of the subject matter. This approach ensures that you can seamlessly integrate the knowledge from the initial slides with the more advanced topics to follow.
DO IT FROM SLIDE {start} to {end}, don't greet, just continue the presentations. Using some questionn such as, you have known about the [content in previous slide ]. Mention the future and the past is crucial and must have
You should hold the tag , #slide# format for each slide.
add emotion, but not too rude, emotion of the speech is identify by ** the caps of the word, the !!! the ??? the capitalism, the -. You are humorous professor, make the atmosphere positive."""
        return prompt

    def replace_batch(self, full_content, processed_batch, start, end):
        slides = re.findall(r'(#slide\d+#.*?(?=#slide\d+#|\Z))', full_content, re.DOTALL)
        new_slides = re.findall(r'(#slide\d+#.*?(?=#slide\d+#|\Z))', processed_batch, re.DOTALL)

        for i, new_slide in enumerate(new_slides):
            slide_number = start + i
            if slide_number <= end and slide_number - 1 < len(slides):
                full_content = full_content.replace(slides[slide_number - 1], new_slide)

        return full_content

    def process_batch(self, client, full_content, start, end, total_slides):
        slides = re.findall(r'(#slide\d+#.*?(?=#slide\d+#|\Z))', full_content, re.DOTALL)
        batch = slides[start - 1:end]
        batch_content = '\n'.join(batch)

        prompt = self.create_prompt(batch_content, start, end, total_slides)

        message = client.chat.completions.create (
            model="gpt-4o",
            messages=[
              {
                "role": "user",
                "content": [
                  {
                    "type": "text",
                    "text": prompt
                  }
                ]
              }
            ],
            temperature=0,
            max_tokens=4000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            response_format={
              "type": "text"
            }            
        )

        response = message.choices[0].message

        print("Type of message.content:", type(response))
        print("Content of message:", response)

        # Return the text content directly
        if isinstance(response, ChatCompletionMessage) and len(response.content) > 0 and hasattr(response.content, '__str__'):
            return response.content
        else:
            return str(response)

    def extract_slide_descriptions(self, final_context):
        slide_descriptions = re.findall(r'#slide\d+#(.*?)(?=#slide\d+#|\Z)', final_context, re.DOTALL)
        return [desc.strip() for desc in slide_descriptions]