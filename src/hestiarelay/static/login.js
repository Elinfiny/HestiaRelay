"use strict";
let csrf;
const form = document.getElementById("login-form");
const key = document.getElementById("access-key");
const button = document.getElementById("login-submit");
const status = document.getElementById("login-status");
async function prepare() {
  try {
    const response = await fetch("/auth/session");
    if (!response.ok) throw new Error("Sign-in is unavailable. Refresh to try again.");
    const data = await response.json();
    if (!data.required || data.authenticated) { location.replace("/"); return; }
    csrf = data.csrf_token;
    button.disabled = false;
    status.textContent = "Ready when you are.";
  } catch (error) { status.textContent = error.message; }
}
form.addEventListener("submit", async event => {
  event.preventDefault();
  button.disabled = true;
  status.textContent = "Checking your access…";
  const supplied = key.value;
  key.value = "";
  try {
    const response = await fetch("/auth/login", {method:"POST", headers:{"Content-Type":"application/json", "X-CSRF-Token":csrf}, body:JSON.stringify({key:supplied})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Sign-in unsuccessful. Try again.");
    location.replace("/");
  } catch (error) { status.textContent = error.message; button.disabled = false; key.focus(); }
});
window.addEventListener("pageshow", event => { if (event.persisted) location.reload(); });
prepare();
