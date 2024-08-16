from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import PDFUploadForm
from .models import Video
from django.views import View
import json
from .gpt_processor import GPTProcessor, GPTProcessor2
from django.conf import settings
import os
from .utils import search_arxiv
from django.http import JsonResponse
import requests

class UploadPDFView(View):
    template_name = 'upload_pdf.html'
    processor = GPTProcessor(api_key=settings.OPENAI_API_KEY)

    def get(self, request):
        form = PDFUploadForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.save()
            output_folder = os.path.join(settings.MEDIA_ROOT, 'videos', pdf.title)
            os.makedirs(output_folder, exist_ok=True)
            video_path, descriptions, rubric, summaries, questions, durations = self.processor.vip_process_pdf_to_video(
                pdf.pdf_file.path, output_folder)

            video = Video.objects.create(
                title=pdf.title,
                video_file=os.path.relpath(video_path, settings.MEDIA_ROOT),
                descriptions=descriptions,
                rubric=rubric,
                summaries=summaries,
                questions=questions,  # Store questions
                durations=durations  # Store durations
            )
            return redirect('watch_video', video_id=video.id)
        return render(request, self.template_name, {'form': form})


class WatchVideoView(View):
    template_name = 'watch_video.html'

    def get(self, request, video_id):
        video = get_object_or_404(Video, id=video_id)
        summary = video.summaries[0]
        related_papers = search_arxiv(summary)
        return render(request, self.template_name, {
            'video': video,
            'related_papers': related_papers
        })


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
                anthropic_api_key=""
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
