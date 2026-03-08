// =============================================================================
// VICTOR COMMAND CENTER — REPO DETAIL COMPONENT
// =============================================================================

class RepoDetail {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
  }

  async loadAndRender(repoName) {
    this.container.innerHTML = '<div class="loading-msg">Loading…</div>';

    try {
      const response = await fetch(`/api/repos/${encodeURIComponent(repoName)}`);
      if (!response.ok) {
        this.container.innerHTML = `<div class="error-msg">Failed to load '${this._esc(repoName)}'.</div>`;
        return;
      }
      const repo = await response.json();
      this._render(repo);
    } catch (err) {
      this.container.innerHTML = `<div class="error-msg">Network error: ${this._esc(err.message)}</div>`;
    }
  }

  renderBrief(repo) {
    this._render(repo);
  }

  // ------------------------------------------------------------------

  _render(repo) {
    const statusBadge = `<span class="repo-status-badge badge-${repo.status || 'unknown'}">${(repo.status || 'UNKNOWN').toUpperCase()}</span>`;

    const depsHtml = (repo.dependencies || []).slice(0, 30).map(d =>
      `<span class="dep-tag">${this._esc(d)}</span>`
    ).join('');

    const entryHtml = (repo.entrypoints || []).map(e =>
      `<span class="dep-tag">${this._esc(e)}</span>`
    ).join('');

    const routeHtml = (repo.api_routes || []).slice(0, 20).map(r =>
      `<span class="dep-tag">${this._esc(r)}</span>`
    ).join('');

    const testHtml = (repo.test_files || []).slice(0, 10).map(t =>
      `<span class="dep-tag">${this._esc(t)}</span>`
    ).join('');

    this.container.innerHTML = `
      <div class="repo-detail-card">
        <h2>${this._esc(repo.name)} ${statusBadge}</h2>
        ${repo.description ? `<div style="color:var(--text-secondary);margin-bottom:12px;">${this._esc(repo.description)}</div>` : ''}

        <div class="detail-row"><span class="detail-label">Language</span><span class="detail-value">${this._esc(repo.language || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Framework</span><span class="detail-value">${this._esc(repo.framework || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Runtime</span><span class="detail-value">${this._esc(repo.runtime || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Package Manager</span><span class="detail-value">${this._esc(repo.package_manager || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Purpose</span><span class="detail-value">${this._esc(repo.purpose || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">Visibility</span><span class="detail-value">${this._esc(repo.visibility || '—')}</span></div>
        <div class="detail-row"><span class="detail-label">TODOs</span><span class="detail-value">${repo.todo_count ?? '—'}</span></div>
        <div class="detail-row"><span class="detail-label">Scanned</span><span class="detail-value">${repo.scan_timestamp ? new Date(repo.scan_timestamp).toLocaleString() : '—'}</span></div>

        ${depsHtml ? `
          <div style="margin-top:12px;">
            <div class="detail-label" style="margin-bottom:6px;">Dependencies (${(repo.dependencies||[]).length})</div>
            <div class="dep-list">${depsHtml}</div>
          </div>` : ''}

        ${entryHtml ? `
          <div style="margin-top:12px;">
            <div class="detail-label" style="margin-bottom:6px;">Entrypoints</div>
            <div class="dep-list">${entryHtml}</div>
          </div>` : ''}

        ${routeHtml ? `
          <div style="margin-top:12px;">
            <div class="detail-label" style="margin-bottom:6px;">API Routes</div>
            <div class="dep-list">${routeHtml}</div>
          </div>` : ''}

        ${testHtml ? `
          <div style="margin-top:12px;">
            <div class="detail-label" style="margin-bottom:6px;">Test Files</div>
            <div class="dep-list">${testHtml}</div>
          </div>` : ''}

        ${repo.build_instructions ? `
          <div style="margin-top:12px;">
            <div class="detail-label" style="margin-bottom:6px;">Build Instructions</div>
            <pre style="background:var(--bg-deep);padding:8px;border-radius:4px;font-size:10px;overflow-x:auto;color:var(--text-secondary);white-space:pre-wrap;">${this._esc(repo.build_instructions)}</pre>
          </div>` : ''}
      </div>`;
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
