"""Local dashboard: http://127.0.0.1:8765  (bound to localhost only).

POST actions require the per-install token in data/.dashboard_token (sent automatically
by the page, which is served with it embedded) so other local web pages can't drive it.
"""
from __future__ import annotations

import json
import mimetypes
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import application_tracker as db
from . import approval_queue, reporting
from .config import home, load_config

PAGE = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>jobbot</title><style>
:root{--bg:#f7f7f5;--fg:#1d1d1b;--mut:#6b6b66;--card:#fff;--line:#e4e4df;--acc:#1f5fbf;--ok:#1d7a46;--warn:#a15c00;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#ececea;--mut:#9a9a94;--card:#1d1d1c;--line:#333;--acc:#7aa7ff;--ok:#5fcf8f;--warn:#e3a54a;--bad:#ff7b72}}
body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{display:flex;gap:12px;align-items:center;padding:14px 18px;border-bottom:1px solid var(--line);flex-wrap:wrap}
h1{font-size:17px;margin:0 12px 0 0}.pill{padding:2px 9px;border-radius:99px;border:1px solid var(--line);font-size:12px}
main{padding:16px 18px;max-width:1280px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}.n{font-size:24px;font-weight:650}
.l{color:var(--mut);font-size:12px}table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:10px;overflow:hidden}
th,td{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;font-size:13px}th{color:var(--mut);font-weight:550}
button,select,input{font:inherit;padding:5px 9px;border-radius:7px;border:1px solid var(--line);background:var(--card);color:var(--fg)}
button.p{background:var(--acc);color:#fff;border-color:var(--acc)}button.d{color:var(--bad)}a{color:var(--acc)}
.tabs{display:flex;gap:6px;margin:16px 0 10px;flex-wrap:wrap}.tabs button.on{border-color:var(--acc);color:var(--acc)}
.r{color:var(--mut);font-size:12px}.ok{color:var(--ok)}.warn{color:var(--warn)}.bad{color:var(--bad)}
.wrap{overflow-x:auto}details{margin-top:4px}code{font-size:12px}
</style></head><body>
<header><h1>jobbot</h1><span id="mode" class="pill"></span><span id="paused" class="pill"></span>
<button onclick="post('/api/pause',{paused:!S.paused})" id="pausebtn"></button>
<input id="q" placeholder="search employer/title/location" oninput="load()"><a href="/api/export.csv">Export CSV</a>
<a href="/report" target="_blank">Today's report</a></header>
<main><div class="grid" id="cards"></div>
<div class="tabs" id="tabs"></div><div class="wrap"><table><thead><tr><th>#</th><th>Score</th><th>Cat</th><th>Employer / Title</th>
<th>Location · Salary</th><th>Status</th><th>Materials</th><th>Actions</th></tr></thead><tbody id="rows"></tbody></table></div>
<h3>Settings</h3><div class="card" id="settings"></div></main>
<script>
const TOKEN="__TOKEN__";let S={},TAB="AWAITING_APPROVAL";
const TABS=["AWAITING_APPROVAL","NEEDS_HUMAN_ACTION","QUALIFIED","SUBMITTED","CONFIRMATION_PENDING","INTERVIEW","FAILED","REJECTED","SCREENED","ALL"];
async function post(u,b){const r=await fetch(u,{method:'POST',headers:{'content-type':'application/json','x-token':TOKEN},body:JSON.stringify(b||{})});
 const j=await r.json();if(j.error)alert(j.error);load();return j}
function esc(s){return String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
async function load(){S=await (await fetch('/api/summary')).json();
 document.getElementById('mode').textContent='mode: '+S.mode;document.getElementById('paused').textContent=S.paused?'PAUSED':'running';
 document.getElementById('pausebtn').textContent=S.paused?'Resume':'Pause';
 const m=S.metrics,b=m.by_status;const c=[['Submitted today',m.submitted_today],['Submitted total',(b.SUBMITTED||0)+(b.INTERVIEW||0)+(b.OFFER||0)],
 ['Awaiting approval',b.AWAITING_APPROVAL||0],['Needs you',b.NEEDS_HUMAN_ACTION||0],['Interviews',b.INTERVIEW||0],['Offers',b.OFFER||0],
 ['Avg qualified score',m.avg_qualified_score],['Active jobs tracked',m.active_jobs],['Emails needing attention',m.emails_attention]];
 document.getElementById('cards').innerHTML=c.map(x=>`<div class=card><div class=n>${esc(x[1])}</div><div class=l>${x[0]}</div></div>`).join('')
  +['A','B','C'].map(k=>`<div class=card><div class=n>${S.today[k].submitted}/${S.quotas[k]}</div><div class=l>Category ${k} today · ${S.today[k].ready} ready</div></div>`).join('');
 document.getElementById('tabs').innerHTML=TABS.map(t=>`<button class="${t==TAB?'on':''}" onclick="TAB='${t}';load()">${t.replace(/_/g,' ').toLowerCase()} ${b[t]!==undefined?'('+b[t]+')':''}</button>`).join('');
 const q=document.getElementById('q').value;const rows=await (await fetch(`/api/apps?status=${TAB=='ALL'?'':TAB}&q=${encodeURIComponent(q)}`)).json();
 document.getElementById('rows').innerHTML=rows.map(r=>{const sal=r.salary_min?`${r.salary_currency||'USD'} ${Math.round(r.salary_min/1000)}–${Math.round(r.salary_max/1000)}k <span class=r>${r.salary_label}</span>`:'<span class=r>salary unknown</span>';
  const el=r.eligibility=='pass'?'ok':r.eligibility=='review'?'warn':'bad';
  const mat=(r.resume_path?`<a href="/file?p=${encodeURIComponent(r.resume_path)}" target=_blank>resume (${esc(r.resume_family)})</a>`:'')+(r.cover_path?` · <a href="/file?p=${encodeURIComponent(r.cover_path)}" target=_blank>cover</a>`:'');
  const act=r.status=='AWAITING_APPROVAL'?(r.approved_at?'<span class=ok>approved ✓</span> ':`<button class=p onclick="post('/api/approve',{id:${r.id}})">Approve</button> `)+`<button class=d onclick="post('/api/reject',{id:${r.id},reason:prompt('Reason?')||'not a fit'})">Reject</button>`
   :r.status=='NEEDS_HUMAN_ACTION'?`<button onclick="post('/api/manual',{id:${r.id},confirmation:prompt('Confirmation number / email subject')})">I applied — record it</button> <button onclick="post('/api/approve',{id:${r.id}})">Resolved → approve</button>`
   :r.status=='SCREENED'?`<button onclick="post('/api/promote',{id:${r.id}})">Promote</button>`
   :r.status=='QUALIFIED'?`<button class=d onclick="post('/api/reject',{id:${r.id},reason:'not interested'})">Skip</button>`:'';
  let reasons='';try{const rs=JSON.parse(r.eligibility_reasons||'[]').filter(x=>x.outcome!='pass');if(rs.length)reasons='<details><summary class=r>'+rs.length+' checks</summary>'+rs.map(x=>`<div class=r>${esc(x.check)}: ${esc(x.outcome)} — ${esc(x.detail)}</div>`).join('')+'</details>'}catch(e){}
  return `<tr><td>${r.id}</td><td><b>${r.score??''}</b><div class="r ${el}">${esc(r.eligibility||'')} · conf ${r.confidence??''}</div></td><td>${esc(r.category)}</td>
  <td><b>${esc(r.employer)}</b><br><a href="${esc(r.job_url||r.apply_url)}" target=_blank>${esc(r.title)}</a>${reasons}</td>
  <td>${esc((r.location||'').slice(0,60))}<br>${sal}</td><td>${esc(r.status)}<div class=r>${esc((r.status_reason||'').slice(0,160))}</div></td><td>${mat}</td><td>${act}</td></tr>`}).join('');
 const s=S.settings;document.getElementById('settings').innerHTML=`
 Quotas A <input size=3 id=qa value=${S.quotas.A}> B <input size=3 id=qb value=${S.quotas.B}> C <input size=3 id=qc value=${S.quotas.C}>
 · Salary floor $<input size=8 id=sf value=${s.salary.floor_usd}> · Min score <input size=3 id=ms value=${s.min_score}>
 · Per-employer/day <input size=2 id=pe value=${s.max_per_employer_per_day}>
 <button onclick="post('/api/settings',{quotas:{A:+qa.value,B:+qb.value,C:+qc.value},salary:Object.assign(S.settings.salary,{floor_usd:+sf.value}),min_score:+ms.value,max_per_employer_per_day:+pe.value})">Save</button>
 <p>Exclude employers (comma separated): <input size=60 id=ex value="${esc((s.employers.exclude||[]).join(', '))}"> <button onclick="post('/api/settings',{employers:Object.assign(S.settings.employers,{exclude:ex.value.split(',').map(x=>x.trim()).filter(Boolean)})})">Save</button></p>
 <p>Geography priority (first = highest): <input size=70 id=geo value="${esc(s.geography.tiers.map(t=>t.name).join(' > '))}"> <button onclick="saveGeo()">Save order</button></p>
 <p>Auto-submit: <b>${S.mode=='auto'?'ENABLED':'off (review mode)'}</b> ${S.mode=='auto'?`<button class=d onclick="post('/api/auto',{enable:false})">Turn off</button>`:`<button onclick="post('/api/auto',{enable:true,confirm:prompt('Type: I authorize automatic submission of standard applications')})">Enable…</button>`}
 <span class=r>Requires 5 approved, confirmed submissions first. Attestations, unknown questions and CAPTCHAs always pause.</span></p>`}
function saveGeo(){const order=geo.value.split('>').map(x=>x.trim());const tiers=[...S.settings.geography.tiers].sort((a,b)=>order.indexOf(a.name)-order.indexOf(b.name));
 const top=100;tiers.forEach((t,i)=>t.score=top-i*5);post('/api/settings',{geography:Object.assign(S.settings.geography,{tiers})})}
load();setInterval(load,30000);
</script></body></html>"""


def _token() -> str:
    f = home() / ".dashboard_token"
    if not f.exists():
        f.write_text(secrets.token_urlsafe(24))
        f.chmod(0o600)
    return f.read_text().strip()


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        b = json.dumps(obj, default=str).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        qs = {k: v[0] for k, v in parse_qs(u.query).items()}
        if u.path == "/":
            b = PAGE.replace("__TOKEN__", _token()).encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/api/summary":
            cfg = load_config()
            today = {c: {"submitted": db.submitted_today(c),
                         "ready": len(db.pipeline_rows(status="AWAITING_APPROVAL", category=c))} for c in "ABC"}
            self._json({"mode": cfg["mode"], "paused": cfg.get("paused", False), "quotas": cfg["quotas"],
                        "metrics": reporting.metrics(), "today": today,
                        "settings": {k: cfg[k] for k in ("salary", "min_score", "max_per_employer_per_day",
                                                         "employers", "geography")}})
        elif u.path == "/api/apps":
            rows = db.pipeline_rows(status=qs.get("status") or None, q=qs.get("q") or None, limit=300)
            self._json([dict(r) for r in rows])
        elif u.path == "/api/export.csv":
            b = reporting.export_csv().encode()
            self.send_response(200)
            self.send_header("content-type", "text/csv")
            self.send_header("content-disposition", "attachment; filename=jobbot_applications.csv")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/report":
            b = reporting.daily_report().encode()
            self.send_response(200)
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b)
        elif u.path == "/file":
            p = Path(qs.get("p", "")).resolve()
            root = (home() / "materials").resolve()
            if root not in p.parents or not p.exists():
                return self._json({"error": "not found"}, 404)
            b = p.read_bytes()
            self.send_response(200)
            self.send_header("content-type", mimetypes.guess_type(p.name)[0] or "application/octet-stream")
            self.end_headers()
            self.wfile.write(b)
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        if self.headers.get("x-token") != _token():
            return self._json({"error": "bad token"}, 403)
        body = json.loads(self.rfile.read(int(self.headers.get("content-length", 0))) or b"{}")
        p = urlparse(self.path).path
        try:
            if p == "/api/approve":
                approval_queue.approve(int(body["id"]))
            elif p == "/api/promote":
                approval_queue.promote(int(body["id"]))
            elif p == "/api/reject":
                approval_queue.reject(int(body["id"]), body.get("reason") or "rejected")
            elif p == "/api/manual":
                approval_queue.mark_submitted_manually(int(body["id"]), body.get("confirmation") or "")
            elif p == "/api/pause":
                db.set_setting("paused", bool(body.get("paused")))
            elif p == "/api/settings":
                for k in ("quotas", "salary", "min_score", "max_per_employer_per_day", "employers", "geography"):
                    if k in body:
                        db.set_setting(k, body[k])
            elif p == "/api/auto":
                if body.get("enable"):
                    approval_queue.authorize_auto_submit(body.get("confirm") or "")
                else:
                    approval_queue.revoke_auto_submit()
            else:
                return self._json({"error": "unknown action"}, 404)
        except Exception as ex:
            return self._json({"error": str(ex)})
        self._json({"ok": True})


def serve(port: int = 8765) -> None:
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"jobbot dashboard: http://127.0.0.1:{port}")
    srv.serve_forever()
