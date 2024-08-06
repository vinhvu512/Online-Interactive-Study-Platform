from django.middleware.csrf import get_token
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import PDFUploadForm
from .models import Video
from django.views import View
import json
from .gpt_processor import GPTProcessor
from django.conf import settings
import os
from .utils import search_arxiv
from django.http import JsonResponse
import requests

from google.cloud import storage
from google.oauth2 import service_account
from google.api_core import exceptions as google_exceptions
import concurrent.futures


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
            'related_papers': related_papers,
            'video_url': video.video_url  # Add this line
        })


class GenerateVideoView(View):

    def post(self, request):
        try:
            data = json.loads(request.body)
            print(data)
            # print(request)
            pdf_url = data.get('pdfUrl')
            print(pdf_url)
            # if not pdf_url:
            #     return JsonResponse({'error': 'PDF URL is required'}, status=400)

            processor = GPTProcessor(api_key=settings.OPENAI_API_KEY)

            output_folder = os.path.join(settings.MEDIA_ROOT, 'generated_videos')
            os.makedirs(output_folder, exist_ok=True)

            video_path, descriptions, rubric, summaries, questions, durations = processor.process_pdf_to_video(
                pdf_url, output_folder)

            # Correct the URL to be served via Django
            # video_url = request.build_absolute_uri(
            #     os.path.join(settings.MEDIA_URL, 'generated_videos', os.path.basename(video_path))
            # )

            # Thiết lập xác thực Google Cloud
            credentials = service_account.Credentials.from_service_account_file(
                '/Users/albuscorleone/PycharmProjects/AI_Challenge/Seraphic_Rarity430816.json',
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )

            # Tên bucket Google Cloud Storage
            bucket_name = "bki-slide-to-vid"

            # Khởi tạo client Google Cloud Storage
            storage_client = storage.Client(credentials=credentials)
            bucket = storage_client.bucket(bucket_name)

            # Hàm tải lên video
            def upload_file(file_path):
                file_name = os.path.basename(file_path)
                video_url = f"https://storage.googleapis.com/{bucket_name}/{file_name}"
                try:
                    # Cố gắng tải lên Google Cloud Storage
                    blob = bucket.blob(file_name)
                    blob.upload_from_filename(file_path)
                    print(f"Đã tải lên GCP: {file_name}")

                    # Xóa file cục bộ
                    os.remove(file_path)
                    print(f"Đã xóa file cục bộ: {file_name}")

                except google_exceptions.Conflict:
                    print(f"File {file_name} đã tồn tại trong bucket. Bỏ qua tải lên.")
                    os.remove(file_path)
                    print(f"Đã xóa file cục bộ: {file_name}")
                except google_exceptions.Forbidden as e:
                    print(f"Lỗi quyền truy cập khi tải lên {file_name}: {e}")
                except Exception as e:
                    print(f"Lỗi khi xử lý {file_name}: {e}")
        
            file_name = os.path.basename(f"{video_path}")
            video_url = f"https://storage.googleapis.com/{bucket_name}/{file_name}"

            print(f"Video path: {video_path}")

            upload_file(f"{video_path}")

            print(f"Video URL: {video_url}")

            return JsonResponse({
                'videoPath': video_url,
                'descriptions': descriptions,
                'rubric': rubric,
                'summaries': summaries,
                'questions': questions
            })

        except Exception as e:
            print(f"Error in GenerateVideoView: {e}")
            return JsonResponse({'error': str(e)}, status=500)


def csrf(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})
