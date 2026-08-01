# AI Copilot Restriction System - Technical Documentation

## Executive Summary

This document provides a comprehensive technical explanation of how the AI Copilot in the HirePilot AI Recruitment and Talent Management Copilot application is restricted to answer **only** Recruitment & Talent Management related questions. The system implements a multi-layered defense-in-depth approach combining system prompts, backend validation, context-aware prompt building, and response validation to ensure the AI never exposes confidential information or answers out-of-scope questions.

---

## 1. Complete Workflow: From User Question to AI Response

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           USER QUESTION                                              │
│                    "Show all employees in Engineering"                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        AI COPILOT UI (Frontend)                                      │
│  • ai_copilot_panel.py - Floating panel component                                   │
│  • Captures user input, manages chat history in session state                       │
│  • Renders messages with typewriter effect                                          │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND CHAT SERVICE (assistant_service.py)                      │
│  • init_assistant_state() - Initializes session state                               │
│  • build_context_prompt() - Builds enriched prompt with context                     │
│  • process_user_input() - Adds user message, triggers AI response                   │
│  • generate_ai_response() - Calls backend via LLM service                           │
│  • get_current_page_context() - Gets current page for context awareness             │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND CHAT API (backend/api/routes/copilot.py)                  │
│  • POST /copilot/chat - Receives message, session_id, history, context              │
│  • Validates input (non-empty message)                                              │
│  • Delegates to ChatService for processing                                          │
│  • Returns ChatResponse with AI reply                                               │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    CHAT SERVICE (backend/services/chat_service.py)                   │
│  • ChatService class - Business logic for chat endpoint                             │
│  • Manages per-session conversation history (bounded: 20 messages, 100 sessions)    │
│  • _get_history() / _append() - Session management                                  │
│  • chat() - Main entry point: retrieves history → calls Ollama → stores reply       │
│  • Error handling with user-friendly messages                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    OLLAMA SERVICE (backend/services/ollama_service.py)               │
│  • OllamaClient class - HTTP client for Ollama API                                  │
│  • chat() - Sends prompt to LLM with system prompt + history + user message         │
│  • SYSTEM_PROMPT - Loaded from frontend/prompts/assistant_system_prompt.md          │
│  • WORKFLOW_PROMPT - Loaded from frontend/prompts/workflow.md                       │
│  • FAQ_PROMPT - Loaded from frontend/prompts/faq.md                                 │
│  • FULL_SYSTEM_PROMPT = SYSTEM_PROMPT + WORKFLOW_PROMPT + FAQ_PROMPT                │
│  • Calls Ollama at http://localhost:11434/api/generate                              │
│  • Model: qwen2.5-coder:7b                                                          │
│  • Temperature: 0.3, max tokens: 512                                                │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    LARGE LANGUAGE MODEL (Ollama - qwen2.5-coder:7b)                  │
│  • Receives: FULL_SYSTEM_PROMPT + Current Page Context + History + User Question    │
│  • Generates response based on system prompt constraints                            │
│  • Returns plain text response                                                      │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                    RESPONSE VALIDATION & RETURN                                      │
│  • ChatService receives reply from Ollama                                           │
│  • Appends to session history (user + assistant)                                    │
│  • Returns response to API route                                                    │
│  • API returns ChatResponse to frontend                                             │
│  • Frontend appends to chat history, re-renders with typewriter effect              │
└─────────────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           AI RESPONSE DISPLAYED                                      │
│  "Here are the employees in the Engineering department:                             │
│  1. John Smith - Senior Software Engineer                                           │
│  2. Jane Doe - DevOps Engineer                                                      │
│  3. Bob Wilson - Frontend Developer                                                 │
│  (Data retrieved from live database context)"                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. System Prompt - The Foundation of Restrictions

### 2.1 Where the System Prompt is Stored

**Primary System Prompt File:** `frontend/prompts/assistant_system_prompt.md`

This file contains the core identity, capabilities, and constraints of the AI Assistant.

**Additional Knowledge Files (Loaded & Concatenated):**
- `frontend/prompts/workflow.md` - End-to-end recruitment workflow
- `frontend/prompts/faq.md` - Frequently asked questions
- `frontend/prompts/knowledge_base.md` - Project overview, modules, tech stack
- `frontend/prompts/navigation.md` - Navigation guide and user flows

### 2.2 Which File Loads It

**Backend:** `backend/services/ollama_service.py` - `_load_prompt()` function loads all prompt files at module initialization and concatenates them into `FULL_SYSTEM_PROMPT`.

```python
PROMPTS_DIR = Path(__file__).parent.parent.parent / "frontend" / "prompts"

def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""

SYSTEM_PROMPT = _load_prompt("assistant_system_prompt.md")
WORKFLOW_PROMPT = _load_prompt("workflow.md")
FAQ_PROMPT = _load_prompt("faq.md")

FULL_SYSTEM_PROMPT = f"""
{SYSTEM_PROMPT}

==================================================
KNOWLEDGE BASE: WORKFLOWS
==================================================
{WORKFLOW_PROMPT}

==================================================
KNOWLEDGE BASE: FAQ
==================================================
{FAQ_PROMPT}
"""
```

**Frontend:** `frontend/services/assistant_service.py` - `build_context_prompt()` builds a dynamic prompt that includes the system prompt plus runtime context.

