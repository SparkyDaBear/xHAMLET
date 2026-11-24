const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const zlib = require("node:zlib");

function explorer(projects, loading = false) {
  const nodes = new Map();
  const context = vm.createContext({
    Intl,
    window: {},
    Blob, DecompressionStream, Response, TextDecoder, Uint8Array,
    document: {
      querySelector(selector) {
        if (!nodes.has(selector)) nodes.set(selector, {
          textContent: "", innerHTML: "", listeners: {},
          querySelectorAll: () => [],
          addEventListener(event, callback) { this.listeners[event] = callback; },
        });
        return nodes.get(selector);
      },
      querySelectorAll: () => [],
      addEventListener() {},
    },
    fetch: () => new Promise(() => {}),
  });
  const source = fs.readFileSync(path.join(__dirname, "../web/results-explorer/assets/app.js"), "utf8");
  vm.runInContext(source, context);
  context.catalog = { projects, project_count: projects.length };
  if (!loading) vm.runInContext("state.catalog = catalog; renderProjects();", context);
  return {
    count: () => nodes.get("#project-count").textContent,
    list: () => nodes.get("#project-list").innerHTML,
    load() { vm.runInContext("state.catalog = catalog; renderProjects();", context); },
    crosslinks(project) {
      context.projectToRender = project;
      return vm.runInContext("renderCrosslinks(projectToRender)", context);
    },
    run(source) { return vm.runInContext(source, context); },
    context,
    node(selector) { return nodes.get(selector); },
    change(selector, value) {
      const event = selector === "#project-search" ? "input" : "change";
      nodes.get(selector).listeners[event]({ target: { checked: value, value } });
    },
  };
}

test("filters can be selected before the catalog finishes loading", () => {
  const app = explorer([
    { accession: "PXD000001", title: "No model" },
    { accession: "PXD000002", title: "Model", predicted_complexes: [{ structure_path: "model.cif" }] },
  ], true);
  app.change("#filter-af3", true);
  app.load();
  assert.equal(app.count(), "1 of 2 projects");
  assert.match(app.list(), /PXD000002/);
  assert.doesNotMatch(app.list(), /PXD000001/);
});

test("crosslink tables identify chemistry groups rather than taxid", () => {
  const app = explorer([]);
  const html = app.crosslinks({
    accession: "PXD000001",
    relink_runs: [
      { path: "relink/taxid_9606/bs3", crosslinks: [{}] },
      { path: "relink/taxid_9606/sulfo_sda", crosslinks: [{}] },
      { path: "relink/taxid_562", crosslinkers: [
        "crosslinker:NonCovalentBound:Name:NonCovalent",
        "crosslinker:SymetricSingleAminoAcidRestrictedCrossLinker:Name:DSSO;MASS:158",
      ], crosslinks: [{}] },
      { path: "relink/taxid_9606/results", crosslinks: [{}] },
    ],
  });
  assert.match(html, /<h2>Cross-linker: BS3<\/h2>/);
  assert.match(html, /<h2>Cross-linker: SULFO SDA<\/h2>/);
  assert.match(html, /<h2>Cross-linker: DSSO<\/h2>/);
  assert.match(html, /<h2>Cross-linker: Not recorded<\/h2>/);
  assert.doesNotMatch(html, /<h2>Taxid/);
  assert.match(html, /relink\/taxid_562/);
});

test("protein accession search preserves exact mappings and project provenance", () => {
  const app = explorer([
    { accession: "PXD000001", title: "First", relink_runs: [{ path: "relink/taxid_9606/dss", crosslinks: [
      { alpha_proteins: ["P12345", "P12345-2"], beta_proteins: ["Q12345"], alpha_sequence: "AK", beta_sequence: "BK" },
    ] }], predicted_complexes: [{ protein_a: "P12345", protein_b: "Q12345", job_name: "one", structure_path: "one.cif" }] },
    { accession: "PXD000002", title: "Second", relink_runs: [{ path: "relink/taxid_9606/dss", crosslinks: [
      { alpha_proteins: ["Q12345"], beta_proteins: ["P12345"], alpha_sequence: "CK", beta_sequence: "DK" },
    ] }], predicted_complexes: [] },
    { accession: "PXD000003", title: "No matches", relink_runs: [], predicted_complexes: [] },
  ]);
  app.run('setSearchMode("protein")');
  app.change("#project-search", "P12345");
  assert.equal(app.count(), "2 matching protein accessions");
  assert.match(app.list(), /P12345-2/);
  app.run('selectProtein("P12345")');
  assert.match(app.node("#metrics").innerHTML, /Cross-link groups/);
  assert.match(app.node("#tab-panel").innerHTML, /PXD000001/);
  assert.match(app.node("#tab-panel").innerHTML, /PXD000002/);
  assert.doesNotMatch(app.node("#tab-panel").innerHTML, /PXD000003/);
  app.run('state.tab = "crosslinks"; renderProject()');
  assert.match(app.node("#tab-panel").innerHTML, /PXD000001/);
  assert.match(app.node("#tab-panel").innerHTML, /PXD000002/);
  app.run('selectProtein("P12345-2"); state.tab = "crosslinks"; renderProject()');
  assert.match(app.node("#tab-panel").innerHTML, /PXD000001/);
  assert.doesNotMatch(app.node("#tab-panel").innerHTML, /PXD000002/);
});

