/**
 * FinTech Risk & Compliance Assistant — Dashboard Application Logic
 */

// Preset Scenarios
function loadScenario(type) {
  const btnApex = document.getElementById("btn-preset-apex");
  const btnOmni = document.getElementById("btn-preset-omni");
  const borrowerSelect = document.getElementById("borrower-select");
  const facilityInput = document.getElementById("facility-input");
  const queryInput = document.getElementById("query-input");

  if (type === "apex") {
    btnApex.classList.add("active");
    btnOmni.classList.remove("active");
    borrowerSelect.value = "BORR-TECH-001";
    facilityInput.value = "10000000";
    queryInput.value = "Please prepare a comprehensive credit committee underwriting memo for Apex Cloud Solutions requesting a $10M revolving facility.";
    document.getElementById("audit-date-picker").value = "2024-06-01";
  } else if (type === "omni") {
    btnOmni.classList.add("active");
    btnApex.classList.remove("active");
    borrowerSelect.value = "BORR-RETL-004";
    facilityInput.value = "5000000";
    queryInput.value = "Review OmniCommerce Global Retail request for credit extension of $5M. Check covenant violations and cash burn runway.";
    document.getElementById("audit-date-picker").value = "2024-11-01";
  }
}

function onBorrowerChange() {
  const borrowerId = document.getElementById("borrower-select").value;
  if (borrowerId === "BORR-TECH-001") {
    loadScenario("apex");
  } else if (borrowerId === "BORR-RETL-004") {
    loadScenario("omni");
  }
}

// Execute Multi-Agent Underwriting
async function runUnderwriting(event) {
  if (event) event.preventDefault();

  const borrowerId = document.getElementById("borrower-select").value;
  const facilityUsd = parseFloat(document.getElementById("facility-input").value);
  const userQuery = document.getElementById("query-input").value;

  const btnSubmit = document.getElementById("btn-submit");
  const btnText = document.getElementById("btn-text");
  const spinner = document.getElementById("submit-spinner");
  const timeline = document.getElementById("agent-timeline-container");

  // UI Loading State
  btnSubmit.disabled = true;
  spinner.style.display = "inline-block";
  btnText.innerText = "Coordinating Agents...";

  timeline.innerHTML = `
    <div class="agent-step active">
      <span class="agent-tag">RouterAgent</span>
      <span>Classifying underwriting intent and parsing credit parameters...</span>
    </div>
  `;

  try {
    const response = await fetch("/api/underwrite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        borrower_id: borrowerId,
        user_query: userQuery,
        requested_facility_usd: facilityUsd,
      }),
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Underwriting execution failed");
    }

    const data = await response.json();
    renderResults(data);
  } catch (error) {
    timeline.innerHTML += `
      <div class="agent-step" style="border-left-color: var(--color-danger);">
        <span class="agent-tag" style="color: var(--color-danger);">Error</span>
        <span>${error.message}</span>
      </div>
    `;
    alert("Underwriting Error: " + error.message);
  } finally {
    btnSubmit.disabled = false;
    spinner.style.display = "none";
    btnText.innerText = "Execute Multi-Agent Underwriting";
  }
}

