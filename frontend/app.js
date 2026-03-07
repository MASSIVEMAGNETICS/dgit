// =============================================================================
// VICTOR COMMAND CENTER — MAIN APPLICATION
// =============================================================================

(function () {
  'use strict';

  // ---- Component instances ------------------------------------------------
  const repoList   = new RepoList('repoList');
  const graphView  = new GraphView('graphContainer');
  const queryPanel = new QueryPanel('queryResults');
  const repoDetail = new RepoDetail('repoDetail');

  // ---- Tab switching -------------------------------------------------------
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const panelId = 'tab-' + tab.dataset.tab;
      document.getElementById(panelId).classList.add('active');
    });
  });

  // ---- Health / status indicator ------------------------------------------
  async function checkHealth() {
    const dot  = document.getElementById('statusDot');
    const text = document.getElementById('statusText');
    try {
      const r = await fetch('/health');
      if (r.ok) {
        dot.className = 'status-dot ok';
        text.textContent = 'ONLINE';
      } else {
        throw new Error('not ok');
      }
    } catch {
      dot.className = 'status-dot err';
      text.textContent = 'OFFLINE';
    }
  }

  // ---- Load repos ----------------------------------------------------------
  async function loadRepos() {
    try {
      const r = await fetch('/api/repos');
      if (!r.ok) throw new Error(r.statusText);
      const data = await r.json();
      repoList.render(data.repos || []);
      return data.repos || [];
    } catch (err) {
      document.getElementById('repoList').innerHTML =
        `<div class="error-msg">⚠ ${err.message}</div>`;
      return [];
    }
  }

  // ---- Load graph ----------------------------------------------------------
  async function loadGraph() {
    try {
      const r = await fetch('/api/graph');
      if (!r.ok) throw new Error(r.statusText);
      const data = await r.json();
      graphView.render(data);
    } catch (err) {
      document.getElementById('graphContainer').innerHTML =
        `<div class="error-msg">⚠ Failed to load graph: ${err.message}</div>`;
    }
  }

  // ---- Repo selection ------------------------------------------------------
  repoList.onSelect = (repo) => {
    // Switch to Repos tab and show detail
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="repos"]').classList.add('active');
    document.getElementById('tab-repos').classList.add('active');

    repoDetail.loadAndRender(repo.name);
  };

  graphView.onNodeClick = (name) => {
    repoList.select(name);
  };

  // ---- Scan button ---------------------------------------------------------
  document.getElementById('btnScan').addEventListener('click', async () => {
    const pathStr = prompt('Enter comma-separated local paths to scan:');
    if (!pathStr) return;
    const paths = pathStr.split(',').map(p => p.trim()).filter(Boolean);
    try {
      const r = await fetch('/api/scan/local', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ paths }),
      });
      const data = await r.json();
      alert(`Scanned ${data.repos_scanned} repo(s).`);
      await loadRepos();
      await loadGraph();
    } catch (err) {
      alert('Scan failed: ' + err.message);
    }
  });

  // ---- Refresh button ------------------------------------------------------
  document.getElementById('btnRefresh').addEventListener('click', async () => {
    await loadRepos();
    await loadGraph();
  });

  // ---- Query input ---------------------------------------------------------
  const queryInput = document.getElementById('queryInput');
  const btnQuery   = document.getElementById('btnQuery');

  async function sendQuery() {
    const text = queryInput.value.trim();
    if (!text) return;
    queryInput.value = '';

    // Switch to Query tab
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-tab="query"]').classList.add('active');
    document.getElementById('tab-query').classList.add('active');

    await queryPanel.submitQuery(text);
  }

  btnQuery.addEventListener('click', sendQuery);
  queryInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') sendQuery();
  });

  // ---- Bootstrap -----------------------------------------------------------
  (async function init() {
    await checkHealth();
    await Promise.all([loadRepos(), loadGraph()]);
  })();
})();
