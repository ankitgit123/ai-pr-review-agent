
from app.services.document_chunker import MarkdownDocumentChunker
from app.services.document_loader import MarkdownDocumentLoader


def test_loader_reads_markdown_and_preserves_relative_source(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    nested_dir = knowledge_dir / "frontend"
    nested_dir.mkdir(parents=True)

    markdown_file = nested_dir / "standards.md"
    markdown_file.write_text(
        "# Frontend Standards\n\nUse accessible components.\n",
        encoding="utf-8",
    )

    loader = MarkdownDocumentLoader(knowledge_dir)
    documents = loader.load_documents()

    assert len(documents) == 1
    assert documents[0].source == "frontend/standards.md"
    assert "# Frontend Standards" in documents[0].content
    assert "Use accessible components." in documents[0].content


def test_loader_skips_empty_markdown_files(tmp_path):
    knowledge_dir = tmp_path / "knowledge"
    knowledge_dir.mkdir()

    (knowledge_dir / "empty.md").write_text("   \n", encoding="utf-8")
    (knowledge_dir / "useful.md").write_text(
        "# Useful\n\nKeep functions small.",
        encoding="utf-8",
    )

    documents = MarkdownDocumentLoader(knowledge_dir).load_documents()

    assert len(documents) == 1
    assert documents[0].source == "useful.md"


def test_loader_raises_for_missing_directory(tmp_path):
    missing_dir = tmp_path / "missing"

    loader = MarkdownDocumentLoader(missing_dir)

    try:
        loader.load_documents()
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass


def test_chunker_preserves_heading_and_source_metadata():
    from app.services.document_loader import LoadedDocument

    document = LoadedDocument(
        source="css-layering-guidelines.md",
        content=(
            "# CSS Layering Guidelines\n\n"
            "General guidance.\n\n"
            "## Header\n\n"
            "Use the documented layering token.\n\n"
            "## Modal Dialogs\n\n"
            "Use the shared modal layer token."
        ),
    )

    chunks = MarkdownDocumentChunker(max_chars=500).chunk_document(
        document
    )

    assert len(chunks) == 3
    assert chunks[0].section == "CSS Layering Guidelines"
    assert chunks[1].section == "CSS Layering Guidelines > Header"
    assert chunks[2].section == "CSS Layering Guidelines > Modal Dialogs"

    assert all(
        chunk.source == "css-layering-guidelines.md"
        for chunk in chunks
    )
    assert all(chunk.content.strip() for chunk in chunks)
    assert len({chunk.chunk_id for chunk in chunks}) == len(chunks)


def test_chunker_respects_maximum_chunk_size():
    from app.services.document_loader import LoadedDocument

    long_text = "word " * 600

    document = LoadedDocument(
        source="long-guideline.md",
        content=f"# Long Guideline\n\n{long_text}",
    )

    chunks = MarkdownDocumentChunker(
        max_chars=200,
        overlap_chars=20,
    ).chunk_document(document)

    assert len(chunks) > 1
    assert all(len(chunk.content) <= 200 for chunk in chunks)
    assert all(chunk.source == "long-guideline.md" for chunk in chunks)
    assert all(chunk.section for chunk in chunks)


def test_chunker_rejects_invalid_size_configuration():
    try:
        MarkdownDocumentChunker(max_chars=100, overlap_chars=100)
        assert False, "Expected ValueError"
    except ValueError:
        pass
