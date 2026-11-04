"""Run:  cd jobs && python -m unittest discover -s tests -v

Uses a temporary JOBBOT_HOME and the fictional profile.example.yaml — never your data,
never a real employer site (the executor tests run against local HTML fixtures).
"""
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
JOBS = HERE.parent
TMP = tempfile.mkdtemp(prefix="jobbot_test_")
os.environ["JOBBOT_HOME"] = TMP
shutil.copy(JOBS / "profile.example.yaml", Path(TMP) / "profile.yaml")

import yaml  # noqa: E402

from jobbot import application_tracker as db  # noqa: E402
from jobbot import approval_queue, eligibility, email_monitor, job_scoring, pipeline, reporting  # noqa: E402
from jobbot.config import load_config, load_yaml  # noqa: E402
from jobbot.evidence import fact_guard, lexicon, profile  # noqa: E402
from jobbot.job_normalization import classify_location, fingerprint, normalize, parse_salary  # noqa: E402

FACTS = {"citizenships": ["united states"], "clearance": "none", "languages": {"english": "native"},
         "licenses": ["acrp-pm", "acrp-cp", "cbet"], "degrees": ["ma", "ba"], "years_professional": 8,
         "sponsor_monitoring_years": 0}


def raw(**kw):
    base = {"source": "test", "source_job_id": kw.pop("sid", "1"), "employer": "Acme Bio", "title": "Clinical Trial Manager",
            "location": "Irvine, CA", "description": "Manage clinical trials. " * 50,
            "job_url": "https://job-boards.greenhouse.io/acme/jobs/1", "apply_url": "https://job-boards.greenhouse.io/acme/jobs/1"}
    base.update(kw)
    return base


def fresh_db():
    db.reset_connection()
    for f in Path(TMP).glob("jobbot.sqlite*"):
        f.unlink()
    db.connect()


class Normalization(unittest.TestCase):
    def test_salary(self):
        self.assertEqual(parse_salary("The range is $120,000 - $150,000 per year")["salary_max"], 150000)
        self.assertEqual(parse_salary("$55-$65 per hour")["salary_min"], 55 * 2080)
        self.assertEqual(parse_salary("€70.000 - €85.000")["salary_currency"], "EUR")
        self.assertEqual(parse_salary("no money here"), {})

    def test_location(self):
        self.assertEqual(classify_location("Irvine, CA")[0], "united states")
        self.assertEqual(classify_location("Remote")[1], 1)
        self.assertEqual(classify_location("Geneva, Switzerland")[0], "switzerland")
        self.assertEqual(classify_location("São Paulo, Brazil")[0], "brazil")

    def test_fingerprint_dedupes_across_sources(self):
        self.assertEqual(fingerprint("Acme Bio", "Clinical Trial Manager (Remote)", "Irvine, CA"),
                         fingerprint("ACME BIO", "clinical trial manager", "irvine ca"))

    def test_html_escaped(self):
        j = normalize(raw(description="&lt;p&gt;Active RN&amp;nbsp;required&lt;/p&gt;"))
        self.assertNotIn("&lt;", j["description"])


class StateMachine(unittest.TestCase):
    def setUp(self):
        fresh_db()

    def test_dedupe_and_one_application_per_job(self):
        j1, new1 = db.upsert_job(normalize(raw(sid="a")))
        j2, new2 = db.upsert_job(normalize(raw(sid="b", source="other")))  # same opening elsewhere
        self.assertTrue(new1)
        self.assertFalse(new2)
        self.assertEqual(j1, j2)
        self.assertEqual(db.connect().execute("SELECT COUNT(*) FROM applications").fetchone()[0], 1)

    def test_illegal_transition(self):
        jid, _ = db.upsert_job(normalize(raw()))
        aid = db.app_by_job(jid)["id"]
        with self.assertRaises(db.TransitionError):
            db.transition(aid, "SUBMITTED")

    def test_submitted_requires_evidence(self):
        jid, _ = db.upsert_job(normalize(raw()))
        aid = db.app_by_job(jid)["id"]
        for s in ("SCREENED", "QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL", "SUBMITTING"):
            db.transition(aid, s)
        with self.assertRaises(db.TransitionError):
            db.transition(aid, "SUBMITTED", "no proof")
        db.transition(aid, "SUBMITTED", "ok", confirmation="Thank you for applying", submitted_at=db.now())
        self.assertEqual(db.submitted_today(), 1)

    def test_crash_recovery_never_resubmits(self):
        jid, _ = db.upsert_job(normalize(raw()))
        aid = db.app_by_job(jid)["id"]
        for s in ("SCREENED", "QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL", "SUBMITTING"):
            db.transition(aid, s)
        att = db.start_attempt(aid, "submit")
        db.mark_submit_clicked(att)  # process dies right after clicking
        db.recover()
        self.assertEqual(db.app(aid)["status"], "CONFIRMATION_PENDING")
        from jobbot.application_executor import execute
        db.transition(aid, "NEEDS_HUMAN_ACTION")
        db.update_app(aid, approved_at=db.now())
        self.assertIn("never resubmit", execute(aid, "submit")["outcome"])

    def test_recovery_before_click_returns_to_approval(self):
        jid, _ = db.upsert_job(normalize(raw()))
        aid = db.app_by_job(jid)["id"]
        for s in ("SCREENED", "QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL", "SUBMITTING"):
            db.transition(aid, s)
        db.recover()
        self.assertEqual(db.app(aid)["status"], "AWAITING_APPROVAL")


