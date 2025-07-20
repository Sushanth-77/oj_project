from django.contrib import admin
from .models import CodeSubmission

@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'problem', 'language', 'timestamp']
    list_filter = ['language', 'timestamp', 'problem']
    search_fields = ['user__username', 'problem__name', 'problem__short_code']
    readonly_fields = ['timestamp']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'problem', 'language', 'timestamp')
        }),
        ('Code', {
            'fields': ('code',),
            'classes': ('collapse',)
        }),
        ('Input/Output', {
            'fields': ('input_data', 'output_data'),
            'classes': ('collapse',)
        }),
    )