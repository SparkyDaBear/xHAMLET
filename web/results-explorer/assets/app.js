const state = { catalog: null, project: null, protein: null, proteinIndex: null, mode: "project", tab: "overview", filter: "", relinkOnly: false, af3Only: false };

const elements = {
  stamp: document.querySelector("#catalog-stamp"),
  list: document.querySelector("#project-list"),
  count: document.querySelector("#project-count"),
  search: document.querySelector("#project-search"),
  relinkFilter: document.querySelector("#filter-relink"),
  af3Filter: document.querySelector("#filter-af3"),
  view: document.querySelector("#project-view"),
  empty: document.querySelector("#empty-state"),
  accession: document.querySelector("#project-accession"),
  title: document.querySelector("#project-title"),
  description: document.querySelector("#project-description"),
  metrics: document.querySelector("#metrics"),
  panel: document.querySelector("#tab-panel"),
  structureModal: document.querySelector("#structure-modal"),
  structureModalTitle: document.querySelector("#structure-modal-title"),
  structureModalScores: document.querySelector("#structure-modal-scores"),
  structureModalStatus: document.querySelector("#structure-modal-status"),
  structureViewer: document.querySelector("#structure-viewer"),
};

const escapeHtml = (value) => String(value ?? "").replace(/[&<>"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[character]);
const formatNumber = (value) => new Intl.NumberFormat().format(Number(value || 0));
const formatBytes = (value) => value < 1024 ? `${value} B` : value < 1024 ** 2 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 ** 2).toFixed(1)} MB`;
const formatValue = (value) => Array.isArray(value) ? value.join("; ") : value ?? "-";
const empty = (text) => `<p class="empty-copy">${escapeHtml(text)}</p>`;

function formatLinkSites(sites, peptide) {
  if (sites == null) return "Not available";
  if (!Array.isArray(sites) || sites.length === 0) return "Not recorded";
  return sites.map((site) => {
    const text = String(site);
    if (text === "-1") return "Unlocalized";
    if (text === "0") return "N-terminus";
    const position = Number(text);
    if (peptide && position === peptide.length + 1) return "C-terminus";
    if (peptide && Number.isInteger(position) && position > 0 && position <= peptide.length) {
      return `${peptide[position - 1]}${position}`;
    }
    return text;
  }).join("; ");
}

function formatCandidateScores(candidates) {
  if (!candidates?.length) return "No candidate results";
  return candidates.map((candidate) => {
    const a = `${candidate.protein_a || "?"} ${candidate.protein_a_aa || "?"}${candidate.protein_a_site || "?"}`;
    const b = `${candidate.protein_b || "?"} ${candidate.protein_b_aa || "?"}${candidate.protein_b_site || "?"}`;
    const score = candidate.xp_exploratory == null ? "XP unavailable" : `exploratory XP ${candidate.xp_exploratory}`;
    const distance = candidate.sasd_A == null ? "SASD unavailable" : `SASD ${candidate.sasd_A} A`;
    return `Hypothesis: ${a} - ${b}; ${score}; ${distance}; ${candidate.status}; ${candidate.model_pxd}/${candidate.model_job}`;
  }).join("\n");
}

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

function renderFilterableTable(tableId, columns, rows, className, cellRenderers) {
  const header = columns.map((column) => `<th scope="col">${escapeHtml(column)}</th>`).join("");
  const filters = columns.map((column, index) => `<th><label class="table-filter-label"><span class="sr-only">Filter ${escapeHtml(column)}</span><input class="table-filter" type="search" data-column="${index}" placeholder="Filter" autocomplete="off"></label></th>`).join("");
  const body = rows.map((row) => `<tr>${row.map((value, index) => `<td>${cellRenderers?.[index] ? cellRenderers[index](value, row) : escapeHtml(formatValue(value))}</td>`).join("")}</tr>`).join("");
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
  if (!state.catalog) return;
  if (state.mode === "protein") return renderProteins();
  const projects = state.catalog.projects.filter((project) =>
    `${project.accession} ${project.title}`.toLowerCase().includes(state.filter)
    && (!state.relinkOnly || project.relink_runs?.some((run) => run.mzid_documents?.some((document) => document.complete === true)))
    && (!state.af3Only || project.predicted_complexes?.some((prediction) => prediction.structure_path))
  );
  elements.count.textContent = `${projects.length} of ${state.catalog.project_count} projects`;
  elements.list.innerHTML = projects.map((project) => `
    <button class="project-link ${state.project?.accession === project.accession ? "is-active" : ""}" data-pxd="${escapeHtml(project.accession)}">
      <span class="project-link-id">${escapeHtml(project.accession)}</span>
      <span class="project-link-title">${escapeHtml(project.title)}</span>
    </button>`).join("") || empty("No matching PXDs.");
  elements.list.querySelectorAll("[data-pxd]").forEach((button) => button.addEventListener("click", () => selectProject(button.dataset.pxd)));
}

function buildProteinIndex() {
  const index = new Map();
  const entry = (accession) => {
    if (!index.has(accession)) index.set(accession, { accession, projects: new Set(), partners: new Set(), groups: 0, structures: 0 });
    return index.get(accession);
  };
  for (const project of state.catalog.projects) {
    for (const run of project.relink_runs || []) {
      for (const crosslink of run.crosslinks || []) {
        const alpha = crosslink.alpha_proteins || [];
        const beta = crosslink.beta_proteins || [];
        for (const accession of new Set([...alpha, ...beta].filter(Boolean))) {
          const protein = entry(accession);
          protein.projects.add(project.accession);
          protein.groups += 1;
          if (alpha.includes(accession)) beta.filter(Boolean).forEach((partner) => protein.partners.add(partner));
          if (beta.includes(accession)) alpha.filter(Boolean).forEach((partner) => protein.partners.add(partner));
        }
      }
    }
    for (const model of project.predicted_complexes || []) {
      for (const accession of new Set([model.protein_a, model.protein_b].filter(Boolean))) {
        const protein = entry(accession);
        protein.projects.add(project.accession);
        if (model.structure_path) protein.structures += 1;
      }
    }
  }
  return index;
}

function renderProteins() {
  if (!state.proteinIndex) state.proteinIndex = buildProteinIndex();
  const matches = [...state.proteinIndex.values()].filter((protein) => protein.accession.toLowerCase().includes(state.filter))
    .sort((a, b) => a.accession.localeCompare(b.accession));
  const shown = matches.slice(0, 100);
  elements.count.textContent = `${formatNumber(matches.length)} matching protein accessions${matches.length > shown.length ? " (first 100 shown)" : ""}`;
  elements.list.innerHTML = shown.map((protein) => `
    <button class="project-link ${state.protein === protein.accession ? "is-active" : ""}" data-protein="${escapeHtml(protein.accession)}">
      <span class="project-link-id">${escapeHtml(protein.accession)}</span>
      <span class="project-link-title">${formatNumber(protein.projects.size)} projects</span>
    </button>`).join("") || empty("No matching protein accessions in the catalog.");
  elements.list.querySelectorAll("[data-protein]").forEach((button) => button.addEventListener("click", () => selectProtein(button.dataset.protein)));
}

function setSearchMode(mode) {
  state.mode = mode;
  state.filter = "";
  elements.search.value = "";
  elements.search.placeholder = mode === "protein" ? "Filter protein accessions" : "Filter PXDs or titles";
  document.querySelector(`input[name="search-mode"][value="${mode}"]`).checked = true;
  elements.relinkFilter.disabled = mode === "protein";
  elements.af3Filter.disabled = mode === "protein";
  renderProjects();
}

function selectProtein(accession) {
  if (!state.proteinIndex) state.proteinIndex = buildProteinIndex();
  if (!state.proteinIndex.has(accession)) return;
  state.protein = accession;
  state.project = null;
  state.tab = "overview";
  if (state.mode !== "protein") setSearchMode("protein");
  renderProjects();
  renderProject();
}

function selectProject(accession) {
  if (state.mode !== "project") setSearchMode("project");
  state.project = state.catalog.projects.find((project) => project.accession === accession) || null;
  state.protein = null;
  renderProjects();
  renderProject();
}

function renderProject() {
  const project = state.project;
  const protein = state.protein && state.proteinIndex?.get(state.protein);
  elements.view.hidden = !project && !protein;
  elements.empty.hidden = Boolean(project || protein);
  document.querySelectorAll(".tab").forEach((tab) => {
    tab.hidden = Boolean(protein) && !["overview", "crosslinks"].includes(tab.dataset.tab);
  });
  if (protein) return renderProtein(protein);
  if (!project) return;
  elements.accession.textContent = project.accession;
  elements.title.textContent = project.title || project.accession;
  elements.description.textContent = project.description || "No project description was captured.";
  const documents = project.relink_runs.flatMap((run) => run.mzid_documents);
  const metrics = [
    ["Raw files", project.file_assignment_count],
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
  wireStructureButtons();
  wireNavigationButtons();
  if (state.tab === "linear") loadLinearPage(project.accession, 1);
  window.lucide?.createIcons();
}

function renderProtein(protein) {
  const projects = state.catalog.projects.filter((project) => protein.projects.has(project.accession));
  elements.accession.textContent = "Protein accession";
  elements.title.textContent = protein.accession;
  elements.description.textContent = "Exact accession reported in cross-links or AF3 models. Isoforms and ambiguous protein mappings are not merged; linear search results are not included.";
  const metrics = [["Projects", projects.length], ["Cross-link groups", protein.groups], ["Reported partners", protein.partners.size], ["AF3 structures", protein.structures]];
  elements.metrics.innerHTML = metrics.map(([label, value]) => `<article class="metric"><span class="metric-label">${label}</span><strong class="metric-value">${formatNumber(value)}</strong></article>`).join("");
  document.querySelectorAll(".tab").forEach((tab) => {
    const active = tab.dataset.tab === state.tab;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", active);
  });
  if (state.tab === "crosslinks") {
    elements.panel.innerHTML = projects.map((project) => {
      const runs = project.relink_runs.map((run) => ({
        ...run,
        crosslinks: (run.crosslinks || []).filter((link) => [...(link.alpha_proteins || []), ...(link.beta_proteins || [])].includes(protein.accession)),
      })).filter((run) => run.crosslinks.length);
      if (!runs.length) return "";
      return `<section class="protein-project"><h2><button class="project-jump" data-pxd="${escapeHtml(project.accession)}">${escapeHtml(project.accession)}</button></h2>${renderCrosslinks({ ...project, relink_runs: runs })}</section>`;
    }).join("") || empty("No cross-link records were found for this accession.");
  } else {
    const rows = projects.map((project) => {
      const models = (project.predicted_complexes || []).filter((model) => model.structure_path && [model.protein_a, model.protein_b].includes(protein.accession));
      const structures = models.map((model) => `<button type="button" class="structure-button" data-pxd="${escapeHtml(project.accession)}" data-job-name="${escapeHtml(model.job_name)}">View ${escapeHtml(model.protein_a)} &times; ${escapeHtml(model.protein_b)}</button>`).join(" ");
      return `<tr><td><button class="project-jump" data-pxd="${escapeHtml(project.accession)}">${escapeHtml(project.accession)}</button></td><td>${escapeHtml(project.title)}</td><td>${structures || "-"}</td></tr>`;
    }).join("");
    elements.panel.innerHTML = `<div class="panel-heading"><h2 class="section-title">Projects and structures</h2><p>Cross-link partners reflect reported mappings, including ambiguous mappings; they do not establish an interaction.</p></div><div class="table-wrap"><table class="search-table"><thead><tr><th>PXD</th><th>Project</th><th>AF3 structures</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }
  wireFilterableTables();
  wireStructureButtons();
  wireNavigationButtons();
  window.lucide?.createIcons();
}

