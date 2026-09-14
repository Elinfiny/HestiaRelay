"use strict";
const $ = (id) => document.getElementById(id);
let snapshot;
let sessionId = sessionStorage.getItem("hestia-session");
let busy = false;
let csrfToken = null;
let leaving = false;
function signIn() {
  if (leaving) return;
  leaving = true; snapshot = null;
  document.body.replaceChildren(); location.replace("/login");
}
const money = (value) => value == null ? "—" : new Intl.NumberFormat("en-US", {style:"currency", currency:"USD", maximumFractionDigits:2}).format(value);
function element(tag, text, className) {
  const el = document.createElement(tag);
  if (text !== undefined) el.textContent = text;
  if (className) el.className = className;
  return el;
}
async function api(path, body) {
  const response = await fetch(path, body ? {method:"POST", headers:{"Content-Type":"application/json", ...(csrfToken ? {"X-CSRF-Token":csrfToken} : {})}, body:JSON.stringify(body)} : {});
  if (response.status === 401) { signIn(); throw new Error("Sign in to continue."); }
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Request failed. Refresh to recover saved state.");
  return data;
}
async function act(work, announcement) {
  if (busy) return;
  busy = true;
  $("error").hidden = true;
  $("status").textContent = "Saving your thread…";
  renderDisabled();
  try { snapshot = await work(); render(); $("status").textContent = announcement; }
  catch (error) { if (leaving) return; $("error").textContent = error.message; $("error").hidden = false; $("status").textContent = "No completion claimed. Your saved thread remains available."; }
  finally { busy = false; renderDisabled(); }
}
function renderDisabled() {
  if (leaving) return;
  document.querySelectorAll("button").forEach(button => { button.disabled = busy; });
  if (!snapshot) return;
  const texts = snapshot.state.turns.map(t => t.user_text);
  for (let i = 0; i < 3; i++) {
    const done = texts.includes(snapshot.canonical_messages[i]);
    $("demo-"+i).disabled = busy || done || (i > 0 && !snapshot.state.goal);
  }
  document.querySelectorAll("button[data-stale]").forEach(button => { button.disabled = true; });
}
async function newSession() {
  const id = crypto.randomUUID();
  const data = await api("/api/session", {session_id:id});
  sessionId = id;
  sessionStorage.setItem("hestia-session", id);
  return data;
}
function render() {
  const state = snapshot.state;
  const currentSession = state.sessions.find(s => s.session_id === sessionId);
  $("session-badge").textContent = currentSession ? `Session ${currentSession.number}` : "Start a new session";
  $("goal-title").textContent = state.goal?.title || "A little room for Friday.";
  $("goal-when").textContent = state.goal?.when || "Start the first conversation to make it a plan.";
  $("goal-status").textContent = state.goal ? "Saved · preparation pending" : "Awaiting a plan";
  $("people").textContent = state.goal?.people || "—";
  $("budget").textContent = money(state.goal?.budget_usd);
  $("goal-evidence").textContent = state.goal ? `Persistent goal ID: ${state.goal.goal_id}` : "No goal saved yet.";
  const transcript = $("transcript"); transcript.replaceChildren();
  if (!state.turns.length) {
    const empty = element("div", undefined, "empty");
    empty.append(element("span", "⌂", "house"), element("strong", "A plan worth coming back to."), element("p", "Start with six people and a Friday evening. We’ll keep the details for next time."));
    transcript.append(empty);
  }
  let previous;
  for (const turn of state.turns) {
    const session = state.sessions.find(s => s.session_id === turn.session_id);
    if (previous !== turn.session_id) transcript.append(element("div", `Session ${session?.number || "—"} · ${session?.recovered_goal_id ? "existing goal recovered" : "a new conversation"}`, "session-divider"));
    previous = turn.session_id;
    for (const [role, text] of [["user",turn.user_text],["assistant",turn.reply]]) {
      const bubble = element("div", undefined, "bubble "+role);
      bubble.append(element("span", role === "user" ? "YOU" : "HESTIARELAY", "speaker"), document.createTextNode(text));
      transcript.append(bubble);
    }
  }
  transcript.scrollTop = transcript.scrollHeight;
  $("preferences").replaceChildren();
  for (const pref of state.preferences) {
    const item = element("div", undefined, "constraint");
    item.append(element("strong", pref.person), element("span", pref.note));
    $("preferences").append(item);
  }
  if (!state.preferences.length) $("preferences").append(element("p", "No constraints recorded yet. A later conversation can add them.", "small"));
  $("checklist").replaceChildren(...state.checklist.map(item => element("li", item)));
  if (!state.checklist.length) $("checklist").append(element("li", "Waiting for your household goal."));
  $("provenance").textContent = state.plan?.source || "Not generated";
  $("provenance").className = "badge " + (state.plan?.used_aws ? "safe" : "");
  $("plan-text").textContent = state.plan?.text || "Your plan will appear after the first conversation.";
  $("planner-detail").textContent = state.plan ? (state.plan.used_aws ? `Bedrock response recorded · ${state.plan.model_id}` : state.plan.fallback_reason === "aws_unavailable" ? "AWS unavailable. Explicit deterministic fallback; no successful Bedrock response." : "Deterministic planner · AWS not configured; no AWS call.") + ` Saved ${new Date(state.plan.created_at).toLocaleString("en-US")}.` : "Provenance is recorded with every generated plan.";
  $("proposals").replaceChildren();
  if (!state.proposals.length) $("proposals").append(element("p", "No decisions waiting. Session 3 will surface a purchase-like proposal for review.", "small"));
  for (const proposal of state.proposals) {
    const card = element("article", undefined, "proposal");
    card.append(element("span", `${proposal.risk.toUpperCase()} · ${proposal.status}`, "badge "+proposal.risk), element("h3", proposal.description));
    card.append(element("p", `Exact proposal: ${proposal.action_id}`, "small"));
    const estimate = proposal.payload;
    const completeEstimate = estimate.estimate_only === true &&
      typeof estimate.estimated_total_usd === "number" && Number.isFinite(estimate.estimated_total_usd) && estimate.estimated_total_usd >= 0 &&
      Array.isArray(estimate.items) && estimate.items.length > 0 && estimate.items.every(item => typeof item === "string" && item.trim()) &&
      typeof estimate.merchant === "string" && estimate.merchant.trim();
    if (completeEstimate) {
      card.append(element("p", `${money(proposal.payload.estimated_total_usd)} · illustrative estimate only`));
      card.append(element("p", `Suggested basket: ${proposal.payload.items.join(", ")}.`));
      card.append(element("p", `Merchant: ${proposal.payload.merchant}. Ingredients and cross-contact remain unverified.`, "small"));
      if (state.goal?.budget_usd != null) card.append(element("p", proposal.payload.estimated_total_usd > state.goal.budget_usd ? "This estimate exceeds your saved budget. Revise before any real purchase." : `${money(state.goal.budget_usd - proposal.payload.estimated_total_usd)} below the budget, before any unquoted costs.`, "small"));
    } else if (estimate.estimate_only) card.append(element("p", "Estimate details are incomplete. Inspect the exact proposal scope below.", "small"));
    const scope = element("details");
    scope.append(element("summary", "Inspect the exact proposal scope"), element("pre", JSON.stringify(proposal.payload, null, 2)));
    card.append(scope);
    card.append(element("p", "Simulation only. Approval records consent for this exact proposal; no external action is performed.", "small"));
    if (proposal.status === "pending") {
      const stale = proposal.context_hash !== snapshot.context_hash;
      if (stale) card.append(element("p", "Context changed. Reject this proposal and request a new one.", "small"));
      const actions = element("div", undefined, "decision-buttons");
      for (const approved of [true, false]) {
        const label = approved ? "Approve this proposal" : "Reject this proposal";
        const button = element("button", label, approved ? "approve" : "reject");
        button.type = "button";
        button.setAttribute("aria-label", `${label}: ${proposal.description}`);
        if (approved && stale) button.dataset.stale = "true";
        button.addEventListener("click", () => act(() => api("/api/decision", {action_id:proposal.action_id, approved}), `${approved ? "Approval" : "Rejection"} saved for this proposal. No external action performed.`));
        actions.append(button);
      }
      card.append(actions);
    } else card.append(element("p", `${proposal.status === "approved" ? "Consent recorded" : "Proposal rejected"}. Nothing executed.`, "decision-result"));
    $("proposals").append(card);
  }
  $("timeline").replaceChildren();
  for (const session of state.sessions) {
    const item = element("li");
    const turns = state.turns.filter(t => t.session_id === session.session_id);
    item.append(element("strong", `Session ${session.number}`), element("span", session.recovered_goal_id ? "Recovered the saved goal" : "Opened without a prior goal"), element("small", `${turns.length} message${turns.length === 1 ? "" : "s"} · ${new Date(session.created_at).toLocaleString("en-US")}`), element("small", `Session ID: ${session.session_id}`));
    if (session.recovered_goal_id) item.append(element("small", `Recovered goal: ${session.recovered_goal_id}`));
    $("timeline").append(item);
  }
  if (!state.sessions.length) $("timeline").append(element("li", "Your first session starts the thread."));
  snapshot.canonical_messages.forEach((text, i) => {
    const done = state.turns.some(t => t.user_text === text);
    $("demo-"+i).className = "step " + (done ? "done" : i === 0 || state.turns.some(t => t.user_text === snapshot.canonical_messages[i-1]) ? "active" : "");
    $("demo-"+i).querySelector(".step-state").textContent = done ? "Saved ✓" : "New session →";
  });
}
for (let i = 0; i < 3; i++) $("demo-"+i).addEventListener("click", () => act(async () => {
  await newSession();
  return api("/api/message", {session_id:sessionId, request_id:crypto.randomUUID(), text:snapshot.canonical_messages[i]});
}, `Session ${i+1} saved. Household context persists across sessions.`));
$("new-session").addEventListener("click", () => act(newSession, "New session opened. Existing household context recovered."));
$("composer").addEventListener("submit", event => {
  event.preventDefault();
  const text = $("message").value.trim();
  if (!text) return;
  act(async () => {
    if (!sessionId || !snapshot.state.sessions.some(s => s.session_id === sessionId)) await newSession();
    const data = await api("/api/message", {session_id:sessionId, request_id:crypto.randomUUID(), text});
    $("message").value = "";
    return data;
  }, "Message and context saved.");
});
async function checkAccess() {
  const access = await api("/auth/session");
  if (access.required && !access.authenticated) { signIn(); return false; }
  csrfToken = access.csrf_token || null;
  $("sign-out").hidden = !access.required;
  return true;
}
$("sign-out").addEventListener("click", async () => {
  try { await api("/auth/logout", {}); sessionStorage.removeItem("hestia-session"); signIn(); }
  catch (error) { if (leaving) return; $("error").textContent = error.message; $("error").hidden = false; }
});
window.addEventListener("pageshow", event => { if (event.persisted) location.reload(); });
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") checkAccess().catch(() => signIn());
});
act(async () => {
  if (!await checkAccess()) throw new Error("Sign in to continue.");
  return api("/api/state");
}, "Saved household context loaded. Ready when you are.");
