/**
 * Hardin Local — Newsletter exit-intent popup
 *
 * Triggers when:
 *   Desktop: mouse leaves viewport through the top
 *   Mobile: user scrolls down 60%+ then pauses for 3s, or back-button tap
 *
 * Shows once per visitor (localStorage flag).
 *
 * Config: set window.HL_API_URL before loading this script.
 *   Local dev:  window.HL_API_URL = "http://localhost:8766"
 *   Production: window.HL_API_URL = "https://your-worker.workers.dev"
 */

(function () {
  var STORAGE_KEY = "hl_newsletter_dismissed";
  var API_URL = window.HL_API_URL || "http://localhost:8766";

  // Already shown or already subscribed
  if (localStorage.getItem(STORAGE_KEY)) return;

  // --- Inject styles ---
  var style = document.createElement("style");
  style.textContent = [
    ".hl-popup-overlay {",
    "  position:fixed; inset:0; z-index:9999;",
    "  background:rgba(0,0,0,.55); backdrop-filter:blur(3px);",
    "  display:flex; align-items:center; justify-content:center;",
    "  padding:1rem;",
    "  animation: hlFadeIn .25s ease;",
    "}",
    ".hl-popup {",
    "  background:#fff; border-radius:16px; max-width:400px; width:100%;",
    "  padding:2rem 1.75rem; text-align:center; position:relative;",
    "  box-shadow:0 20px 60px rgba(0,0,0,.25);",
    "  animation: hlSlideUp .3s ease;",
    "}",
    ".hl-popup-close {",
    "  position:absolute; top:12px; right:14px;",
    "  background:none; border:none; font-size:1.4rem;",
    "  color:#999; cursor:pointer; line-height:1; padding:4px;",
    "}",
    ".hl-popup-close:hover { color:#333; }",
    ".hl-popup-eyebrow {",
    "  font-size:.72rem; font-weight:700; letter-spacing:.1em;",
    "  text-transform:uppercase; color:#4885ed; margin-bottom:.5rem;",
    "}",
    ".hl-popup h2 {",
    "  font-size:1.35rem; font-weight:800; color:#333943;",
    "  line-height:1.25; margin:0 0 .5rem;",
    "}",
    ".hl-popup p {",
    "  font-size:.92rem; color:#6b7280; line-height:1.5; margin:0 0 1.25rem;",
    "}",
    ".hl-popup-form {",
    "  display:flex; gap:.5rem; flex-wrap:wrap;",
    "}",
    ".hl-popup-input {",
    "  flex:1; min-width:0; padding:.7rem 1rem;",
    "  font-size:.92rem; border:2px solid #e5e7eb; border-radius:999px;",
    "  outline:none; font-family:inherit; color:#333943;",
    "  transition: border-color .15s ease;",
    "}",
    ".hl-popup-input:focus { border-color:#4885ed; }",
    ".hl-popup-input::placeholder { color:#aaa; }",
    ".hl-popup-submit {",
    "  padding:.7rem 1.25rem; font-size:.88rem; font-weight:700;",
    "  background:#4885ed; color:#fff; border:none; border-radius:999px;",
    "  cursor:pointer; font-family:inherit; white-space:nowrap;",
    "  transition: background .15s ease;",
    "}",
    ".hl-popup-submit:hover { background:#3070d6; }",
    ".hl-popup-submit:disabled { background:#a0b8e8; cursor:wait; }",
    ".hl-popup-msg {",
    "  font-size:.82rem; margin-top:.6rem; min-height:1.2em;",
    "}",
    ".hl-popup-msg.error { color:#D32F2F; }",
    ".hl-popup-msg.success { color:#2E7D32; }",
    ".hl-popup-skip {",
    "  display:inline-block; margin-top:1rem; font-size:.78rem;",
    "  color:#999; cursor:pointer; border:none; background:none;",
    "  font-family:inherit; text-decoration:underline;",
    "}",
    ".hl-popup-skip:hover { color:#666; }",
    "@keyframes hlFadeIn { from{opacity:0} to{opacity:1} }",
    "@keyframes hlSlideUp { from{transform:translateY(30px);opacity:0} to{transform:translateY(0);opacity:1} }",
    "@media (max-width:480px) {",
    "  .hl-popup { padding:1.5rem 1.25rem; }",
    "  .hl-popup h2 { font-size:1.15rem; }",
    "  .hl-popup-form { flex-direction:column; }",
    "  .hl-popup-submit { width:100%; }",
    "}"
  ].join("\n");
  document.head.appendChild(style);

  // --- Build popup DOM ---
  function show() {
    if (document.getElementById("hlPopup")) return;

    var overlay = document.createElement("div");
    overlay.className = "hl-popup-overlay";
    overlay.id = "hlPopup";
    overlay.innerHTML = [
      '<div class="hl-popup">',
      '  <button class="hl-popup-close" id="hlClose" aria-label="Close">&times;</button>',
      '  <div class="hl-popup-eyebrow">Hardin Local</div>',
      '  <h2>Enjoy our content?</h2>',
      '  <p>Sign up for our email newsletter — coming soon. Be the first to get local events, traffic updates, and community news straight to your inbox.</p>',
      '  <form class="hl-popup-form" id="hlForm">',
      '    <input type="email" class="hl-popup-input" id="hlEmail" placeholder="your@email.com" required autocomplete="email" />',
      '    <button type="submit" class="hl-popup-submit" id="hlSubmit">Count me in</button>',
      '  </form>',
      '  <div class="hl-popup-msg" id="hlMsg"></div>',
      '  <button class="hl-popup-skip" id="hlSkip">No thanks</button>',
      '</div>'
    ].join("\n");

    document.body.appendChild(overlay);

    // Close handlers
    document.getElementById("hlClose").onclick = dismiss;
    document.getElementById("hlSkip").onclick = dismiss;
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) dismiss();
    });

    // Submit handler
    document.getElementById("hlForm").addEventListener("submit", function (e) {
      e.preventDefault();
      submit();
    });
  }

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    var el = document.getElementById("hlPopup");
    if (el) el.remove();
  }

  function submit() {
    var emailInput = document.getElementById("hlEmail");
    var btn = document.getElementById("hlSubmit");
    var msg = document.getElementById("hlMsg");
    var email = emailInput.value.trim();

    if (!email) return;

    btn.disabled = true;
    btn.textContent = "Sending...";
    msg.className = "hl-popup-msg";
    msg.textContent = "";

    var source = location.pathname.split("/").pop() || "index.html";

    var xhr = new XMLHttpRequest();
    xhr.open("POST", API_URL + "/subscribe");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = function () {
      try {
        var data = JSON.parse(xhr.responseText);
        if (xhr.status === 200 && data.ok) {
          msg.className = "hl-popup-msg success";
          msg.textContent = "You're on the list! We'll be in touch.";
          localStorage.setItem(STORAGE_KEY, "subscribed");
          btn.textContent = "Done";
          setTimeout(function () {
            var el = document.getElementById("hlPopup");
            if (el) el.remove();
          }, 2000);
        } else {
          msg.className = "hl-popup-msg error";
          msg.textContent = data.error || "Something went wrong. Try again.";
          btn.disabled = false;
          btn.textContent = "Count me in";
        }
      } catch (_) {
        msg.className = "hl-popup-msg error";
        msg.textContent = "Something went wrong. Try again.";
        btn.disabled = false;
        btn.textContent = "Count me in";
      }
    };
    xhr.onerror = function () {
      msg.className = "hl-popup-msg error";
      msg.textContent = "Connection error. Try again.";
      btn.disabled = false;
      btn.textContent = "Count me in";
    };
    xhr.send(JSON.stringify({ email: email, source: source }));
  }

  // --- Exit-intent triggers ---
  var shown = false;
  var minTimeOnPage = 5000; // wait 5s before arming
  var armed = false;

  setTimeout(function () { armed = true; }, minTimeOnPage);

  // Desktop: mouse leaves through top of viewport
  document.addEventListener("mouseout", function (e) {
    if (!armed || shown) return;
    if (e.clientY <= 0 && e.relatedTarget == null) {
      shown = true;
      show();
    }
  });

  // Mobile: user scrolls 60%+ then stops for 3s
  var scrollTimer = null;
  var hitThreshold = false;
  window.addEventListener("scroll", function () {
    if (!armed || shown) return;
    var scrollPct = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
    if (scrollPct > 0.6) hitThreshold = true;
    if (hitThreshold) {
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(function () {
        if (!shown) { shown = true; show(); }
      }, 3000);
    }
  });

  // Mobile: back button / visibilitychange
  document.addEventListener("visibilitychange", function () {
    if (!armed || shown) return;
    if (document.visibilityState === "hidden") {
      // Can't show popup when hidden, but mark for next visit?
      // Skip — exit intent on mobile is best-effort
    }
  });
})();
