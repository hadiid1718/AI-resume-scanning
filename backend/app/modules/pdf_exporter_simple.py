from __future__ import annotations

from typing import Any


class SimplePDFWriter:
    def __init__(self) -> None:
        self.pages: list[list[str]] = [[]]
        self.y = 780

    def heading(self, text: str) -> None:
        self._text(text, 50, self.y, size=18)
        self.y -= 30

    def text(self, text: str, indent: int = 0) -> None:
        for line in self._wrap(str(text), width=88):
            self._ensure_space(16)
            self._text(line, 50 + indent, self.y, size=10)
            self.y -= 14

    def render(self) -> bytes:
        objects: list[bytes] = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        ]
        content = "\n".join(self.pages[-1]).encode("latin-1", errors="replace")
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> "
            b"/Contents 4 0 R >>"
        )
        objects.append(
            f"<< /Length {len(content)} >>\nstream\n".encode("ascii") + content + b"\nendstream"
        )
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for object_id, body in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
            pdf.extend(body)
            pdf.extend(b"\nendobj\n")
        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )
        return bytes(pdf)

    def _ensure_space(self, needed: int) -> None:
        if self.y - needed < 50:
            self.pages.append([])
            self.y = 780

    def _text(self, text: str, x: float, y: float, size: int = 10) -> None:
        escaped = str(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.pages[-1].append(f"BT /F1 {size} Tf {x:.1f} {y:.1f} Td ({escaped}) Tj ET")

    @staticmethod
    def _wrap(text: str, width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if len(candidate) > width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        return lines or [""]
