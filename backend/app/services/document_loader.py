
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LoadedDocument:
    """A Markdown document and its source metadata."""

    source: str
    content: str


class MarkdownDocumentLoader:
    """Load Markdown documents from a configured directory."""

    def __init__(self, knowledge_dir: str | Path) -> None:
        self.knowledge_dir = Path(knowledge_dir).resolve()

    def load_documents(self) -> list[LoadedDocument]:
        """Load all Markdown files recursively from the knowledge directory."""

        if not self.knowledge_dir.exists():
            raise FileNotFoundError(
                f"Knowledge directory not found: {self.knowledge_dir}"
            )

        if not self.knowledge_dir.is_dir():
            raise NotADirectoryError(
                f"Knowledge path is not a directory: {self.knowledge_dir}"
            )

        documents: list[LoadedDocument] = []

        for file_path in sorted(self.knowledge_dir.rglob("*.md")):
            # Ignore symbolic links so files cannot escape the knowledge root.
            if file_path.is_symlink():
                continue

            resolved_path = file_path.resolve()

            if not resolved_path.is_relative_to(self.knowledge_dir):
                continue

            content = resolved_path.read_text(encoding="utf-8").strip()

            if not content:
                continue

            documents.append(
                LoadedDocument(
                    source=resolved_path.relative_to(
                        self.knowledge_dir
                    ).as_posix(),
                    content=content,
                )
            )

        return documents
