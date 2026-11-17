"""jobbot — PRG autonomous job application system.

Pipeline: DISCOVER -> NORMALIZE -> SCREEN (eligibility) -> SCORE -> PREPARE
(resume + cover letter) -> APPROVE -> SUBMIT -> VERIFY -> REPORT.

Deterministic code owns state, counting, dedupe, retries and files. Claude
(headless `claude -p`) is an optional semantic layer for matching and
requirement interpretation; every Claude output is fact-checked against the
evidence library before it can reach a document.
"""

__version__ = "0.1.0"
