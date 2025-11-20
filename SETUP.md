# 🤖 AI Job Search Application Setup

## 📋 Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API keys for external services

## 🚀 Quick Setup

### 1. Clone and Setup Environment
```bash
cd /path/to/AI_Slop
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your actual API keys
nano .env  # or use your preferred editor
```

### 3. Required API Keys

#### Groq API (for AI processing)
1. Visit https://console.groq.com/
2. Sign up for free account (6,000 requests/day)
3. Generate API key
4. Add to `.env`: `GROQ_API_KEY=your_key_here`

#### RapidAPI JSearch (for job data)
1. Visit https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Subscribe to JSearch API (free tier available)
3. Get your RapidAPI key
4. Add to `.env`: `RAPIDAPI_KEY=your_key_here`

### 4. Run the Application
```bash
# Run Django migrations (if needed)
python manage.py migrate

# Start the development server
python manage.py runserver
```

### 5. Access the Application
Open your browser to: http://localhost:8000

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LLM_PROVIDER` | LLM provider: groq/ollama/openai | groq | No |
| `GROQ_API_KEY` | Groq AI API key | - | If using Groq |
| `OLLAMA_HOST` | Ollama server URL | http://localhost:11434 | If using Ollama |
| `OLLAMA_MODEL` | Ollama model name | llama3 | If using Ollama |
| `OPENAI_API_KEY` | OpenAI API key | - | If using OpenAI |
| `RAPIDAPI_KEY` | RapidAPI key for job search | - | Yes |
| `DEBUG` | Django debug mode | True | No |
| `SECRET_KEY` | Django secret key | auto-generated | No |
| `MAX_JOB_RESULTS` | Max jobs to fetch per search | 15 | No |
| `DEFAULT_LOCATION` | Default job search location | United States | No |

### LLM Provider Configuration (LangChain)

The application uses LangChain for unified LLM provider switching. Simply change an environment variable to switch providers:

#### Groq Cloud API (Default)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here
```
- ✅ Works anywhere with internet
- ✅ 6,000 free requests/day
- ✅ Fast inference times

#### Local Ollama
```env
LLM_PROVIDER=ollama
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3
```

**Setup Steps for Ollama:**
1. Install Ollama: https://ollama.ai/
2. Start Ollama: `ollama serve`
3. Pull model: `ollama pull llama3`
4. Update `.env` with `LLM_PROVIDER=ollama`
5. Restart application

#### OpenAI (Optional)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_key_here
```

## 📁 File Structure
```
AI_Slop/
├── .env                 # Your environment variables (not in git)
├── .env.example         # Template for environment variables
├── .gitignore          # Git ignore file (includes .env)
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── AI_Slop/           # Main Django project
│   ├── orchestrator.py # AI workflow coordinator
│   ├── agents.py      # AI task agents
│   ├── llm_client.py  # Unified LLM client (LangChain)
│   ├── jsearch_client.py # Job search API client
│   └── settings.py    # Django settings (uses .env)
├── frontend/          # Web interface
│   └── views.py      # Request handlers
└── templates/         # HTML templates
    └── index.html    # Main application interface
```

## 🛡️ Security Best Practices

1. **Never commit `.env` to git** - It's already in `.gitignore`
2. **Use different keys for development/production**
3. **Rotate API keys regularly**
4. **Set `DEBUG=False` in production**
5. **Use strong `SECRET_KEY` in production**

## 🔍 Troubleshooting

### Common Issues

**API Key Errors**
```
ERROR: GROQ_API_KEY not found in .env file
```
- Solution: Ensure `.env` file exists and contains your API key

**Module Import Errors**
```
ModuleNotFoundError: No module named 'dotenv'
```
- Solution: `pip install python-dotenv`

**Job Search Failures**
```
ERROR: RAPIDAPI_KEY environment variable not set
```
- Solution: Add your RapidAPI key to `.env`

**LLM Provider Errors**
```
ERROR: Unsupported provider: invalid_provider
```
- Solution: Set `LLM_PROVIDER` to `groq`, `ollama`, or `openai`

**Ollama Connection Issues**
```
LLM Error (ollama): Connection refused
```
- Solution: Start Ollama server with `ollama serve`

**LangChain Import Errors**
```
ModuleNotFoundError: No module named 'langchain'
```
- Solution: `pip install langchain langchain-groq langchain-ollama`

### Getting Help

1. Check your `.env` file has all required variables
2. Verify API keys are valid and have sufficient quota
3. Ensure virtual environment is activated
4. Check Django logs for detailed error messages

## 🎯 Next Steps

1. Add your API keys to `.env`
2. Test with a sample job search
3. Explore the AI agents in `agents.py`
4. Customize job search parameters in `.env`

Happy job hunting! 🚀
