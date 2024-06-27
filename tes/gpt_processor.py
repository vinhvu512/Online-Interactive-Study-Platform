import fitz  # PyMuPDF
import base64
import requests
import os
from pathlib import Path
from PIL import Image
import numpy as np
from moviepy.editor import ImageSequenceClip, AudioFileClip, concatenate_videoclips
import openai
from moviepy.video.VideoClip import TextClip


class GPTProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=api_key)

    def encode_image(self, image_path):
        """Encodes an image to a base64 string."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def images_from_folder(self, folder_path):
        """Reads all images from a folder and sorts them."""
        image_files = [os.path.join(folder_path, file) for file in os.listdir(folder_path) if
                       file.lower().endswith(('.png', '.jpg', '.jpeg'))]
        return sorted(image_files)

    def describe_single_image(self, image_files):
        """Uses GPT-4 to describe each image."""
        descriptions = []
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        for image_file in image_files:
            base64_image = self.encode_image(image_file)
            payload = {
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "You are the professor, and this is one slide of all presentation. Give a small lecture of this slide like a professor. Remember, just this slide, aware of length, you should focus on important part and inform shortly, enough for a slide. You should give me raw text. Don't give me outline number. This supports overall lecture on CNN and RNN for sentiment analysis.Limit to 20 word",
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            if response.status_code == 200:
                try:
                    description = response.json()['choices'][0]['message']['content']
                    descriptions.append(description)
                except KeyError:
                    print(f"Error in response for image {image_file}: {response.json()}")
                    descriptions.append("Error in generating description.")
            else:
                print(f"Failed to get response for image {image_file}: {response.text}")
                descriptions.append("Failed to get description.")
        return descriptions

    def text_to_speech_with_openai(self, descriptions, output_dir="audio_files"):
        """Converts text descriptions to speech using OpenAI TTS."""
        os.makedirs(output_dir, exist_ok=True)
        audio_files = []

        for i, description in enumerate(descriptions):
            speech_file_path = Path(output_dir) / f"slide_{i + 1}.mp3"
            response = self.client.audio.speech.create(
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
            img_array = np.array(img)
            img_clip = ImageSequenceClip([img_array], durations=[duration])
            img_clip = img_clip.set_audio(audio)
            img_clip = img_clip.set_fps(fps)  # Set the fps for each image clip
            clips.append(img_clip)

        if clips:
            final_clip = concatenate_videoclips(clips, method="compose")
            final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac", fps=fps)
        else:
            print("No clips to concatenate")

        return durations

    def pdf_to_images(self, pdf_path, output_folder):
        """Converts a PDF into images."""
        pdf_document = fitz.open(pdf_path)
        num_pages = pdf_document.page_count

        os.makedirs(output_folder, exist_ok=True)

        image_paths = []
        for page_num in range(num_pages):
            page = pdf_document.load_page(page_num)
            pix = page.get_pixmap()
            image_path = os.path.join(output_folder, f"slide_{page_num + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)
        return image_paths

    def generate_rubric(self, descriptions):
        rubric = []
        for description in descriptions:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"This is the description {descriptions}, give me the outline, just the main outline for this"}
                ]
            )
            rubric.append(response.choices[0].message.content)
        return rubric

    def generate_summary(self, descriptions):
        """Generates a summary from descriptions."""
        summaries = []
        for description in descriptions:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Summarize this text: {description}"}
                ]
            )
            summaries.append(response.choices[0].message.content)
        return summaries

    def generate_questions(self, descriptions):
        questions = []
        for i, description in enumerate(descriptions):
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": f"Generate a multiple choice question and an essay question based on the following description: {description}"}
                ]
            )
            questions.append(response.choices[0].message.content)
        return questions

    def vip_process_pdf_to_video(self, pdf_path, output_folder):
        image_folder = os.path.join(output_folder, 'images')
        audio_folder = os.path.join(output_folder, 'audio')

        image_files = self.pdf_to_images(pdf_path, image_folder)
        descriptions = self.describe_single_image(image_files)
        audio_files = self.text_to_speech_with_openai(descriptions, audio_folder)
        video_path = os.path.join(output_folder, f"{Path(pdf_path).stem}.mp4")

        durations = self.create_video(image_files, audio_files, video_path)
        rubric = self.generate_rubric(descriptions)
        summaries = self.generate_summary(descriptions)
        questions = self.generate_questions(descriptions)
        return video_path, descriptions, rubric, summaries, questions, durations
    def download_pdf(self, pdf_url, output_path):
        response = requests.get(pdf_url)
        response.raise_for_status()  # Raise an error for bad responses
        with open(output_path, 'wb') as f:
            f.write(response.content)

    def process_pdf_to_video(self, pdf_url, output_folder):
        """Converts a PDF from a URL into a video."""
        # Download the PDF first
        pdf_path = os.path.join(output_folder, 'downloaded.pdf')
        self.download_pdf(pdf_url, pdf_path)

        image_folder = os.path.join(output_folder, 'images')
        audio_folder = os.path.join(output_folder, 'audio')

        image_files = self.pdf_to_images(pdf_path, image_folder)
        descriptions = self.describe_single_image(image_files)
        audio_files = self.text_to_speech_with_openai(descriptions, audio_folder)
        video_path = os.path.join(output_folder, f"{Path(pdf_path).stem}.mp4")

        durations = self.create_video(image_files, audio_files, video_path)
        rubric = self.generate_rubric(descriptions)
        summaries = self.generate_summary(descriptions)
        questions = self.generate_questions(descriptions)
        return video_path, descriptions, rubric, summaries, questions, durations

