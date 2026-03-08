// =============================================================================
// VICTOR COMMAND CENTER — REPO LIST COMPONENT
// =============================================================================

class RepoList {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.repos = [];
    this.selectedName = null;
    this.onSelect = null; // callback(repo)
  }

  render(repos) {
    this.repos = repos || [];
    if (!this.repos.length) {
      this.container.innerHTML = '<div class="loading-msg">No repos found.</div>';
      return;
    }

    this.container.innerHTML = this.repos.map(r => this._itemHtml(r)).join('');

    this.container.querySelectorAll('.repo-item').forEach(el => {
      el.addEventListener('click', () => {
        const name = el.dataset.name;
        this.select(name);
      });
    });
  }

  select(name) {
    this.selectedName = name;
    this.container.querySelectorAll('.repo-item').forEach(el => {
      el.classList.toggle('active', el.dataset.name === name);
    });
    const repo = this.repos.find(r => r.name === name);
    if (repo && this.onSelect) this.onSelect(repo);
  }

  _itemHtml(repo) {
    const badge = `<span class="repo-status-badge badge-${repo.status || 'unknown'}">${(repo.status || 'unknown').toUpperCase()}</span>`;
    const lang = repo.language ? `<div class="repo-item-lang">${repo.language}${repo.framework ? ' · ' + repo.framework : ''}</div>` : '';
    return `
      <div class="repo-item" data-name="${this._esc(repo.name)}">
        <div class="repo-item-name">${this._esc(repo.name)}${badge}</div>
        ${lang}
      </div>
    `;
  }

  _esc(str) {
    return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  }
}
