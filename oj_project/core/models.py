# core/models.py - Simplified version without execution_time and memory_used
from django.db import models
from django.contrib.auth.models import User

class Problem(models.Model):
    DIFFICULTY_CHOICES = [
        ('E', 'Easy'),
        ('M', 'Medium'),
        ('H', 'Hard'),
    ]
    
    name = models.CharField(max_length=200)
    short_code = models.CharField(max_length=20, unique=True)
    statement = models.TextField()
    difficulty = models.CharField(max_length=1, choices=DIFFICULTY_CHOICES)
    
    def __str__(self):
        return f"{self.short_code}: {self.name}"
    
    def get_difficulty_display_with_icon(self):
        icons = {
            'E': '🟢',
            'M': '🟡', 
            'H': '🔴'
        }
        return f"{icons.get(self.difficulty, '')} {self.get_difficulty_display()}"
    
    class Meta:
        ordering = ['difficulty', 'name']

class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='testcases')
    input = models.TextField(blank=True)
    output = models.TextField()
    is_hidden = models.BooleanField(default=False)
    order = models.IntegerField(default=1)
    
    def __str__(self):
        visibility = "Hidden" if self.is_hidden else "Visible"
        return f"{self.problem.short_code} - Test Case {self.order} ({visibility})"
    
    class Meta:
        ordering = ['problem', 'order']
        unique_together = ['problem', 'order']

class Submission(models.Model):
    LANGUAGE_CHOICES = [
        ('py', 'Python 3'),
        ('cpp', 'C++'),
        ('c', 'C'),
        ('java', 'Java'),
    ]
    
    VERDICT_CHOICES = [
        ('AC', 'Accepted'),
        ('WA', 'Wrong Answer'),
        ('TLE', 'Time Limit Exceeded'),
        ('RE', 'Runtime Error'),
        ('CE', 'Compilation Error'),
        ('PE', 'Pending Evaluation'),
        ('IE', 'Internal Error'),
    ]
    
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code_text = models.TextField()
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='py')
    verdict = models.CharField(max_length=5, choices=VERDICT_CHOICES, default='PE')
    submitted = models.DateTimeField(auto_now_add=True)
    # Note: execution_time and memory_used fields removed temporarily
    
    def __str__(self):
        return f"{self.user.username} - {self.problem.short_code} ({self.get_verdict_display()})"
    
    def get_language_display(self):
        language_map = {
            'py': 'Python 3',
            'cpp': 'C++',
            'c': 'C',
            'java': 'Java',
        }
        return language_map.get(self.language, self.language.upper())
    
    def get_verdict_display_with_icon(self):
        icons = {
            'AC': '✅',
            'WA': '❌',
            'TLE': '⏰',
            'RE': '💥',
            'CE': '⚠️',
            'PE': '⏳',
            'IE': '🔧',
        }
        return f"{icons.get(self.verdict, '❓')} {self.get_verdict_display()}"
    
    def get_status_color_class(self):
        color_map = {
            'AC': 'status-accepted',
            'WA': 'status-rejected',
            'TLE': 'status-rejected',
            'RE': 'status-rejected',
            'CE': 'status-rejected',
            'PE': 'status-pending',
            'IE': 'status-rejected',
        }
        return color_map.get(self.verdict, 'status-pending')
    
    def is_accepted(self):
        return self.verdict == 'AC'
    
    def is_pending(self):
        return self.verdict == 'PE'
    
    def is_error(self):
        return self.verdict in ['WA', 'TLE', 'RE', 'CE', 'IE']
    
    class Meta:
        ordering = ['-submitted']
        indexes = [
            models.Index(fields=['user', 'problem']),
            models.Index(fields=['problem', 'verdict']),
            models.Index(fields=['user', 'verdict']),
        ]