function wireNavigationButtons() {
  elements.panel.querySelectorAll(".project-jump").forEach((button) => button.addEventListener("click", () => selectProject(button.dataset.pxd)));
  elements.panel.querySelectorAll(".protein-button").forEach((button) => button.addEventListener("click", () => selectProtein(button.dataset.protein)));
}

function renderTab(project) {
  if (state.tab === "metadata") return renderMetadata(project);
  if (state.tab === "searches") return renderSearches(project);
  if (state.tab === "crosslinks") return renderCrosslinks(project);
  if (state.tab === "linear") return renderLinear();
  if (state.tab === "files") return renderFiles(project);
  return renderOverview(project);
}

const linearState = { indexPromise: null, accession: null, chunkIndex: null, chunk: null, request: 0 };

function renderLinear() {
  return `<div class="panel-heading"><h2 class="section-title">Linear search results</h2>
    <p>Rank-1 target matches from the linear search; these are not necessarily FDR-filtered. Results are in source order.</p></div>
    <div id="linear-results">Loading linear results...</div>`;
}

async function linearIndex() {
  if (!linearState.indexPromise) {
    linearState.indexPromise = fetch("data/linear/index.json").then((response) => {
      if (!response.ok) throw new Error(`Linear index: HTTP ${response.status}`);
      return response.json();
    }).then((index) => {
      if (index.version !== 1 || index.page_size !== 100 || !Number.isInteger(index.chunk_size)
          || index.chunk_size < index.page_size || index.chunk_size % index.page_size || !index.projects) {
        throw new Error("Unsupported or invalid linear index");
      }
      return index;
    }).catch((error) => {
      linearState.indexPromise = null;
      throw error;
    });
  }
  return linearState.indexPromise;
}

