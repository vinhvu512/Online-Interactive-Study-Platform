from .views import UploadPDFView, WatchVideoView, csrf
from django.urls import path
from .views import GenerateVideoView

urlpatterns = [
    path('upload/', UploadPDFView.as_view(), name='upload_pdf'),
    path('<int:video_id>/', WatchVideoView.as_view(), name='watch_video'),
    path('generate-video/', GenerateVideoView.as_view(), name='generate_video'),
    path('csrf/', csrf, name='csrf'),  # Add this line
]