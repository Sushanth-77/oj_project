from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Problem(models.Model):
    DIFFICULTY = (('E','Easy'),('M','Medium'),('H','Hard'))
    name = models.CharField(max_length=100)
    short_code = models.CharField(max_length=40,unique=True)
    statement = models.TextField()
    difficulty = models.CharField(max_length=1,choices=DIFFICULTY)

    def __str__(self):
        return self.name
    
class TestCase(models.Model):
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE, related_name='testcases')
    input = models.TextField()
    output = models.TextField()
    is_hidden = models.BooleanField(default=False)  # Add this field
    order = models.IntegerField(default=0)  # For ordering test cases

    class Meta:
        ordering = ['order']

    def __str__(self):
        visibility = "Hidden" if self.is_hidden else "Visible"
        return f'{visibility} Test Case for {self.problem.short_code}'
    
class Submission(models.Model):
    VERDICTS = (('AC','Accepted'),('WA','Wrong Answer'),('TLE','Time Limit Exceeded'),('RE','Runtime Error'),('CE','Compilation Error'))
    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code_text = models.TextField()
    verdict = models.CharField(max_length=3,choices=VERDICTS)
    submitted = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted']
        indexes = [
            models.Index(fields=['user', 'problem']),
            models.Index(fields=['user', '-submitted']),
            models.Index(fields=['problem', '-submitted']),
        ]

    def __str__(self):
        return f'Submission by {self.user} for {self.problem.short_code} - {self.verdict}'
    