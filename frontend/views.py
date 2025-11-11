from django.shortcuts import render
from django.http import JsonResponse
from AI_Slop.ollama_client import query_ollama
from AI_Slop.orchestrator import Orchestrator
from AI_Slop.agents import JobAnalysisAgent
from django.views.decorators.csrf import csrf_exempt
import PyPDF2
import docx
import io


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
        if not job_position or not job_keywords or not resume_file:
            return JsonResponse({
                'status': 'error',
                'message': 'Please provide job position, keywords, and resume'
            }, status=400)
        
        try:
            # Extract text from resume
            resume_content = extract_text_from_file(resume_file)
            
            # Initialize orchestrator and agents
            orchestrator = Orchestrator(model="llama3")
            
            # Register a generic agent or specialized job analysis agent
            job_agent = JobAnalysisAgent()
            orchestrator.register_agent(job_agent)
            
            # Execute workflow
            job_data = {
                "job_position": job_position,
                "job_keywords": job_keywords,
                "resume": resume_content
            }
            
            result = orchestrator.execute_workflow(job_data)
            
            # Extract the agent's response
            agent_response = result["agent_results"][0]["result"] if result["agent_results"] else "No response generated"
            
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
                'hint': 'Make sure Ollama is running (ollama serve) and the model is installed (ollama pull llama3)'
            }, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def ai_response(request):
    user_prompt = request.GET.get("prompt", "Say hello!")  # simple GET param example
    result = query_ollama("llama3", user_prompt)
    return JsonResponse({"response": result})