"""Greenhouse hosted application form (job-boards.greenhouse.io / boards.greenhouse.io / embeds)."""
import re

from .base import run_form


def form_url(url: str, job: dict | None = None) -> str:
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", url)
    if m:
        return f"https://job-boards.greenhouse.io/{m.group(1)}/jobs/{m.group(2)}"
    # company careers page that embeds Greenhouse (?gh_jid=...): go to the hosted form directly
    jid = re.search(r"gh_jid=(\d+)", url)
    src = (job or {}).get("source") or ""
    if jid and src.startswith("greenhouse:"):
        return f"https://job-boards.greenhouse.io/{src.split(':', 1)[1]}/jobs/{jid.group(1)}"
    return url


def open_and_fill(page, url, job, pr, app_row, evid, wait_human_seconds=0):
    page.goto(form_url(url, job), wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    btn = page.locator("button:has-text('Apply'), a:has-text('Apply for this job')")
    if btn.count() and not page.locator("input[type=file]").count():
        btn.first.click()
        page.wait_for_timeout(1500)
    return run_form(page, job, pr, app_row, evid, wait_human_seconds)


def submit(page):
    page.locator("button[type=submit]:has-text('Submit'), input[type=submit], button:has-text('Submit application')").first.click()
