(function () {
  "use strict";

  var API_BASE = window.OLS_API_BASE;
  var textarea = document.getElementById("input-text");
  var charCount = document.getElementById("char-count");
  var submitBtn = document.getElementById("submit-btn");
  var submitError = document.getElementById("submit-error");
  var promptList = document.getElementById("prompt-list");
  var emptyNote = document.getElementById("empty-note");

  var personalitiesCache = [];
  var pollTimers = {};

  function esc(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  textarea.addEventListener("input", function () {
    charCount.textContent = textarea.value.length + " / 2000";
  });

  function loadPersonalities() {
    return fetch(API_BASE + "/personalities")
      .then(function (r) { return r.json(); })
      .then(function (data) { personalitiesCache = data.personalities || []; });
  }

  function renderAnswers(promptId, answers) {
    var el = document.getElementById("answers-" + promptId);
    if (!el) return;
    el.innerHTML = answers.map(function (a) {
      var author = a.author_type === "personality" ? a.personality_name : (a.authenticated_user_id || a.display_name || "Anonymous");
      if (a.status === "pending") {
        return '<div class="answer-row"><span class="answer-author">' + esc(author) + '</span><span class="answer-pending">&hellip;thinking</span></div>';
      }
      if (a.status === "error") {
        return '<div class="answer-row"><span class="answer-author">' + esc(author) + '</span><span class="answer-error">failed to respond: ' + esc(a.text) + '</span></div>';
      }
      return '<div class="answer-row"><span class="answer-author">' + esc(author) + '</span>' + esc(a.text) + '</div>';
    }).join("");
  }

  function loadAnswers(promptId) {
    return fetch(API_BASE + "/answers/" + promptId)
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var answers = data.answers || [];
        renderAnswers(promptId, answers);
        var stillPending = answers.some(function (a) { return a.status === "pending"; });
        if (stillPending) {
          pollTimers[promptId] = setTimeout(function () { loadAnswers(promptId); }, 2000);
        }
      });
  }

  function loadFeed() {
    Object.keys(pollTimers).forEach(function (k) { clearTimeout(pollTimers[k]); });
    pollTimers = {};
    return fetch(API_BASE + "/prompts")
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
          return '<div class="prompt-item" data-prompt-id="' + esc(p.prompt_id) + '">' +
            '<div class="prompt-row"><span class="prompt-time">' + esc(when) + '</span>' +
            '<span class="prompt-author">' + esc(author) + '</span>' + esc(p.text) + '</div>' +
            '<div class="answers-list" id="answers-' + esc(p.prompt_id) + '"></div>' +
            '<button class="reply-btn" data-action="toggle-reply">Reply</button>' +
            '<div class="reply-panel" id="reply-' + esc(p.prompt_id) + '" style="display:none;">' +
              '<div class="reply-tabs">' +
                '<button class="tab-btn active" data-mode="self">Respond as yourself</button>' +
                '<button class="tab-btn" data-mode="personality">Respond as a personality</button>' +
              '</div>' +
              '<div class="reply-mode-self">' +
                '<textarea class="reply-text" maxlength="2000" placeholder="Your answer..."></textarea>' +
              '</div>' +
              '<div class="reply-mode-personality" style="display:none;">' +
                '<select class="personality-select">' +
                  (personalitiesCache.length === 0
                    ? '<option value="">No personalities exist yet</option>'
                    : personalitiesCache.map(function (per) {
                        return '<option value="' + esc(per.personality_id) + '">' + esc(per.name) + '</option>';
                      }).join("")) +
                '</select>' +
              '</div>' +
              '<div class="composer-row"><span></span><button class="md-btn" data-action="submit-reply">Submit</button></div>' +
              '<div class="error-note reply-error"></div>' +
            '</div>' +
            '</div>';
        }).join("");
        prompts.forEach(function (p) { loadAnswers(p.prompt_id); });
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

  promptList.addEventListener("click", function (e) {
    var promptItem = e.target.closest(".prompt-item");
    if (!promptItem) return;
    var promptId = promptItem.getAttribute("data-prompt-id");

    if (e.target.matches('[data-action="toggle-reply"]')) {
      var panel = document.getElementById("reply-" + promptId);
      panel.style.display = panel.style.display === "none" ? "block" : "none";
      return;
    }

    if (e.target.matches(".tab-btn")) {
      var tabs = promptItem.querySelectorAll(".tab-btn");
      tabs.forEach(function (t) { t.classList.remove("active"); });
      e.target.classList.add("active");
      var mode = e.target.getAttribute("data-mode");
      promptItem.querySelector(".reply-mode-self").style.display = mode === "self" ? "block" : "none";
      promptItem.querySelector(".reply-mode-personality").style.display = mode === "personality" ? "block" : "none";
      return;
    }

    if (e.target.matches('[data-action="submit-reply"]')) {
      var panelEl = promptItem.querySelector(".reply-panel");
      var activeMode = panelEl.querySelector(".tab-btn.active").getAttribute("data-mode");
      var errorEl = panelEl.querySelector(".reply-error");
      var session = window.OLS.getSession();
      errorEl.textContent = "";

      var payload = {
        prompt_id: promptId,
        session_id: session.session_id,
        display_name: session.display_name,
        authenticated_user_id: session.authenticated_user_id,
        mode: activeMode,
      };

      if (activeMode === "self") {
        var text = panelEl.querySelector(".reply-text").value.trim();
        if (!text) { errorEl.textContent = "Answer text is required."; return; }
        payload.text = text;
      } else {
        var personalityId = panelEl.querySelector(".personality-select").value;
        if (!personalityId) { errorEl.textContent = "Choose a personality."; return; }
        payload.personality_id = personalityId;
      }

      e.target.disabled = true;
      fetch(API_BASE + "/answers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) { return r.json().then(function (d) { return { status: r.status, d: d }; }); })
        .then(function (res) {
          e.target.disabled = false;
          if (res.status !== 201 && res.status !== 202) {
            errorEl.textContent = (res.d && res.d.error) || "Unexpected error.";
            return;
          }
          panelEl.style.display = "none";
          if (activeMode === "self") panelEl.querySelector(".reply-text").value = "";
          loadAnswers(promptId);
        })
        .catch(function () {
          e.target.disabled = false;
          errorEl.textContent = "Network error.";
        });
    }
  });

  loadPersonalities().then(loadFeed);
})();
