"""
AI Agent Tracing System for monitoring workflow execution.
"""
import hashlib
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from .models import AgentTrace, AgentTraceContent, WorkflowSession


class AgentTracer:
    """
    Handles tracing of AI agent interactions for debugging and monitoring.
    """
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or self._generate_session_id()
        self.current_session = None
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        timestamp = str(int(time.time()))
        return f"session_{timestamp}_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"
    
    def start_session(self, job_position: str, job_keywords: str = None) -> WorkflowSession:
        """Start a new workflow session."""
        self.current_session = WorkflowSession.objects.create(
            session_id=self.session_id,
            job_position=job_position,
            job_keywords=job_keywords
        )
        return self.current_session
    
    def end_session(self, success: bool = True, total_jobs: int = None, 
                   spreadsheet_path: str = None):
        """End the current workflow session."""
        if self.current_session:
            self.current_session.end_time = datetime.now()
            self.current_session.workflow_success = success
            if total_jobs is not None:
                self.current_session.total_jobs_found = total_jobs
            if spreadsheet_path:
                self.current_session.spreadsheet_path = spreadsheet_path
            self.current_session.save()
    
    def log_interaction(self, agent_name: str, prompt: str, response: str, 
                       execution_time_ms: int, context: Dict[str, Any] = None,
                       success: bool = True, error_message: str = None,
                       llm_provider: str = 'unknown') -> AgentTrace:
        """
        Log a complete agent interaction.
        
        Args:
            agent_name: Name of the agent
            prompt: Full prompt sent to LLM
            response: Full response from LLM
            execution_time_ms: Execution time in milliseconds
            context: Additional context data
            success: Whether execution was successful
            error_message: Error message if failed
            llm_provider: LLM provider used
            
        Returns:
            AgentTrace: Created trace record
        """
        # Generate prompt hash for duplicate detection
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        
        # Create main trace record with previews
        trace = AgentTrace.objects.create(
            session_id=self.session_id,
            agent_name=agent_name,
            prompt_hash=prompt_hash,
            prompt_preview=prompt[:500] + ("..." if len(prompt) > 500 else ""),
            response_preview=response[:1000] + ("..." if len(response) > 1000 else ""),
            execution_time_ms=execution_time_ms,
            success=success,
            error_message=error_message,
            llm_provider=llm_provider,
            job_position=context.get('job_position') if context else None,
            keywords=context.get('job_keywords') if context else None
        )
        
        # Store full content separately
        AgentTraceContent.objects.create(
            trace=trace,
            full_prompt=prompt,
            full_response=response,
            context_data=context or {}
        )
        
        return trace
    
    def get_session_traces(self) -> list:
        """Get all traces for current session."""
        return list(AgentTrace.objects.filter(session_id=self.session_id).order_by('timestamp'))
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary statistics for current session."""
        traces = AgentTrace.objects.filter(session_id=self.session_id)
        
        if not traces.exists():
            return {}
        
        total_time = sum(trace.execution_time_ms for trace in traces)
        success_count = traces.filter(success=True).count()
        
        return {
            'session_id': self.session_id,
            'total_agents': traces.count(),
            'successful_agents': success_count,
            'failed_agents': traces.count() - success_count,
            'total_execution_time_ms': total_time,
            'average_execution_time_ms': total_time / traces.count() if traces.count() > 0 else 0,
            'success_rate': (success_count / traces.count() * 100) if traces.count() > 0 else 0,
            'agents_executed': list(traces.values_list('agent_name', flat=True).distinct())
        }


class TracingContextManager:
    """
    Context manager for automatic tracing of agent executions.
    """
    
    def __init__(self, tracer: AgentTracer, agent_name: str, prompt: str, 
                 context: Dict[str, Any] = None, llm_provider: str = 'unknown'):
        self.tracer = tracer
        self.agent_name = agent_name
        self.prompt = prompt
        self.context = context
        self.llm_provider = llm_provider
        self.start_time = None
        self.trace = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = int((time.time() - self.start_time) * 1000)
        
        if exc_type is None:
            # Success case - response should be set by caller
            response = getattr(self, 'response', 'No response captured')
            self.trace = self.tracer.log_interaction(
                agent_name=self.agent_name,
                prompt=self.prompt,
                response=response,
                execution_time_ms=execution_time,
                context=self.context,
                success=True,
                llm_provider=self.llm_provider
            )
        else:
            # Error case
            error_message = str(exc_val) if exc_val else str(exc_type)
            self.trace = self.tracer.log_interaction(
                agent_name=self.agent_name,
                prompt=self.prompt,
                response=f"ERROR: {error_message}",
                execution_time_ms=execution_time,
                context=self.context,
                success=False,
                error_message=error_message,
                llm_provider=self.llm_provider
            )
        
        return False  # Don't suppress exceptions
    
    def set_response(self, response: str):
        """Set the response for successful execution."""
        self.response = response