const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

function explorer(projects, loading = false) {
  const nodes = new Map();
  const context = vm.createContext({
    Intl,
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
