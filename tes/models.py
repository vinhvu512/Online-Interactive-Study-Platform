from django.db import models

class PDF(models.Model):
    title = models.CharField(max_length=100)
    pdf_file = models.FileField(upload_to='pdfs/')

    def __str__(self):
        return self.title

class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    descriptions = models.JSONField(null=True, blank=True)
    rubric = models.JSONField(null=True, blank=True)
    summaries = models.JSONField(null=True, blank=True)
    questions = models.JSONField(null=True, blank=True)  # Add questions field
    durations = models.JSONField(null=True, blank=True)  # Add durations field

    def __str__(self):
        return self.title

class GeneratedContent(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='generated_content')
    content_file = models.FileField(upload_to='generated_content/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Content for {self.video.title}"