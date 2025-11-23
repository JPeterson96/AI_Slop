from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from AI_Slop.ollama_client import query_ollama
from AI_Slop.orchestrator import Orchestrator
from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
from django.views.decorators.csrf import csrf_exempt
import PyPDF2
import docx
import io
import os
import json
import time
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv('auth.env')

# Global workflow status tracker for real-time updates
workflow_status = {}


def index(request):
    """Render the main page with the job application form."""
    return render(request, 'index.html')


def extract_text_from_file(file):
    """
    Extract text from uploaded resume file.
    Supports PDF, DOCX, and TXT formats.
    
    Args:
        file: Uploaded file object
        
    Returns:
        str: Extracted text content
    """
    filename = file.name.lower()
    
    try:
        if filename.endswith('.pdf'):
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        
        elif filename.endswith('.docx'):
            # Extract text from DOCX
            doc = docx.Document(file)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        
        elif filename.endswith('.txt'):
            # Read text file
            return file.read().decode('utf-8')
        
        else:
            return "Unsupported file format"
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"


@csrf_exempt
def submit_text(request):
    """
    Handle job application submission with position, keywords, and resume.
    Uses the orchestrator and agents to process the data.
    """
    # Add debug logging to track duplicate calls
    import time
    request_id = f"{int(time.time() * 1000)}"
    print(f"\n[REQUEST {request_id}] submit_text called")
    print(f"[REQUEST {request_id}] Method: {request.method}")
    
    if request.method == 'POST':
        print(f"[REQUEST {request_id}] Processing POST request")
        job_position = request.POST.get('job_position', '')
        job_keywords = request.POST.get('job_keywords', '')
        resume_file = request.FILES.get('resume')
        
        # Validate inputs
        if not job_position or not resume_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide job position and resume (keywords are optional)'
            }, status=400)
        
        try:
            # Extract text from resume
            resume_content = extract_text_from_file(resume_file)
            
            # Initialize orchestrator and agents following architecture diagram
            orchestrator = Orchestrator()
            
            # Setup status tracking for real-time updates
            workflow_status[request_id] = {'status': 'Starting...', 'progress': 0}
            
            original_update = orchestrator._update_status
            def tracked_update(status):
                workflow_status[request_id] = {'status': status, 'progress': 0}
                print(f"[STATUS UPDATE] {status}", flush=True)
                if original_update:
                    return original_update(status)
            
            orchestrator._update_status = tracked_update
            
            # Register agents per workflow: ExtractJobPostingInfo -> JobRankingAndAnalysis -> SpreadsheetExportAgent
            from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
            
            extraction_agent = ExtractJobPostingInfo()
            ranking_agent = JobRankingAndAnalysis()
            export_agent = SpreadsheetExportAgent()
            
            orchestrator.register_agent(extraction_agent)
            orchestrator.register_agent(ranking_agent)
            orchestrator.register_agent(export_agent)
            
            # Execute workflow
            print(f"[REQUEST {request_id}] Starting orchestrator workflow...")
            job_data = {
                "job_position": job_position,
                "job_keywords": job_keywords if job_keywords.strip() else "No specific skills filter",
                "resume": resume_content
            }
            
            result = orchestrator.execute_workflow(job_data)
            
            # Extract the agent's response from the new workflow structure
            workflow_stages = result.get("workflow_stages", {})
            
            # Get response from job ranking stage (primary) or job extraction, or final recommendations
            if workflow_stages.get("job_ranking"):
                agent_response = workflow_stages["job_ranking"] 
            elif workflow_stages.get("job_extraction"):
                agent_response = workflow_stages["job_extraction"]
            elif result.get("final_recommendations"):
                final_rec = result["final_recommendations"]
                agent_response = f"Analysis Summary: {final_rec.get('summary', 'Job search completed')}\n\nTotal jobs analyzed: {final_rec.get('total_jobs_analyzed', 0)}\n\nNext steps: {', '.join(final_rec.get('next_steps', []))}"
            else:
                agent_response = "Job search workflow completed. Please check the workflow stages for detailed results."
            
            # Extract job count and top jobs for the new UI
            job_count = result.get("final_recommendations", {}).get("total_jobs_analyzed", 0)
            top_jobs = []
            
            # Try to get job data from orchestrator context
            try:
                # First try to get the parsed data from the spreadsheet agent (most accurate)
                parsed_jobs = orchestrator.context.get("parsed_jobs_data", [])
                
                print(f"[DEBUG] Parsed jobs count: {len(parsed_jobs)}", flush=True)
                
                if parsed_jobs:
                    job_count = len(parsed_jobs)
                    for idx, job in enumerate(parsed_jobs[:5]):
                        score = job.get("Match Score", 0)
                        print(f"[DEBUG] Top job {idx+1}: {job.get('Job Title')} - Score: {score} (type: {type(score).__name__})", flush=True)
                        
                        # Ensure score is a string representation of the integer
                        score_str = str(score) if isinstance(score, int) else str(score) if score else "0"
                        
                        top_jobs.append({
                            "title": job.get("Job Title", "Unknown Position"),
                            "company": job.get("Company", "Unknown Company"),
                            "score": score_str
                        })
                else:
                    # Fallback to raw job data if parsed data not available
                    raw_job_data = orchestrator.context.get("raw_job_data", [])
                    if raw_job_data and isinstance(raw_job_data, list):
                        # Use first 5 jobs from the raw data
                        for i, job in enumerate(raw_job_data[:5]):
                            if isinstance(job, dict):
                                top_jobs.append({
                                    "title": job.get("title", f"Job Position {i+1}"),
                                    "company": job.get("company", "Company Name"),
                                    "score": f"{8-i}"  # Mock score, decreasing from 8
                                })
                            else:
                                # Fallback for non-dict job data
                                top_jobs.append({
                                    "title": str(job)[:50] if job else f"Position {i+1}",
                                    "company": "Various",
                                    "score": f"{8-i}"
                                })
                    else:
                        # Extract from text if raw data not available
                        if workflow_stages.get("job_ranking"):
                            ranking_text = workflow_stages["job_ranking"]
                            lines = ranking_text.split('\n')
                            job_counter = 0
                            
                            for line in lines:
                                if job_counter >= 5:
                                    break
                                if any(keyword in line.lower() for keyword in ['job #', 'position:', 'title:']):
                                    if ':' in line:
                                        title = line.split(':', 1)[1].strip()
                                        if title and len(title) > 5:
                                            top_jobs.append({
                                                "title": title[:60],
                                                "company": "Company Name",
                                                "score": f"{8-job_counter}"
                                            })
                                            job_counter += 1
                    
            except Exception as e:
                print(f"[DEBUG] Job extraction error: {e}")
            
            # Fallback if no jobs extracted
            if not top_jobs:
                if job_position:
                    top_jobs = [{
                        "title": f"Positions matching '{job_position}'",
                        "company": "Various Companies",
                        "score": "7"
                    }]
                else:
                    top_jobs = [{
                        "title": "No specific jobs found",
                        "company": "N/A",
                        "score": "0"
                    }]
            
            # Extract spreadsheet path from export result
            spreadsheet_path = None
            spreadsheet_export = workflow_stages.get("spreadsheet_export", "")
            if "File Created:" in spreadsheet_export:
                match = re.search(r'File Created:\*\* (.+\.xlsx)', spreadsheet_export)
                if match:
                    filename = match.group(1)
                    spreadsheet_path = f"/exports/{filename}"
            
            print(f"[REQUEST {request_id}] Workflow complete, returning response", flush=True)
            
            # Clear status tracker
            if request_id in workflow_status:
                del workflow_status[request_id]
            
            return JsonResponse({
                'status': 'success',
                'message': 'Job application analyzed successfully',
                'job_position': job_position,
                'job_keywords': job_keywords,
                'response': agent_response,
                'job_count': job_count,
                'top_jobs': top_jobs[:5],  # Ensure max 5 jobs
                'spreadsheet_path': spreadsheet_path,
                'request_id': request_id
            })
            
        except Exception as e:
            print(f"[REQUEST {request_id}] Error: {str(e)}", flush=True)
            
            # Clear status tracker
            if request_id in workflow_status:
                del workflow_status[request_id]
            
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}',
                'hint': 'Check your LLM provider configuration. For Ollama: ensure "ollama serve" is running. For Groq: set GROQ_API_KEY in auth.env'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def ai_response(request):
    user_prompt = request.GET.get("prompt", "Say hello!")  # simple GET param example
    result = query_ollama("llama3", user_prompt)
    return JsonResponse({"response": result})


