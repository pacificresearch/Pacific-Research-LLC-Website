/* Pacific Research Group LLC — site interactions (vanilla JS, no build step) */
(function () {
  "use strict";

  // ---- Icons: turn [data-icon] into Lucide glyphs (prepended so text survives) ----
  function mountIcons() {
    document.querySelectorAll("[data-icon]").forEach(function (el) {
      if (el.dataset.iconMounted) return;
      el.dataset.iconMounted = "1";
      var i = document.createElement("i");
      i.setAttribute("data-lucide", el.getAttribute("data-icon"));
      el.insertBefore(i, el.firstChild);
    });
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
  }
  if (document.readyState !== "loading") mountIcons();
  else document.addEventListener("DOMContentLoaded", mountIcons);

  // ---- Sticky header state ----
  var header = document.getElementById("header");
  function onScroll() {
    if (!header) return;
    header.classList.toggle("scrolled", window.scrollY > 24);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ---- Mobile drawer ----
  var drawer = document.getElementById("drawer");
  var menuToggle = document.getElementById("menuToggle");
  var drawerClose = document.getElementById("drawerClose");
  function openDrawer() { drawer && drawer.classList.add("open"); document.body.style.overflow = "hidden"; }
  function closeDrawer() { drawer && drawer.classList.remove("open"); document.body.style.overflow = ""; }
  menuToggle && menuToggle.addEventListener("click", openDrawer);
  drawerClose && drawerClose.addEventListener("click", closeDrawer);
  if (drawer) {
    drawer.addEventListener("click", function (e) { if (e.target === drawer) closeDrawer(); });
    drawer.querySelectorAll("a").forEach(function (a) { a.addEventListener("click", closeDrawer); });
  }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") closeDrawer(); });

  // ---- Scroll reveal ----
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("in"); });
  }

  // ---- Contact form → mailto (no backend required) ----
  var form = document.getElementById("contactForm");
  var success = document.getElementById("formSuccess");
  var RECIPIENT = "contact@pacificresearchllc.com";
  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = (form.name.value || "").trim();
      var email = (form.email.value || "").trim();
      var org = (form.org.value || "").trim();
      var vehicle = form.vehicle.value || "";
      var message = (form.message.value || "").trim();
      if (!name || !email) {
        form.querySelector(name ? "#f-email" : "#f-name").focus();
        return;
      }
      var subject = "Capability Statement Request — " + (org || name);
      var body =
        "Name: " + name + "\n" +
        "Email: " + email + "\n" +
        "Agency / Organization: " + (org || "—") + "\n" +
        "Contract vehicle: " + vehicle + "\n\n" +
        "Message:\n" + (message || "—") + "\n";
      var href = "mailto:" + RECIPIENT +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);
      window.location.href = href;
      form.classList.add("hidden");
      if (success) { success.classList.remove("hidden"); mountIcons(); }
    });
  }

  // ---- Talent pool form ----------------------------------------------------
  // Primary path: POST the multipart form (CV file included) to Netlify Forms.
  // Fallback: if that fails for any reason, hand the visitor a pre-filled
  // mailto so the submission still reaches PRG — they attach the CV there.
  var talentForm = document.getElementById("talentForm");
  var talentSuccess = document.getElementById("talentSuccess");
  var talentFallback = document.getElementById("talentFallback");
  var MAX_CV_BYTES = 8 * 1024 * 1024;

  function talentMailto(fd) {
    function g(k) { return (fd.get(k) || "").toString().trim() || "\u2014"; }
    var subject = "Talent Pool Submission \u2014 " + g("name") + " (" + g("discipline") + ")";
    var body =
      "TALENT POOL SUBMISSION\n" +
      "Please attach your CV to this email before sending.\n\n" +
      "Name: " + g("name") + "\n" +
      "Email: " + g("email") + "\n" +
      "Phone: " + g("phone") + "\n" +
      "Location: " + g("location") + "\n" +
      "Primary discipline: " + g("discipline") + "\n" +
      "Years of experience: " + g("years") + "\n" +
      "Security clearance: " + g("clearance") + "\n" +
      "Work authorization: " + g("work_authorization") + "\n" +
      "Availability: " + g("availability") + "\n" +
      "Relocation & travel: " + g("mobility") + "\n" +
      "Credentials: " + g("credentials") + "\n" +
      "LinkedIn / portfolio: " + g("link") + "\n" +
      "Veteran / military spouse: " + (fd.get("veteran") ? "Yes" : "Not stated") + "\n" +
      "Consent to retention & contact: " + (fd.get("consent") ? "Yes" : "No") + "\n\n" +
      "Notes:\n" + g("notes") + "\n";
    return "mailto:" + RECIPIENT +
      "?subject=" + encodeURIComponent(subject) +
      "&body=" + encodeURIComponent(body);
  }

  function showTalentResult(el) {
    talentForm.classList.add("hidden");
    if (el) { el.classList.remove("hidden"); mountIcons(); }
  }

  if (talentForm) {
    talentForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var name = (talentForm.elements.name.value || "").trim();
      var email = (talentForm.elements.email.value || "").trim();
      var consent = talentForm.elements.consent.checked;
      if (!name) { talentForm.querySelector("#t-name").focus(); return; }
      if (!email) { talentForm.querySelector("#t-email").focus(); return; }
      if (!consent) { talentForm.querySelector("#t-consent").focus(); return; }

      var fd = new FormData(talentForm);
      var cv = talentForm.elements.cv.files[0];
      if (cv && cv.size > MAX_CV_BYTES) {
        window.alert("That CV is larger than 8 MB. Please upload a smaller file, " +
                     "or submit without it and email the CV to " + RECIPIENT + ".");
        return;
      }

      var btn = talentForm.querySelector('button[type="submit"]');
      if (btn) { btn.disabled = true; btn.textContent = "Sending\u2026"; }

      var done = false;
      function finish(ok) {
        if (done) return;
        done = true;
        if (ok) { showTalentResult(talentSuccess); }
        else {
          try { window.location.href = talentMailto(fd); } catch (err) { /* no-op */ }
          showTalentResult(talentFallback);
        }
      }

      if (!window.fetch) { finish(false); return; }
      fetch(talentForm.getAttribute("action") || "/", { method: "POST", body: fd })
        .then(function (res) { finish(res.ok); })
        .catch(function () { finish(false); });
    });
  }
})();
