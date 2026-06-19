# 🤖 AI Hiring System

An end-to-end **Multi-Agent AI System** that automates the hiring pipeline — from CV analysis to final HR report — using LangGraph, GPT-4o, and FastAPI.

---

## 🎯 Problem Statement

HR teams waste **40+ hours per week** manually reading CVs, conducting initial interviews, and making subjective hiring decisions.

This system automates the entire pipeline with AI agents that **think, decide, and act autonomously**.

---

## 🏗️ System Architecture

```
                    ┌─────────────────────────┐
                    │      HR Interface        │
                    │   FastAPI + Dashboard    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   LangGraph Orchestrator │
                    │     (Master Brain)       │
                    └────────────┬────────────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼────────┐  ┌─────────▼────────┐  ┌─────────▼────────┐
│  CV Analyzer     │  │ Interview Agent  │  │  Scoring Agent   │
│     Agent        │→ │  (LangGraph      │→ │  (Weighted       │
│  (GPT-4o +       │  │   Loop)          │  │   Ranking)       │
│   PyMuPDF)       │  │                  │  │                  │
└──────────────────┘  └──────────────────┘  └─────────┬────────┘
                                                       │
                                            ┌─────────▼────────┐
                                            │  Report Writer   │
                                            │     Agent        │
                                            │  (HR-Ready       │
                                            │   Report)        │
                                            └──────────────────┘
```

---

## ✨ Key Features

- **Automated CV Parsing** — Extracts structured data from any PDF using PyMuPDF + GPT-4o
- **AI-Conducted Interviews** — Dynamic, personalized questions based on CV + Job Description
- **Objective Scoring** — Weighted evaluation across technical skills, job fit, and interview performance
- **Executive HR Report** — Decision-ready report with ranked candidates and hiring insights
- **Production-Ready** — Async processing, retry logic, rate limiting, and error handling

---

## 🧠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **LLM** | GPT-4o | Brain of every agent |
| **Orchestration** | LangGraph | Multi-agent workflow & loops |
| **LLM Framework** | LangChain | Chains, prompts, structured output |
| **PDF Processing** | PyMuPDF | CV text extraction |
| **API** | FastAPI | REST endpoints for HR interface |
| **Database** | PostgreSQL + asyncpg | Session & results storage |
| **Validation** | Pydantic | Structured LLM output |
| **Concurrency** | AsyncIO + Semaphore | Parallel CV processing |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- OpenAI API Key
- PostgreSQL (optional for production)

### Installation

```bash
# Clone the repository
git clone https://github.com/amira-mhmd-ml/ai-hiring-system.git
cd ai-hiring-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

### Run the System

```bash
uvicorn main:app --reload
```

Open API docs at: `http://localhost:8000/docs`

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/upload-cvs` | Upload CVs + Job Description |
| `POST` | `/analyze/{session_id}` | Start analysis pipeline |
| `GET` | `/status/{session_id}` | Check processing status |
| `GET` | `/report/{session_id}` | Get final HR report |
| `GET` | `/health` | System health check |

### Example Flow

```bash
# 1. Upload CVs
POST /upload-cvs
  - job_description: "Senior AI Engineer..."
  - files: [cv1.pdf, cv2.pdf, ...]

# 2. Start Analysis
POST /analyze/{session_id}

# 3. Check Status (poll until complete)
GET /status/{session_id}

# 4. Get Report
GET /report/{session_id}
```

---

## 📁 Project Structure

```
ai-hiring-system/
│
├── agents/
│   ├── cv_analyzer.py       # CV Analysis Agent
│   ├── interview_agent.py   # AI Interview Agent (LangGraph)
│   ├── scoring_agent.py     # Weighted Scoring Agent
│   ├── report_writer.py     # HR Report Generation Agent
│   └── orchestrator.py      # Master Orchestrator (LangGraph)
│
├── uploads/                 # Uploaded CV storage
├── main.py                  # FastAPI application
├── requirements.txt         # Dependencies
├── .env.example             # Environment variables template
└── README.md
```

---

## 🔑 Key Engineering Decisions

**Why LangGraph over LangChain?**
LangGraph supports loops and conditional edges — essential for the interview agent that needs to decide the next question based on the previous answer.

**Why Async + Semaphore?**
Processing 500 CVs sequentially would take 83+ minutes. With async concurrency (10 parallel), it drops to ~8 minutes.

**Why Weighted Scoring (not just interview answers)?**
Different candidates get different questions, making raw answer comparison unfair. Weighted scoring across CV fit (30%), interview (50%), and experience (20%) ensures objective evaluation.

**Why Exponential Backoff?**
API rate limits are inevitable at scale. Retrying immediately increases pressure. Backoff (1s → 2s → 4s) gives the API time to recover.

---

## 📊 Performance

| Metric | Value |
|---|---|
| CV Processing | ~8 min for 500 CVs (async) |
| Interview Questions | 5 dynamic questions per candidate |
| Scoring Accuracy | Weighted 3-factor evaluation |
| API Retry | 3 attempts with exponential backoff |

---

## 🛣️ Roadmap

- [ ] Voice interviews using Whisper + ElevenLabs
- [ ] PostgreSQL persistent storage
- [ ] React Dashboard for HR
- [ ] Docker deployment
- [ ] Multi-language CV support

---

## 👩‍💻 Author

Built as a portfolio project demonstrating **Multi-Agent AI Systems** using LangGraph and GPT-4o.

---

## 📄 License

MIT License