class Eligibility(unittest.TestCase):
    def check(self, desc, title="Program Manager", country="united states"):
        return eligibility.screen({"title": title, "description": desc, "country": country}, FACTS)

    def test_clearance(self):
        self.assertEqual(self.check("Active Secret clearance required.")["eligibility"], "fail")
        self.assertEqual(self.check("Must have the ability to obtain a Secret clearance.")["eligibility"], "review")
        self.assertEqual(self.check("Ability to obtain a Public Trust.")["eligibility"], "pass")

    def test_license(self):
        self.assertEqual(self.check("Active RN license required.")["eligibility"], "fail")
        self.assertEqual(self.check("PMP preferred.")["eligibility"], "pass")

    def test_language(self):
        self.assertEqual(self.check("Fluency in Portuguese is required.")["eligibility"], "fail")
        r = self.check("Spanish proficiency is a plus.")
        self.assertEqual(r["eligibility"], "pass")

    def test_years(self):
        self.assertEqual(self.check("Minimum 15 years of experience required.")["eligibility"], "fail")
        self.assertEqual(self.check("Requires 5+ years of experience.")["eligibility"], "pass")
        self.assertEqual(self.check("Bachelor's and 12 years of experience, or Master's and 6 years of experience required."
                                    )["eligibility"], "pass")

    def test_citizenship(self):
        self.assertEqual(self.check("Applicants must be citizens of Kenya.", country="kenya")["eligibility"], "fail")
        self.assertEqual(self.check("Must be a U.S. citizen.")["eligibility"], "pass")

    def test_cra_monitoring_gap(self):
        r = self.check("2 years of independent monitoring experience required.", title="Clinical Research Associate II")
        self.assertEqual(r["eligibility"], "review")

    def test_good_score_never_overrides_fail(self):
        job = normalize(raw(description="Clinical trial GCP CRO sponsor NIH. Active Top Secret clearance required. " * 20))
        el = eligibility.screen(job, FACTS)
        sc = job_scoring.score(job, el, load_config(), load_yaml("search.yaml"), {}, set())
        self.assertEqual(el["eligibility"], "fail")
        self.assertEqual(sc["score"], 0)


class Scoring(unittest.TestCase):
    def test_category_and_geo(self):
        terms, cfg = load_yaml("search.yaml"), load_config()
        a = normalize(raw(title="Clinical Trial Manager", location="Irvine, CA"))
        c = normalize(raw(title="Health Program Officer", location="Geneva, Switzerland"))
        self.assertEqual(job_scoring.categorize(a, terms), "A")
        self.assertEqual(job_scoring.categorize(c, terms), "C")
        el = {"eligibility": "pass", "eligibility_reasons": []}
        sa = job_scoring.score(a, el, cfg, terms, {}, set())
        self.assertEqual(sa["subscores"]["geo"], 82)  # major city (remote > hybrid > major cities)
        r = job_scoring.score(normalize(raw(sid="r", location="Remote")), el, cfg, terms, {}, set())
        h = job_scoring.score(normalize(raw(sid="h", location="Boston, MA (Hybrid)")), el, cfg, terms, {}, set())
        self.assertGreater(r["subscores"]["geo"], h["subscores"]["geo"])
        self.assertGreater(h["subscores"]["geo"], sa["subscores"]["geo"])
        self.assertEqual(sa["salary"]["label"], "estimated")

    def test_weights_sum(self):
        self.assertAlmostEqual(sum(job_scoring.WEIGHTS.values()), 1.0)


