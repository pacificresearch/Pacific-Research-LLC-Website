"""Lever hosted application form (jobs.lever.co/<co>/<id>/apply)."""
from .base import run_form


def open_and_fill(page, url, job, pr, app_row, evid, wait_human_seconds=0):
    if not url.rstrip("/").endswith("/apply"):
        url = url.rstrip("/") + "/apply"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    return run_form(page, job, pr, app_row, evid, wait_human_seconds)


def submit(page):
    page.locator("#btn-submit, button[type=submit]:has-text('Submit')").first.click()