async function readLinearChunk(path) {
  const response = await fetch(`data/linear/${path}`);
  if (!response.ok) throw new Error(`Linear chunk: HTTP ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  let text;
  if (bytes[0] === 0x1f && bytes[1] === 0x8b) {
    if (typeof DecompressionStream !== "function") throw new Error("This browser cannot decompress linear results.");
    text = await new Response(new Blob([bytes]).stream().pipeThrough(new DecompressionStream("gzip"))).text();
  } else {
    text = new TextDecoder().decode(bytes);
  }
  const rows = JSON.parse(text);
  if (!Array.isArray(rows)) throw new Error("Invalid linear result chunk");
  return rows;
}

async function loadLinearPage(accession, page) {
  const request = ++linearState.request;
  const active = () => request === linearState.request && state.project?.accession === accession && state.tab === "linear";
  const results = elements.panel.querySelector("#linear-results");
  if (!results) return;
  results.textContent = "Loading linear results...";
  try {
    const index = await linearIndex();
    if (!active()) return;
    const project = index.projects[accession];
    if (!project) {
      results.innerHTML = empty("No linear search export is available for this project.");
      return;
    }
    if (!project.row_count) {
      results.innerHTML = empty("This linear search export contains no rank-1 target matches.");
      return;
    }
    const pages = Math.ceil(project.row_count / index.page_size);
    if (!Number.isSafeInteger(page) || page < 1 || page > pages) throw new Error(`Page must be between 1 and ${pages}.`);
    const offset = (page - 1) * index.page_size;
    const chunkIndex = Math.floor(offset / index.chunk_size);
    if (linearState.accession !== accession || linearState.chunkIndex !== chunkIndex) {
      const path = project.chunks[chunkIndex];
      if (!path) throw new Error("The requested linear chunk is missing from the index.");
      const chunk = await readLinearChunk(path);
      if (!active()) return;
      linearState.accession = accession;
      linearState.chunkIndex = chunkIndex;
      linearState.chunk = chunk;
    }
    const start = offset % index.chunk_size;
    const rows = linearState.chunk.slice(start, start + index.page_size);
    const expected = Math.min(index.page_size, project.row_count - offset);
    if (rows.length !== expected || rows.some((row) => !Array.isArray(row) || row.length !== 11)) {
      throw new Error("Linear chunk does not match the index.");
    }
    if (!active()) return;
    const columns = ["Protein", "Peptide", "Modified peptide", "Start", "xi score", "Charge", "Search group", "Source run", "Scan", "Scan ID", "Spectrum title"];
    const body = rows.map((row) => {
      const displayed = [...row.slice(0, 9), row[10], row[9]];
      return `<tr>${displayed.map((value, i) => `<td>${i === 1 || i === 2 ? `<span class="peptide-scroll" tabindex="0">${escapeHtml(value)}</span>` : escapeHtml(value)}</td>`).join("")}</tr>`;
    }).join("");
    results.innerHTML = `<div class="linear-pagination" aria-label="Linear result pages">
      <button type="button" data-linear-page="${page - 1}" ${page === 1 ? "disabled" : ""}>Previous</button>
      <span role="status">Page ${formatNumber(page)} of ${formatNumber(pages)} | rows ${formatNumber(offset + 1)}-${formatNumber(offset + rows.length)} of ${formatNumber(project.row_count)}</span>
      <button type="button" data-linear-page="${page + 1}" ${page === pages ? "disabled" : ""}>Next</button>
      <form class="linear-jump"><label>Go to page <input type="number" name="page" min="1" max="${pages}" required></label> <button type="submit">Go</button></form>
    </div>
    <div class="table-wrap interactive-table-wrap"><table class="search-table linear-table"><thead><tr>${columns.map((column) => `<th scope="col">${escapeHtml(column)}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table></div>`;
    results.querySelectorAll("[data-linear-page]").forEach((button) => button.addEventListener("click", () => loadLinearPage(accession, Number(button.dataset.linearPage))));
    results.querySelector(".linear-jump").addEventListener("submit", (event) => {
      event.preventDefault();
      loadLinearPage(accession, Number(event.currentTarget.elements.page.value));
    });
  } catch (error) {
    if (active()) {
      results.innerHTML = `<p class="linear-error">Could not load linear results: ${escapeHtml(error.message)}</p>
        <button type="button" class="linear-retry">Try again</button>`;
      results.querySelector(".linear-retry").addEventListener("click", () => loadLinearPage(accession, page));
    }
  }
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

function crosslinkerLabel(run) {
  const group = run.path?.match(/(?:^|\/)taxid_[^/]+\/([^/]+)(?:\/|$)/)?.[1];
  if (group && group !== "results") return group.replaceAll("_", " ").toUpperCase();
  const names = (run.crosslinkers || [])
    .filter((line) => /^crosslinker:/i.test(line))
    .map((line) => line.match(/(?:^|:)Name:([^;]+)/i)?.[1])
    .filter((name) => name && name.toLowerCase() !== "noncovalent");
  return [...new Set(names)].join(", ") || "Not recorded";
}

function renderCrosslinks(project) {
  const runs = project.relink_runs.filter((run) => run.crosslinks?.length);
  if (!runs.length) return empty("No compact cross-link records were included in this catalog.");
  const predictionsByJob = new Map((project.predicted_complexes || []).map((prediction) => [prediction.job_name, prediction]));
  return runs.map((run) => {
    const columns = ["Protein A", "Protein B", "Structure", "Alpha peptide", "Beta peptide", "Alpha positions", "Beta positions", "Alpha site (peptide)", "Beta site (peptide)", "PSMs", "Best xi score", "Hypothetical site scores", "Source RAW"];
    const rows = run.crosslinks.map((crosslink) => [
      crosslink.alpha_proteins || [], crosslink.beta_proteins || [], crosslink.predicted_complex || "",
      crosslink.alpha_sequence || "-", crosslink.beta_sequence || "-",
      formatValue(crosslink.alpha_positions), formatValue(crosslink.beta_positions),
      formatLinkSites(crosslink.alpha_link_sites, crosslink.alpha_sequence), formatLinkSites(crosslink.beta_link_sites, crosslink.beta_sequence),
      formatNumber(crosslink.observations), crosslink.best_xi_score ?? "-",
      formatCandidateScores(crosslink.candidate_scores), crosslink.source_file || "[unresolved RAW]",
    ]);
    const proteinCell = (accessions) => accessions.map((accession) => `<button type="button" class="protein-button" data-protein="${escapeHtml(accession)}">${escapeHtml(accession)}</button>`).join("; ") || "-";
    const peptideCell = (value) => `<span class="peptide-scroll" tabindex="0" aria-label="Peptide sequence, scroll horizontally if needed">${escapeHtml(value)}</span>`;
    const cellRenderers = {
      0: proteinCell,
      1: proteinCell,
      2: (jobName) => {
        if (!jobName || !predictionsByJob.has(jobName)) return `<span class="structure-unavailable">-</span>`;
        return `<button type="button" class="structure-button" data-pxd="${escapeHtml(project.accession)}" data-job-name="${escapeHtml(jobName)}">
          <i data-lucide="box" aria-hidden="true"></i> View
        </button>`;
      },
      3: peptideCell,
      4: peptideCell,
    };
    return `<article class="run"><div class="run-heading"><h2>Cross-linker: ${escapeHtml(crosslinkerLabel(run))}</h2><span class="run-path">${escapeHtml(run.path)}</span></div>
      <p>Link sites are peptide-relative. Hypothetical site scores are exploratory and do not establish an observed site or covalent link.</p>
      ${renderFilterableTable(`crosslinks-${project.accession}-${run.path.replaceAll(/[^a-z0-9]+/gi, "-")}`, columns, rows, "search-table crosslink-table", cellRenderers)}
    </article>`;
  }).join("");
}

function renderFiles(project) {
  const rows = project.artifacts.map((artifact) => `<tr><td>${escapeHtml(artifact.category)}</td><td>${artifact.url ? `<a class="file-link" href="${escapeHtml(artifact.url)}" target="_blank" rel="noreferrer">${escapeHtml(artifact.path)} <i data-lucide="external-link" aria-hidden="true"></i></a>` : escapeHtml(artifact.path)}</td><td>${formatBytes(artifact.size)}</td><td>${escapeHtml(artifact.modified_at)}</td></tr>`).join("");
  return `<div class="table-wrap"><table class="file-table"><thead><tr><th>Type</th><th>Artifact</th><th>Size</th><th>Modified</th></tr></thead><tbody>${rows || `<tr><td colspan="4">No artifacts were indexed.</td></tr>`}</tbody></table></div>`;
}

function wireStructureButtons() {
  elements.panel.querySelectorAll(".structure-button").forEach((button) => {
    button.addEventListener("click", () => {
      const project = state.catalog.projects.find((item) => item.accession === button.dataset.pxd);
      if (project) openStructureViewer(project, button.dataset.jobName);
    });
  });
}

const molstarState = { assetsPromise: null, viewer: null };

const MOLSTAR_VERSION = "5.13.1";

function registerChainConfidenceTheme(viewer) {
  const registry = viewer.plugin.representation.structure.themes.colorThemeRegistry;
  const confidence = registry.get("plddt-confidence");
  if (confidence.name !== "plddt-confidence") throw new Error("Mol* pLDDT confidence theme is unavailable.");
  const shades = new Map([
    [0xff7d45, [0xffd5d0, 0xd5e8ff]],
    [0xffdb13, [0xf79589, 0x8dbbf2]],
    [0x65cbf3, [0xdc5048, 0x397ed0]],
    [0x0053d6, [0x9c1c25, 0x10458f]],
  ]);
  const factory = (context, props) => {
    const base = confidence.factory(context, props);
    return {
      ...base,
      factory,
      legend: undefined,
      color: (location, isSecondary) => {
        const unit = location.kind === "element-location" ? location.unit : location.aUnit;
        const element = location.kind === "element-location" ? location.element : unit?.elements[location.aIndex];
        if (!unit || unit.kind !== 0 || element == null) return 0xaaaaaa;
        const hierarchy = unit.model.atomicHierarchy;
        const chain = hierarchy.chains.label_asym_id.value(hierarchy.chainAtomSegments.index[element]);
        const palette = shades.get(base.color(location, isSecondary));
        if (!palette || (chain !== "A" && chain !== "B")) return 0xaaaaaa;
        return palette[chain === "A" ? 0 : 1];
      },
    };
  };
  registry.add({ ...confidence, name: "xhamlet-chain-confidence", label: "Chain and pLDDT", factory });
}

function loadMolstarAssets() {
  if (molstarState.assetsPromise) return molstarState.assetsPromise;
  molstarState.assetsPromise = new Promise((resolve, reject) => {
    if (window.molstar) {
      resolve(window.molstar);
      return;
    }
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = `https://cdn.jsdelivr.net/npm/molstar@${MOLSTAR_VERSION}/build/viewer/molstar.css`;
    document.head.appendChild(link);
    const script = document.createElement("script");
    script.src = `https://cdn.jsdelivr.net/npm/molstar@${MOLSTAR_VERSION}/build/viewer/molstar.js`;
    script.onload = () => (window.molstar ? resolve(window.molstar) : reject(new Error("Mol* failed to initialize.")));
    script.onerror = () => reject(new Error("Failed to load the Mol* structure viewer library from the CDN."));
    document.body.appendChild(script);
  });
  return molstarState.assetsPromise;
}

async function getFreshMolstarViewer() {
  const molstar = await loadMolstarAssets();
  molstarState.viewer?.dispose();
  elements.structureViewer.innerHTML = "";
  molstarState.viewer = await molstar.Viewer.create(elements.structureViewer, {
    layoutIsExpanded: false,
    layoutShowControls: false,
    layoutShowSequence: true,
    layoutShowLog: false,
    layoutShowLeftPanel: false,
    viewportShowExpand: true,
    viewportShowSelectionMode: false,
    viewportShowAnimation: false,
  });
  registerChainConfidenceTheme(molstarState.viewer);
  return molstarState.viewer;
}

function scoreChip(label, value) {
  const text = typeof value === "number" ? value.toFixed(2) : "-";
  return `<span class="score-chip"><strong>${escapeHtml(label)}</strong> ${escapeHtml(text)}</span>`;
}

async function openStructureViewer(project, jobName) {
  const prediction = (project.predicted_complexes || []).find((item) => item.job_name === jobName);
  if (!prediction) return;
  elements.structureModal.hidden = false;
  elements.structureModalTitle.textContent = `${prediction.protein_a} \u00d7 ${prediction.protein_b}`;
  elements.structureModalScores.innerHTML = [
    scoreChip("pTM", prediction.ptm),
    scoreChip("ipTM", prediction.iptm),
    scoreChip("Ranking score", prediction.ranking_score),
    `<span class="score-chip"><strong>Clashes</strong> ${prediction.has_clash ? "yes" : "no"}</span>`,
  ].join("");
  elements.structureModalStatus.textContent = "Loading structure\u2026";
  try {
    const viewer = await getFreshMolstarViewer();
    const data = await viewer.plugin.builders.data.download({ url: prediction.structure_path, isBinary: false, label: jobName });
    const trajectory = await viewer.plugin.builders.structure.parseTrajectory(data, "mmcif");
    await viewer.plugin.builders.structure.hierarchy.applyPreset(trajectory, "default", {
      representationPreset: "auto",
      representationPresetParams: { theme: { globalName: "xhamlet-chain-confidence" } },
    });
    elements.structureModalStatus.textContent = "";
  } catch (error) {
    elements.structureModalStatus.textContent = `Could not load structure: ${error.message}`;
  }
}

function closeStructureViewer() {
  elements.structureModal.hidden = true;
  molstarState.viewer?.dispose();
  molstarState.viewer = null;
  elements.structureViewer.innerHTML = "";
}

document.querySelectorAll("[data-close-structure-modal]").forEach((element) => element.addEventListener("click", closeStructureViewer));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !elements.structureModal.hidden) closeStructureViewer();
});

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => { state.tab = tab.dataset.tab; renderProject(); }));
document.querySelectorAll('input[name="search-mode"]').forEach((input) => input.addEventListener("change", () => setSearchMode(input.value)));
elements.search.addEventListener("input", (event) => { state.filter = event.target.value.trim().toLowerCase(); renderProjects(); });
elements.relinkFilter.addEventListener("change", (event) => { state.relinkOnly = event.target.checked; renderProjects(); });
elements.af3Filter.addEventListener("change", (event) => { state.af3Only = event.target.checked; renderProjects(); });

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