test("crosslink table places proteins and structure before scrollable peptides", () => {
  const app = explorer([]);
  const html = app.crosslinks({ accession: "PXD000001", predicted_complexes: [{ job_name: "model" }], relink_runs: [
    { path: "relink/taxid_9606/dss", crosslinks: [{
      alpha_proteins: ["P12345"], beta_proteins: ["Q12345"], predicted_complex: "model",
      alpha_sequence: "LONGPEPTIDESEQUENCE", beta_sequence: "SHORT",
    }] },
  ] });
  assert.ok(html.indexOf(">Protein A</th>") < html.indexOf(">Structure</th>"));
  assert.ok(html.indexOf(">Structure</th>") < html.indexOf(">Alpha peptide</th>"));
  assert.match(html, /data-pxd="PXD000001" data-job-name="model"/);
  assert.match(html, /class="peptide-scroll"[^>]*>LONGPEPTIDESEQUENCE/);
  assert.match(html, /data-protein="P12345"/);
});

test("chain confidence theme maps Mol* confidence categories to chain shades", () => {
  const app = explorer([]);
  const confidence = { name: "plddt-confidence", factory: () => ({ color: (location) => location.score }) };
  let added;
  app.context.viewer = { plugin: { representation: { structure: { themes: { colorThemeRegistry: {
    get: () => confidence, add: (provider) => { added = provider; },
  } } } } } };
  app.run("registerChainConfidenceTheme(viewer)");
  const theme = added.factory({}, {});
  const location = (chain, score) => ({
    kind: "element-location", element: 0, score,
    unit: { kind: 0, model: { atomicHierarchy: { chainAtomSegments: { index: [0] }, chains: { label_asym_id: { value: () => chain } } } } },
  });
  assert.equal(theme.color(location("A", 0x0053d6)), 0x9c1c25);
  assert.equal(theme.color(location("B", 0xff7d45)), 0xd5e8ff);
  assert.equal(theme.color(location("A", 0xaaaaaa)), 0xaaaaaa);
  assert.equal(theme.color(location("C", 0x0053d6)), 0xaaaaaa);
});

test("structure loading explicitly applies the chain confidence theme", async () => {
  const app = explorer([]);
  const calls = [];
  const confidence = { name: "plddt-confidence", factory: () => ({ color: () => 0x0053d6 }) };
  const registry = { get: () => confidence, add: (provider) => calls.push(provider.name) };
  app.context.window.molstar = { Viewer: { create: async () => ({
    dispose() {},
    plugin: {
      representation: { structure: { themes: { colorThemeRegistry: registry } } },
      builders: {
        data: { download: async (params) => { calls.push(params.url); return "data"; } },
        structure: {
          parseTrajectory: async (data, format) => { calls.push(`${data}:${format}`); return "trajectory"; },
          hierarchy: { applyPreset: async (trajectory, preset, params) => {
            calls.push(`${trajectory}:${preset}:${params.representationPreset}:${params.representationPresetParams.theme.globalName}`);
          } },
        },
      },
    },
  }) } };
  app.context.projectToRender = { predicted_complexes: [{
    job_name: "one", protein_a: "P12345", protein_b: "Q12345", structure_path: "one.cif",
  }] };
  await app.run('openStructureViewer(projectToRender, "one")');
  assert.deepEqual(calls, [
    "xhamlet-chain-confidence", "one.cif", "data:mmcif", "trajectory:default:auto:xhamlet-chain-confidence",
  ]);
  assert.equal(app.node("#structure-modal-status").textContent, "");
});

