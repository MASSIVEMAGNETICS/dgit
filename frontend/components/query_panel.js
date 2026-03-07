// =============================================================================
// VICTOR COMMAND CENTER — QUERY PANEL COMPONENT
// =============================================================================

class QueryPanel {
  constructor(resultsContainerId) {
    this.container = document.getElementById(resultsContainerId);
    this.history = [];
  }

  async submitQuery(queryText) {
    if (!queryText.trim()) return;

    this._appendUserBubble(queryText);

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: queryText }),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: response.statusText }));
        this._appendError(`Query failed: ${err.detail || response.statusText}`);
        return;
      }

      const data = await response.json();
      this.history.push(data);
      this._appendResponseBubble(data);
    } catch (err) {
      this._appendError(`Network error: ${err.message}`);
    }
  }

  // ------------------------------------------------------------------

  _appendUserBubble(text) {
    const el = document.createElement('div');
    el.className = 'query-bubble';
    el.innerHTML = `<div class="query-bubble-user">YOU › ${this._esc(text)}</div>`;
    this.container.appendChild(el);
    this._scrollBottom();
    return el;
  }

  _appendResponseBubble(data) {
    const results = data.results || [];
    const resultHtml = results.slice(0, 20).map(r => {
      const text = r.name
        ? `<strong>${this._esc(r.name)}</strong>${r.language ? ' [' + this._esc(r.language) + ']' : ''}${r.status ? ' — ' + this._esc(r.status) : ''}`
        : this._esc(JSON.stringify(r).slice(0, 200));
      return `<div class="query-result-item">${text}</div>`;
    }).join('');

    const el = document.createElement('div');
    el.className = 'query-bubble';
    el.innerHTML = `
      <span class="query-bubble-intent">${this._esc((data.intent || 'unknown').toUpperCase())}</span>
      <div class="query-bubble-summary">${this._esc(data.summary || '')}</div>
      ${resultHtml}
    `;
    this.container.appendChild(el);
    this._scrollBottom();
  }

  _appendError(msg) {
    const el = document.createElement('div');
    el.className = 'query-bubble';
    el.innerHTML = `<div class="error-msg">⚠ ${this._esc(msg)}</div>`;
    this.container.appendChild(el);
    this._scrollBottom();
  }

  _scrollBottom() {
    this.container.scrollTop = this.container.scrollHeight;
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
