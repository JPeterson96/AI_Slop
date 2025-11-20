from django.shortcuts import render
from django.http import JsonResponse
from AI_Slop.ollama_client import query_ollama
from AI_Slop.orchestrator import Orchestrator
from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
from django.views.decorators.csrf import csrf_exempt
import PyPDF2
import docx
import io
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
    if request.method == 'POST':
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
            model = os.getenv('OLLAMA_MODEL', 'llama3')
            orchestrator = Orchestrator(model=model)
            
            # Register agents per workflow: ExtractJobPostingInfo -> JobRankingAndAnalysis -> SpreadsheetExportAgent
            from AI_Slop.agents import ExtractJobPostingInfo, JobRankingAndAnalysis, SpreadsheetExportAgent
            
            extraction_agent = ExtractJobPostingInfo()
            ranking_agent = JobRankingAndAnalysis()
            export_agent = SpreadsheetExportAgent()
            
            orchestrator.register_agent(extraction_agent)
            orchestrator.register_agent(ranking_agent)
            orchestrator.register_agent(export_agent)
            
            # Execute workflow
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
            
            return JsonResponse({
                'status': 'success',
                'message': 'Job application analyzed successfully',
                'job_position': job_position,
                'job_keywords': job_keywords,
                'response': agent_response
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error: {str(e)}',
                'hint': 'Make sure GROQ_API_KEY is set in environment variables. Get your free key from https://console.groq.com/'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def ai_response(request):
    user_prompt = request.GET.get("prompt", "Say hello!")  # simple GET param example
    result = query_ollama("llama3", user_prompt)
    return JsonResponse({"response": result})