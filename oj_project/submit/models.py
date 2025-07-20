
# Create your models here.
from django.db import models
from django.contrib.auth.models import User
from core.models import Problem

class CodeSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, null=True, blank=True)  # Optional for general compiler
    language = models.CharField(max_length=100)
    code = models.TextField()
    input_data = models.TextField(null=True, blank=True)
    output_data = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Submission by {self.user.username} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']