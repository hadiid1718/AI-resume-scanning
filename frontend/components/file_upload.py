from __future__ import annotations

import streamlit as st


def resume_uploader(
    key: str = "resume_uploader",
    label: str = "Upload resume(s)",
    help_text: str = "PDF, DOCX, TXT, or MD — single or batch (max 10 MB each)",
    multiple: bool = True,
) -> list[tuple[object, bytes]]:
    uploaded = st.file_uploader(
        label,
        type=["pdf", "docx", "txt", "md"],
        help=help_text,
        key=key,
        accept_multiple_files=multiple,
    )
    if not uploaded:
        return []
    files = uploaded if isinstance(uploaded, list) else [uploaded]
    return [(f, f.getvalue()) for f in files]
