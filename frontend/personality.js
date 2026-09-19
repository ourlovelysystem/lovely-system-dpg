(function () {
  "use strict";

  var API_BASE = window.OLS_API_BASE;

  var signinGate = document.getElementById("signin-gate");
  var composerFields = document.getElementById("composer-fields");
  var nameInput = document.getElementById("name-input");
  var promptsInput = document.getElementById("prompts-input");
  var modelSelect = document.getElementById("model-select");
  var charCount = document.getElementById("char-count");
  var submitBtn = document.getElementById("submit-btn");
  var submitError = document.getElementById("submit-error");
  var personalityList = document.getElementById("personality-list");
  var emptyNote = document.getElementById("empty-note");

  function esc(s) {
    return String(s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  promptsInput.addEventListener("input", function () {
    charCount.textContent = promptsInput.value.length + " / 4000";
  });

  function loadModels() {
    var session = window.OLS.getSession();
    if (!session.authenticated_user_id) {
      signinGate.style.display = "block";
      composerFields.style.display = "none";
      return;
    }
    fetch(API_BASE + "/models?authenticated_user_id=" + encodeURIComponent(session.authenticated_user_id))
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, d: d }; }); })
      .then(function (res) {
        if (res.status !== 200) {
          signinGate.textContent = (res.d && res.d.error) || "Sign in to see available models.";
          signinGate.style.display = "block";
          composerFields.style.display = "none";
          return;
        }
        signinGate.style.display = "none";
        composerFields.style.display = "block";
        var models = res.d.models || [];
        modelSelect.innerHTML = models.map(function (m) {
          return '<option value="' + esc(m.id) + '">' + esc(m.provider) + ' — ' + esc(m.name) + '</option>';
        }).join("");
      });
  }

  function loadPersonalities() {
    fetch(API_BASE + "/personalities")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var personalities = data.personalities || [];
        if (personalities.length === 0) {
          personalityList.innerHTML = "";
          emptyNote.style.display = "block";
          return;
        }
        emptyNote.style.display = "none";
        personalityList.innerHTML = personalities.map(function (p) {
          var author = p.authenticated_user_id || p.display_name || "Anonymous";
          var when = new Date(p.created_at).toLocaleString();
          return '<div class="personality-row">' +
            '<span class="personality-author">' + esc(when) + ' &middot; ' + esc(author) + '</span>' +
            '<span class="personality-name">' + esc(p.name) + '</span>' +
            '<span class="personality-model">' + esc(p.model_id) + '</span>' +
            '<div class="personality-prompts">' + esc(p.prompts) + '</div>' +
            '</div>';
        }).join("");
      });
  }

  submitBtn.addEventListener("click", function () {
    var session = window.OLS.getSession();
    var name = nameInput.value.trim();
    var prompts = promptsInput.value.trim();
    var modelId = modelSelect.value;
    submitError.textContent = "";
    if (!name) { submitError.textContent = "Name is required."; return; }
    if (!prompts) { submitError.textContent = "Prompts are required."; return; }
    if (!modelId) { submitError.textContent = "Choose a model."; return; }

    submitBtn.disabled = true;
    fetch(API_BASE + "/personalities", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: session.session_id,
        display_name: session.display_name,
        authenticated_user_id: session.authenticated_user_id,
        name: name,
        prompts: prompts,
        model_id: modelId,
      }),
    })
      .then(function (r) { return r.json().then(function (d) { return { status: r.status, d: d }; }); })
      .then(function (res) {
        submitBtn.disabled = false;
        if (res.status !== 201) {
          submitError.textContent = (res.d && res.d.error) || "Unexpected error.";
          return;
        }
        nameInput.value = "";
        promptsInput.value = "";
        charCount.textContent = "0 / 4000";
        loadPersonalities();
      })
      .catch(function () {
        submitBtn.disabled = false;
        submitError.textContent = "Network error.";
      });
  });

  document.getElementById("refresh-btn").addEventListener("click", loadPersonalities);

  loadModels();
  loadPersonalities();
})();
