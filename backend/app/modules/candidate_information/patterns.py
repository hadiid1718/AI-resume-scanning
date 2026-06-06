from __future__ import annotations

import re


EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_PATTERN = re.compile(
    r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)?\d{3,4}[\s.-]?\d{4}"
)
LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9\-_/]+/?",
    re.IGNORECASE,
)
GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9\-_.]+/?",
    re.IGNORECASE,
)

NAME_LABEL_PATTERN = re.compile(r"(?im)^(?:full\s*name|name)\s*[:\-]\s*(.+)$")
LOCATION_LABEL_PATTERN = re.compile(r"(?im)^(?:location|address|based\s*in)\s*[:\-]\s*(.+)$")
SECTION_STOPWORDS = {
    "summary",
    "experience",
    "education",
    "skills",
    "projects",
    "certifications",
    "contact",
}
