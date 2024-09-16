from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
import json
from django.conf import settings
import os
from datetime import datetime
import uuid
from django.http import JsonResponse
import requests
from django.core.files import File
from .utils import search_arxiv, generate_summary, generate_multiple_choice, generate_main_content
from .gpt_processor import GPTProcessor2
from .models import Video, GeneratedContent
from dotenv import load_dotenv

load_dotenv()

class GenerateVideoView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            print(data)
            pdf_url = data.get('pdfUrl')
            chapter_id = data.get('chapterId')

            if not pdf_url:
                return JsonResponse({'error': 'PDF URL and Chapter ID are required'}, status=400)

            # Download the PDF file
            response = requests.get(pdf_url)
            if response.status_code == 200:
                output_folder = os.path.join(settings.MEDIA_ROOT, 'generated_videos')
                os.makedirs(output_folder, exist_ok=True)
                pdf_path = os.path.join(output_folder, 'downloaded.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
            else:
                return JsonResponse({'error': 'Failed to download PDF'}, status=400)

            processor = GPTProcessor2(
                openai_api_key = os.getenv("OPENAI_API_KEY"),
                anthropic_api_key = os.getenv("ANTHROPIC_API_KEY"),
            )

            # Process the downloaded PDF to generate the video
            descriptions_file, image_files = processor.process_pdf_to_descriptions(pdf_path, output_folder)
            
            # Generate a unique filename for the final context file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            final_context_filename = f"context_{timestamp}_{unique_id}.txt"
            
            # Create the directory if it doesn't exist
            generated_contents_dir = os.path.join(settings.MEDIA_ROOT, 'generated_contents')
            os.makedirs(generated_contents_dir, exist_ok=True)
            
            # Set the path for the final context file
            final_context_file = os.path.join(generated_contents_dir, final_context_filename)
            
            # Process with Claude and save the result to the new location
            processor.process_with_claude(descriptions_file, final_context_file)
            
            video_path, _, _ = processor.create_video_from_context(final_context_file, image_files, output_folder)
            
            # Generate summary, multiple-choice questions, and find arXiv papers
            with open(final_context_file, 'r') as f:
                context = f.read()
            main_topics = generate_main_content(context)
            summary = generate_summary(context)
            multiple_choice = generate_multiple_choice(main_topics)
            arxiv_papers = search_arxiv(main_topics, max_results=5)

            # Save the video and content file
            video_filename = os.path.basename(video_path)
            content_filename = os.path.basename(final_context_file)
            
            video = Video.objects.create(title=video_filename)
            
            with open(final_context_file, 'rb') as content_file:
                generated_content = GeneratedContent(video=video)
                generated_content.content_file.save(content_filename, File(content_file))
                generated_content.save()

            # Correct the URL to be served via Django
            video_url = request.build_absolute_uri(
                os.path.join(settings.MEDIA_URL, 'generated_videos', video_filename)
            )

            # Update the chapter in Prisma
            # prisma_url = "http://localhost:3000/api/updateChapter"  # Adjust this URL to your Next.js API route
            # prisma_data = {
            #     "chapterId": chapter_id,
            #     "videoUrl": video_url,
            #     "summary": summary,
            #     "multipleChoice": json.dumps(multiple_choice),
            #     "arxivPapers": json.dumps(arxiv_papers)
            # }
            
            # Use requests instead of httpx for synchronous request
            # response = requests.post(prisma_url, json=prisma_data)
            # if response.status_code != 200:
            #     print(f"Error updating chapter in Prisma: {response.text}")
            #     return JsonResponse({'error': 'Failed to update chapter in Prisma'}, status=500)

            return JsonResponse({
                'videoPath': video_url,
                'contentId': generated_content.id,
                'summary': summary,
                'multipleChoice': multiple_choice,
                'arxivPapers': arxiv_papers,
                'finalContextFile': os.path.relpath(final_context_file, settings.MEDIA_ROOT)
            })

        except Exception as e:
            print(f"Error in GenerateVideoView: {e}")
            return JsonResponse({'error': str(e)}, status=500)

def csrf(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})