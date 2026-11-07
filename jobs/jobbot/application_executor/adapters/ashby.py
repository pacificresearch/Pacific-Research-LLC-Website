"""Ashby hosted application form (jobs.ashbyhq.com/<co>/<id>/application)."""
from .base import run_form


def open_and_fill(page, url, job, pr, app_row, evid, wait_human_seconds=0):
    if not url.rstrip("/").endswith("/application"):
        url = url.rstrip("/") + "/application"
    page.goto(url, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(2000)
    return run_form(page, job, pr, app_row, evid, wait_human_seconds)


def submit(page):
    page.locator("button:has-text('Submit Application'), button[type=submit]").first.click()
