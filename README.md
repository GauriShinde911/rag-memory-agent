# RAG Research Assistant with Long-Term Memory & Function Calling

A production-quality, demo-ready personal research assistant built with **LangGraph**, **Chroma Vector DB**, **FastAPI**, and **React + TypeScript + Tailwind CSS**.

The assistant remembers facts across sessions, uses external tools via function calling, and self-corrects its vector memory when the user provides corrections or updates. Every response visibly demonstrates retrieval distance scores, tool execution telemetry, and memory mutations for viva explainability.

---

## 🏛️ Architecture & Interaction Flow

```mermaid
flowchart TD
    User([User Query]) -->|1. Search| Retriever[Chroma Vector Retriever\nCosine Distance top-k=4]
    Chroma[(Chroma DB\nPersistent Long-Term Memory)] <-->|Embed / Search| Retriever
    Retriever -->|Retrieved Memories| PromptAssembler[Prompt Assembler]
    STM[Short-Term Memory\nSliding Window Buffer] -->|Session History| PromptAssembler
    User -->|Latest Message| PromptAssembler

    PromptAssembler -->|System Prompt + Memories + History| Agent[LangGraph ReAct Agent]
    
    subgraph Tools [External Tools with @logged Trace]
        Calc[calculator: Safe AST Evaluator]
        Web[web_search: DuckDuckGo]
        Py[python_executor: Subprocess 5s Timeout]
    end

    Agent <-->|Function Calling| Tools
    Agent -->|Reply| UIAnswer([Assistant Reply])
    
    UIAnswer -->|Append exchange| STM
    UIAnswer -->|User + Reply + Retrieved IDs| Updater[Memory Feedback Loop\nLLM JSON Extraction]
    
    Updater -->|Validate Ops: add / update v+1 / delete| Chroma
    Updater -->|Explainability Trace| ExplainUI[UI Collapsible Chips:\n🔍 Retrieved | 🛠️ Tools | 🧠 Memory Ops]
```

---

## 🚀 Key Features

1. **Dual-Tier Memory System**:
   - **Short-Term Memory**: In-memory sliding-window buffer (last 8 turns) maintaining conversational context for one session. Discarded on new session.
   - **Long-Term Memory**: Persistent Chroma vector store using `sentence-transformers/all-MiniLM-L6-v2` embeddings with cosine distance (0.0 = identical). Tracks versioning (`v1 -> v2`), session origin, and audit history.
2. **Self-Correcting Feedback Loop**:
   - LLM inspects user message, reply, and retrieved memories.
   - Emits structured JSON operations (`add`, `update`, `delete`).
   - If user corrects a fact, the existing memory ID is updated with `version + 1` instead of creating conflicting duplicates.
3. **Audited Function Calling**:
   - **`calculator`**: Safe AST expression evaluator (`_eval`) with whitelisted operations and math functions (`sqrt`, `log`, `sin`, `abs`, etc.). Rejects arbitrary code or imports.
   - **`web_search`**: DuckDuckGo search returning top 3 snippets.
   - **`python_executor`**: Isolated subprocess execution with 5-second timeout, temporary working directory, and capped output length.
   - **Request-Scoped Telemetry**: Uses `contextvars` to ensure each turn captures strictly its own tool calls even under concurrent requests.
4. **Offline Test Suite & Parity with Notebook**:
   - 18 automated unit tests with `FakeLLM` and deterministic mock embeddings that run 100% offline in seconds without requiring API keys.
   - Re-runs the notebook's 3 multi-session scenarios and calculates **Hit@4**, **MRR**, **Stale Fact Rate**, **Tool Call Success**, and **Tool Selection Accuracy**.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11, FastAPI, LangGraph, langchain-chroma, sentence-transformers, Pydantic v2, pytest.
- **LLM Support**: Gemini (`gemini-2.5-flash`) or OpenAI (`gpt-4o-mini`) via switchable environment variables.
- **Frontend**: React 19, TypeScript 6 (strict mode), Vite 8, Tailwind CSS (minimal, clean, light/dark mode aware).

---

## ⚡ Quick Start (Windows & Cross-Platform)

### 1. Clone & Configure Environment

```bash
git clone https://github.com/GauriShinde911/rag-memory-agent.git
cd rag-memory-agent

# Copy environment template
cp .env.example .env
```

Edit `.env` to configure your API key:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GOOGLE_API_KEY=your_gemini_api_key_here
```
*(Or set `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini`, `OPENAI_API_KEY=your_key`)*

---

### 2. Start Servers

#### Option A: Windows PowerShell Launcher (One Command)
```powershell
.\scripts\dev.ps1
```

#### Option B: Plain Terminal Commands (Recommended)

**Terminal 1 — Backend:**
```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend runs on: `http://127.0.0.1:8000` (Swagger docs at `/docs`, health check at `/api/health`)*

