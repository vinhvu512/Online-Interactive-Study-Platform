from .views import csrf
from django.urls import path
from .views import GenerateVideoView

urlpatterns = [
    path('generate-video/', GenerateVideoView.as_view(), name='generate_video'),
    path('csrf/', csrf, name='csrf'),  # Add this line
]