"""Modern Panel UI for the document Q&A application."""

from __future__ import annotations

from html import escape

import panel as pn
from dotenv import load_dotenv

from rag import DocumentQA


load_dotenv()

APP_CSS = """
:root {
  --dq-navy: #0f172a;
  --dq-blue: #4f46e5;
  --dq-blue-soft: #eef2ff;
  --dq-slate: #64748b;
  --dq-border: #e2e8f0;
}
body { background: #f8fafc; }
.main-panel {
  background: #ffffff;
  border: 1px solid var(--dq-border);
  border-radius: 18px;
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.07);
  overflow: hidden;
}
.workspace-head { padding: 20px 24px 8px 24px; }
.workspace-head h2 { margin: 0; color: var(--dq-navy); font-size: 22px; }
.workspace-head p { margin: 5px 0 0 0; color: var(--dq-slate); font-size: 13px; }
.workspace-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}
.meta-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #f8fafc;
  color: #475569;
  font-size: 11px;
  font-weight: 600;
}
.composer {
  margin: 0 20px 20px 20px;
  padding: 10px;
  border: 1px solid #cbd5e1;
  border-radius: 15px;
  background: white;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
}
.source-chip {
  display: inline-block;
  margin: 4px 6px 0 0;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--dq-blue-soft);
  color: #4338ca;
  font-size: 12px;
  font-weight: 600;
}
.evidence-card {
  padding: 10px 12px;
  border-left: 3px solid #818cf8;
  border-radius: 8px;
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  line-height: 1.5;
}
.evidence-label { color: #4338ca; font-weight: 700; margin-bottom: 4px; }
.upload-hint { color: #94a3b8; font-size: 11px; margin-top: -6px; }
.sidebar-brand { padding: 4px 2px 16px 2px; }
.sidebar-brand .mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: white;
  font-size: 19px;
  font-weight: 800;
  margin-right: 9px;
}
.sidebar-brand strong { color: #f8fafc; font-size: 18px; }
.sidebar-brand p { color: #94a3b8; margin: 8px 0 0 0; font-size: 12px; line-height: 1.45; }
.status-box, .doc-box, .privacy-box {
  border-radius: 11px;
  padding: 10px 12px;
  font-size: 12px;
  line-height: 1.45;
}
.status-neutral { background: rgba(255,255,255,.08); color: #cbd5e1; }
.status-success { background: rgba(16,185,129,.16); color: #a7f3d0; }
.status-error { background: rgba(239,68,68,.16); color: #fecaca; }
.doc-box { background: rgba(79,70,229,.2); color: #e0e7ff; word-break: break-word; }
.privacy-box { background: rgba(255,255,255,.06); color: #94a3b8; }
.prompt-button button { text-align: left !important; justify-content: flex-start !important; }
.bk-Card { border-radius: 14px !important; }
@media (max-width: 760px) {
  .workspace-head { padding: 16px 16px 6px 16px; }
  .composer { margin: 0 10px 10px 10px; padding: 8px; }
  .main-panel { border-radius: 12px; }
  .workspace-meta { flex-wrap: wrap; }
}
"""

pn.extension(sizing_mode="stretch_width", notifications=True, raw_css=[APP_CSS])