### 2.3 Why the System Prompt is Required

The system prompt serves as the **constitutional document** for the AI's behavior. It:

1. **Defines Identity** - "You are HirePilot AI Assistant, an intelligent recruitment copilot"
2. **Establishes Scope** - Explicitly lists what the AI CAN answer (recruitment, HR, candidates, jobs, interviews, etc.)
3. **Enforces Constraints** - "Never hallucinate features", "Do NOT provide access to sensitive data", "Do NOT execute actions on behalf of the user"
4. **Provides Domain Knowledge** - Recruitment workflow, page-specific guidance, module capabilities
5. **Sets Response Style** - Concise, professional, step-by-step, markdown formatting

### 2.4 How It Controls the Model

The system prompt is sent as the **first message** in every conversation to the LLM (via Ollama's `prompt` parameter). The LLM treats this as its "instructions" or "constitution" that persists for the entire conversation. Because it's prepended to every request, the model **cannot ignore it** - it's the framing context for every response.

### 2.5 How It Keeps AI Focused on the Project

The system prompt explicitly enumerates:
- **Allowed topics**: Recruitment, Talent Acquisition, Candidate Management, Resume Parsing, ATS Score, Candidate Ranking, Job Description Generation, Interview Scheduling, Employee Management, Analytics, Reports, Dashboard, Navigation, Application Features
- **Forbidden topics**: Politics, Sports, Movies, Religion, History, Programming (unrelated), Mathematics, Science, Cooking, Medical/Legal/Investment advice, Cryptocurrency, News, Weather, Gaming, General Knowledge, Homework, Personal Opinions, Jokes
- **Behavioral rules**: Never fabricate data, only use database info/uploaded resume/user question/recruitment knowledge/project features

---

## 3. Project Restriction Rules - Allowed Knowledge Scope

The AI is explicitly instructed to answer **ONLY** questions related to these domains:

| Category | Specific Topics |
|----------|-----------------|
| **Recruitment** | Hiring process, talent acquisition, sourcing, pipeline management |
| **Talent Management** | Employee development, performance, skills, projects, career growth |
| **Employees** | Employee records, onboarding, conversion from candidates, employee management |
| **Candidates** | Search, filter, match scoring, skill matching, status tracking, notes, tags |
| **Jobs** | Create/edit/publish/archive jobs, job descriptions, department management |
| **Resume Parser** | Upload PDF/DOCX/TXT/CSV, extract skills/experience/education, parse contacts |
| **AI Screening** | Automated evaluation, custom criteria, batch screening, match scores |
| **Interviews** | Schedule, manage slots, collect feedback, track status |
| **Dashboard** | Metrics, KPIs, hiring velocity, recent activity, quick actions |
| **Reports** | Generate recruitment reports, hiring metrics, export CSV/PDF |
| **Analytics** | Time-to-hire, source effectiveness, diversity metrics, custom reports |
| **Employee Skills** | Skill tracking, gap analysis, development planning |
| **Employee Performance** | Reviews, feedback, goal tracking, promotion readiness |
| **Employee Projects** | Project assignments, contributions, portfolio |
| **AI Insights** | Executive summary, technical/leadership assessment, promotion readiness, risk level |
| **Hiring Process** | End-to-end workflow, best practices, phase transitions |
| **Offer Letters** | Generation, email delivery, attachment handling, negotiation |
| **Communication Module** | Email generation, rejection emails, offer letters, notifications |
| **Navigation** | Page-to-page guidance, feature location, user flows |
| **Project Features** | Module capabilities, configuration, settings |

### Why These Topics Form the Allowed Scope

These topics directly map to the **application's actual modules and features** as defined in:
- `frontend/prompts/knowledge_base.md` - Lists all 13 modules
- `frontend/prompts/workflow.md` - Defines the 6-phase recruitment process
- `frontend/prompts/navigation.md` - Documents all navigation paths

The scope is **closed** - the AI cannot answer about anything not implemented in the application. This prevents hallucination of non-existent features and keeps responses grounded in reality.

---

## 4. Out-of-Scope Detection & Handling

### 4.1 How Unrelated Questions Are Recognized

The system uses a **multi-layered detection approach**:

#### Layer 1: System Prompt (Primary Defense)
The `FULL_SYSTEM_PROMPT` in `ollama_service.py` contains an explicit **"OUT OF SCOPE QUESTIONS"** section listing 25+ forbidden categories. The LLM is instructed:
> "You must NOT answer questions about: [list]... Do not provide any additional information about the out-of-scope topic."

#### Layer 2: Explicit Refusal Template
The system prompt provides a **canned refusal response** that the LLM must use verbatim:
> "I'm HirePilot AI, designed specifically for the AI Recruitment and Talent Management Copilot. I can help you with: [list of allowed topics]. Please ask me something related to recruitment, hiring, HR processes, your uploaded resume, or this application."

#### Layer 3: Prompt Builder Context Injection (Frontend)
`frontend/services/assistant_service.py` → `build_context_prompt()` injects:
- Current page context
- Session context (selected job/candidate/interview)
- Knowledge base search results relevant to the query

This **grounds** the LLM in project-specific context, making out-of-scope answers less likely.

#### Layer 4: Knowledge Base Search
`frontend/services/knowledge_service.py` → `search_knowledge_base()` searches the project's knowledge base for relevant terms. If no matches found, the context explicitly states "No specific knowledge base entries found for this query."

### 4.2 Enforcement Mechanism

| Layer | Enforcement Point | Mechanism |
|-------|-------------------|-----------|
| System Prompt | LLM Inference | Constitutional instructions in every prompt |
| Prompt Builder | Request Construction | Context grounding + knowledge base injection |
| Knowledge Service | Pre-processing | Semantic relevance filtering |
| Backend Validation | API Layer | Input validation (non-empty message) |

**All layers work together** - the system prompt is the primary enforcement, but the prompt builder and knowledge service reduce the chance of the LLM even considering out-of-scope answers by providing strong in-scope context.

### 4.3 Why the AI Refuses

The AI refuses because the system prompt **explicitly commands it to refuse** with a specific template. The LLM (qwen2.5-coder:7b) is trained to follow system instructions. When a user asks "Who won the FIFA World Cup?", the LLM:
1. Receives the system prompt forbidding sports questions
2. Recognizes the query matches a forbidden category
3. Outputs the prescribed refusal response instead of answering

---

## 5. Friendly Refusal Response

### 5.1 Example Refusal Response

> **I'm HirePilot AI, designed specifically for the AI Recruitment and Talent Management Copilot.**
>
> **I can help you with:**
> - Resume Analysis
> - Resume Parsing
> - ATS Score
> - Candidate Screening
> - Hiring Recommendations
> - Candidate Comparison
> - Job Descriptions
> - Interview Scheduling
> - Employee Management
> - Recruitment Analytics
> - Dashboard Insights
> - Application Navigation
>
> **Please ask me something related to recruitment, hiring, HR processes, your uploaded resume, or this application.**

### 5.2 Where This Behavior Is Defined

**Primary Definition:** `backend/services/ollama_service.py` → `SYSTEM_PROMPT` variable (loaded from `frontend/prompts/assistant_system_prompt.md`)

The refusal template is embedded in the system prompt under the section:
```
==================================================
WHEN USER ASKS OUT OF SCOPE QUESTION
==================================================
```

### 5.3 How It's Consistently Applied

1. **Every request** to Ollama includes the full system prompt
2. The system prompt is **static and immutable** at runtime (loaded once at startup)
3. The LLM **cannot override** its own system instructions
4. The refusal template is **explicitly provided** in the prompt, so the LLM copies it rather than improvising

---

## 6. Prompt Building Process

### 6.1 Final Prompt Structure Sent to LLM

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM PROMPT (FULL_SYSTEM_PROMPT)           │
│  • Identity: HirePilot AI Assistant                             │
│  • Capabilities: 10 listed items                                │
│  • Context Awareness: Current page, module, recent actions      │
│  • Response Guidelines: Concise, bullets, steps, no hallucination│
│  • Recruitment Workflow: 11-phase process                       │
│  • Page-Specific Guidance: All 13 modules                       │
│  • Knowledge Base: Project overview, modules, tech stack        │
│  • Constraints: No sensitive data, no actions, privacy first    │
│  • OUT OF SCOPE RULES: 25+ forbidden categories + refusal template│
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROJECT RESTRICTIONS (Embedded in System)    │
│  • Only answer recruitment/HR/application questions             │
│  • Never fabricate candidates/jobs/employees/interviews         │
│  • Only use: Database info, Uploaded resume, User question,     │
│    Recruitment knowledge, Project features                      │
│  • If unavailable: Clearly state unavailability                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LIVE DATABASE CONTEXT (Dynamic)              │
│  • Current page: e.g., "Employees"                              │
│  • Page description: "Manage hired candidates as employees"     │
│  • Available actions: ["View employees", "Onboard employee",    │
│    "Convert candidate"]                                         │
│  • Session context: Selected job/candidate/interview/employee   │
│  • Search query from UI                                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT PAGE CONTEXT (Dynamic)               │
│  • Page-specific guidance from navigation.md                    │
│  • Module-specific capabilities                                 │
│  • Common user flows for this page                              │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    USER QUESTION (Dynamic)                      │
│  "Show all employees in Engineering"                            │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Purpose of Each Section

| Section | Purpose | Safety/Quality Impact |
|---------|---------|----------------------|
| **System Prompt** | Constitutional instructions | Prevents hallucination, defines scope, sets tone |
| **Project Restrictions** | Hard boundaries | Enforces domain-only responses, blocks sensitive data |
| **Live Database Context** | Grounding in reality | Ensures answers reflect actual data, not imagination |
| **Current Page Context** | Contextual relevance | Tailors answers to where user is, enables navigation help |
| **User Question** | The actual query | The target of the response |

### 6.3 Why This Structure Improves Quality & Safety

1. **Layered Defense** - Multiple independent restrictions (system prompt + context + knowledge base)
2. **Grounding** - Live context prevents hallucination of database records
3. **Relevance** - Page context ensures answers are actionable where the user is
4. **Consistency** - Same system prompt every time = consistent behavior
5. **Auditability** - Prompt structure is visible and reviewable in code

---

## 7. Database Context & RAG Architecture

### 7.1 How AI Retrieves Only Required Information

The system implements a **lightweight RAG (Retrieval-Augmented Generation)** pattern:

#### Intent Detection
- **Frontend:** `assistant_service.py` → `build_context_prompt()` analyzes user message
- **Knowledge Service:** `knowledge_service.py` → `search_knowledge_base(query)` searches project KB
- **Context Service:** `context_service.py` → `get_page_context()`, `get_session_context()` extracts runtime state

#### Context Retrieval
```python
# In assistant_service.py - build_context_prompt()
knowledge_snippets = KnowledgeService.search_knowledge_base(user_message)
knowledge_context = "\n".join(knowledge_snippets) if knowledge_snippets else "No specific knowledge base entries found for this query."

page_context = ContextService.get_page_context(current_page)
session_context = ContextService.get_session_context()
```

#### Relevant Record Selection
- **Knowledge Base:** Keyword matching against project documentation (modules, workflow, FAQ)
- **Session State:** Selected job/candidate/interview/employee IDs from `st.session_state`
- **Page Context:** Static mapping of page → description + available actions

#### Prompt Injection
The retrieved context is **injected into the prompt** as structured sections (see 6.1), not as raw database dumps.

### 7.2 Why This Follows RAG Architecture

| RAG Component | Implementation |
|---------------|----------------|
| **Retriever** | `KnowledgeService.search_knowledge_base()` + `ContextService.get_*_context()` |
| **Augmentation** | `build_context_prompt()` injects retrieved snippets into system prompt |
| **Generator** | Ollama LLM (qwen2.5-coder:7b) generates response from augmented prompt |
| **No Vector DB** | Uses keyword search on structured knowledge base (lightweight, no embeddings needed) |
| **No Full DB Dump** | Only relevant snippets + session state sent, never entire database |

**Key Principle:** The LLM never sees raw database tables. It receives **curated, relevant context** assembled by the backend services.

---

## 8. Security Restrictions - Preventing Sensitive Information Exposure

### 8.1 Protected Information Categories

| Category | Protection Mechanism |
|----------|---------------------|
| **API Keys** | Never included in prompts; stored in backend `.env`, not sent to LLM |
| **Passwords** | Never in prompts; hashed in DB, never exposed |
| **Environment Variables** | Backend-only; `ollama_service.py` uses constants, not `os.environ` in prompts |
| **Database Credentials** | Backend-only; SQLite file path in config, not in prompts |
| **SQL Queries** | Never generated by LLM; backend uses SQLAlchemy ORM |
| **Hidden System Prompts** | System prompt is visible in codebase; no "hidden" instructions |
| **Internal Instructions** | All instructions in `assistant_system_prompt.md` (reviewable) |
| **Secret Configuration** | `backend/core/config.py` - not sent to LLM |
| **Private Files** | Uploaded resumes parsed by backend; only extracted text sent to LLM |

### 8.2 Implementation Layers

| Layer | File | Protection |
|-------|------|------------|
| **System Prompt** | `frontend/prompts/assistant_system_prompt.md` | "Do NOT provide access to sensitive data", "Prioritize user privacy and data security" |
| **Prompt Builder** | `frontend/services/assistant_service.py` | Only injects: page context, session IDs, knowledge snippets - **never** secrets |
| **Backend Validation** | `backend/api/routes/copilot.py` | Input validation (non-empty message); no secret leakage in responses |
| **Response Validation** | `backend/services/chat_service.py` | Returns only LLM text; no internal state exposed |
| **Ollama Service** | `backend/services/ollama_service.py` | System prompt loaded from file; constants for URLs/model; no env vars in prompt |

### 8.3 Defense-in-Depth Summary

The system uses **ALL FOUR LAYERS** together:
1. **System Prompt** - Tells LLM what NOT to reveal
2. **Prompt Builder** - Never includes secrets in constructed prompt
3. **Backend Validation** - Sanitizes inputs/outputs at API boundary
4. **Response Validation** - Chat service returns only the LLM's text response

---

## 9. Complete Workflow Examples

### Example 1: In-Scope Question

**User:** "Show all employees in Engineering."

#### Step-by-Step Execution:

| Step | Component | Action |
|------|-----------|--------|
| 1 | **AI Copilot UI** (`ai_copilot_panel.py`) | User types message, clicks Send |
| 2 | **Frontend Chat Service** (`assistant_service.py`) | `process_user_input()` adds user message to session state, sets `ai_assistant_typing=True`, triggers rerun |
| 3 | **Frontend Chat Service** | `generate_ai_response()` called on rerun → `build_context_prompt()` constructs prompt |
| 4 | **Context Retrieval** | `ContextService.get_current_page()` → "Employees"<br>`ContextService.get_page_context("Employees")` → `{actions: ["View employees", "Onboard employee", "Convert candidate"]}`<br>`ContextService.get_session_context()` → `{selected_employee_id: None, ...}`<br>`KnowledgeService.search_knowledge_base("employees engineering")` → relevant KB snippets |
| 5 | **Prompt Construction** | Builds full prompt: SYSTEM_PROMPT + Page Context + Session Context + KB Snippets + User Question |
| 6 | **LLM Service** (`llm_service.py`) | `chat()` sends POST to `http://localhost:8000/copilot/chat` with message, history, context |
| 7 | **Backend API** (`copilot.py`) | `chat_with_copilot()` validates → calls `chat_service.chat(session_id, message)` |
| 8 | **Chat Service** (`chat_service.py`) | Retrieves session history → calls `ollama_service.chat(message, history)` |
| 9 | **Ollama Service** (`ollama_service.py`) | Constructs final prompt: `FULL_SYSTEM_PROMPT` + history + user message → POST to Ollama |
| 10 | **LLM (Ollama)** | Generates response using database context (if provided by backend) and system prompt constraints |
| 11 | **Response Path** | Ollama → ChatService → API → LLM Service → Frontend → `append_assistant_message()` → UI render |

**Final Answer:** "Here are the employees in the Engineering department: [list from actual database]"

---

### Example 2: Out-of-Scope Question

**User:** "Who won the FIFA World Cup?"

#### Step-by-Step Execution:

| Step | Component | Action |
|------|-----------|--------|
| 1-5 | **Same as Example 1** | Prompt built with system prompt + context |
| 6 | **LLM Receives Prompt** | System prompt contains explicit OUT OF SCOPE rules listing "Sports" as forbidden |
| 7 | **LLM Processing** | Recognizes "FIFA World Cup" → matches "Sports" category in forbidden list |
| 8 | **LLM Response Generation** | Instead of answering, outputs the prescribed refusal template from system prompt |
| 9-11 | **Response Path** | Same return path |

**Final Answer:**
> **I'm HirePilot AI, designed specifically for the AI Recruitment and Talent Management Copilot.**
>
> **I can help you with:**
> - Resume Analysis
> - Resume Parsing
> - ATS Score
> - Candidate Screening
> - Hiring Recommendations
> - Candidate Comparison
> - Job Descriptions
> - Interview Scheduling
> - Employee Management
> - Recruitment Analytics
> - Dashboard Insights
> - Application Navigation
>
> **Please ask me something related to recruitment, hiring, HR processes, your uploaded resume, or this application.**

---

## 10. File-by-File Explanation of Restriction Mechanism

### 10.1 Backend Files

| File | Purpose | Responsibility | Inputs | Outputs | Interaction |
|------|---------|----------------|--------|---------|-------------|
| `backend/services/ollama_service.py` | **Core LLM Interface** | Loads system prompts, calls Ollama API, enforces system prompt | User message, history | LLM response text | Called by `chat_service.py`; loads prompts from `frontend/prompts/` |
| `backend/services/chat_service.py` | **Session & History Manager** | Manages per-session conversation history (bounded), error handling | Session ID, user message | Assistant reply | Called by `copilot.py`; uses `ollama_service` |
| `backend/api/routes/copilot.py` | **Chat API Endpoint** | HTTP interface: validates input, calls ChatService, returns JSON | POST `/copilot/chat` {message, session_id} | ChatResponse {response} | Called by frontend `llm_service.py` |
| `backend/api/routes/assistant.py` | **Assistant API Endpoint** | Alternative chat endpoint with richer context (page, history) | POST `/assistant/chat` {message, session_id, history, current_page} | AssistantChatResponse | Called by frontend `assistant_service.py` via `llm_service` |
| `backend/services/assistant_service.py` | **Backend Assistant Logic** | Processes messages with full context, calls Ollama directly | Message, session_id, current_page, history | CopilotResponse (reply + action metadata) | Used by `/assistant/chat` route; loads prompts from `frontend/prompts/` |

### 10.2 Frontend Files

| File | Purpose | Responsibility | Inputs | Outputs | Interaction |
|------|---------|----------------|--------|---------|-------------|
| `frontend/components/ai_copilot_panel.py` | **Main UI Component** | Renders floating chat panel, handles user input, displays messages | Session state | UI events | Uses `assistant_service.py` for logic |
| `frontend/services/assistant_service.py` | **Frontend Chat Logic** | Manages chat state, builds context prompts, calls backend | User message, session state | AI response (via backend) | Calls `llm_service.chat()`; uses `ContextService`, `KnowledgeService` |
| `frontend/services/llm_service.py` | **Backend HTTP Client** | Sends chat requests to backend API | Message, history, context | Response text | Called by `assistant_service.py`; POSTs to `/copilot/chat` |
| `frontend/services/context_service.py` | **Runtime Context Provider** | Extracts current page, session selections, page-specific actions | `st.session_state` | Page context dict, session context dict | Called by `assistant_service.build_context_prompt()` |
| `frontend/services/knowledge_service.py` | **Knowledge Base Search** | Keyword search against project documentation | User query | Relevant KB snippets | Called by `assistant_service.build_context_prompt()` |
| `frontend/services/copilot_service.py` | **Alternative Copilot Logic** | Session persistence (SQLite), resume context, message handling | User message, file uploads | Response with actions | Used by `ai_copilot.py` (legacy) |
| `frontend/prompts/assistant_system_prompt.md` | **System Prompt (Primary)** | Defines AI identity, capabilities, constraints, refusal template | N/A (static file) | System prompt text | Loaded by `ollama_service.py` and `assistant_service.py` |
| `frontend/prompts/workflow.md` | **Workflow Knowledge** | End-to-end recruitment process documentation | N/A | Workflow text | Concatenated into `FULL_SYSTEM_PROMPT` |
| `frontend/prompts/faq.md` | **FAQ Knowledge** | Common questions and answers | N/A | FAQ text | Concatenated into `FULL_SYSTEM_PROMPT` |
| `frontend/prompts/knowledge_base.md` | **Project Knowledge** | Modules, tech stack, features, database schema | N/A | KB text | Concatenated into `FULL_SYSTEM_PROMPT`; searched by `knowledge_service.py` |
| `frontend/prompts/navigation.md` | **Navigation Guide** | Page flows, user journeys, quick tips | N/A | Navigation text | Used for page context in `context_service.py` |

### 10.3 How Each File Contributes to Restrictions

| File | Restriction Contribution |
|------|-------------------------|
| `ollama_service.py` | **Primary enforcement** - Loads and sends system prompt with explicit out-of-scope rules to every LLM call |
| `assistant_system_prompt.md` | **Constitutional document** - Defines allowed/forbidden topics, refusal response, behavioral constraints |
| `chat_service.py` | **Session isolation** - Prevents cross-session contamination; bounds history to prevent prompt injection via history stuffing |
| `copilot.py` (route) | **Input validation** - Rejects empty messages; ensures only text reaches LLM |
| `assistant_service.py` (frontend) | **Context grounding** - Injects current page/session/KB context to keep LLM focused on relevant domain |
| `context_service.py` | **Scope limiting** - Only exposes page actions and session IDs, never database internals or secrets |
| `knowledge_service.py` | **Relevance filtering** - Only project-relevant KB snippets injected, reducing hallucination surface |
| `llm_service.py` | **Transport security** - Only sends user message + history + context; never sends secrets |
| `ai_copilot_panel.py` | **UI constraint** - User can only input text; no file upload to LLM, no code execution |

---

## 11. Workflow Diagram with Detailed Explanations

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                    USER                                              │
│                          Types question in chat input                                │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                          AI COPILOT UI (ai_copilot_panel.py)                         │
│  • Renders floating panel with message history                                       │
│  • Captures user input via st.chat_input()                                           │
│  • Displays messages with typewriter effect                                          │
│  • Manages minimize/close state                                                      │
│  • Calls assistant_service.process_user_input() on submit                            │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    FRONTEND CHAT SERVICE (assistant_service.py)                       │
│  • init_assistant_state() - Initializes session state with welcome message           │
│  • process_user_input() - Appends user message, sets typing flag, triggers rerun    │
│  • generate_ai_response() - Called on rerun when typing=True                        │
│    → build_context_prompt() - Constructs enriched prompt                            │
│    → llm_service.chat() - Sends to backend                                          │
│    → append_assistant_message() - Adds AI response to history                       │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    CONTEXT RETRIEVAL (context_service.py + knowledge_service.py)     │
│  • ContextService.get_current_page() → "Employees"                                   │
│  • ContextService.get_page_context() → {description, actions}                        │
│  • ContextService.get_session_context() → {selected_job_id, selected_candidate_id}   │
│  • KnowledgeService.search_knowledge_base(query) → relevant KB snippets              │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    PROMPT BUILDER (assistant_service.build_context_prompt)           │
│  Constructs:                                                                         │
│  SYSTEM_PROMPT (from assistant_system_prompt.md)                                     │
│  + PAGE_CONTEXT (current page, description, actions)                                 │
│  + SESSION_CONTEXT (selected entities)                                               │
│  + KNOWLEDGE_CONTEXT (relevant KB snippets)                                          │
│  + USER_MESSAGE                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    BACKEND CHAT API (backend/api/routes/copilot.py)                  │
│  • POST /copilot/chat                                                                │
│  • Validates: message not empty                                                      │
│  • Extracts: session_id (or generates default)                                       │
│  • Delegates to: chat_service.chat(session_id, message)                              │
│  • Returns: ChatResponse(response=reply)                                             │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    CHAT SERVICE (backend/services/chat_service.py)                   │
│  • ChatService class (singleton)                                                     │
│  • _get_history(session_id) - Retrieves or creates session history (max 20 msgs)    │
│  • _append(session_id, role, content) - Adds message, enforces bounds               │
│  • chat(session_id, message) - Main flow:                                           │
│      1. Get history                                                                   │
│      2. Call ollama_service.chat(message, history)                                   │
│      3. Handle errors (OllamaServiceError → user-friendly message)                   │
│      4. Append user + assistant messages to history                                  │
│      5. Return reply                                                                  │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    OLLAMA SERVICE (backend/services/ollama_service.py)               │
│  • OllamaClient class                                                                 │
│  • Module-level constants: OLLAMA_URL, MODEL_NAME, SYSTEM_PROMPT, FULL_SYSTEM_PROMPT │
│  • SYSTEM_PROMPT loaded from frontend/prompts/assistant_system_prompt.md              │
│  • WORKFLOW_PROMPT loaded from frontend/prompts/workflow.md                          │
│  • FAQ_PROMPT loaded from frontend/prompts/faq.md                                    │
│  • FULL_SYSTEM_PROMPT = concatenation of all three                                   │
│  • chat(message, history) - Builds final prompt:                                     │
│      FULL_SYSTEM_PROMPT + "\n\n" + formatted_history + "\n\nUSER: " + message        │
│    POSTs to Ollama /api/generate with: model, prompt, stream=false, temp=0.3        │
│  • Returns response text                                                              │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    LARGE LANGUAGE MODEL (Ollama: qwen2.5-coder:7b)                   │
│  • Receives complete prompt with system instructions                                 │
│  • Applies system prompt constraints (scope, refusal, style)                         │
│  • Uses conversation history for context                                             │
│  • Generates response token-by-token                                                 │
│  • Returns complete response                                                         │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                    RESPONSE VALIDATION & RETURN                                       │
│  • OllamaService returns text → ChatService receives reply                           │
│  • ChatService appends to session history (user + assistant)                         │
│  • ChatService returns reply to API route                                            │
│  • API route wraps in ChatResponse → JSON response                                   │
│  • Frontend llm_service receives JSON → returns response text                        │
│  • assistant_service.append_assistant_message() adds to UI history                   │
│  • UI rerenders with new message (typewriter effect)                                 │
└──────────────────────────────────────────────────────────────────────────────────────┘
                                           │
                                           ▼
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                    AI RESPONSE                                        │
│  Displayed in chat panel with markdown formatting                                    │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Arrow Explanations

| Arrow | Data Flow | Description |
|-------|-----------|-------------|
| User → UI | Text input | User types question, presses Enter |
| UI → Frontend Service | Function call | `process_user_input(message)` |
| Frontend Service → Context Services | Function calls | `get_current_page()`, `get_page_context()`, `search_knowledge_base()` |
| Context Services → Prompt Builder | Return values | Context dicts, KB snippets list |
| Prompt Builder → LLM Service | HTTP POST | JSON: {message, history, context} |
| LLM Service → Backend API | HTTP POST | JSON to `/copilot/chat` |
| Backend API → Chat Service | Function call | `chat_service.chat(session_id, message)` |
| Chat Service → Ollama Service | Function call | `ollama_service.chat(message, history)` |
| Ollama Service → LLM | HTTP POST | Prompt to `http://localhost:11434/api/generate` |
| LLM → Ollama Service | HTTP Response | JSON with `response` field |
| Ollama Service → Chat Service | Return value | Response text string |
| Chat Service → API | Return value | Response text string |
| API → LLM Service | HTTP Response | JSON `ChatResponse` |
| LLM Service → Frontend Service | Return value | Response text string |
| Frontend Service → UI | State update | `append_assistant_message()` + `st.rerun()` |
| UI → User | Visual render | Message appears in chat panel |

---

## 12. Architecture Explanation - Component Responsibilities

### 12.1 Component Responsibility Matrix

| Component | File(s) | Primary Responsibility | Restriction Role |
|-----------|---------|----------------------|------------------|
| **AI Copilot UI** | `ai_copilot_panel.py`, `ai_copilot.py` | Render chat interface, capture input, display responses | **Presentation layer only** - no logic, no prompt construction |
| **Frontend Chat Service** | `assistant_service.py` | Manage chat state, build context-enriched prompts, coordinate with backend | **Context grounding** - injects page/session/KB context to keep LLM focused |
| **Backend Chat API** | `copilot.py`, `assistant.py` | HTTP endpoints, request validation, response formatting | **API boundary** - validates input, prevents malformed requests |
| **Chat Service** | `chat_service.py` | Session management, history bounding, error handling, delegates to LLM | **Session isolation** - prevents history stuffing attacks; bounds context window |
| **Context Retrieval Service** | `context_service.py`, `knowledge_service.py` | Extract runtime context (page, selections), search project KB | **Scope limiting** - only exposes relevant context, never secrets |
| **Prompt Builder** | `assistant_service.build_context_prompt()` | Assembles final prompt from system prompt + dynamic context | **Prompt engineering** - structures prompt for optimal constraint adherence |
| **Restriction Layer** | `ollama_service.py` (system prompt), `assistant_system_prompt.md` | Defines and enforces behavioral constraints | **Constitutional layer** - primary enforcement of scope, refusal, style |
| **System Prompt** | `assistant_system_prompt.md`, `workflow.md`, `faq.md`, `knowledge_base.md` | Static instructions loaded at startup | **Immutable rules** - cannot be overridden at runtime |
| **Live Database** | Backend services (not directly exposed to LLM) | Actual data storage (SQLite via SQLAlchemy) | **Data source** - accessed by backend, relevant snippets provided to LLM |
| **Large Language Model** | Ollama (qwen2.5-coder:7b) | Text generation based on prompt | **Executor** - follows system prompt instructions |
| **Response Formatter** | `chat_service.py` → API → `llm_service.py` → UI | Pass-through with error handling | **Sanitization** - only returns LLM text, no internal state |

### 12.2 How Components Work Together

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESTRICTION ENFORCEMENT FLOW                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. STATIC RULES (Loaded at startup)                                        │
│     └─ assistant_system_prompt.md → ollama_service.py → FULL_SYSTEM_PROMPT │
│        └─ Defines: Identity, Allowed Topics, Forbidden Topics, Refusal     │
│                                                                             │
│  2. DYNAMIC CONTEXT (Per request)                                           │
│     └─ context_service.py + knowledge_service.py → build_context_prompt()  │
│        └─ Adds: Current page, Session selections, Relevant KB snippets     │
│                                                                             │
│  3. PROMPT ASSEMBLY (Per request)                                           │
│     └─ FULL_SYSTEM_PROMPT + Dynamic Context + User Message → Final Prompt  │
│                                                                             │
│  4. LLM INFERENCE (Per request)                                             │
│     └─ Ollama receives Final Prompt → Generates constrained response       │
│                                                                             │
│  5. RESPONSE RETURN (Per request)                                           │
│     └─ LLM text → ChatService → API → Frontend → UI                        │
│        └─ No post-processing of content (trusts system prompt)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Key Insight:** The restriction is **not** implemented as a post-filter on LLM output. It's implemented as **pre-conditioning** via the system prompt. The LLM itself generates the refusal because its instructions tell it to. This is more robust than output filtering because:
- No false positives/negatives from keyword matching
- The LLM understands *why* it's refusing
- The refusal message is consistent and professional
- Works for any out-of-scope topic, not just predefined ones

---

## 13. Final Technical Summary

### 13.1 How the System Ensures Only Recruitment & Talent Management Questions Are Answered

1. **Constitutional System Prompt** - The `assistant_system_prompt.md` explicitly enumerates 16 allowed domains and 25+ forbidden categories. This is the "constitution" the LLM must follow.

2. **Explicit Refusal Template** - The system prompt provides a verbatim refusal response for out-of-scope questions, eliminating improvisation.

3. **Context Grounding** - Every request includes current page, session selections, and relevant knowledge base snippets, keeping the LLM anchored to the application domain.

4. **Session Isolation** - Bounded conversation history (20 messages) prevents prompt injection via history stuffing.

5. **No Direct Database Access** - The LLM never sees raw SQL, schemas, or full tables. Only curated context snippets.

### 13.2 How Live Project Data Is Used Through RAG

1. **Retrieval** - `KnowledgeService.search_knowledge_base()` + `ContextService` extract relevant project documentation and runtime state.

2. **Augmentation** - `build_context_prompt()` injects retrieved snippets into the system prompt as structured context sections.

3. **Generation** - LLM generates response using augmented prompt, producing answers grounded in actual project features and current user context.

4. **No Vector Database** - Uses lightweight keyword search on structured markdown knowledge base, sufficient for project documentation.

### 13.3 How Unrelated Questions Are Politely Declined

1. **Detection** - LLM recognizes query matches forbidden category (via system prompt's explicit list).

2. **Refusal Generation** - LLM outputs the prescribed refusal template from system prompt.

3. **Consistent Tone** - Professional, helpful, redirects to allowed topics without being dismissive.

4. **No Partial Answers** - The system prompt explicitly says "Do not provide any additional information about the out-of-scope topic."

### 13.4 How Sensitive System Information Is Protected

| Protection Layer | Mechanism |
|------------------|-----------|
| **Prompt Construction** | `build_context_prompt()` only includes: page name, description, actions, session IDs, KB snippets. Never includes: env vars, DB credentials, API keys, SQL, internal code. |
| **System Prompt** | Explicitly states: "Do NOT provide access to sensitive data", "Prioritize user privacy and data security" |
| **Backend API** | Validates input, returns only LLM text. No internal state in response. |
| **Ollama Service** | Uses constants for URLs/model. System prompt loaded from file, not constructed from secrets. |
| **Frontend** | No direct LLM access. All requests proxied through backend. |

### 13.5 How Existing Project Functionality Remains Unchanged

- The AI Copilot is a **purely additive feature** - a floating panel that provides guidance.
- It **does not modify** any existing pages, data models, API endpoints, or business logic.
- It **reads** session state (current page, selections) but **does not write** to it (except its own chat history).
- It **calls** existing backend APIs (via `/copilot/chat`) but those APIs are new, not modifications.
- All existing recruitment workflows (Jobs, Candidates, Resume Parser, Interviews, etc.) operate identically.

### 13.6 How the AI Behaves as a Secure, Project-Specific Intelligent Assistant

| Security Property | Implementation |
|-------------------|----------------|
| **Domain Confinement** | System prompt + context grounding + knowledge base scope |
| **Data Minimization** | Only relevant context snippets sent to LLM |
| **No Secret Leakage** | Secrets never in prompt; backend proxies all LLM calls |
| **Input Validation** | API rejects empty messages; history bounded |
| **Output Safety** | LLM constrained by system prompt; no post-processing needed |
| **Auditability** | All prompts, system instructions, and knowledge bases in version-controlled files |
| **Consistency** | Same system prompt every request; deterministic refusal behavior |
| **Extensibility** | New modules added by updating knowledge base files, not code |

---

## 14. Conclusion

The AI Copilot Restriction System in the HirePilot AI Recruitment and Talent Management Copilot implements a **defense-in-depth** approach to ensure the AI assistant:

1. **Answers only recruitment/HR/application questions** - Enforced by constitutional system prompt with explicit allow/deny lists
2. **Uses live project data via RAG** - Lightweight retrieval of knowledge base + runtime context injected into every prompt
3. **Politely declines unrelated questions** - Prescribed refusal template in system prompt, triggered by LLM's own classification
4. **Protects sensitive information** - Secrets never enter prompt construction; backend proxies all LLM communication
5. **Preserves existing functionality** - Purely additive UI component with read-only access to session state
6. **Operates as a secure, project-specific assistant** - All constraints visible in version-controlled prompt files; no hidden logic

The system achieves this through **four coordinated layers**:
- **Static Constitutional Layer** (`assistant_system_prompt.md` + `ollama_service.py`)
- **Dynamic Context Layer** (`context_service.py` + `knowledge_service.py` + `assistant_service.py`)
- **API Boundary Layer** (`copilot.py` + `chat_service.py`)
- **Presentation Layer** (`ai_copilot_panel.py`)

This architecture is maintainable (prompts in markdown), auditable (all rules in plain text), and effective (LLM self-enforces constraints via instruction following).