test("linear pages load one compressed chunk at a time and show 100 rows", async () => {
  const project = { accession: "PXD000001", title: "Test", relink_runs: [], predicted_complexes: [] };
  const app = explorer([project]);
  const results = {
    innerHTML: "", textContent: "", querySelectorAll: () => [],
    querySelector: () => ({ addEventListener() {} }),
  };
  app.node("#tab-panel").querySelector = () => results;
  app.run('state.project = catalog.projects[0]; state.tab = "linear"');
  const row = (n) => [`P${n}`, "PEPTIDE", "MOD", "1", "12", "2", "taxid_9606/dss", "raw.mzML", "7", "scan=7", `${n}`];
  const chunks = { first: Array.from({ length: 5000 }, (_, i) => row(i)), second: [row(5000)] };
  const calls = [];
  app.context.fetch = async (url) => {
    calls.push(url);
    if (url.endsWith("index.json")) return { ok: true, json: async () => ({
      version: 1, page_size: 100, chunk_size: 5000,
      projects: { PXD000001: { row_count: 5001, chunks: ["first", "second"] } },
    }) };
    const bytes = zlib.gzipSync(JSON.stringify(chunks[url.split("/").pop()]));
    return { ok: true, arrayBuffer: async () => Uint8Array.from(bytes).buffer };
  };
  await app.run('loadLinearPage("PXD000001", 1)');
  assert.match(results.innerHTML, /rows 1-100 of 5,001/);
  assert.equal((results.innerHTML.match(/<tr>/g) || []).length, 101);
  assert.match(results.innerHTML, />P99</);
  assert.doesNotMatch(results.innerHTML, />P100</);
  await app.run('loadLinearPage("PXD000001", 2)');
  assert.match(results.innerHTML, /rows 101-200 of 5,001/);
  assert.equal(calls.length, 2);
  await app.run('loadLinearPage("PXD000001", 51)');
  assert.match(results.innerHTML, /rows 5,001-5,001 of 5,001/);
  assert.match(results.innerHTML, />P5000</);
  assert.equal(calls.length, 3);
});

test("linear page reports missing chunks and does not render late results after navigation", async () => {
  const app = explorer([{ accession: "PXD000001", title: "Test" }]);
  const results = {
    innerHTML: "", textContent: "", querySelectorAll: () => [],
    querySelector: () => ({ addEventListener() {} }),
  };
  app.node("#tab-panel").querySelector = () => results;
  app.run('state.project = catalog.projects[0]; state.tab = "linear"');
  app.context.fetch = async (url) => url.endsWith("index.json")
    ? { ok: true, json: async () => ({ version: 1, page_size: 100, chunk_size: 5000, projects: {
      PXD000001: { row_count: 1, chunks: ["missing"] },
    } }) }
    : { ok: false, status: 404 };
  await app.run('loadLinearPage("PXD000001", 1)');
  assert.match(results.innerHTML, /Linear chunk: HTTP 404/);
  let release;
  app.context.fetch = () => new Promise((resolve) => { release = resolve; });
  const loading = app.run('loadLinearPage("PXD000001", 1)');
  await new Promise((resolve) => setImmediate(resolve));
  app.run('state.tab = "overview"');
  results.innerHTML = "different view";
  release({ ok: false, status: 404 });
  await loading;
  assert.equal(results.innerHTML, "different view");
});

test("quick filters combine with each other and search, preserving zero-hit completed results", () => {
  const app = explorer([
    { accession: "PXD000001", title: "Complete empty", relink_runs: [
      { mzid_documents: [{ complete: true, passing_items: 0 }] },
      { mzid_documents: [{ complete: false }] },
    ] },
    { accession: "PXD000002", title: "Both", relink_runs: [
      { mzid_documents: [{ complete: true }] },
    ], predicted_complexes: [{ structure_path: "model.cif" }] },
    { accession: "PXD000003", title: "Incomplete", relink_runs: [
      { mzid_documents: [{ complete: false }] },
    ], predicted_complexes: [{}] },
    { accession: "PXD000004", title: "No results" },
  ]);
  assert.equal(app.count(), "4 of 4 projects");
  app.change("#filter-relink", true);
  assert.equal(app.count(), "2 of 4 projects");
  assert.match(app.list(), /PXD000001/);
  app.change("#filter-af3", true);
  assert.equal(app.count(), "1 of 4 projects");
  assert.match(app.list(), /PXD000002/);
  app.change("#project-search", "missing");
  assert.equal(app.count(), "0 of 4 projects");
  assert.match(app.list(), /No matching PXDs/);
  app.change("#project-search", "both");
  assert.equal(app.count(), "1 of 4 projects");
  app.change("#project-search", "");
  app.change("#filter-relink", false);
  app.change("#filter-af3", false);
  assert.equal(app.count(), "4 of 4 projects");
});

test("current catalog counts match the rendered quick filters", () => {
  const catalog = JSON.parse(fs.readFileSync(
    path.join(__dirname, "../web/results-explorer/data/catalog.json"), "utf8",
  ));
  const app = explorer(catalog.projects);
  const relink = (p) => p.relink_runs?.some((r) => r.mzid_documents?.some((d) => d.complete === true));
  const af3 = (p) => p.predicted_complexes?.some((r) => r.structure_path);
  app.change("#filter-relink", true);
  assert.equal(app.count(), `${catalog.projects.filter(relink).length} of ${catalog.project_count} projects`);
  app.change("#filter-af3", true);
  assert.equal(app.count(), `${catalog.projects.filter((p) => relink(p) && af3(p)).length} of ${catalog.project_count} projects`);
  app.change("#filter-relink", false);
  assert.equal(app.count(), `${catalog.projects.filter(af3).length} of ${catalog.project_count} projects`);
});
