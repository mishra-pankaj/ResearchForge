# ResearchForge

A multi-agent research app that searches the web, reads the sources it finds, and writes a cited report. Each user has an account, and can give feedback on the reports they generate.

**Demo video:** [Watch the walkthrough](VIDEO_LINK_HERE)

![Landing page](SCREENSHOT_LINK_HERE)

---

## What it does

A user enters a research topic. Three agents then run in order: a search agent finds sources, a scraper reads the pages, and a writer produces a report using only what was read.

- Register and log in with an email and password
- Start a research job and watch its progress
- Read the report, with the sources it was based on
- Download the report as a PDF
- Give a thumbs-up or thumbs-down reply on each report
- Revisit past reports in your history

---

## How it works

1. The frontend sends the topic to the FastAPI backend.
2. The backend saves a job in PostgreSQL and hands it to a background worker.
3. The worker runs three steps: search, scrape, and write.
4. The finished report is saved, and the frontend shows it.

The worker runs one job at a time. The local model has limited memory, and the free API tier has per-minute limits, so queuing keeps both stable.

---

## Design decisions

- **Background worker:** a run takes several minutes, so the API returns `202` at once and the frontend polls for progress.
- **One job at a time:** protects the model's memory and the free quota.
- **404 for other users' jobs:** job ids can't be probed, since another user's job looks the same as one that doesn't exist.
- **Results stored as JSON:** the report is always read as a whole, so one column is simpler than several tables.
- **Filtered sources:** only pages that were actually read and passed the checks are listed as sources.

---

## Tech stack

| Layer | Tools |
|---|---|
| Backend | FastAPI, SQLAlchemy, PostgreSQL, Pydantic |
| Auth | bcrypt, PyJWT |
| AI | LangChain, Groq or Ollama, Tavily search |
| Scraping | requests, BeautifulSoup |
| Frontend | React, Vite, Tailwind CSS, React Router, react-markdown, jsPDF |
| Testing | pytest, FastAPI TestClient |

---

## Project structure

---

## Setup

**Prerequisites:** Python 3.11, Node.js 18 or newer, and PostgreSQL.

1. **Create the database**
   ```bash
   createdb research_forge
   ```

2. **Set up the backend**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Create the environment file.** Copy `.env.example` to `.env` and fill in your values (see below).

4. **Create the tables**
   ```bash
   python -m backend.init_db
   ```

5. **Start the backend**
   ```bash
   uvicorn backend.main:app --reload
   ```

6. **Start the frontend.** In a second terminal:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

7. **Open the app** at `http://localhost:5173`.

### Environment variables

| Variable | What it does |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string, for example `postgresql+psycopg://user@localhost:5432/research_forge` |
| `JWT_SECRET` | Long random secret used to sign login tokens. Generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
| `LLM_PROVIDER` | `ollama` for a local model, or `groq` for the hosted API |
| `OLLAMA_MODEL` | Local model name, used when `LLM_PROVIDER=ollama` |
| `GROQ_API_KEY` | Groq API key, used when `LLM_PROVIDER=groq` |
| `LLM_MODEL` | Groq model name, used when `LLM_PROVIDER=groq` |
| `TAVILY_API_KEY` | Tavily search API key |
| `GLOBAL_DAILY_JOB_CAP` | Maximum jobs accepted across all users in 24 hours |

Never commit `.env`. It holds your keys.

---

## Running the tests

```bash
python -m pytest -v
```

The suite covers authentication, research routes, background jobs, input validation, password and token security, and feedback. The tests clean up the rows they create.

Current result: **69 passing**.

---

## Limits and known issues

- Some topics return few sources, because many sites block automated scrapers.
- The model has a per-minute token limit, so very large jobs can be slowed or rejected.
- The local setup needs Ollama installed and about 8 GB of memory.
- The project has no database migrations yet, so a schema change needs a manual step.

---

## Roadmap

- Deploy to a free hosting platform (Render for the backend, Vercel for the frontend, Neon for the database)
- Add database migrations with Alembic
- Add a per-user daily job limit

---

## Security

- Passwords are hashed with bcrypt, and are never stored or returned in plain text.
- Login tokens are signed with a secret kept in `.env`.
- Tokens are stored in the browser's local storage, a trade-off accepted for this project.

---

## Author

**Pankaj Mishra**
GitHub: [mishra-pankaj](https://github.com/mishra-pankaj)