**Terminal 2 — Frontend:**
```bash
cd frontend
npm install
npm run dev
```
*Frontend runs on: `http://localhost:5173`*

---

## 🧪 Running Offline Tests

Run the comprehensive pytest suite offline without API keys:
```bash
# In PowerShell:
$env:PYTHONPATH='backend'; python -m pytest backend/tests/ -v

# In Bash / macOS / Linux:
PYTHONPATH=backend pytest backend/tests/ -v
```

All 18 tests will pass in ~8 seconds:
- Memory CRUD & versioning (`v1 -> v2`)
- Short-term memory sliding window & clear
- AST calculator safety checks & code injection rejection
- Python executor 5-second timeout
- Request-scoped per-turn tool logging
- Memory updater Pydantic validation & resilience to invalid JSON
- Evaluation metric calculation parity (Hit@4, MRR, stale rate, tool metrics)
- Complete FastAPI endpoint smoke tests

---

## 🎓 Viva Demo Script

Use this step-by-step walkthrough to demonstrate the core architecture during a viva or presentation:

### Phase 1: Teach a Long-Term Fact (Session A)
1. In the chat, type:
   > *"I'm doing a literature review on transformer-based time-series forecasting. My supervisor is Prof. Kulkarni and wants IEEE citation style."*
2. Look at the assistant's reply:
   - Click the green **`+add`** chip under the message to view the extracted memory mutation.
   - Look at the right panel **Memory Tab**: you will see the new fact indexed with `v1` and ID badge.

### Phase 2: Cross-Session Recall (Session B)
1. Click **"✨ New Session"** in the top bar.
   - A toast appears: *"Short-term memory cleared, long-term memory kept."*
   - Chat history is reset.
2. Ask:
   > *"Which citation style does my supervisor want?"*
3. The agent replies with IEEE style.
   - Expand the **🔍 Retrieved** chip: show the examiner that the fact was retrieved from the persistent **Chroma vector database** with a cosine distance score (~0.25), proving it came from disk and not from the conversational buffer!

### Phase 3: Memory Correction & Stale-Fact Elimination
1. In the chat, enter an initial fact:
   > *"My cloud GPU budget is $50 per month."*
2. Click **"✨ New Session"**.
3. Correct the fact:
   > *"Correction: my GPU budget was raised to $80 per month, not $50."*
4. Expand the **🧠 Memory** chip:
   - Notice the operation was an **`↺upd`** on the **same ID**, incrementing its version to **`v2`**.
5. Click **"✨ New Session"** again and ask:
   > *"What is my monthly GPU budget?"*
6. Notice:
   - The assistant answers **$80**.
   - Expand **🔍 Retrieved**: verify that `$80` is retrieved and the stale `$50` value was completely eliminated.

### Phase 4: External Tools with Safe Execution
1. **Calculator**:
   > *"There are 16 days left and I plan to read 4 papers a day. How many papers is that in total?"*
   - Assistant answers 64. Expand **🛠️ Tools**: show `calculator` executed with AST safety in ~0.002s.
2. **Web Search**:
   > *"Search the web for what FAISS is and save a one-line summary to your memory."*
   - Assistant invokes DuckDuckGo, synthesizes a summary, and automatically saves it to long-term memory.
3. **Python Executor**:
   > *"Use Python to compute how many months a $400 GPU purchase lasts with an $80 monthly budget."*
   - Assistant executes isolated python snippet in a 5s-capped subprocess and prints the result.

### Phase 5: Multi-Session Evaluation Tab
1. Switch to the **📊 Evaluation** tab in the right panel.
2. Click **"▶ Run 3 Scenarios"**.
3. Watch the progress bar execute the 3 notebook test scenarios against isolated collections:
   - **S1**: Profile & project recall
   - **S2**: Correction / feedback loop (checks stale fact elimination)
   - **S3**: Web research persistence across sessions
4. View the 5 metric cards and full turn-by-turn verification table:
   - **Retrieval Accuracy (Hit@4)**: 100%
   - **Mean Reciprocal Rank (MRR)**: ~0.95 - 1.00
   - **Stale Facts Retrieved**: 0/1 (0%)
   - **Tool-Call Success Rate**: 100%
   - **Tool Selection Accuracy**: 100%
5. Click **"📥 Export Log"** to download `test_log.json`.

---

## 🔒 Security & Sandbox Notice

The `python_executor` tool runs code in a separate subprocess with a 5-second timeout, capped output length, and a temporary directory. It is designed for demonstration and educational purposes. It is **not** a hardened kernel sandbox (such as gVisor or Firecracker). Server binding is restricted to `127.0.0.1` by default. Code execution can be completely disabled at any time by setting `ENABLE_PYTHON_EXECUTOR=false` in `.env`.

---

## 📜 License

MIT License. Designed and built for assignment and viva demonstration.
