
import re
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.services.document_loader import LoadedDocument


@dataclass(frozen=True)
class DocumentChunk:
    """A text chunk with metadata linking it to its source."""

    chunk_id: str
    source: str
    section: str
    content: str


class MarkdownDocumentChunker:
    """Split Markdown documents by headings, with a size limit."""

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
    DEFAULT_MAX_CHARS = 1000
    DEFAULT_OVERLAP_CHARS = 100

    def __init__(
        self,
        max_chars: int = DEFAULT_MAX_CHARS,
        overlap_chars: int = DEFAULT_OVERLAP_CHARS,
    ) -> None:
        if max_chars <= 0:
            raise ValueError("max_chars must be positive.")

        if overlap_chars < 0 or overlap_chars >= max_chars:
            raise ValueError(
                "overlap_chars must be non-negative and smaller than max_chars."
            )

        self.max_chars = max_chars
        self.overlap_chars = overlap_chars

    def chunk_document(
        self,
        document: LoadedDocument,
    ) -> list[DocumentChunk]:
        """Split one document and preserve its heading hierarchy."""

        sections: list[tuple[str, list[str]]] = []
        heading_stack: list[tuple[int, str]] = []
        current_lines: list[str] = []

        
        def save_section() -> None:
            content = "\n".join(current_lines).strip()
            if not content:
                return

            # Do not create chunks containing only Markdown headings.
            body_lines = [
                line.strip()
                for line in current_lines
                if line.strip()
                and not self.HEADING_PATTERN.match(line.strip())
            ]

            if not body_lines:
                return

            section_name = " > ".join(
                heading for _, heading in heading_stack
            ) or "Introduction"

            sections.append((section_name, [content]))


        for line in document.content.splitlines():
            match = self.HEADING_PATTERN.match(line)

            if not match:
                current_lines.append(line)
                continue

            # Save content belonging to the previous section.
            save_section()
            current_lines = []

            level = len(match.group(1))
            heading = match.group(2).strip()

            # A heading replaces any previous heading at the same
            # or deeper level.
            heading_stack = [
                (existing_level, existing_heading)
                for existing_level, existing_heading in heading_stack
                if existing_level < level
            ]
            heading_stack.append((level, heading))

            # Keep the heading in the section content for context.
            current_lines.append(line)

        save_section()

        chunks: list[DocumentChunk] = []
        source_stem = PurePosixPath(document.source).with_suffix("").as_posix()

        for section_name, section_contents in sections:
            section_text = "\n".join(section_contents).strip()
            pieces = self._split_text(section_text)

            for piece_index, piece in enumerate(pieces, start=1):
                chunk_id = (
                    f"{source_stem}:{self._slug(section_name)}:{piece_index}"
                )

                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        source=document.source,
                        section=section_name,
                        content=piece,
                    )
                )

        return chunks

    def chunk_documents(
        self,
        documents: list[LoadedDocument],
    ) -> list[DocumentChunk]:
        """Split multiple loaded documents."""

        chunks: list[DocumentChunk] = []

        for document in documents:
            chunks.extend(self.chunk_document(document))

        return chunks

    def _split_text(self, text: str) -> list[str]:
        """Split oversized sections at paragraph boundaries where possible."""

        if len(text) <= self.max_chars:
            return [text]

        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]

        pieces: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > self.max_chars:
                if current:
                    pieces.append(current)
                    current = ""

                pieces.extend(self._split_long_paragraph(paragraph))
                continue

            candidate = f"{current}\n\n{paragraph}".strip()

            if len(candidate) <= self.max_chars:
                current = candidate
            else:
                if current:
                    pieces.append(current)
                current = paragraph

        if current:
            pieces.append(current)

        return self._add_overlap(pieces)

    def _split_long_paragraph(self, text: str) -> list[str]:
        """Fallback for a paragraph larger than the configured limit."""

        pieces: list[str] = []
        start = 0

        while start < len(text):
            end = min(start + self.max_chars, len(text))

            # Prefer a word boundary when one is available.
            if end < len(text):
                boundary = text.rfind(" ", start, end)
                if boundary > start:
                    end = boundary

            piece = text[start:end].strip()
            if piece:
                pieces.append(piece)

            if end >= len(text):
                break

            start = max(0, end - self.overlap_chars)

        return pieces

    def _add_overlap(self, pieces: list[str]) -> list[str]:
        """Carry a small tail of the previous piece into the next piece."""

        if self.overlap_chars == 0 or len(pieces) < 2:
            return pieces

        result = [pieces[0]]

        for piece in pieces[1:]:
            previous_tail = result[-1][-self.overlap_chars:]
            separator = " " if previous_tail and piece else ""
            combined = f"{previous_tail}{separator}{piece}".strip()

            # Overlap can increase a piece's size, so retain the limit.
            if len(combined) <= self.max_chars:
                result.append(combined)
            else:
                result.append(piece)

        return result

    @staticmethod
    def _slug(value: str) -> str:
        """Create a readable, stable identifier from a section name."""

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
        return slug or "section"
