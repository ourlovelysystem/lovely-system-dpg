(function () {
  "use strict";

  // Top banner only (2026-09-19): alias/self-ID, session id, sign-in/out -
  // adapted from Touchstone's ols-session-banner.js. Deliberately excludes
  // Touchstone-specific pieces (bottom approve/disapprove banner, admin
  // group, calibration) - those aren't part of the generic shared banner.

  var COOKIE_NAME = "ols_session";
  var COOKIE_DOMAIN = ".ourlovelysystem.org";

  var COGNITO_DOMAIN = "https://ourlovelysystem-867712763388.auth.us-east-1.amazoncognito.com";
  var COGNITO_CLIENT_ID = "2ll91kmvbmpqofej9h5kkeg8no";
  var REDIRECT_URI = "https://dpg.ourlovelysystem.org/";

  function randomId() {
    return "s" + Math.random().toString(36).slice(2) + Date.now().toString(36);
  }

  function base64url(bytes) {
    var s = btoa(String.fromCharCode.apply(null, bytes));
    return s.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  }

  function readCookie() {
    var match = document.cookie.match(new RegExp("(?:^|; )" + COOKIE_NAME + "=([^;]*)"));
    if (!match) return null;
    try {
      return JSON.parse(decodeURIComponent(match[1]));
    } catch (e) {
      return null;
    }
  }

  function writeCookie(session) {
    var value = encodeURIComponent(JSON.stringify(session));
    var expires = new Date(Date.now() + 400 * 24 * 60 * 60 * 1000).toUTCString();
    document.cookie =
      COOKIE_NAME + "=" + value + "; expires=" + expires + "; path=/; domain=" + COOKIE_DOMAIN + "; SameSite=Lax";
  }

  var session = readCookie();
  if (!session) {
    session = { session_id: randomId(), display_name: "", authenticated_user_id: null, id_token: null };
    writeCookie(session);
  }

  var style = document.createElement("style");
  style.textContent =
    ".ols-session-banner{font-family:Roboto,Arial,sans-serif;background:#1565c0;color:#ffffff;" +
    "display:grid;grid-template-columns:1fr 1fr 1fr;align-items:center;gap:10px 24px;padding:12px 20px;box-shadow:0 2px 4px rgba(0,0,0,0.3);" +
    "position:relative;z-index:1000;font-size:13px;line-height:1.6;}" +
    ".ols-session-banner .ols-field{display:flex;align-items:center;gap:8px;flex-wrap:wrap;min-height:28px;}" +
    ".ols-session-banner .ols-field.ols-left{justify-content:flex-start;}" +
    ".ols-session-banner .ols-field.ols-center{justify-content:center;}" +
    ".ols-session-banner .ols-field.ols-right{justify-content:flex-end;}" +
    ".ols-session-banner label{opacity:0.85;white-space:nowrap;}" +
    ".ols-session-banner code{word-break:break-all;background:rgba(255,255,255,0.15);padding:2px 6px;border-radius:3px;}" +
    ".ols-session-banner input{background:#ffffff;color:#111111;border:none;border-radius:4px;padding:5px 9px;font-size:13px;}" +
    ".ols-session-banner button{background:#ffffff;color:#1565c0;border:none;border-radius:4px;padding:5px 12px;" +
    "font-size:13px;cursor:pointer;font-weight:500;white-space:nowrap;}";
  document.head.appendChild(style);

  var banner = document.createElement("div");
  banner.className = "ols-session-banner";
  banner.innerHTML =
    '<div class="ols-field ols-left"><label>Alias</label>' +
    '<input id="ols-name-input" type="text" maxlength="80" placeholder="alias (optional)" value="' +
    (session.display_name || "").replace(/"/g, "&quot;") + '"/>' +
    '<button id="ols-name-submit">Update</button></div>' +
    '<div class="ols-field ols-center"><label>Session</label>' +
    '<code id="ols-session-id">' + session.session_id + "</code></div>" +
    '<div class="ols-field ols-right" id="ols-auth-field"></div>';
  document.body.insertBefore(banner, document.body.firstChild);

  function renderAuthField() {
    var field = document.getElementById("ols-auth-field");
    if (session.authenticated_user_id) {
      field.innerHTML =
        '<label>Signed in</label><code>' + session.authenticated_user_id + "</code>" +
        '<button id="ols-signout-btn">Sign out</button>';
      document.getElementById("ols-signout-btn").addEventListener("click", signOut);
    } else {
      field.innerHTML = '<button id="ols-signin-btn">Sign in (Google / Amazon / Apple)</button>';
      document.getElementById("ols-signin-btn").addEventListener("click", signIn);
    }
  }

  function signIn() {
    var verifierBytes = crypto.getRandomValues(new Uint8Array(32));
    var codeVerifier = base64url(verifierBytes);
    sessionStorage.setItem("ols_pkce_verifier", codeVerifier);
    crypto.subtle.digest("SHA-256", new TextEncoder().encode(codeVerifier)).then(function (hashBuf) {
      var codeChallenge = base64url(new Uint8Array(hashBuf));
      var url = COGNITO_DOMAIN + "/oauth2/authorize" +
        "?client_id=" + encodeURIComponent(COGNITO_CLIENT_ID) +
        "&response_type=code" +
        "&scope=" + encodeURIComponent("openid email profile") +
        "&redirect_uri=" + encodeURIComponent(REDIRECT_URI) +
        "&code_challenge_method=S256" +
        "&code_challenge=" + codeChallenge;
      window.location.href = url;
    });
  }

  function signOut() {
    session.authenticated_user_id = null;
    session.id_token = null;
    writeCookie(session);
    var url = COGNITO_DOMAIN + "/logout" +
      "?client_id=" + encodeURIComponent(COGNITO_CLIENT_ID) +
      "&logout_uri=" + encodeURIComponent(REDIRECT_URI);
    window.location.href = url;
  }

  function decodeJwtPayload(jwt) {
    var payload = jwt.split(".")[1];
    payload = payload.replace(/-/g, "+").replace(/_/g, "/");
    while (payload.length % 4) payload += "=";
    return JSON.parse(atob(payload));
  }

  function exchangeCodeForToken(code) {
    var codeVerifier = sessionStorage.getItem("ols_pkce_verifier");
    if (!codeVerifier) return;
    var body = new URLSearchParams({
      grant_type: "authorization_code",
      client_id: COGNITO_CLIENT_ID,
      code: code,
      redirect_uri: REDIRECT_URI,
      code_verifier: codeVerifier,
    });
    fetch(COGNITO_DOMAIN + "/oauth2/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    })
      .then(function (r) { return r.json(); })
      .then(function (tokens) {
        if (!tokens.id_token) return;
        var claims = decodeJwtPayload(tokens.id_token);
        session.authenticated_user_id = claims.email || claims.sub;
        session.id_token = tokens.id_token;
        writeCookie(session);
        renderAuthField();
        var cleanUrl = window.location.origin + window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
      });
  }

  var urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has("code")) {
    exchangeCodeForToken(urlParams.get("code"));
  }

  document.getElementById("ols-name-submit").addEventListener("click", function () {
    session.display_name = document.getElementById("ols-name-input").value.slice(0, 80);
    writeCookie(session);
  });

  renderAuthField();

  window.OLS = {
    getSession: function () {
      return {
        session_id: session.session_id,
        display_name: session.display_name,
        authenticated_user_id: session.authenticated_user_id,
      };
    },
  };
})();