// Render Results to DOM
function renderResults(data) {
  // 1. Metric Tiles
  const verdictEl = document.getElementById("res-verdict");
  const badgeEl = document.getElementById("res-badge");
  const probEl = document.getElementById("res-default-prob");
  const tierEl = document.getElementById("res-risk-tier");
  const ratingEl = document.getElementById("res-scd2-rating");
  const scoreEl = document.getElementById("res-scd2-score");
  const latencyEl = document.getElementById("res-latency");
  const guardrailsEl = document.getElementById("res-guardrails");

  const tier = data.risk_tier || "MODERATE";
  probEl.innerText = data.default_probability_percent || "0.0%";
  tierEl.innerText = `Risk Tier: ${tier}`;

  if (tier === "LOW" || tier === "MODERATE") {
    verdictEl.innerText = "APPROVE";
    verdictEl.style.color = "var(--color-success)";
    badgeEl.innerText = "APPROVED";
    badgeEl.className = "verdict-badge verdict-approved";
    ratingEl.innerText = "AA";
    ratingEl.style.color = "var(--color-success)";
    scoreEl.innerText = "Score: 780 / 850";
  } else if (tier === "ELEVATED") {
    verdictEl.innerText = "CONDITIONAL";
    verdictEl.style.color = "var(--color-warning)";
    badgeEl.innerText = "CONDITIONAL";
    badgeEl.className = "verdict-badge verdict-conditional";
    ratingEl.innerText = "BB";
    ratingEl.style.color = "var(--color-warning)";
    scoreEl.innerText = "Score: 640 / 850";
  } else {
    verdictEl.innerText = "DECLINE";
    verdictEl.style.color = "var(--color-danger)";
    badgeEl.innerText = "REJECTED";
    badgeEl.className = "verdict-badge verdict-declined";
    ratingEl.innerText = "CCC";
    ratingEl.style.color = "var(--color-danger)";
    scoreEl.innerText = "Score: 495 / 850";
  }

  const metrics = data.llmops_metrics || {};
  latencyEl.innerText = `${metrics.latency_ms || 120} ms`;
  guardrailsEl.innerText = `Guardrails: ${metrics.guardrail_status || "COMPLIANT"} (${Math.round((metrics.citation_grounding_score || 1) * 100)}% Citations)`;

  // 2. Multi-Agent Timeline
  const timeline = document.getElementById("agent-timeline-container");
  timeline.innerHTML = "";
  (data.agent_logs || []).forEach(log => {
    const parts = log.match(/\[([A-Za-z0-9_]+)\]\s*(.*)/);
    const agentName = parts ? parts[1] : "Agent";
    const text = parts ? parts[2] : log;

    const stepDiv = document.createElement("div");
    stepDiv.className = "agent-step done";
    stepDiv.innerHTML = `
      <span class="agent-tag">${agentName}</span>
      <span>${text}</span>
    `;
    timeline.appendChild(stepDiv);
  });

  // 3. Render Markdown Memo
  const memoContainer = document.getElementById("memo-output-container");
  memoContainer.innerHTML = parseMarkdownToHTML(data.underwriting_memo || "No memo generated.");

  // 4. Citations
  const citationsContainer = document.getElementById("citations-container");
  citationsContainer.innerHTML = "";
  (data.citations || []).forEach(c => {
    const card = document.createElement("div");
    card.className = "citation-card";
    card.innerHTML = `
      <span class="citation-badge">${c.source_id} (${c.type})</span>
      <div style="font-weight: 600; color: #fff; margin-bottom: 0.2rem;">${c.reference}</div>
      <div style="color: var(--text-secondary);">${c.fact}</div>
    `;
    citationsContainer.appendChild(card);
  });
}

// SCD-2 Point-in-Time Time Travel Query (R2 Q4)
async function runTimeTravelQuery() {
  const borrowerId = document.getElementById("borrower-select").value;
  const targetDate = document.getElementById("audit-date-picker").value;
  const outputEl = document.getElementById("time-travel-output");

  outputEl.style.display = "block";
  outputEl.innerHTML = `<span style="color: var(--accent-cyan);">Executing temporal time-travel lookup for ${borrowerId} on ${targetDate}...</span>`;

  try {
    const res = await fetch(`/api/scd2/time-travel?borrower_id=${borrowerId}&date_str=${targetDate}`);
    if (!res.ok) {
      throw new Error(`No historical record active on ${targetDate}`);
    }
    const profile = await res.json();
    outputEl.innerHTML = `
      <div style="font-weight: 700; color: var(--accent-cyan); margin-bottom: 0.35rem;">
        Temporal State Reconstructed on ${targetDate}:
      </div>
      <div><strong>Rating Grade:</strong> <span style="color: #fff;">${profile.rating_grade}</span> (Score: ${profile.credit_score})</div>
      <div><strong>PD Estimate:</strong> ${(profile.pd_estimate * 100).toFixed(2)}% | <strong>D/E:</strong> ${profile.debt_to_equity.toFixed(2)}x</div>
      <div><strong>Effective Window:</strong> ${profile.effective_start_date ? profile.effective_start_date.substring(0, 10) : 'N/A'} &rarr; ${profile.effective_end_date ? profile.effective_end_date.substring(0, 10) : 'ACTIVE'}</div>
      <div style="margin-top: 0.25rem; font-style: italic; color: var(--text-muted);">${profile.change_reason || 'Periodic Assessment'}</div>
    `;
  } catch (err) {
    outputEl.innerHTML = `<span style="color: var(--color-danger);">${err.message}</span>`;
  }
}

// Lightweight Markdown to HTML parser
function parseMarkdownToHTML(md) {
  let html = md
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^#### (.*$)/gim, '<h4>$1</h4>')
    .replace(/^\> (.*$)/gim, '<blockquote>$1</blockquote>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/`([^`]+)`/gim, '<code style="background: rgba(255,255,255,0.1); padding: 0.15rem 0.35rem; border-radius: 4px; font-family: monospace;">$1</code>')
    .replace(/\n\n/gim, '<br><br>');

  return html;
}

// Initial auto-run on page load
window.addEventListener("DOMContentLoaded", () => {
  loadScenario("apex");
});