class Materials(unittest.TestCase):
    def setUp(self):
        fresh_db()

    def test_fact_guard(self):
        self.assertEqual(fact_guard("Coordinated enrollment for 300 participants."), [])
        self.assertTrue(fact_guard("Managed 4,000 participants."))
        self.assertTrue(fact_guard("PMP-certified leader fluent in French."))

    def test_resume_and_cover(self):
        from jobbot import cover_letter_builder, resume_builder
        job = normalize(raw(description="Our mission is to bring clinical trials to every patient everywhere we work. "
                                        "Requires REDCap and enrollment experience. Please include a cover letter."))
        jid, _ = db.upsert_job(job)
        res = resume_builder.build(1, dict(db.job(jid)), "clinical")
        self.assertTrue(Path(res["pdf"]).exists() and Path(res["docx"]).exists())
        man = json.loads((Path(res["pdf"]).parent / "resume_manifest.json").read_text())
        self.assertEqual(man["sha256"], res["sha256"])
        need, why = cover_letter_builder.needed(job, "A", 90)
        self.assertTrue(need)
        cov = cover_letter_builder.build(1, dict(db.job(jid)), "clinical")
        self.assertIn("Acme Bio", Path(cov["txt"]).read_text())

    def test_pipeline_end_to_end(self):
        db.upsert_job(normalize(raw(sid="x1", title="Senior Clinical Trial Manager",
                                    description="Manage clinical trials with CROs and sponsors under GCP. REDCap, enrollment, "
                                                "recruitment, protocol, IRB, NIH, decentralized, infectious disease. "
                                                "Salary $130,000 - $160,000. " * 3, posted_date=db.today())))
        db.upsert_job(normalize(raw(sid="x2", title="Clinical Research Nurse", location="Boston, MA",
                                    description="Active RN license required.")))
        st = pipeline.qualify(use_semantic=False)
        self.assertEqual(st["failed_eligibility"], 1)
        sl = pipeline.shortlist()
        ids = [r["id"] for r in sl["A"]]
        self.assertTrue(ids)
        pipeline.prepare(ids)
        self.assertEqual(db.app(ids[0])["status"], "AWAITING_APPROVAL")
        self.assertTrue(Path(db.app(ids[0])["resume_path"]).exists())
        rep = reporting.daily_report({})
        self.assertIn("Category breakdown", rep)


class ApprovalAndEmail(unittest.TestCase):
    def setUp(self):
        fresh_db()
        jid, _ = db.upsert_job(normalize(raw(employer="Formation Bio", title="Clinical Operations Manager")))
        self.aid = db.app_by_job(jid)["id"]
        for s in ("SCREENED", "QUALIFIED", "MATERIALS_READY", "AWAITING_APPROVAL"):
            db.transition(self.aid, s)

    def test_review_mode_refuses_unapproved_submit(self):
        from jobbot.application_executor import execute
        self.assertIn("not approved", execute(self.aid, "submit")["outcome"])

    def test_auto_submit_requires_track_record(self):
        with self.assertRaises(PermissionError):
            approval_queue.authorize_auto_submit("I authorize automatic submission of standard applications")

    def test_email_confirmation_and_rejection(self):
        for s in ("SUBMITTING", "CONFIRMATION_PENDING"):
            db.transition(self.aid, s)
        email_monitor.ingest({"message_id": "m1", "sender": "no-reply@formationbio.com",
                              "subject": "Thank you for applying to Formation Bio",
                              "body": "We have received your application for Clinical Operations Manager."})
        self.assertEqual(db.app(self.aid)["status"], "SUBMITTED")
        email_monitor.ingest({"message_id": "m2", "sender": "talent@formationbio.com", "subject": "Your application",
                              "body": "Unfortunately we are moving forward with other candidates for the Clinical "
                                      "Operations Manager role at Formation Bio."})
        self.assertEqual(db.app(self.aid)["status"], "REJECTED")
        self.assertEqual(email_monitor.ingest({"message_id": "m2"}), {"duplicate": True})


