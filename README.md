# Q&A Chatbot for Documents

This is a corrected version of `QnAChatBotForDocuments.ipynb`. PDF extraction
and retrieval run locally with TF-IDF; answers use OpenRouter's free-model
router. No OpenAI API account or Ollama model download is required.

## Prerequisites

- Python 3.11 or 3.12 (recommended)
- VS Code
- VS Code extensions: **Python** and **Jupyter**
- A free OpenRouter account and API key

## 1. Create an OpenRouter key

Create a key at <https://openrouter.ai/keys>. Keep it private and never commit
it to Git.

## 2. Install the Python dependencies (macOS / Linux)

Open this folder in VS Code, then run in its integrated terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and replace `replace_with_your_openrouter_key` with your actual key.
Do not add quotation marks around it.

Start the app:

```bash
python -m panel serve app.py --show --autoreload
```

If the browser does not open automatically, visit <http://localhost:5006/app>.

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m panel serve app.py --show --autoreload
```

Edit `.env` before starting the app. If PowerShell blocks activation for this
terminal session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate `.venv` again. Do not commit `.env`; it is already ignored.

## Select the VS Code interpreter

1. Press `Ctrl/Cmd+Shift+P`.
2. Choose **Python: Select Interpreter**.
3. Select the interpreter inside `.venv`.

For the notebook, also use **Select Kernel** in its top-right corner and choose
the same `.venv` environment.

## Use the app

1. Choose a PDF containing selectable text.
2. Click **Index PDF**. The local TF-IDF search index is created without an API call.
3. Enter a question and click **Ask**.
4. Check **Retrieved sources** for the pages used.

Scanned/image-only PDFs need OCR first. `openrouter/free` has no model charge,
but free-model rate limits and availability apply.

## Verification

Run the offline tests (they use a fake API client and spend no API credits):

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Also verify that the Panel server starts:

```bash
python -m panel serve app.py --address 127.0.0.1 --port 5006
```

Stop it with `Ctrl+C` after the terminal prints the server URL.

## Common errors

- `OPENROUTER_API_KEY is missing`: confirm `.env` exists beside `app.py`, then restart.
- `401` or invalid key: create a new key at <https://openrouter.ai/keys>.
- `429`: the free-model rate limit is temporarily reached; wait and retry.
- `No selectable text was found`: OCR the PDF or use a text-based PDF.
- Port 5006 is busy: add `--port 5007` and open <http://localhost:5007/app>.
- VS Code imports look unresolved: reselect the `.venv` interpreter.

To choose a specific free model, replace `openrouter/free` in `.env` with a
currently available model ID ending in `:free`.
