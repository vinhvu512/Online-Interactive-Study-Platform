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
import boto3
from botocore.exceptions import ClientError
import concurrent.futures
import gc

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

            processor = GPTProcessor2(openai_api_key = os.getenv("OPENAI_API_KEY"))

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
            processor.process_with_openai(descriptions_file, final_context_file)
            
            video_path, _, _ = processor.create_video_from_context(final_context_file, image_files, output_folder)
            
            # Tạo tên file động cho video khi lưu lên object storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_id = uuid.uuid4().hex[:8]
            dynamic_video_filename = f"video_{timestamp}_{unique_id}.mp4"

            # Upload generated video to S3 (works without GCS credentials).
            bucket_name = os.getenv("S3_BUCKET_NAME")
            if not bucket_name:
                return JsonResponse({"error": "Missing S3_BUCKET_NAME env var"}, status=500)

            s3_region = os.getenv("AWS_REGION", "us-east-1")
            s3_public_base_url = os.getenv("S3_PUBLIC_BASE_URL")  # optional (e.g. CloudFront domain)
            aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

            s3_client = boto3.client(
                "s3",
                region_name=s3_region,
                aws_access_key_id=aws_access_key_id or None,
                aws_secret_access_key=aws_secret_access_key or None,
            )

            def build_s3_url(cloud_filename: str) -> str:
                if s3_public_base_url:
                    return f"{s3_public_base_url.rstrip('/')}/{cloud_filename}"
                if s3_region == "us-east-1":
                    return f"https://{bucket_name}.s3.amazonaws.com/{cloud_filename}"
                return f"https://{bucket_name}.s3.{s3_region}.amazonaws.com/{cloud_filename}"

            def upload_file(file_path, cloud_filename):
                video_url = build_s3_url(cloud_filename)

                # If object already exists, skip re-upload to save time.
                try:
                    s3_client.head_object(Bucket=bucket_name, Key=cloud_filename)
                    print(f"File already exists in S3, skipping: {cloud_filename}")
                    os.remove(file_path)
                    return video_url
                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code", "")
                    # head_object returns 404 / NoSuchKey if it doesn't exist.
                    if code not in {"404", "NoSuchKey", "NotFound"}:
                        raise

                # Upload (public-read so the frontend can use the URL in <video src="...">).
                extra_args = {"ACL": "public-read", "ContentType": "video/mp4"}
                s3_client.upload_file(file_path, bucket_name, cloud_filename, ExtraArgs=extra_args)
                print(f"Đã tải lên S3: {cloud_filename}")

                os.remove(file_path)
                print(f"Đã xóa file cục bộ: {file_path}")
                return video_url

            print(f"Video path: {video_path}")
            video_url = upload_file(video_path, dynamic_video_filename)
            print(f"Video URL: {video_url}")

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
            # video_url = request.build_absolute_uri(
            #     os.path.join(settings.MEDIA_URL, 'generated_videos', video_filename)
            # )
            ##
            
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
        finally:
            #Ensure all resources are released
            gc.collect()
def csrf(request):
    token = get_token(request)
    return JsonResponse({'csrfToken': token})