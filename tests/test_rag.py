from types import SimpleNamespace

from sklearn.feature_extraction.text import TfidfVectorizer

from rag import DocumentQA


class FakeClient:
    def generate(self, *, model, system, prompt):
        assert model
        assert "retrieved" in system.lower()
        assert "Question:" in prompt
        return "The answer is supported [p. 1]."


def test_split_text_has_overlap():
    qa = DocumentQA(client=FakeClient(), chunk_size=30, chunk_overlap=5)
    chunks = list(qa._split_text("one two three four five six seven eight nine ten"))
    assert len(chunks) >= 2
    assert all(chunks)


def test_retrieve_and_ask_without_network():
    qa = DocumentQA(client=FakeClient(), top_k=1)
    qa.chunks = [
        SimpleNamespace(text="Battery storage", page=1, index=0),
        SimpleNamespace(text="Solar forecast", page=2, index=1),
    ]
    qa._vectorizer = TfidfVectorizer().fit([chunk.text for chunk in qa.chunks])
    qa._document_matrix = qa._vectorizer.transform([chunk.text for chunk in qa.chunks])

    answer, matches = qa.ask("What does the battery do?")

    assert answer.endswith("[p. 1].")
    assert matches[0][0].page == 1
    assert qa.history


def test_missing_index_is_actionable():
    qa = DocumentQA(client=FakeClient())
    try:
        qa.retrieve("question")
    except RuntimeError as exc:
        assert "index a PDF" in str(exc)
    else:
        raise AssertionError("Expected retrieve() to reject a missing index")
