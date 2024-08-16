from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import PDFUploadForm
from .models import Video
from django.views import View
import json
from .gpt_processor import GPTProcessor2
from django.conf import settings
import os
from .utils import search_arxiv
from django.http import JsonResponse
import requests
class GenerateVideoView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            pdf_url = data.get('pdfUrl')

            if not pdf_url:
                return JsonResponse({'error': 'PDF URL is required'}, status=400)

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
                openai_api_key="",
                anthropic_api_key = ""
            )

            # Process the downloaded PDF to generate the video
            descriptions_file, image_files = processor.process_pdf_to_descriptions(pdf_path, output_folder)
            final_context_file = processor.process_with_claude(descriptions_file, output_folder)
            video_path, _, _ = processor.create_video_from_context(final_context_file, image_files, output_folder)

            # Correct the URL to be served via Django
            video_url = request.build_absolute_uri(
                os.path.join(settings.MEDIA_URL, 'generated_videos', os.path.basename(video_path))
            )

            return JsonResponse({
                'videoPath': video_url
            })

        except Exception as e:
            print(f"Error in GenerateVideoView: {e}")
            return JsonResponse({'error': str(e)}, status=500)



def csrf(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})
