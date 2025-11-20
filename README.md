# 🤖 AI Job Search Assistant

An intelligent job search and analysis system that uses AI to match resumes with real job postings, rank opportunities, and provide actionable insights for job seekers.

## 🎯 Features

- **Real Job Data Integration**: Fetches live job postings from LinkedIn, Indeed, Monster, and other major job sites via JSearch API
- **AI-Powered Analysis**: Uses Groq's cloud LLM (or local Ollama) for intelligent job matching and ranking
- **Resume Processing**: Supports PDF, DOCX, and TXT resume uploads with automatic text extraction
- **Smart Job Ranking**: Ranks jobs by best fit based on skills, experience, and preferences
- **Skills Gap Analysis**: Identifies missing skills and provides development recommendations
- **Spreadsheet Export**: Exports detailed analysis results to Excel for further review
- **Modern UI**: Sleek cyberpunk-themed interface with real-time status updates

## 🏗️ System Architecture

```
UI (Frontend) → Django Views → AI Orchestrator → [Job Search API + AI Agents] → Results
```

**Workflow:**
1. **Job Extraction Agent**: Filters relevant jobs from API data
2. **Job Ranking Agent**: Analyzes fit and ranks positions
3. **Spreadsheet Export Agent**: Generates detailed Excel reports

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API keys (see setup below)

### Installation

1. **Clone and Setup Environment**
   ```bash
   git clone https://github.com/JPeterson96/AI_Slop.git
   cd AI_Slop
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   ```bash
   cp auth.env.example auth.env
   # Edit auth.env with your API keys (see API Setup section)
   ```

3. **Run the Application**
   ```bash
   python manage.py runserver
   ```

4. **Test LangChain Integration**
   ```bash
   python test_langchain_integration.py
   ```

5. **Access Application**
   - Open browser to: http://localhost:8000
   - Upload your resume, enter job positions and skills
   - Let AI analyze and rank the best opportunities!

## 🔑 API Setup

### Required APIs

#### 1. Groq AI API (for LLM processing)
```bash
# Get free API key from https://console.groq.com/
# 6,000 requests/day free tier
export GROQ_API_KEY="your_groq_api_key_here"
```

#### 2. RapidAPI JSearch (for job data)
```bash
# Subscribe at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
# Free tier available
export RAPIDAPI_KEY="your_rapidapi_key_here"
```

### Environment Configuration

Edit your `auth.env` file with these required variables:

```env
# LLM Provider (LangChain Unified Interface)
LLM_PROVIDER=groq  # or "ollama"

# Groq Cloud API (if using groq)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

# Ollama Local API (if using ollama)  
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3

# Job Search API
RAPIDAPI_KEY=your_rapidapi_key_here
RAPIDAPI_HOST=jsearch.p.rapidapi.com

# Django Settings
SECRET_KEY=your_django_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Application Settings
MAX_JOB_RESULTS=15
DEFAULT_LOCATION=United States
```

## 📁 Project Structure

```
AI_Slop/
├── auth.env              # Environment variables (create from template)
├── requirements.txt      # Python dependencies
├── manage.py            # Django management script
├── SETUP.md             # Detailed setup instructions
├── test_resume.txt      # Sample resume for testing
├── AI_Slop/             # Main Django project
│   ├── orchestrator.py  # AI workflow coordinator (LangChain integrated)
│   ├── agents.py        # Specialized AI task agents
│   ├── llm_client.py    # Unified LLM client (LangChain)
│   ├── jsearch_client.py # Job search API integration
│   ├── ollama_client.py # Legacy local LLM integration
│   └── settings.py      # Django configuration
├── frontend/            # Web interface
│   ├── views.py        # Request handlers and file processing
│   └── urls.py         # URL routing
├── templates/           
│   └── index.html      # Modern cyberpunk UI
├── exports/            # Generated Excel reports
└── static/             # Static assets
```

## 🎮 How to Use

### 1. Job Search Process

1. **Enter Target Positions**
   - Software Engineer, Data Scientist, DevOps Engineer
   - Separate multiple positions with commas

2. **Add Skill Filters (Optional)**
   - Python, Docker, React, Machine Learning
   - Used for filtering, not job title matching

3. **Upload Resume**
   - Supports: PDF, DOCX, TXT formats
   - Automatically extracts and analyzes content

4. **Review AI Analysis**
   - Job rankings with match scores
   - Pros/cons for each position
   - Skills gap analysis
   - Downloadable Excel report

### 2. Understanding Results

- **Match Score**: 1-10 rating based on skills and requirements
- **Pros/Cons**: Specific advantages and challenges for each job
- **Skills Analysis**: Required vs. existing skills comparison
- **Recommendations**: Actionable next steps for improvement

## 🛠️ Technical Details

### AI Agents

| Agent | Purpose | Output |
|-------|---------|--------|
| **ExtractJobPostingInfo** | Filters relevant jobs from API data | Matched job listings |
| **JobRankingAndAnalysis** | Ranks jobs and analyzes fit | Scored recommendations |
| **SpreadsheetExportAgent** | Generates Excel reports | Downloadable analysis |

### LLM Integration (LangChain Unified Interface)

**🔄 Easy Provider Switching:**
```env
# Change provider instantly - no code changes needed!
LLM_PROVIDER=groq     # Groq Cloud API (default)
LLM_PROVIDER=ollama   # Local Ollama
```

**Groq Cloud API (Default)**
- ✅ Works anywhere with internet
- ✅ 6,000 free requests/day
- ✅ Fast inference times
- ✅ Zero local setup required

**Local Ollama (Alternative)**
- ✅ Complete privacy and control
- ✅ No API rate limits
- ✅ Works offline
- ⚙️ Requires local installation

### Job Data Sources

Via JSearch API integration:
- LinkedIn Jobs
- Indeed
- Monster  
- ZipRecruiter
- Glassdoor
- AngelList
- And 20+ more job sites

## 📊 Sample Output

The system generates comprehensive analysis including:

```
Job Rankings (Best to Worst Fit)

