(function () {
  "use strict";

  var API_BASE = window.OLS_API_BASE;
  var textarea = document.getElementById("input-text");
  var charCount = document.getElementById("char-count");
  var submitBtn = document.getElementById("submit-btn");
  var submitError = document.getElementById("submit-error");
  var promptList = document.getElementById("prompt-list");
  var emptyNote = document.getElementById("empty-note");

  function esc(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  textarea.addEventListener("input", function () {
    charCount.textContent = textarea.value.length + " / 2000";
  });

  function loadFeed() {
    fetch(API_BASE + "/prompts")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var prompts = data.prompts || [];
        if (prompts.length === 0) {
          promptList.innerHTML = "";
          emptyNote.style.display = "block";
          return;
        }
        emptyNote.style.display = "none";
        promptList.innerHTML = prompts.map(function (p) {
          var author = p.authenticated_user_id || p.display_name || "Anonymous";
          var when = new Date(p.created_at).toLocaleString();
          return '<div class="prompt-row"><span class="prompt-time">' + esc(when) + '</span>' +
            '<span class="prompt-author">' + esc(author) + '</span>' + esc(p.text) + '</div>';
        }).join("");
      });
  }

  submitBtn.addEventListener("click", function () {
    var text = textarea.value.trim();
    submitError.textContent = "";
    if (!text) { submitError.textContent = "Prompt text is required."; return; }
    var session = window.OLS.getSession();
    submitBtn.disabled = true;
    fetch(API_BASE + "/prompts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: session.session_id,
        display_name: session.display_name,
        authenticated_user_id: session.authenticated_user_id,
        text: text,
      }),
    })
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, d: d }; }); })
      .then(function (res) {
        submitBtn.disabled = false;
        if (res.status !== 201) {
          submitError.textContent = (res.d && res.d.error) || "Unexpected error.";
          return;
        }
        textarea.value = "";
        charCount.textContent = "0 / 2000";
        loadFeed();
      })
      .catch(function () {
        submitBtn.disabled = false;
        submitError.textContent = "Network error.";
      });
  });

  document.getElementById("refresh-btn").addEventListener("click", loadFeed);

  loadFeed();
})();