class Guards(unittest.TestCase):
    def test_classification_edge_cases(self):
        from jobbot.application_executor.guards import classify, match_option
        self.assertEqual(classify("Have you managed sponsor-initiated clinical trials?*")[0], "unknown")
        self.assertEqual(classify("Will you require visa sponsorship?")[1], "requires_sponsorship")
        self.assertEqual(classify("Full name ✱")[1], "full_name")
        self.assertEqual(classify("Start date month*")[1], "education_dates")
        self.assertEqual(classify("Do you consent to receiving text messages?")[1], "sms_consent")
        self.assertEqual(classify("I certify the information is true and correct")[1], "attestation")
        self.assertEqual(match_option("No", ["Select...", "Yes", "No"]), "No")
        self.assertIsNone(match_option("Maybe", ["Yes", "No"]))

    def test_routes(self):
        from jobbot.application_executor import route
        self.assertEqual(route({"apply_url": "https://wd1.myworkdaysite.com/recruiting/x/y/job/z/apply"}), "workday")
        self.assertEqual(route({"apply_url": "https://jobs.lever.co/a/b/apply"}), "lever")
        self.assertEqual(route({"apply_url": "https://www.linkedin.com/jobs/view/1"}), "linkedin")

    def test_deadline(self):
        r = eligibility.screen({"title": "x", "description": "Applications close on January 5, 2026.",
                                "country": "united states"}, FACTS)
        self.assertEqual(r["eligibility"], "fail")


class CredentialsAndHarvest(unittest.TestCase):
    def test_password_strength_and_storage(self):
        from jobbot import credentials
        pw = credentials.generate_password()
        self.assertEqual(len(pw), 16)
        self.assertTrue(any(c.isupper() for c in pw) and any(c.islower() for c in pw) and any(c.isdigit() for c in pw))
        self.assertTrue(any(c in credentials.SYMBOLS for c in pw))
        c1, new1 = credentials.get_or_create("https://acme.wd1.myworkdayjobs.com/x/job/1", "a@example.com")
        c2, new2 = credentials.get_or_create("https://acme.wd1.myworkdayjobs.com/other", "a@example.com")
        self.assertTrue(new1)
        self.assertFalse(new2)
        self.assertEqual(c1["password"], c2["password"])  # one account per portal host
        f = credentials._file()
        self.assertEqual(oct(f.stat().st_mode)[-3:], "600")
        csvp = credentials.export_chrome_csv()
        self.assertIn("name,url,username,password,note", open(csvp).read())

    def test_workday_dates(self):
        from jobbot.application_executor.adapters.workday import parse_dates
        self.assertEqual(parse_dates("Nov 2021 - Feb 2026"), ((11, 2021), (2, 2026), False))
        self.assertEqual(parse_dates("Mar 2026 - Present"), ((3, 2026), None, True))

    def test_parse_board_urls(self):
        from jobbot.job_discovery.web_search import parse
        self.assertEqual(parse("https://job-boards.greenhouse.io/pfm/jobs/1")["slug"], "pfm")
        self.assertEqual(parse("https://jobs.lever.co/alimentiv-2/abc")["slug"], "alimentiv-2")
        self.assertIsNone(parse("https://jobs.lever.co/jobgether/abc"))  # aggregator
        wd = parse("https://georgetown.wd1.myworkdayjobs.com/en-US/Georgetown_Admin_Careers/job/x")
        self.assertEqual((wd["tenant"], wd["wd"], wd["site"]), ("georgetown", "wd1", "Georgetown_Admin_Careers"))
        self.assertIsNone(parse("https://www.careerbuilder.com/job/x"))


