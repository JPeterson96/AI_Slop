"""
Django models for AI agent tracing and workflow monitoring.
"""
from django.db import models
import uuid
from datetime import datetime


class AgentTrace(models.Model):
    """
    Stores high-level information about agent executions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session_id = models.CharField(max_length=100, db_index=True)
    agent_name = models.CharField(max_length=100, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Prompt and response previews (truncated for quick viewing)
    prompt_hash = models.CharField(max_length=64)  # SHA256 hash for duplicate detection
    prompt_preview = models.TextField(max_length=500)  # First 500 chars
    response_preview = models.TextField(max_length=1000)  # First 1000 chars
    
    # Execution metrics
    execution_time_ms = models.IntegerField()
    token_count = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(null=True, blank=True)
    
    # Context metadata
    llm_provider = models.CharField(max_length=50, default='unknown')
    job_position = models.CharField(max_length=200, null=True, blank=True)
    keywords = models.TextField(null=True, blank=True)
    
    class Meta:
        db_table = 'agent_traces'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['agent_name', 'timestamp']),
            models.Index(fields=['success', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.agent_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class AgentTraceContent(models.Model):
    """
    Stores full content separately to avoid bloating the main traces table.
    """
    trace = models.OneToOneField(AgentTrace, on_delete=models.CASCADE, related_name='content')
    full_prompt = models.TextField()
    full_response = models.TextField()
    context_data = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'agent_trace_content'


class WorkflowSession(models.Model):
    """
    Groups related agent traces into workflow sessions.
    """
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    # Workflow metadata
    job_position = models.CharField(max_length=200)
    job_keywords = models.TextField(null=True, blank=True)
    total_jobs_found = models.IntegerField(null=True, blank=True)
    workflow_success = models.BooleanField(default=False)
    
    # Results
    spreadsheet_path = models.CharField(max_length=500, null=True, blank=True)
    
    class Meta:
        db_table = 'workflow_sessions'
        ordering = ['-start_time']

    def __str__(self):
        return f"Session {self.session_id} - {self.job_position}"

    @property
    def duration_ms(self):
        """Calculate session duration in milliseconds."""
        if self.end_time and self.start_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None

    @property  
    def agent_count(self):
        """Count of agents executed in this session."""
        return AgentTrace.objects.filter(session_id=self.session_id).count()


class TraceEntry(models.Model):
    """
    Simplified trace model for compatibility with existing trace infrastructure.
    """
    session_id = models.CharField(max_length=255, blank=True)
    agent_name = models.CharField(max_length=255, blank=True)
    job_position = models.CharField(max_length=255, blank=True)
    keywords = models.CharField(max_length=500, blank=True)
    prompt_preview = models.TextField(blank=True)
    response_preview = models.TextField(blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    execution_time_ms = models.IntegerField(default=0)
    token_count = models.IntegerField(default=0)
    llm_provider = models.CharField(max_length=100, blank=True, default='groq')
    prompt_hash = models.CharField(max_length=255, blank=True)
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trace_entries'
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.agent_name} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"