### Job #1: Senior Python Developer at TechCorp
Match Score: 8/10
Summary: Strong alignment with Python expertise and remote work preference

PROS:
- Perfect match for Python/Django skills
- Remote-first company culture  
- Competitive salary range ($120k-160k)

CONS:
- Requires 2+ years DevOps experience
- Fast-paced startup environment

Skills Analysis:
- High-demand skills: Python, Docker, Kubernetes
- Missing skills: AWS certification, Terraform
```

## 🔧 Customization

### Adding New Job Sites

Extend [`jsearch_client.py`](AI_Slop/jsearch_client.py):

```python
def search_custom_site(self, query: str) -> List[Dict]:
    # Add integration for new job site
    pass
```

### Creating Custom Agents

Extend [`agents.py`](AI_Slop/agents.py):

```python
class CustomAnalysisAgent(BaseAgent):
    def execute(self, context, orchestrator):
        # Your custom analysis logic
        return results
```

### Modifying AI Prompts

Update agent prompts in [`agents.py`](AI_Slop/agents.py) for different analysis styles or languages.

## 🐛 Troubleshooting

### Common Issues

**API Key Errors**
```
ERROR: GROQ_API_KEY not found
```
- Solution: Add API key to `auth.env` file

**No Jobs Found**
```
No matching jobs found
```  
- Check your internet connection
- Verify RapidAPI key is valid
- Try broader job position terms

**Module Import Errors**
```
ModuleNotFoundError: No module named 'PyPDF2'
```
- Solution: `pip install -r requirements.txt`

**LangChain Import Errors**
```
ModuleNotFoundError: No module named 'langchain_groq'
```
- Solution: `pip install langchain langchain-groq langchain-ollama`

**Provider Switching Issues**
```
LLM Error (ollama): Connection refused
```
- Solution: Start Ollama with `ollama serve` or switch to Groq with `LLM_PROVIDER=groq`

### Debug Mode

Enable detailed logging by setting in `auth.env`:
```env
DEBUG=True
```

## 📦 Dependencies

### Core Requirements
```
Django>=4.2.0
python-dotenv>=1.0.0
groq>=0.4.0
langchain>=1.0.0
langchain-groq>=1.0.0
langchain-ollama>=1.0.0
requests>=2.31.0
PyPDF2>=3.0.0
python-docx>=0.8.11
pandas>=2.0.0
openpyxl>=3.1.0
```

### Installation
```bash
pip install -r requirements.txt
```

### Testing LangChain Integration
```bash
# Test LLM providers and switching
python test_langchain_integration.py

# Should show:
# ✅ PASS LLM Client
# ✅ PASS Orchestrator  
# ✅ PASS Provider Switching
```

## 🚀 Deployment

### Production Settings

1. **Update Environment**
   ```env
   DEBUG=False
   SECRET_KEY=strong_production_key
   ALLOWED_HOSTS=yourdomain.com
   ```

2. **Security**
   - Use environment variables for all secrets
   - Enable HTTPS
   - Set up proper database (PostgreSQL recommended)

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Groq**: Fast LLM inference API
- **JSearch API**: Real-time job data aggregation
- **Django**: Robust web framework
- **PyPDF2**: PDF text extraction

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/JPeterson96/AI_Slop/issues)
- 📖 Documentation: See [`SETUP.md`](SETUP.md) for detailed setup

---

**Happy Job Hunting! 🎯**