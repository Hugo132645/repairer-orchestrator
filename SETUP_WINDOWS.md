# Windows setup and Codex CLI guide

Follow this guide from top to bottom on the private laptop.

## 1. Use Codex CLI with this project first

### 1.1 Verify the CLI you already downloaded

Open PowerShell and run:

```powershell
codex --version
Get-Command codex
```

If `codex` is not found, close and reopen PowerShell. If it is still missing, install the current CLI through the official installer or the npm fallback:

```powershell
npm install -g @openai/codex
```

The npm fallback requires a current Node.js LTS installation.

### 1.2 Sign in with the ChatGPT account

```powershell
codex login
codex login status
```

Choose **Sign in with ChatGPT**. ChatGPT Plus can authenticate Codex; an OpenAI API key is not required for this Codex workflow.

### 1.3 Open Codex inside the repository

After extracting the ZIP:

```powershell
cd "C:\path\to\repairer-orchestrator-prototype"
codex
```

Useful commands inside Codex:

```text
/status       show the current repository, model and permissions
/permissions  choose what Codex may read, edit and execute
/model        choose the available model and reasoning effort
/review       review changes or the working tree
```

`AGENTS.md` is already included, so do not overwrite it with `/init` unless you intentionally want to replace the repository instructions.

### 1.4 Safe first Codex prompts

Start read-only:

```text
Read AGENTS.md, README.md, SETUP_WINDOWS.md and pyproject.toml. Explain the architecture and the startup flow. Do not edit files or install anything yet.
```

After the environment is installed:

```text
Inspect the repository, run the unit tests and Ruff checks, and report failures. Fix only genuine project defects. Keep the LangGraph validation-before-delegation edge and A2A routing intact. Show the diff and rerun verification.
```

For a focused change:

```text
Plan the smallest change needed for <describe task>. List the files you intend to touch before editing. Add tests, run pytest and Ruff, and summarize the final diff.
```

### 1.5 Put the project under Git before allowing edits

```powershell
git init
git add .
git commit -m "Initial corrected repairer orchestrator prototype"
```

Create another commit after each successful Codex task. This gives you a simple rollback point.

## 2. Install the required desktop software

Install these applications:

1. **Python 3.12, 64-bit**. During installation, enable **Add Python to PATH**.
2. **Visual Studio Code**.
3. **Git for Windows**.
4. **Node.js LTS**, only if you installed or update Codex through npm.

Verify:

```powershell
py -3.12 --version
git --version
code --version
codex --version
```

Do not use Python 3.13 for this repository. The project intentionally targets Python 3.12.

## 3. Open the folder correctly in VS Code

From PowerShell:

```powershell
cd "C:\path\to\repairer-orchestrator-prototype"
code .
```

Open the repository folder itself, not its parent directory and not a single Python file.

## 4. Install the VS Code extensions

VS Code should offer the recommendations from `.vscode/extensions.json`. Install:

- **Codex – OpenAI's coding agent** (`openai.chatgpt`)
- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`)
- **Python Debugger** (`ms-python.debugpy`)
- **Ruff** (`charliermarsh.ruff`)
- **GitLens** (`eamodio.gitlens`, optional but useful)

Open Codex from the Activity Bar. If the icon is hidden, use the Command Palette and run **Codex: Open Codex Sidebar**. The IDE extension and CLI can use the same ChatGPT sign-in.

## 5. Create a completely new Python environment

In the VS Code PowerShell terminal:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
```

`pyproject.toml` explicitly includes the gateway, shared code, orchestrator,
portal, and service-agent packages. This avoids ambiguous flat-layout package
discovery.

If PowerShell blocks activation, run this once for your Windows account and reopen the terminal:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then select the interpreter in VS Code:

```text
Ctrl+Shift+P → Python: Select Interpreter → .venv\Scripts\python.exe
```

## 6. Configure the model credential

The default example uses Azure OpenAI's OpenAI-compatible v1 endpoint through
LiteLLM. In Azure AI Foundry, copy the v1 endpoint, key,
and deployment name. The deployment name can differ from the underlying model
name. The v1 endpoint does not use a dated API version.

