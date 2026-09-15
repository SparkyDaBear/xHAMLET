const state = { catalog: null, project: null, tab: "overview", filter: "" };

const elements = {
  stamp: document.querySelector("#catalog-stamp"),
  list: document.querySelector("#project-list"),
  count: document.querySelector("#project-count"),
  search: document.querySelector("#project-search"),
  view: document.querySelector("#project-view"),
  empty: document.querySelector("#empty-state"),
  accession: document.querySelector("#project-accession"),
  title: document.querySelector("#project-title"),
  description: document.querySelector("#project-description"),
  metrics: document.querySelector("#metrics"),
  panel: document.querySelector("#tab-panel"),
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
const formatNumber = (value) => new Intl.NumberFormat().format(Number(value || 0));
const formatBytes = (value) => value < 1024 ? `${value} B` : value < 1024 ** 2 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 ** 2).toFixed(1)} MB`;
const formatValue = (value) => Array.isArray(value) ? value.join("; ") : value ?? "-";
const empty = (text) => `<p class="empty-copy">${escapeHtml(text)}</p>`;

function statusClass(status) {
  const value = String(status || "").toLowerCase();
  if (value.includes("warning") || value.includes("failed")) return "warning";
  if (value.includes("success")) return "success";
  return "neutral";
}

function renderProjects() {
  const projects = state.catalog.projects.filter((project) => `${project.accession} ${project.title}`.toLowerCase().includes(state.filter));
  elements.count.textContent = `${projects.length} of ${state.catalog.project_count} projects`;
  elements.list.innerHTML = projects.map((project) => `
    <button class="project-link ${state.project?.accession === project.accession ? "is-active" : ""}" data-pxd="${escapeHtml(project.accession)}">
      <span class="project-link-id">${escapeHtml(project.accession)}</span>
      <span class="project-link-title">${escapeHtml(project.title)}</span>
    </button>`).join("") || empty("No matching PXDs.");
  elements.list.querySelectorAll("[data-pxd]").forEach((button) => button.addEventListener("click", () => selectProject(button.dataset.pxd)));
}

function selectProject(accession) {
  state.project = state.catalog.projects.find((project) => project.accession === accession) || null;
  renderProjects();
  renderProject();
}

function renderProject() {
  const project = state.project;
  elements.view.hidden = !project;
  elements.empty.hidden = Boolean(project);
  if (!project) return;
  elements.accession.textContent = project.accession;
  elements.title.textContent = project.title || project.accession;
  elements.description.textContent = project.description || "No project description was captured.";
  const documents = project.relink_runs.flatMap((run) => run.mzid_documents);
  const metrics = [
    ["Raw assignments", project.file_assignment_count],
    ["Search runs", project.relink_runs.length],
    ["mzIdentML documents", documents.length],
    ["Passing items", documents.reduce((sum, document) => sum + Number(document.passing_items || 0), 0)],
  ];
  elements.metrics.innerHTML = metrics.map(([label, value]) => `<article class="metric"><span class="metric-label">${label}</span><strong class="metric-value">${formatNumber(value)}</strong></article>`).join("");
  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.tab === state.tab;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", active);
  });
  elements.panel.innerHTML = renderTab(project);
  window.lucide?.createIcons();
}

function renderTab(project) {
  if (state.tab === "metadata") return renderMetadata(project);
  if (state.tab === "searches") return renderSearches(project);
  if (state.tab === "crosslinks") return renderCrosslinks(project);
  if (state.tab === "files") return renderFiles(project);
  return renderOverview(project);
}

function renderOverview(project) {
  const organisms = project.organisms.map((organism) => organism.name || organism.label || JSON.stringify(organism)).join("; ") || "-";
  const spectral = project.spectral_summary || {};
  const stageRows = Object.entries(project.stages || {}).map(([stage, status]) => `<div class="stage"><span class="stage-name">${escapeHtml(stage.replaceAll("_", " "))}</span><span class="badge ${statusClass(status)}">${escapeHtml(status)}</span></div>`).join("");
  return `<div class="overview-grid">
    <section><h2 class="section-title">Project context</h2><dl class="definition-list">
      <div><dt>Organism</dt><dd>${escapeHtml(organisms)}</dd></div>
      <div><dt>DOI</dt><dd>${project.doi ? `<a class="file-link" href="https://doi.org/${encodeURIComponent(project.doi)}" target="_blank" rel="noreferrer">${escapeHtml(project.doi)}</a>` : "-"}</dd></div>
      <div><dt>Processed</dt><dd>${escapeHtml(project.processed_at || "-")}</dd></div>
      <div><dt>Instrument</dt><dd>${escapeHtml(formatValue(spectral.instrument || "-"))}</dd></div>
      <div><dt>Fragmentation</dt><dd>${escapeHtml(formatValue(spectral.fragmentation || "-"))}</dd></div>
    </dl></section>
    <section><h2 class="section-title">Pipeline status</h2><div class="stage-list">${stageRows || empty("No pipeline status was captured.")}</div></section>
  </div>`;
}

function renderMetadata(project) {
  const rows = project.metadata_fields.map((field) => `<tr><td>${escapeHtml(field.key)}</td><td>${escapeHtml(formatValue(field.value))}</td><td>${escapeHtml(formatValue(field.accession))}</td><td>${escapeHtml(field.confidence || "-")}</td></tr>`).join("");
  return rows ? `<div class="table-wrap"><table class="metadata-table"><thead><tr><th>Field</th><th>Value</th><th>Accession</th><th>Confidence</th></tr></thead><tbody>${rows}</tbody></table></div>` : empty("No selected LLM metadata fields were captured.");
}

function renderSearches(project) {
  if (!project.relink_runs.length) return empty("No ReLink mzIdentML result documents were found.");
  return project.relink_runs.map((run) => {
    const rows = run.mzid_documents.map((document) => `<tr><td>${escapeHtml(document.path)}</td><td>${formatNumber(document.spectra)}</td><td>${formatNumber(document.items)}</td><td>${formatNumber(document.passing_items)}</td><td>${document.complete ? "Complete" : "Partial"}</td></tr>`).join("");
    return `<article class="run"><div class="run-heading"><h2>Taxid ${escapeHtml(run.taxid || "unknown")}</h2><span class="run-path">${escapeHtml(run.path)}</span></div>
      <dl class="definition-list"><div><dt>FASTA</dt><dd>${escapeHtml(run.fasta || "Not recorded")}</dd></div></dl>
      <code class="config-code">${escapeHtml(run.crosslinkers.join("\n") || "No crosslinker configuration was found.")}</code>
      <div class="table-wrap"><table class="search-table"><thead><tr><th>Result document</th><th>Spectra</th><th>Items</th><th>Passing</th><th>XML</th></tr></thead><tbody>${rows}</tbody></table></div>
    </article>`;
  }).join("");
}

function renderCrosslinks(project) {
  const runs = project.relink_runs.filter((run) => run.crosslinks?.length);
  if (!runs.length) return empty("No compact cross-link records were included in this catalog.");
  return runs.map((run) => {
    const rows = run.crosslinks.map((crosslink) => `<tr>
      <td>${escapeHtml(crosslink.source_file || "[unresolved RAW]")}</td>
      <td>${escapeHtml(crosslink.alpha_sequence || "-")}<br>${escapeHtml(crosslink.beta_sequence || "-")}</td>
      <td>${escapeHtml(formatValue(crosslink.alpha_proteins))}<br>${escapeHtml(formatValue(crosslink.beta_proteins))}</td>
      <td>${escapeHtml(formatValue(crosslink.alpha_positions))}<br>${escapeHtml(formatValue(crosslink.beta_positions))}</td>
      <td>${formatNumber(crosslink.observations)}</td><td>${crosslink.best_xi_score ?? "-"}</td>
    </tr>`).join("");
    return `<article class="run"><div class="run-heading"><h2>Taxid ${escapeHtml(run.taxid || "unknown")}</h2><span class="run-path">${escapeHtml(run.path)}</span></div>
      <div class="table-wrap"><table class="search-table"><thead><tr><th>Source RAW</th><th>Peptides</th><th>Proteins</th><th>Positions</th><th>PSMs</th><th>Best xi score</th></tr></thead><tbody>${rows}</tbody></table></div>
    </article>`;
  }).join("");
}

function renderFiles(project) {
  const rows = project.artifacts.map((artifact) => `<tr><td>${escapeHtml(artifact.category)}</td><td>${artifact.url ? `<a class="file-link" href="${escapeHtml(artifact.url)}" target="_blank" rel="noreferrer">${escapeHtml(artifact.path)} <i data-lucide="external-link" aria-hidden="true"></i></a>` : escapeHtml(artifact.path)}</td><td>${formatBytes(artifact.size)}</td><td>${escapeHtml(artifact.modified_at)}</td></tr>`).join("");
  return `<div class="table-wrap"><table class="file-table"><thead><tr><th>Type</th><th>Artifact</th><th>Size</th><th>Modified</th></tr></thead><tbody>${rows || `<tr><td colspan="4">No artifacts were indexed.</td></tr>`}</tbody></table></div>`;
}

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => { state.tab = tab.dataset.tab; renderProject(); }));
elements.search.addEventListener("input", (event) => { state.filter = event.target.value.trim().toLowerCase(); renderProjects(); });

fetch("data/catalog.json")
  .then((response) => response.ok ? response.json() : Promise.reject(new Error(`HTTP ${response.status}`)))
  .then((catalog) => {
    state.catalog = catalog;
    elements.stamp.textContent = `${catalog.project_count} projects | generated ${new Date(catalog.generated_at).toLocaleString()}`;
    selectProject(catalog.projects[0]?.accession);
  })
  .catch((error) => {
    elements.stamp.textContent = "Catalog unavailable";
    elements.empty.hidden = false;
    elements.empty.innerHTML = `<p class="eyebrow">Catalog unavailable</p><h1>${escapeHtml(error.message)}</h1>`;
  });