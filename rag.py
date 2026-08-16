"""Local PDF retrieval with free-model answers through OpenRouter."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import os
from typing import Iterable

import httpx
import numpy as np
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer


@dataclass(frozen=True)
class Chunk:
    text: str
    page: int
    index: int


class OpenRouterClient:
    """Minimal client for OpenRouter's OpenAI-compatible chat endpoint."""

    def __init__(self, base_url: str | None = None, timeout: float = 180.0) -> None:
        self.base_url = (
            base_url or os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")
        self.timeout = timeout

    def generate(self, *, model: str, system: str, prompt: str) -> str:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is missing. Copy .env.example to .env and add your key."
            )
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-OpenRouter-Title": "Q&A Chatbot for Documents",
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.ConnectError as exc:
            raise RuntimeError("Cannot connect to OpenRouter. Check your internet connection.") from exc
        except httpx.HTTPStatusError as exc:
            try:
                error = exc.response.json().get("error", {})
                detail = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            except ValueError:
                detail = exc.response.text
            raise RuntimeError(f"OpenRouter request failed: {detail}") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError("OpenRouter timed out. Wait briefly and try again.") from exc

        try:
            answer = str(data["choices"][0]["message"]["content"]).strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenRouter returned an unexpected response.") from exc
        if not answer:
            raise RuntimeError("OpenRouter returned an empty answer.")
        return answer


class DocumentQA:
    """Index PDFs locally and answer with an OpenRouter free model."""

    def __init__(
        self,
        *,
        chat_model: str | None = None,
        chunk_size: int = 1_200,
        chunk_overlap: int = 180,
        top_k: int = 4,
        client: OpenRouterClient | None = None,
    ) -> None:
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chat_model = chat_model or os.getenv(
            "OPENROUTER_CHAT_MODEL", "openrouter/free"
        )
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self._client = client
        self.chunks: list[Chunk] = []
        self.page_count = 0
        self._vectorizer: TfidfVectorizer | None = None
        self._document_matrix = None
        self.history: list[tuple[str, str]] = []

    @property
    def client(self) -> OpenRouterClient:
        if self._client is None:
            self._client = OpenRouterClient()
        return self._client

    def index_pdf_bytes(self, pdf_bytes: bytes) -> int:
        if not pdf_bytes:
            raise ValueError("The uploaded PDF is empty.")

        reader = PdfReader(BytesIO(pdf_bytes))
        self.page_count = len(reader.pages)
        chunks: list[Chunk] = []
        chunk_index = 0
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            for text in self._split_text(page_text):
                chunks.append(Chunk(text=text, page=page_number, index=chunk_index))
                chunk_index += 1

        if not chunks:
            raise ValueError(
                "No selectable text was found. This may be a scanned PDF; run OCR first."
            )

        vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        try:
            document_matrix = vectorizer.fit_transform([chunk.text for chunk in chunks])
        except ValueError as exc:
            raise ValueError("The PDF does not contain enough searchable text.") from exc
        self.chunks = chunks
        self._vectorizer = vectorizer
        self._document_matrix = document_matrix
        self.history.clear()
        return len(chunks)

    def retrieve(self, query: str, *, top_k: int | None = None) -> list[tuple[Chunk, float]]:
        query = query.strip()
        if not query:
            raise ValueError("Enter a question.")
        if not self.chunks or self._vectorizer is None or self._document_matrix is None:
            raise RuntimeError("Upload and index a PDF first.")

        query_vector = self._vectorizer.transform([query])
        scores = (self._document_matrix @ query_vector.T).toarray().ravel()
        k = min(top_k or self.top_k, len(self.chunks))
        indices = np.argsort(scores)[-k:][::-1]
        return [(self.chunks[int(i)], float(scores[int(i)])) for i in indices]

    def ask(self, question: str) -> tuple[str, list[tuple[Chunk, float]]]:
        matches = self.retrieve(question)
        context = "\n\n".join(
            f"[Page {chunk.page}, chunk {chunk.index}]\n{chunk.text}"
            for chunk, _score in matches
        )
        recent_history = "\n".join(
            f"User: {user}\nAssistant: {assistant}"
            for user, assistant in self.history[-4:]
        )
        prompt = f"""Question: {question}

Recent conversation:
{recent_history or '(none)'}

Retrieved document excerpts:
{context}
"""
        answer = self.client.generate(
            model=self.chat_model,
            system=(
                "Answer only from the retrieved document excerpts. "
                "If the excerpts do not contain the answer, say so. "
                "Cite supporting pages inline as [p. N]. Be concise and accurate."
            ),
            prompt=prompt,
        )
        self.history.append((question, answer))
        return answer, matches

    def clear_history(self) -> None:
        self.history.clear()

    def _split_text(self, text: str) -> Iterable[str]:
        text = " ".join(text.split())
        if not text:
            return
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start + self.chunk_size // 2:
                    end = boundary
            chunk = text[start:end].strip()
            if chunk:
                yield chunk
            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)
