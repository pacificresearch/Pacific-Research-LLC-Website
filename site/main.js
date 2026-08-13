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
})();
