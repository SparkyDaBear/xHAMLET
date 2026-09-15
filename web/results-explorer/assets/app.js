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

function parseTsv(text) {
  const rows = [];
  let cell = "";
  let row = [];
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (character === '"') {
      if (quoted && text[index + 1] === '"') {
        cell += '"';
        index += 1;
      } else quoted = !quoted;
    } else if (!quoted && character === "\t") {
      row.push(cell);
      cell = "";
    } else if (!quoted && (character === "\n" || character === "\r")) {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(cell);
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      cell = "";
    } else cell += character;
  }
  row.push(cell);
  if (row.some((value) => value !== "")) rows.push(row);
  return rows;
}

function renderFilterableTable(tableId, columns, rows, className) {
  const header = columns.map((column) => `<th scope="col">${escapeHtml(column)}</th>`).join("");
  const filters = columns.map((column, index) => `<th><label class="table-filter-label"><span class="sr-only">Filter ${escapeHtml(column)}</span><input class="table-filter" type="search" data-column="${index}" placeholder="Filter" autocomplete="off"></label></th>`).join("");
  const body = rows.map((row) => `<tr>${row.map((value) => `<td>${escapeHtml(formatValue(value))}</td>`).join("")}</tr>`).join("");
  return `<div class="table-wrap interactive-table-wrap"><table id="${escapeHtml(tableId)}" class="${className} interactive-table"><thead><tr>${header}</tr><tr class="table-filter-row">${filters}</tr></thead><tbody>${body}</tbody></table><p class="table-count" data-table-count="${escapeHtml(tableId)}"></p></div>`;
}

function wireFilterableTables() {
  elements.panel.querySelectorAll(".interactive-table").forEach((table) => {
    const count = elements.panel.querySelector(`[data-table-count="${table.id}"]`);
    const applyFilters = () => {
      const filters = [...table.querySelectorAll(".table-filter")].map((input) => input.value.trim().toLowerCase());
      let visible = 0;
      [...table.tBodies[0].rows].forEach((row) => {
        const matches = filters.every((filter, index) => !filter || row.cells[index].textContent.toLowerCase().includes(filter));
        row.hidden = !matches;
        if (matches) visible += 1;
      });
      count.textContent = `${formatNumber(visible)} of ${formatNumber(table.tBodies[0].rows.length)} rows`;
    };
    table.querySelectorAll(".table-filter").forEach((input) => input.addEventListener("input", applyFilters));
    applyFilters();
  });
}

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
  wireFilterableTables();
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
  if (!project.sdrf?.text) return empty("No SDRF TSV content was included in this catalog.");
  const [columns, ...rows] = parseTsv(project.sdrf.text);
  if (!columns?.length) return empty("The stored SDRF TSV is empty.");
  const normalizedRows = rows.map((row) => columns.map((_, index) => row[index] || ""));
  return `<div class="panel-heading"><h2 class="section-title">${escapeHtml(project.sdrf.path)}</h2><p>Full xHAMLET SDRF metadata for this project.</p></div>${renderFilterableTable(`sdrf-${project.accession}`, columns, normalizedRows, "metadata-table")}`;
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
    const columns = ["Source RAW", "Alpha peptide", "Beta peptide", "Alpha proteins", "Beta proteins", "Alpha positions", "Beta positions", "PSMs", "Best xi score"];
    const rows = run.crosslinks.map((crosslink) => [
      crosslink.source_file || "[unresolved RAW]", crosslink.alpha_sequence || "-", crosslink.beta_sequence || "-",
      formatValue(crosslink.alpha_proteins), formatValue(crosslink.beta_proteins),
      formatValue(crosslink.alpha_positions), formatValue(crosslink.beta_positions),
      formatNumber(crosslink.observations), crosslink.best_xi_score ?? "-",
    ]);
    return `<article class="run"><div class="run-heading"><h2>Taxid ${escapeHtml(run.taxid || "unknown")}</h2><span class="run-path">${escapeHtml(run.path)}</span></div>
      ${renderFilterableTable(`crosslinks-${project.accession}-${run.path.replaceAll(/[^a-z0-9]+/gi, "-")}`, columns, rows, "search-table")}
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