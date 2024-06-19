from django import forms
from .models import Video
from .models import PDF
class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['title', 'video_file']

class PDFUploadForm(forms.ModelForm):
    class Meta:
        model = PDF
        fields = ['title', 'pdf_file']