def trace_dashboard(request):
    """Render the trace visualization dashboard."""
    return render(request, 'trace.html')


def workflow_status_stream(request):
    """Stream real-time workflow status updates using Server-Sent Events."""
    request_id = request.GET.get('request_id')
    
    def event_stream():
        """Generator that yields status updates."""
        max_iterations = 600  # 5 minutes max (600 * 0.5s)
        iteration = 0
        
        while iteration < max_iterations:
            if request_id in workflow_status:
                status_data = workflow_status[request_id]
                yield f"data: {json.dumps(status_data)}\n\n"
            else:
                # Workflow completed or doesn't exist
                yield f"data: {json.dumps({'status': 'complete', 'progress': 100})}\n\n"
                break
            
            time.sleep(0.5)  # Check every 500ms
            iteration += 1
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


def trace_api(request):
    """API endpoint for trace data."""
    try:
        # Check what tracing models are available
        from django.db.models import Avg, Count
        
        # First check if we have the old TraceEntry model
        try:
            from AI_Slop.models import TraceEntry
            # Use TraceEntry model with correct field names
            recent_traces = TraceEntry.objects.all().order_by('-timestamp')[:50]
            traces_data = []
            
            for trace in recent_traces:
                traces_data.append({
                    "id": str(trace.id),
                    "agent_name": trace.agent_name or "Unknown",
                    "session_id": trace.session_id or "N/A",
                    "status": "success" if trace.success else "error",
                    "execution_time_ms": trace.execution_time_ms or 0,
                    "timestamp": trace.timestamp.isoformat() if trace.timestamp else None,
                    "llm_provider": trace.llm_provider or "unknown",
                    "prompt_hash": trace.prompt_hash[:8] if trace.prompt_hash else None,
                    "error_message": trace.error_message or "",
                    "job_position": trace.job_position or "",
                    "keywords": trace.keywords or "",
                    "prompt_preview": trace.prompt_preview or "",
                    "response_preview": trace.response_preview or ""
                })
            
            # Calculate metrics
            total_traces = TraceEntry.objects.count()
            avg_time = TraceEntry.objects.filter(success=True).aggregate(avg_time=Avg('execution_time_ms'))['avg_time'] or 0
            success_count = TraceEntry.objects.filter(success=True).count()
            success_rate = (success_count / total_traces * 100) if total_traces > 0 else 0
            
            # Agent usage statistics
            agent_stats = TraceEntry.objects.values('agent_name').annotate(
                count=Count('id'),
                avg_time=Avg('execution_time_ms')
            ).order_by('-count')[:10]
            
            agents_usage = [
                {
                    "name": stat['agent_name'] or "Unknown",
                    "count": stat['count'],
                    "avg_time_ms": round(stat['avg_time'] or 0, 2)
                }
                for stat in agent_stats
            ]
            
            return JsonResponse({
                "traces": traces_data,
                "metrics": {
                    "total_traces": total_traces,
                    "avg_execution_time_ms": round(avg_time, 2),
                    "success_rate": round(success_rate, 2),
                    "agents_usage": agents_usage
                },
                "sessions": [],
                "debug_info": {
                    "model_used": "TraceEntry",
                    "fields_available": [f.name for f in TraceEntry._meta.fields]
                }
            })
            
        except ImportError:
            # Try the new AgentTrace model
            try:
                from AI_Slop.models import AgentTrace, WorkflowSession
                return JsonResponse({
                    "error": "New tracing models detected but TraceEntry preferred for compatibility",
                    "traces": [],
                    "metrics": {"total_traces": 0, "avg_execution_time_ms": 0, "success_rate": 0, "agents_usage": []},
                    "sessions": []
                })
            except ImportError:
                return JsonResponse({
                    "error": "No tracing models available - tracing infrastructure not set up",
                    "traces": [],
                    "metrics": {"total_traces": 0, "avg_execution_time_ms": 0, "success_rate": 0, "agents_usage": []},
                    "sessions": []
                })
        
    except Exception as e:
        return JsonResponse({
            "error": f"Failed to fetch trace data: {str(e)}",
            "traces": [],
            "metrics": {"total_traces": 0, "avg_execution_time_ms": 0, "success_rate": 0, "agents_usage": []},
            "sessions": [],
            "debug_info": {"exception_type": type(e).__name__}
        })