Create the local environment file:

```powershell
Copy-Item .env.example .env
code .env
```

Set:

```dotenv
LLM_PROVIDER=azure_openai_v1
OPENAI_API_KEY=paste_your_azure_openai_key_here
OPENAI_BASE_URL=https://your-resource-name.services.ai.azure.com/openai/v1/
AGENT_MODEL=gpt-5-1
```

`AGENT_MODEL` is the Azure deployment name. If Azure shows a different
deployment name, use that exact value instead of `gpt-5-1`.
`OPENAI_BASE_URL` must end in `/openai/v1/`; do not append
`/chat/completions`, `/responses`, or an `api-version` query parameter.

To use Gemini instead:

```dotenv
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your_google_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=FALSE
AGENT_MODEL=gemini-3.6-flash
```

Do not commit `.env`; it is already ignored by Git.

Important distinction:

- `codex login` authenticates the OpenAI Codex CLI/extension through ChatGPT.
- The Azure or Gemini API key authenticates the model used by this LangGraph application.
- They are separate services and separate credentials.

## 7. Verify the installation

```powershell
python -m pytest -v
python -m ruff check .
python -m ruff format --check .
```

Expected result: all tests pass and Ruff reports no errors.

You can also run the VS Code tasks with:

```text
Ctrl+Shift+P → Tasks: Run Task
```

## 8. Start the portal and all agents

Simplest option:

```powershell
.\start_all.ps1
```

The launcher first runs `scripts/preflight.py`. No service windows are opened
unless Python, LangGraph, the model credential, registry, modules, synthetic data, and
ports pass validation.

This opens separate PowerShell windows for:

- Dual-protocol Agent Gateway: `127.0.0.1:8004`
- Authenticated Repairer Portal and Repairer Orchestrator: `127.0.0.1:8000`

Check the A2A agent cards and MCP tool catalogue:

```powershell
python scripts/check_services.py
```

Then open:

```text
http://127.0.0.1:8000
```

Sign in with the synthetic prototype credentials:

```text
Username: demo.repairer
Password: Synthetic123!

Administrator username: demo.admin
Administrator password: AdminSynthetic123!
```

The portal provides the chat interface and invokes the LangGraph orchestrator
server-side. Login sessions remain in memory, while synthetic accounts,
preferences, conversations, messages, service history, and repair orders are
stored in `data/portal.db`.

Stop everything with:

```powershell
.\stop_all.ps1
```

With the stack running, execute the complete Windows demo verification:

```powershell
.\verify_demo.ps1
```

This runs preflight, tests, Ruff, A2A and MCP health checks, and a portal smoke test.

## 9. Confirm the key behaviors

### Multi-agent orchestration

Use:

```text
For Demo Compact Hatchback in the EU, assess P0301, find the matching synthetic procedure, and check availability of a synthetic ignition coil. Consult every relevant service and consolidate the answer.
```

The root orchestrator should receive each selected service result and produce one
final answer.

### Error handling before delegation

Use:

```text
Diagnose my warning light and find the repair procedure.
```

Because the vehicle model and fault code are absent, the orchestrator should ask for them. The LangGraph routing guardrail prevents it from invoking a remote service first.

## 10. Common problems

### `Multiple top-level packages discovered in a flat-layout`

You are probably using the old `pyproject.toml`. Use the one in this corrected folder and rerun:

```powershell
python -m pip install -e ".[dev]"
```

### `codex` is not recognized

Reopen PowerShell, then run:

```powershell
npm install -g @openai/codex
codex --version
```

### The portal opens but model calls fail

Check `.env`, confirm the credential for the selected provider is valid, and
restart all processes after editing environment variables.

### An A2A or MCP agent is unavailable

Run:

```powershell
python scripts/check_services.py
```

Restart the gateway Uvicorn process. Also make sure port 8004 is not already occupied.

### You changed routing code but behavior did not change

Stop every old Python process and start the stack again. Graphs and the registry are built at import time.
