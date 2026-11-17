"""ReliefWeb jobs RSS (UN agencies, WHO, UNICEF, IOM, UNHCR, WFP, and global-health NGOs post here).

Andrew 11/13: 5-10 UN / WHO / global-health applications per day (lane F). The public RSS feed is used
because the JSON API needs an approved appname. Applications go through each organization's own portal
(Inspira, WHO, UNICEF, Oracle, NGO sites), so these jobs are prepared as packets unless the employer's own
ATS is one the executor supports.
Employer entry: {ats: reliefweb, name: ReliefWeb}
"""
from __future__ import annotations

import html
import re
from datetime import datetime

from .base import http, relevant_title

QUERIES = ["global health", "public health program", "health program manager", "health project manager",
           "epidemiology", "health emergency", "health monitoring evaluation", "clinical", "health coordinator",
           "health specialist", "health officer", "biomedical", "immunization", "health security",
           "health information", "medical coordinator"]
CLOSING = re.compile(r"Closing date:\s*(\d{1,2} \w{3} \d{4})")


def _text(h: str) -> str:
    h = html.unescape(h or "")
    h = re.sub(r"<(br|/p|/li|/div|/h\d)[^>]*>", "\n", h, flags=re.I)
    return re.sub(r"[ \t]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def _items(query: str):
    xml = http("GET", "https://reliefweb.int/jobs/rss.xml", params={"search": query}).text
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        get = lambda tag: re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", it, re.S)  # noqa: E731
        yield {"title": html.unescape((get("title") or [""])[0]).strip(),
               "link": (get("link") or [""])[0].strip(),
               "org": html.unescape((get("author") or [""])[0]).strip(),
               "cats": [html.unescape(c).strip() for c in get("category")],
               "desc": _text((get("description") or [""])[0]),
               "pub": (get("pubDate") or [""])[0]}


def fetch(e: dict, terms: dict):
    seen = set()
    for q in QUERIES:
        for it in _items(q):
            m = re.search(r"/job/(\d+)", it["link"])
            if not m or m.group(1) in seen or not relevant_title(it["title"], terms):
                continue
            seen.add(m.group(1))
            country = it["cats"][0] if it["cats"] else ""
            closing = CLOSING.search(it["desc"])
            try:
                posted = datetime.strptime(it["pub"][:16], "%a, %d %b %Y").date().isoformat()
            except ValueError:
                posted = ""
            us = country.lower() in ("united states of america", "united states", "usa")
            yield {"source_job_id": m.group(1), "employer": it["org"] or "ReliefWeb", "title": it["title"],
                   "location": country, "country": "united states" if us else country.lower(),
                   "description": it["desc"] + (f"\n\nClosing date: {closing.group(1)}" if closing else ""),
                   "posted_date": posted, "ats": "reliefweb", "job_url": it["link"], "apply_url": it["link"],
                   "deadline": datetime.strptime(closing.group(1), "%d %b %Y").date().isoformat() if closing else None}