class DocumentChatApp:
    EXAMPLE_PROMPTS = (
        "Summarize this document",
        "What are the key parameters?",
        "Explain the methodology",
        "What are the main limitations?",
    )

    def __init__(self) -> None:
        self.qa = DocumentQA()
        self.indexed_filename = ""
        self.question_count = 0

        self.file_input = pn.widgets.FileInput(name="Choose a PDF", accept=".pdf")
        self.load_button = pn.widgets.Button(
            name="Index document", button_type="primary", height=42
        )
        self.clear_button = pn.widgets.Button(
            name="New conversation", button_type="light", height=38
        )
        self.status = pn.pane.HTML(
            '<div class="status-box status-neutral">● Waiting for a PDF</div>'
        )
        self.document_meta = pn.pane.HTML("", visible=False)

        self.chat = pn.chat.ChatFeed(
            min_height=610,
            sizing_mode="stretch_both",
            show_activity_dot=True,
            placeholder_text="Searching your document…",
            message_params={
                "show_reaction_icons": False,
                "show_copy_icon": True,
                "show_timestamp": False,
            },
            css_classes=["chat-feed"],
        )
        self.question = pn.chat.ChatAreaInput(
            placeholder="Ask a question about your document…",
            auto_grow=True,
            max_rows=4,
            height=52,
            disabled=True,
            enter_sends=True,
        )
        self.ask_button = pn.widgets.Button(
            name="Send  ↑", button_type="primary", width=110, height=42, disabled=True
        )

        self.prompt_buttons: list[pn.widgets.Button] = []
        for prompt in self.EXAMPLE_PROMPTS:
            button = pn.widgets.Button(
                name=prompt,
                button_type="light",
                height=36,
                disabled=True,
                css_classes=["prompt-button"],
            )
            button.on_click(self._prompt_handler(prompt))
            self.prompt_buttons.append(button)

        self.load_button.on_click(self._load_pdf)
        self.ask_button.on_click(self._ask)
        self.clear_button.on_click(self._clear)
        self.question.param.watch(self._submit_on_enter, "enter_pressed")
        self._show_welcome()

    def _submit_on_enter(self, event) -> None:
        if event.new and not self.question.disabled:
            self._ask(None)

    def _prompt_handler(self, prompt: str):
        def handler(_event) -> None:
            self.question.value = prompt
            self._ask(None)

        return handler

    def _show_welcome(self) -> None:
        self.chat.clear()
        self.chat.send(
            pn.pane.Markdown(
                "### Welcome 👋\nUpload and index a PDF, then ask questions in plain language. "
                "Answers include page-level sources so you can verify them quickly."
            ),
            user="DocuQuery",
            avatar="✦",
            respond=False,
        )

    def _load_pdf(self, _event) -> None:
        if not self.file_input.value:
            self._set_status("Choose a PDF before indexing.", "error")
            return

        self.load_button.loading = True
        self.load_button.name = "Indexing…"
        try:
            count = self.qa.index_pdf_bytes(self.file_input.value)
            self.indexed_filename = self.file_input.filename or "document.pdf"
            safe_name = escape(self.indexed_filename)
            self.document_meta.object = (
                f'<div class="doc-box"><strong>✓ Ready</strong><br>{safe_name}'
                f'<br><span style="opacity:.75">{self.qa.page_count} pages · '
                f'{count} searchable chunks</span></div>'
            )
            self.document_meta.visible = True
            self._set_status("Document indexed successfully", "success")
            self.question.disabled = False
            self.ask_button.disabled = False
            for button in self.prompt_buttons:
                button.disabled = False
            self._show_welcome()
            self.chat.send(
                f"**{safe_name}** is ready. What would you like to know?",
                user="DocuQuery",
                avatar="✦",
                respond=False,
            )
        except Exception as exc:
            self._set_status(str(exc), "error")
        finally:
            self.load_button.loading = False
            self.load_button.name = "Index document"

    def _ask(self, _event) -> None:
        question = self.question.value.strip()
        if not question:
            return

        self.question.value = ""
        self.ask_button.loading = True
        self.question.disabled = True
        self.chat.send(question, user="You", avatar="RA", respond=False)
        try:
            answer, matches = self.qa.ask(question)
            self.question_count += 1
            source_html = "".join(
                f'<span class="source-chip">p. {chunk.page} · {score:.2f}</span>'
                for chunk, score in matches
            )
            evidence_items = []
            for chunk, score in matches:
                excerpt = escape(chunk.text[:360])
                if len(chunk.text) > 360:
                    excerpt += "…"
                evidence_items.append(
                    pn.pane.HTML(
                        '<div class="evidence-card">'
                        f'<div class="evidence-label">Page {chunk.page} · relevance {score:.2f}</div>'
                        f'{excerpt}</div>'
                    )
                )
            evidence = pn.Accordion(
                (f"Evidence used ({len(evidence_items)})", pn.Column(*evidence_items)),
                active=[],
                sizing_mode="stretch_width",
            )
            response = pn.Column(
                pn.pane.Markdown(answer, sizing_mode="stretch_width"),
                pn.pane.HTML(f'<div style="margin-top:6px">{source_html}</div>'),
                evidence,
                sizing_mode="stretch_width",
            )
            self.chat.send(response, user="DocuQuery", avatar="✦", respond=False)
        except Exception as exc:
            self.chat.send(
                f"⚠️ **I couldn't complete that request.**\n\n{escape(str(exc))}",
                user="DocuQuery",
                avatar="✦",
                respond=False,
            )
        finally:
            self.ask_button.loading = False
            self.question.disabled = False

    def _clear(self, _event) -> None:
        self.qa.clear_history()
        self.question_count = 0
        self._show_welcome()
        if self.indexed_filename:
            self.chat.send(
                f"Your document **{escape(self.indexed_filename)}** is still indexed.",
                user="DocuQuery",
                avatar="✦",
                respond=False,
            )

    def _set_status(self, message: str, state: str) -> None:
        css_state = {
            "success": "status-success",
            "error": "status-error",
        }.get(state, "status-neutral")
        self.status.object = (
            f'<div class="status-box {css_state}">● {escape(message)}</div>'
        )

    def view(self):
        brand = pn.pane.HTML(
            '<div class="sidebar-brand"><div><span class="mark">D</span>'
            '<strong>DocuQuery</strong></div><p>Evidence-backed answers from your PDF, '
            'with page citations.</p></div>'
        )
        prompt_section = pn.Column(
            pn.pane.Markdown("#### Try asking"),
            *self.prompt_buttons,
            sizing_mode="stretch_width",
        )
        privacy = pn.pane.HTML(
            '<div class="privacy-box">🔒 PDF retrieval stays local. Only selected '
            'text excerpts are sent to OpenRouter when you ask a question.</div>'
        )
        sidebar = [
            brand,
            pn.pane.Markdown("#### Document"),
            self.file_input,
            pn.pane.HTML('<div class="upload-hint">Text-based PDF · processed in memory</div>'),
            self.load_button,
            self.status,
            self.document_meta,
            pn.layout.Divider(),
            prompt_section,
            pn.Spacer(height=12),
            self.clear_button,
            privacy,
        ]

        workspace_header = pn.pane.HTML(
            '<div class="workspace-head"><h2>Chat with your document</h2>'
            '<p>Ask focused questions and verify every response using the source pages.</p>'
            '<div class="workspace-meta">'
            '<span class="meta-pill">✦ OpenRouter Free</span>'
            '<span class="meta-pill">⌕ Local retrieval</span>'
            '<span class="meta-pill">▣ Page citations</span>'
            '</div></div>'
        )
        composer = pn.Row(
            self.question,
            self.ask_button,
            align="end",
            sizing_mode="stretch_width",
            css_classes=["composer"],
        )
        main = pn.Column(
            workspace_header,
            self.chat,
            composer,
            sizing_mode="stretch_both",
            min_height=760,
            css_classes=["main-panel"],
        )

        return pn.template.FastListTemplate(
            title="DocuQuery",
            sidebar=sidebar,
            main=[main],
            sidebar_width=320,
            main_layout=None,
            accent_base_color="#4F46E5",
            header_background="#0F172A",
            theme_toggle=False,
        )


app = DocumentChatApp().view()
app.servable()
