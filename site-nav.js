/**
 * Hardin Local — mobile header nav toggle
 * Shows/hides the stacked nav menu behind the hamburger button.
 * Button is hidden on desktop via CSS; script is a no-op if button absent.
 */
(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".header-nav");
  if (!toggle || !nav) return;

  function setOpen(open) {
    nav.classList.toggle("open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.innerHTML = open ? "&times;" : "&#9776;";
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }

  toggle.addEventListener("click", function (e) {
    e.stopPropagation();
    setOpen(!nav.classList.contains("open"));
  });

  // Close on link click (nice for in-page anchors)
  nav.addEventListener("click", function (e) {
    if (e.target.closest(".nav-link")) setOpen(false);
  });

  // Close on outside tap or Esc
  document.addEventListener("click", function (e) {
    if (nav.classList.contains("open") && !nav.contains(e.target) && e.target !== toggle) {
      setOpen(false);
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && nav.classList.contains("open")) setOpen(false);
  });
})();