class Executor(unittest.TestCase):
    """Drives local HTML forms with the real Playwright code path."""

    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright  # noqa
        except ImportError:
            raise unittest.SkipTest("playwright not installed")

    def setUp(self):
        fresh_db()
        from jobbot import cover_letter_builder, resume_builder
        jid, _ = db.upsert_job(normalize(raw()))
        self.aid = db.app_by_job(jid)["id"]
        res = resume_builder.build(self.aid, dict(db.job(jid)), "clinical")
        db.update_app(self.aid, resume_path=res["pdf"])
        self.job = dict(db.job(jid))

    def _run(self, html_extra="", answers=None, submit=False):
        import glob
        from playwright.sync_api import sync_playwright
        from jobbot.application_executor import Blocked, verify
        from jobbot.application_executor.adapters import base
        d = Path(tempfile.mkdtemp())
        (d / "form.html").write_text((HERE / "fixtures/gh_form.html").read_text().replace("<!--EXTRA-->", html_extra))
        shutil.copy(HERE / "fixtures/thanks.html", d / "thanks.html")
        pr = dict(profile())
        pr["approved_answers"] = dict(pr["approved_answers"], **(answers or {}))
        with sync_playwright() as pw:
            kw = {}
            c = glob.glob("/opt/pw-browsers/chromium-*/chrome-linux*/chrome")
            if c:
                kw["executable_path"] = c[0]
            b = pw.chromium.launch(**kw)
            page = b.new_page()
            page.goto((d / "form.html").as_uri())
            try:
                log = base.run_form(page, self.job, pr, db.app(self.aid), d)
            except Blocked as e:
                b.close()
                return "blocked", e.reasons
            vals = {l["key"]: l["value"] for l in log}
            if submit:
                page.locator("button[type=submit]").click()
                res = verify(page, d)
                b.close()
                return res["state"], vals
            b.close()
            return "filled", vals

    def test_blocks_without_approved_answers(self):
        state, reasons = self._run()
        self.assertEqual(state, "blocked")
        self.assertTrue(any("legally authorized us not approved" in r for r in reasons))
        self.assertTrue(any("sponsorship not approved" in r for r in reasons))

    def test_fills_with_approved_answers_and_confirms(self):
        state, vals = self._run(answers={"legally_authorized_us": "Yes", "requires_sponsorship": "No"}, submit=True)
        self.assertEqual(state, "confirmed")

    def test_fill_values(self):
        state, vals = self._run(answers={"legally_authorized_us": "Yes", "requires_sponsorship": "No"})
        self.assertEqual(state, "filled")
        self.assertEqual(vals["first_name"], "Jordan")
        self.assertNotIn("how_did_you_hear", vals)  # optional
        self.assertEqual(vals["legally_authorized_us"], "Yes")
        self.assertTrue(vals["resume"].startswith("<file:"))

    def test_attestation_and_custom_question_block(self):
        extra = ('<label for="att">I certify that the information provided is true and correct *</label>'
                 '<input type="checkbox" id="att" name="q9" required>'
                 '<label for="why">Why do you want to work at Acme? *</label><textarea id="why" name="q10" required></textarea>')
        state, reasons = self._run(extra, answers={"legally_authorized_us": "Yes", "requires_sponsorship": "No"})
        self.assertEqual(state, "blocked")
        self.assertTrue(any("attestation" in r for r in reasons))
        self.assertTrue(any("custom question" in r for r in reasons))

    def test_captcha_is_not_bypassed(self):
        extra = '<iframe src="https://hcaptcha.com/challenge" style="width:300px;height:150px"></iframe>'
        state, reasons = self._run(extra, answers={"legally_authorized_us": "Yes", "requires_sponsorship": "No"})
        self.assertEqual(state, "blocked")
        self.assertTrue(any("CAPTCHA" in r for r in reasons))

    def test_optional_disclosures_skipped_required_declined(self):
        ok = {"legally_authorized_us": "Yes", "requires_sponsorship": "No"}
        opt = ('<label for="g">Gender</label><select id="g" name="eeo_gender"><option>Select</option><option>Male</option>'
               '<option>Female</option><option>Decline to self-identify</option></select>')
        state, vals = self._run(opt, answers=ok)
        self.assertEqual(state, "filled")
        self.assertNotIn("gender", vals)  # optional -> left blank
        self.assertNotIn("linkedin", vals)  # optional non-core field -> skipped
        req = ('<label for="v">Veteran status *</label><select id="v" name="vet" required><option>Select</option>'
               '<option>I am a protected veteran</option><option>I am not a protected veteran</option>'
               '<option>I don\'t wish to answer</option></select>')
        state, vals = self._run(req, answers=ok)
        self.assertEqual(vals["veteran_status"], "I don't wish to answer")
        nodecl = ('<label for="d">Disability *</label><select id="d" name="dis" required><option>Select</option>'
                  '<option>Yes</option><option>No</option></select>')
        state, reasons = self._run(nodecl, answers=ok)
        self.assertEqual(state, "blocked")


if __name__ == "__main__":
    unittest.main()
