# Q&A Chatbot for Documents

A lightweight local Q&A web app that indexes PDFs (selectable text) with a local TF‑IDF retriever and produces answers via a remote OpenRouter model. This project is a corrected, easier-to-run version of `QnAChatBotForDocuments.ipynb` and is intended to run locally without requiring an OpenAI account or downloading large local models.

Key points 

- PDF text extraction and retrieval run locally using TF‑IDF.
- Answers are generated through an OpenRouter model (a free-model router can be used).
- No OpenAI API account or Ollama model download is required, but an OpenRouter API key is required for the remote model calls.

## Features

- Index selectable-text PDFs and run local TF‑IDF retrieval.
- Simple Panel-based web UI.
- Optionally inspect which source pages were used to produce answers.

## Prerequisites

- Python 3.11 or 3.12 (recommended)
- VS Code (recommended)
- VS Code extensions: **Python** and **Jupyter**
- A free OpenRouter account and API key: https://openrouter.ai/keys

Environment variables

The app reads configuration from a `.env` file placed next to `app.py`. At minimum set:

- OPENROUTER_API_KEY — your OpenRouter API key (keep private, never commit to Git)
- OPENROUTER_MODEL — optional; defaults to a free-model router like `openrouter/free` (replace with a currently available model ID ending in `:free` if you prefer a specific model)

Do not surround values with quotes in `.env`.

## Install (macOS / Linux)

Open this folder in VS Code or a terminal and run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and replace the `OPENROUTER_API_KEY` placeholder with your key.

Start the app:

```bash
python -m panel serve app.py --show --autoreload
```

If the browser does not open automatically, visit: http://localhost:5006/app

## Windows PowerShell

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python -m panel serve app.py --show --autoreload
```

If PowerShell blocks activation for this terminal session, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate `.venv` again. Do not commit `.env`; it is already ignored by `.gitignore`.

## Select the VS Code interpreter

1. Press `Ctrl/Cmd+Shift+P`.
2. Choose **Python: Select Interpreter**.
3. Select the interpreter inside `.venv`.

For the notebook, also use **Select Kernel** in its top-right corner and choose the same `.venv` environment.

## Using the app

1. Choose a PDF containing selectable text (images-only PDFs require OCR first).
2. Click **Index PDF**. This creates a local TF‑IDF search index — no API calls for indexing.
3. Enter a question and click **Ask**.
4. Check **Retrieved sources** to see which pages were used in the answer.

Notes: free OpenRouter models (e.g. `openrouter/free`) may have rate limits or availability constraints; if `openrouter/free` stops being available, set `OPENROUTER_MODEL` in `.env` to a current free-model ID.

## Running tests (offline)

The repository contains offline tests that use a fake API client and do not spend API credits. To run them:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Also verify that the Panel server starts:

```bash
python -m panel serve app.py --address 127.0.0.1 --port 5006
```

Stop the server with `Ctrl+C` after the terminal prints the server URL.

## Common errors & troubleshooting

- `OPENROUTER_API_KEY is missing`: confirm `.env` exists beside `app.py`, then restart the app.
- `401` or invalid key: create a new key at https://openrouter.ai/keys and update `.env`.
- `429`: free-model rate limit reached; wait and retry or switch to another model.
- `No selectable text was found`: the PDF is image-only. Run OCR or use a text-based PDF.
- Port 5006 is busy: add `--port 5007` and open http://localhost:5007/app
- VS Code imports look unresolved: reselect the `.venv` interpreter.

## Contributing

Contributions and improvements are welcome. Please open issues or PRs if you find bugs or want to propose enhancements.

## License

This repository does not include a license file. If you want to use or distribute this project, please add a suitable LICENSE file.

## Contact

For questions, open an issue in this repository.
