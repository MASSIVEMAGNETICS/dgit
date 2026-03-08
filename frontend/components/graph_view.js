// =============================================================================
// VICTOR COMMAND CENTER — GRAPH VIEW COMPONENT
// =============================================================================

class GraphView {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.onNodeClick = null; // callback(nodeName)
  }

  render(graphData) {
    if (!graphData || !graphData.nodes || !graphData.nodes.length) {
      this.container.innerHTML = '<div class="loading-msg">No graph data available. Scan repos to build the graph.</div>';
      return;
    }

    const nodes = graphData.nodes;
    const edges = graphData.edges || [];

    // Simple SVG layout: arrange nodes in a circle
    const W = Math.max(this.container.clientWidth || 800, 600);
    const H = Math.max(this.container.clientHeight || 500, 400);
    const cx = W / 2;
    const cy = H / 2;
    const radius = Math.min(W, H) * 0.38;

    const positions = {};
    nodes.forEach((node, i) => {
      const angle = (2 * Math.PI * i) / nodes.length - Math.PI / 2;
      positions[node.id] = {
        x: cx + radius * Math.cos(angle),
        y: cy + radius * Math.sin(angle),
      };
    });

    const colorMap = {
      python: '#3572a5',
      javascript: '#f1e05a',
      typescript: '#2b7489',
      rust: '#dea584',
      go: '#00add8',
      java: '#b07219',
      unknown: '#555577',
    };

    const statusColor = {
      active: '#00ff41',
      broken: '#ff3860',
      archived: '#ffe900',
      partial: '#ff6b35',
      experimental: '#9b59ff',
      unknown: '#555577',
    };

    // Build SVG
    let edgeSvg = edges.map(e => {
      const src = positions[e.source];
      const tgt = positions[e.target];
      if (!src || !tgt) return '';
      return `<line x1="${src.x.toFixed(1)}" y1="${src.y.toFixed(1)}" x2="${tgt.x.toFixed(1)}" y2="${tgt.y.toFixed(1)}" class="graph-edge-line" title="${this._esc(e.relationship)}" />`;
    }).join('');

    let nodeSvg = nodes.map(node => {
      const pos = positions[node.id];
      if (!pos) return '';
      const lang = (node.metadata && node.metadata.language) || 'unknown';
      const status = (node.metadata && node.metadata.status) || 'unknown';
      const fill = colorMap[lang] || colorMap.unknown;
      const stroke = statusColor[status] || statusColor.unknown;
      const label = node.label.length > 18 ? node.label.slice(0, 16) + '…' : node.label;
      return `
        <g class="graph-node" data-id="${this._esc(node.id)}" style="cursor:pointer">
          <circle cx="${pos.x.toFixed(1)}" cy="${pos.y.toFixed(1)}" r="18"
            fill="${fill}" fill-opacity="0.35"
            stroke="${stroke}" stroke-width="1.5" />
          <text x="${pos.x.toFixed(1)}" y="${(pos.y + 30).toFixed(1)}"
            text-anchor="middle" fill="#e0e0ff" font-size="10"
            font-family="'Courier New', monospace">${this._esc(label)}</text>
        </g>`;
    }).join('');

    this.container.innerHTML = `
      <svg class="graph-svg" viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">
        <style>
          .graph-edge-line { stroke: #1e1e3a; stroke-width: 1; }
          .graph-node:hover circle { stroke-width: 3; }
        </style>
        <g class="edges">${edgeSvg}</g>
        <g class="nodes">${nodeSvg}</g>
      </svg>`;

    // Attach click handlers
    this.container.querySelectorAll('.graph-node').forEach(el => {
      el.addEventListener('click', () => {
        const id = el.dataset.id;
        if (id && this.onNodeClick) this.onNodeClick(id);
      });
    });
  }

  _esc(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }
}
