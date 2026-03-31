# 🚀 Dream Job Copilot

An **agentic AI pipeline** that takes your resume, scours the job market, gathers employee reviews, tailors your resume per role, and simulates job applications – all orchestrated with LangGraph.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Dream Job Copilot Pipeline                       │
│                          (LangGraph StateGraph)                         │
│                                                                         │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────┐   │
│  │ 1. Parse &   │──▶│ 2. Search    │──▶│ 3. Recommend Roles       │   │
│  │    Review    │   │    Jobs      │   │    (AI ranking + scoring) │   │
│  │  (ResumeAgent│   │ (JobSearch-  │   │ (RecommendationAgent)    │   │
│  │  + PyPDF2/   │   │  Agent +     │   └────────────┬─────────────┘   │
│  │   python-    │   │  Tavily)     │                │                  │
│  │   docx)      │   └──────────────┘   ┌────────────▼─────────────┐   │
│  └──────────────┘                      │ 4. Collect Feedback       │   │
│                                        │    (Interactive Rich UI)  │   │
│                                        │    (FeedbackAgent)        │   │
│                                        └────────────┬─────────────┘   │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────▼─────────────┐   │
│  │ 7. Select    │◀──│ 6. Fetch     │◀──│ 5. Refine Search         │   │
│  │    Best Jobs │   │    Employee  │   │    (preference-aware re-  │   │
│  │  (rating +   │   │    Reviews   │   │     search via Tavily)    │   │
│  │   match      │   │ (ReviewAgent)│   └──────────────────────────┘   │
│  │   combined)  │   └──────────────┘                                  │
│  └──────┬───────┘                                                      │
│         │         ┌──────────────────┐   ┌───────────────────────┐    │
│         └────────▶│ 8. Enhance       │──▶│ 9. Apply to Jobs      │    │
│                   │    Resumes       │   │    (save to disk +     │    │
│                   │ (ResumeEnhance-  │   │     log applications)  │    │
│                   │  mentAgent)      │   │ (ApplicationAgent)     │    │
│                   └──────────────────┘   └───────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Library |
|---|---|
| LLM orchestration | LangChain + LangGraph |
| Language model | OpenAI `gpt-4o-mini` |
| Job / review search | Tavily API |
| Resume parsing | PyPDF2, python-docx |
| Data models | Pydantic v2 |
| Terminal UI | Rich |
| Settings | pydantic-settings |
| Tests | pytest + pytest-mock |

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/your-org/dream-job-copilot.git
cd dream-job-copilot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
# Edit .env and add your keys:
#   OPENAI_API_KEY=sk-...
#   TAVILY_API_KEY=tvly-...
```

### 3. Run

```bash
# Interactive mode (recommended for first run)
python main.py --resume /path/to/your/resume.pdf

# Non-interactive (CI/automation)
python main.py --resume resume.docx --non-interactive

# Custom output directory
python main.py --resume resume.pdf --output-dir ./my-applications
```

---

## Pipeline Stages

| Stage | Description |
|---|---|
| **1 – Parse & Review** | Extracts text from PDF/DOCX; LLM identifies skills, experience, target roles and writes a review |
| **2 – Search Jobs** | Builds keyword queries from your profile; Tavily fetches live job postings |
| **3 – Recommend Roles** | LLM scores and ranks job postings against your resume |
| **4 – Collect Feedback** | Rich table shows top roles; you select favourites and set preferences |
| **5 – Refine Search** | Re-searches Tavily incorporating your location/industry preferences |
| **6 – Fetch Reviews** | Tavily searches Glassdoor/Indeed for each shortlisted company; LLM parses ratings |
| **7 – Select Best Jobs** | Ranks by combined score: 70% match + 30% employee rating |
| **8 – Enhance Resumes** | LLM rewrites your resume to mirror each job description's keywords |
| **9 – Apply to Jobs** | Saves tailored resumes to `./output/`; logs all applications to `applications.log` |

---

## Project Structure

```
src/
  config.py                    # pydantic-settings env config
  models.py                    # Pydantic v2 data models + LangGraph TypedDict
  agents/
    resume_agent.py            # Parse + AI-review resume
    job_search_agent.py        # Search job market via Tavily
    recommendation_agent.py    # AI-rank roles
    feedback_agent.py          # Interactive Rich feedback UI
    review_agent.py            # Fetch employee reviews
    resume_enhancement_agent.py# Tailor resume per role
    application_agent.py       # Save resumes + log applications
  pipeline/
    copilot_pipeline.py        # LangGraph StateGraph + run_pipeline()
  tools/
    resume_parser.py           # PDF/DOCX -> text
    llm_client.py              # ChatOpenAI factory
    search_client.py           # Tavily wrapper
tests/
  conftest.py                  # pytest fixtures
  test_models.py
  test_resume_agent.py
  test_job_search_agent.py
  test_recommendation_agent.py
  test_pipeline.py
main.py                        # CLI entry point
```

---

## Running Tests

```bash
pytest
# or with coverage
pytest --tb=short -q
```

All tests mock external APIs (OpenAI, Tavily) so they run offline.

---

## API Requirements

| API | Purpose | Free tier? |
|---|---|---|
| [OpenAI](https://platform.openai.com/api-keys) | LLM (gpt-4o-mini) | Pay-per-use |
| [Tavily](https://tavily.com) | Job & review search | 1,000 free calls/month |

---

## Output Files

All output is written to `./output/` (configurable via `--output-dir`):

- `resume_<Company>_<Title>_<timestamp>.txt` – enhanced resume per role
- `applications.log` – append-only log of every application attempt

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | _(required)_ | OpenAI API key |
| `TAVILY_API_KEY` | _(required)_ | Tavily search API key |
| `LLM_MODEL` | `gpt-4o-mini` | OpenAI model |
| `MAX_JOB_RESULTS` | `20` | Max results per Tavily query |
| `MAX_SHORTLISTED_JOBS` | `5` | Jobs to shortlist for applications |
| `OUTPUT_DIR` | `./output` | Directory for saved resumes |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and add tests
4. Run `pytest` and ensure all tests pass
5. Run `ruff check src/ tests/` for linting
6. Submit a pull request

---

## License

MIT – see [LICENSE](LICENSE).
