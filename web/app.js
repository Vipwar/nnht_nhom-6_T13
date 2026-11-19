/* ============================================================================
   LexAutomata Studio — Interactive Frontend Engine (Zero External Dependencies)
   Topic T13: Automata-based Lexical Analyzer (UEH Formal Languages)
   ============================================================================ */

(() => {
  "use strict";

  const SVG_NS = "http://www.w3.org/2000/svg";

  // Global Application State
  const AppState = {
    presets: {},
    singleExamples: [],
    activePreset: "minilang",
    lastPresetId: "minilang",
    automataData: null,
    scanData: null,
    currentAutoView: "min_dfa",
    graphCategoryFilter: "all",
    selectedTraceIdx: 0,
    animStepIdx: 0,
    animTimer: null,
    singleReData: null,
    singleReView: "nfa",
    editorSpecs: [],
    testReport: null,
    testFilter: "all",
    panZoomControllers: {},
  };

  // ==================== UTILITIES ====================
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  function escHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function svgEl(tag, attrs = {}, text = null) {
    const el = document.createElementNS(SVG_NS, tag);
    for (const [k, v] of Object.entries(attrs)) {
      el.setAttribute(k, String(v));
    }
    if (text !== null) el.textContent = text;
    return el;
  }

  async function apiGet(url) {
    const resp = await fetch(url);
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
    return data;
  }

  async function apiPost(url, body) {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || `HTTP ${resp.status}`);
    return data;
  }

  function showGlobalAlert(msg, kind = "ok") {
    const box = $("#global-alert");
    if (!msg) {
      box.classList.add("hidden");
      return;
    }
    box.className = `alert-banner alert-${kind}`;
    box.textContent = msg;
    box.classList.remove("hidden");
  }

  function downloadBlob(content, filename, mime = "text/plain;charset=utf-8") {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function categoryBadgeClass(cat) {
    const allowed = new Set([
      "keyword", "identifier", "literal", "operator", "delimiter", "comment", "whitespace", "error",
    ]);
    return allowed.has(cat) ? `badge-${cat}` : "badge-other";
  }

  function formatLexeme(s) {
    return String(s)
      .replace(/\\/g, "\\\\")
      .replace(/\n/g, "\\n")
      .replace(/\t/g, "\\t")
      .replace(/\r/g, "\\r");
  }

  // ==================== PAN & ZOOM SVG CONTROLLER ====================
  function attachPanZoom(viewportEl, svgElNode, key) {
    const state = { scale: 1, tx: 20, ty: 20, dragging: false, startX: 0, startY: 0, contentW: 800, contentH: 400 };
    AppState.panZoomControllers[key] = state;

    const apply = () => {
      const g = svgElNode.querySelector("g.pz-root");
      if (g) {
        g.setAttribute("transform", `translate(${state.tx.toFixed(1)}, ${state.ty.toFixed(1)}) scale(${state.scale.toFixed(3)})`);
      }
    };

    state.fit = () => {
      const rect = viewportEl.getBoundingClientRect();
      const vw = Math.max(300, rect.width);
      const vh = Math.max(260, rect.height);
      const pad = 36;
      const sx = (vw - pad * 2) / Math.max(100, state.contentW);
      const sy = (vh - pad * 2) / Math.max(100, state.contentH);
      state.scale = Math.max(0.18, Math.min(1.25, Math.min(sx, sy)));
      state.tx = (vw - state.contentW * state.scale) / 2;
      state.ty = (vh - state.contentH * state.scale) / 2;
      apply();
    };

    state.zoomBy = (factor) => {
      const rect = viewportEl.getBoundingClientRect();
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const next = Math.max(0.15, Math.min(3.5, state.scale * factor));
      const ratio = next / state.scale;
      state.tx = cx - (cx - state.tx) * ratio;
      state.ty = cy - (cy - state.ty) * ratio;
      state.scale = next;
      apply();
    };

    if (viewportEl.dataset.pzBound) return state;
    viewportEl.dataset.pzBound = "1";

    viewportEl.addEventListener("mousedown", (e) => {
      if (e.target.closest(".state-node")) return;
      state.dragging = true;
      state.startX = e.clientX - state.tx;
      state.startY = e.clientY - state.ty;
    });

    window.addEventListener("mousemove", (e) => {
      if (!state.dragging) return;
      state.tx = e.clientX - state.startX;
      state.ty = e.clientY - state.startY;
      apply();
    });

    window.addEventListener("mouseup", () => {
      state.dragging = false;
    });

    viewportEl.addEventListener("wheel", (e) => {
      e.preventDefault();
      const rect = viewportEl.getBoundingClientRect();
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const factor = e.deltaY < 0 ? 1.14 : 0.88;
      const next = Math.max(0.14, Math.min(3.8, state.scale * factor));
      const ratio = next / state.scale;
      state.tx = mx - (mx - state.tx) * ratio;
      state.ty = my - (my - state.ty) * ratio;
      state.scale = next;
      apply();
    }, { passive: false });

    return state;
  }

  // ==================== AUTOMATA GRAPH SVG RENDERER ====================
  function renderAutomataSVG(svgNode, viewportEl, graph, pzKey, onSelectNode = null, categoryFilter = "all") {
    svgNode.innerHTML = "";
    if (!graph || !graph.nodes || graph.nodes.length === 0) return;

    const nodes = graph.nodes;
    const edges = graph.edges || [];

    // Build adjacency and reverse adjacency for BFS layering & category path filtering
    const adj = new Map();
    const revAdj = new Map();
    for (const n of nodes) {
      adj.set(n.id, []);
      revAdj.set(n.id, []);
    }
    for (const e of edges) {
      if (adj.has(e.from)) adj.get(e.from).push(e.to);
      if (revAdj.has(e.to)) revAdj.get(e.to).push(e.from);
    }

    // Compute active node set when filtering by token category
    let activeNodeIds = null;
    if (categoryFilter && categoryFilter !== "all" && AppState.automataData?.specs) {
      const catByToken = new Map(AppState.automataData.specs.map((s) => [s.name, s.category]));
      const matchCat = (tokName) => {
        const c = catByToken.get(tokName) || "other";
        if (categoryFilter === "comment") return c === "comment" || c === "whitespace";
        return c === categoryFilter;
      };
      activeNodeIds = new Set();
      const rQueue = [];
      for (const n of nodes) {
        if (n.is_accept && n.accept_token && matchCat(n.accept_token)) {
          activeNodeIds.add(n.id);
          rQueue.push(n.id);
        }
      }
      while (rQueue.length > 0) {
        const v = rQueue.shift();
        for (const u of revAdj.get(v) || []) {
          if (!activeNodeIds.has(u)) {
            activeNodeIds.add(u);
            rQueue.push(u);
          }
        }
      }
      activeNodeIds.add(graph.start_state);
    }

    const level = new Map();
    const queue = [graph.start_state];
    level.set(graph.start_state, 0);
    while (queue.length > 0) {
      const u = queue.shift();
      for (const v of adj.get(u) || []) {
        if (!level.has(v)) {
          level.set(v, level.get(u) + 1);
          queue.push(v);
        }
      }
    }
    let maxLvl = Math.max(0, ...Array.from(level.values()));
    for (const n of nodes) {
      if (!level.has(n.id)) {
        maxLvl += 1;
        level.set(n.id, maxLvl);
      }
    }

    const layers = new Map();
    for (const n of nodes) {
      const l = level.get(n.id);
      if (!layers.has(l)) layers.set(l, []);
      layers.get(l).push(n.id);
    }

    // Order within layers to keep branches tidy (sort by parent average y)
    const maxNodesPerCol = Math.max(...Array.from(layers.values()).map((a) => a.length));
    const xGap = nodes.length > 40 ? 185 : 152;
    const yGap = nodes.length > 40 ? 96 : 98;
    const R = nodes.length > 40 ? 21 : 24;

    const pos = new Map();
    const totalH = Math.max(240, (maxNodesPerCol - 1) * yGap + 160);
    const orderedLevels = Array.from(layers.keys()).sort((a, b) => a - b);

    for (const l of orderedLevels) {
      const ids = layers.get(l);
      if (l > 0) {
        const parents = new Map();
        for (const e of edges) {
          if (level.get(e.from) === l - 1 && level.get(e.to) === l) {
            if (!parents.has(e.to)) parents.set(e.to, []);
            parents.get(e.to).push(pos.get(e.from)?.y ?? 0);
          }
        }
        ids.sort((a, b) => {
          const pa = parents.get(a);
          const pb = parents.get(b);
          const avgA = pa ? pa.reduce((s, v) => s + v, 0) / pa.length : a * 10;
          const avgB = pb ? pb.reduce((s, v) => s + v, 0) / pb.length : b * 10;
          return avgA - avgB || a - b;
        });
      }
      const colH = (ids.length - 1) * yGap;
      const yStart = (totalH - colH) / 2;
      ids.forEach((id, idx) => {
        pos.set(id, { x: 95 + l * xGap, y: yStart + idx * yGap });
      });
    }

    const maxX = Math.max(...Array.from(pos.values()).map((p) => p.x)) + 120;
    const maxY = totalH + 60;

    // SVG defs (arrowheads)
    const defs = svgEl("defs");
    const mkMarker = (id, color) => {
      const m = svgEl("marker", {
        id, viewBox: "0 0 10 10", refX: "9", refY: "5",
        markerWidth: "7", markerHeight: "7", orient: "auto-start-reverse",
      });
      m.appendChild(svgEl("path", { d: "M 0 1.2 L 9.5 5 L 0 8.8 z", fill: color }));
      return m;
    };
    defs.appendChild(mkMarker(`arrow-std-${pzKey}`, "#64748b"));
    defs.appendChild(mkMarker(`arrow-eps-${pzKey}`, "#2563eb"));
    defs.appendChild(mkMarker(`arrow-start-${pzKey}`, "#059669"));
    svgNode.appendChild(defs);

    const rootG = svgEl("g", { class: "pz-root" });
    svgNode.appendChild(rootG);

    const edgeSet = new Set(edges.map((e) => `${e.from}->${e.to}`));

    // Group edges sharing same (from, to)
    const multiEdgeGroups = new Map();
    for (const e of edges) {
      const k = `${e.from}->${e.to}`;
      if (!multiEdgeGroups.has(k)) multiEdgeGroups.set(k, []);
      multiEdgeGroups.get(k).push(e);
    }

    const edgeLayer = svgEl("g", { class: "edges-layer" });
    const labelLayer = svgEl("g", { class: "labels-layer" });
    const nodeLayer = svgEl("g", { class: "nodes-layer" });
    rootG.appendChild(edgeLayer);
    rootG.appendChild(labelLayer);
    rootG.appendChild(nodeLayer);

    // Collision-avoiding label placement
    const placedBoxes = [];
    for (const p of pos.values()) {
      placedBoxes.push({ x1: p.x - R - 4, y1: p.y - R - 4, x2: p.x + R + 24, y2: p.y + R + 22 });
    }

    const drawLabelPill = (x, y, text, isEps, isDimmed) => {
      if (isDimmed) return;
      const clean = text.length > 16 ? text.slice(0, 14) + "…" : text;
      const w = Math.max(20, clean.length * 7.2 + 10);
      const h = 18;
      let bestX = x;
      let bestY = y;
      const offsets = [0, -19, 19, -36, 36, -54, 54];
      for (const dy of offsets) {
        const cy = y + dy;
        const bx1 = x - w / 2 - 2;
        const by1 = cy - h / 2 - 2;
        const bx2 = x + w / 2 + 2;
        const by2 = cy + h / 2 + 2;
        const collides = placedBoxes.some(
          (b) => !(bx2 < b.x1 || bx1 > b.x2 || by2 < b.y1 || by1 > b.y2)
        );
        if (!collides) {
          bestY = cy;
          break;
        }
      }
      placedBoxes.push({
        x1: bestX - w / 2,
        y1: bestY - h / 2,
        x2: bestX + w / 2,
        y2: bestY + h / 2,
      });

      const g = svgEl("g");
      g.appendChild(svgEl("title", {}, text));
      g.appendChild(svgEl("rect", {
        x: bestX - w / 2, y: bestY - h / 2, width: w, height: h, rx: 5,
        fill: isEps ? "#eff6ff" : "#ffffff",
        stroke: isEps ? "#93c5fd" : "#cbd5e1",
        "stroke-width": 1,
      }));
      g.appendChild(svgEl("text", {
        x: bestX, y: bestY + 4,
        "text-anchor": "middle",
        "font-family": "var(--mono)",
        "font-size": 11,
        "font-weight": 700,
        fill: isEps ? "#1d4ed8" : "#0f172a",
      }, clean));
      labelLayer.appendChild(g);
    };

    // Draw all edges
    for (const group of multiEdgeGroups.values()) {
      const first = group[0];
      const combinedLabel = group.map((e) => e.label).join(", ");
      const isEps = group.every((e) => e.is_epsilon);
      const p1 = pos.get(first.from);
      const p2 = pos.get(first.to);
      if (!p1 || !p2) continue;

      const isEdgeActive = !activeNodeIds || (activeNodeIds.has(first.from) && activeNodeIds.has(first.to));
      const strokeColor = isEps ? "#3b82f6" : "#64748b";
      const markerUrl = `url(#${isEps ? "arrow-eps" : "arrow-std"}-${pzKey})`;
      const edgeOpacity = isEdgeActive ? "1" : "0.14";

      if (first.from === first.to) {
        const x0 = p1.x - R * 0.45;
        const y0 = p1.y - R * 0.88;
        const x1 = p1.x + R * 0.45;
        const y1 = p1.y - R * 0.88;
        const d = `M ${x0} ${y0} C ${p1.x - 32} ${p1.y - R - 46}, ${p1.x + 32} ${p1.y - R - 46}, ${x1} ${y1}`;
        const pathEl = svgEl("path", {
          d, fill: "none", stroke: strokeColor, "stroke-width": 1.6,
          "stroke-dasharray": isEps ? "5,3" : "none",
          "marker-end": markerUrl,
          opacity: edgeOpacity,
        });
        pathEl.appendChild(svgEl("title", {}, `${first.from} → ${first.to}: ${combinedLabel}`));
        edgeLayer.appendChild(pathEl);
        drawLabelPill(p1.x, p1.y - R - 34, combinedLabel, isEps, !isEdgeActive);
        continue;
      }

      const dx = p2.x - p1.x;
      const dy = p2.y - p1.y;
      const dist = Math.hypot(dx, dy) || 1;
      const ux = dx / dist;
      const uy = dy / dist;
      const hasReverse = edgeSet.has(`${first.to}->${first.from}`);
      const lvlDiff = (level.get(first.to) ?? 0) - (level.get(first.from) ?? 0);

      let curveOffset = 0;
      if (hasReverse) {
        curveOffset = 28;
      } else if (lvlDiff < 0) {
        curveOffset = -Math.min(92, 42 + Math.abs(lvlDiff) * 16);
      } else if (lvlDiff > 1 && Math.abs(dy) < 25) {
        curveOffset = 38;
      }

      const sx = p1.x + ux * R;
      const sy = p1.y + uy * R;
      const ex = p2.x - ux * (R + 3);
      const ey = p2.y - uy * (R + 3);

      const mx = (sx + ex) / 2;
      const my = (sy + ey) / 2;
      const nx = -uy;
      const ny = ux;
      const cx = mx + nx * curveOffset;
      const cy = my + ny * curveOffset;

      const d = `M ${sx.toFixed(1)} ${sy.toFixed(1)} Q ${cx.toFixed(1)} ${cy.toFixed(1)} ${ex.toFixed(1)} ${ey.toFixed(1)}`;
      const pathEl = svgEl("path", {
        d, fill: "none", stroke: strokeColor, "stroke-width": 1.6,
        "stroke-dasharray": isEps ? "5,3" : "none",
        "marker-end": markerUrl,
        opacity: edgeOpacity,
      });
      pathEl.appendChild(svgEl("title", {}, `${first.from} → ${first.to}: ${combinedLabel}`));
      edgeLayer.appendChild(pathEl);

      // Place label at t=0.44 or t=0.56 depending on source parity to stagger labels along parallel corridors
      const t = (first.from % 2 === 0) ? 0.44 : 0.56;
      const omt = 1 - t;
      const lx = omt * omt * sx + 2 * omt * t * cx + t * t * ex;
      const ly = omt * omt * sy + 2 * omt * t * cy + t * t * ey;
      drawLabelPill(lx, ly, combinedLabel, isEps, !isEdgeActive);
    }

    // Start incoming arrow
    const sp = pos.get(graph.start_state);
    if (sp) {
      edgeLayer.appendChild(svgEl("line", {
        x1: sp.x - R - 42, y1: sp.y, x2: sp.x - R - 4, y2: sp.y,
        stroke: "#059669", "stroke-width": 2.4, "marker-end": `url(#arrow-start-${pzKey})`,
      }));
      edgeLayer.appendChild(svgEl("text", {
        x: sp.x - R - 26, y: sp.y - 8, "text-anchor": "middle",
        "font-size": 11, "font-weight": 700, fill: "#059669",
      }, "start"));
    }

    // Draw state nodes
    let activeCircleEl = null;
    for (const n of nodes) {
      const p = pos.get(n.id);
      if (!p) continue;
      const isNodeActive = !activeNodeIds || activeNodeIds.has(n.id);
      const g = svgEl("g", {
        class: "state-node",
        style: "cursor:pointer",
        opacity: isNodeActive ? "1" : "0.18",
      });

      const fill = n.is_accept ? "#ecfdf5" : n.is_start ? "#eff6ff" : "#ffffff";
      const stroke = n.is_accept ? "#059669" : n.is_start ? "#2563eb" : "#334155";

      const outer = svgEl("circle", {
        cx: p.x, cy: p.y, r: R,
        fill, stroke, "stroke-width": n.is_start || n.is_accept ? 2.4 : 1.8,
      });
      g.appendChild(outer);

      if (n.is_accept) {
        g.appendChild(svgEl("circle", {
          cx: p.x, cy: p.y, r: R - 4.5,
          fill: "none", stroke: "#059669", "stroke-width": 1.6,
        }));
      }

      g.appendChild(svgEl("text", {
        x: p.x, y: p.y + 4.5,
        "text-anchor": "middle",
        "font-family": "var(--mono)",
        "font-size": nodes.length > 40 ? 11.5 : 12.5,
        "font-weight": 700,
        fill: "#0f172a",
      }, n.label));

      // Token badge underneath accept states
      if (n.is_accept && n.accept_token && n.accept_token !== "ACCEPT" && n.accept_token !== "TOKEN") {
        const tLabel = n.accept_token.length > 13 ? n.accept_token.slice(0, 12) + "…" : n.accept_token;
        const bw = Math.max(36, tLabel.length * 6.5 + 10);
        g.appendChild(svgEl("rect", {
          x: p.x - bw / 2, y: p.y + R + 5, width: bw, height: 16, rx: 4,
          fill: "#059669",
        }));
        g.appendChild(svgEl("text", {
          x: p.x, y: p.y + R + 16,
          "text-anchor": "middle",
          "font-family": "var(--mono)",
          "font-size": 9.8,
          "font-weight": 700,
          fill: "#ffffff",
        }, tLabel));
      }

      g.addEventListener("click", (ev) => {
        ev.stopPropagation();
        if (activeCircleEl) activeCircleEl.setAttribute("stroke-width", "2");
        outer.setAttribute("stroke-width", "4");
        activeCircleEl = outer;
        if (onSelectNode) onSelectNode(n, graph);
      });

      nodeLayer.appendChild(g);
    }

    const ctrl = attachPanZoom(viewportEl, svgNode, pzKey);
    ctrl.contentW = maxX;
    ctrl.contentH = maxY;
    ctrl.fit();
  }

  // ==================== ANNOTATED SYNTAX TREE RENDERER (DIRECT RE -> DFA) ====================
  function renderSyntaxTreeSVG(svgNode, viewportEl, treeRoot) {
    svgNode.innerHTML = "";
    if (!treeRoot) return;

    // Assign x via inorder leaf indexing and y via depth
    let leafCursor = 0;
    const xGap = 98;
    const yGap = 72;
    const coords = new Map();
    let maxDepth = 0;

    function layout(node, depth) {
      maxDepth = Math.max(maxDepth, depth);
      if (!node.children || node.children.length === 0) {
        const x = 75 + leafCursor * xGap;
        leafCursor += 1;
        coords.set(node.id, { x, y: 55 + depth * yGap });
        return x;
      }
      const childXs = node.children.map((c) => layout(c, depth + 1));
      const x = (childXs[0] + childXs[childXs.length - 1]) / 2;
      coords.set(node.id, { x, y: 55 + depth * yGap });
      return x;
    }
    layout(treeRoot, 0);

    const rootG = svgEl("g", { class: "pz-root" });
    svgNode.appendChild(rootG);

    const edgeG = svgEl("g");
    const nodeG = svgEl("g");
    rootG.appendChild(edgeG);
    rootG.appendChild(nodeG);

    function drawNode(node) {
      const p = coords.get(node.id);
      for (const c of node.children || []) {
        const cp = coords.get(c.id);
        edgeG.appendChild(svgEl("line", {
          x1: p.x, y1: p.y + 18, x2: cp.x, y2: cp.y - 18,
          stroke: "#94a3b8", "stroke-width": 1.8,
        }));
        drawNode(c);
      }

      const isEnd = node.kind === "END";
      const isLeaf = node.kind === "LEAF" || isEnd;
      const fill = isEnd ? "#fef3c7" : isLeaf ? "#ecfdf5" : "#eff6ff";
      const stroke = isEnd ? "#d97706" : isLeaf ? "#059669" : "#2563eb";

      nodeG.appendChild(svgEl("circle", {
        cx: p.x, cy: p.y, r: 19, fill, stroke, "stroke-width": 2,
      }));
      const lbl = node.label.length > 6 ? node.label.slice(0, 5) + "…" : node.label;
      nodeG.appendChild(svgEl("text", {
        x: p.x, y: p.y + 4.5, "text-anchor": "middle",
        "font-family": "var(--mono)", "font-size": 12.5, "font-weight": 800, fill: "#0f172a",
      }, lbl));

      // Nullable badge above (T = green, F = red, matching Slide 51!)
      nodeG.appendChild(svgEl("text", {
        x: p.x, y: p.y - 24, "text-anchor": "middle",
        "font-family": "var(--mono)", "font-size": 11.5, "font-weight": 800,
        fill: node.nullable ? "#059669" : "#dc2626",
      }, node.nullable ? "T" : "F"));

      // Firstpos on left, Lastpos on right
      const fpStr = `{${(node.firstpos || []).join(",")}}`;
      const lpStr = `{${(node.lastpos || []).join(",")}}`;
      nodeG.appendChild(svgEl("text", {
        x: p.x - 24, y: p.y + 4, "text-anchor": "end",
        "font-family": "var(--mono)", "font-size": 10.5, "font-weight": 700, fill: "#1d4ed8",
      }, fpStr));
      nodeG.appendChild(svgEl("text", {
        x: p.x + 24, y: p.y + 4, "text-anchor": "start",
        "font-family": "var(--mono)", "font-size": 10.5, "font-weight": 700, fill: "#7c3aed",
      }, lpStr));

      // Leaf position index below
      if (node.position != null) {
        nodeG.appendChild(svgEl("rect", {
          x: p.x - 11, y: p.y + 23, width: 22, height: 15, rx: 4, fill: "#0f172a",
        }));
        nodeG.appendChild(svgEl("text", {
          x: p.x, y: p.y + 34, "text-anchor": "middle",
          "font-family": "var(--mono)", "font-size": 10, "font-weight": 700, fill: "#ffffff",
        }, String(node.position)));
      }
    }
    drawNode(treeRoot);

    const ctrl = attachPanZoom(viewportEl, svgNode, "direct-tree");
    ctrl.contentW = Math.max(400, leafCursor * xGap + 120);
    ctrl.contentH = Math.max(260, (maxDepth + 1) * yGap + 95);
    ctrl.fit();
  }

  // ==================== TAB 1: SCANNER & LIVE STEP ANIMATOR ====================
  async function runScan() {
    stopAnimation();
    const code = $("#source-input").value;
    const useMin = $("#chk-use-min").checked;
    const errorRecovery = $("#sel-error-recovery")?.value || "panic_char";
    try {
      const data = await apiPost("/api/scan", {
        code,
        use_minimized: useMin,
        error_recovery: errorRecovery,
      });
      AppState.scanData = data;
      renderScanResults();
      // Select first visible token or first error trace automatically
      const traces = data.traces || [];
      let firstInteresting = traces.findIndex((t) => !t.skipped);
      if (firstInteresting < 0) firstInteresting = 0;
      selectTrace(firstInteresting);
    } catch (err) {
      showGlobalAlert(`Lỗi khi quét từ vựng: ${err.message}`, "err");
    }
  }

  function renderScanResults() {
    const data = AppState.scanData;
    if (!data) return;
    const showSkipped = $("#chk-show-skipped").checked;

    // KPIs
    $("#kpi-tokens").textContent = data.stats.visible_token_count;
    $("#kpi-errors").textContent = data.stats.error_count;
    $("#kpi-backtracks").textContent = data.stats.backtrack_events;
    $("#kpi-transitions").textContent = data.stats.total_transitions;
    $("#kpi-time").textContent = `${data.stats.elapsed_ms.toFixed(2)} ms`;

    // Errors Box
    const errBox = $("#errors-box");
    const recModeLabel = data.stats.error_recovery_mode === "smart_sync"
      ? "Smart-Sync (gom cụm chuỗi/comment lỗi)"
      : "Panic-mode cổ điển (tiến 1 ký tự)";
    if (data.errors.length > 0) {
      errBox.classList.remove("hidden");
      errBox.innerHTML =
        `<strong>⚠ Phát hiện ${data.errors.length} lỗi từ vựng (Chế độ: ${escHtml(recModeLabel)}):</strong>` +
        data.errors
          .map((e) => {
            const trIdx = data.traces.findIndex((tr) => tr.kind === "ERROR" && tr.start_pos === e.pos);
            const lexInfo = e.lexeme && e.lexeme.length > 1 ? ` [Lexeme thu hồi: "${formatLexeme(e.lexeme)}"]` : "";
            return `<div class="err-item" data-trace-idx="${trIdx}">• [Dòng ${e.line}, Cột ${e.col}] ${escHtml(e.message)}${escHtml(lexInfo)}</div>`;
          })
          .join("");
      errBox.querySelectorAll(".err-item").forEach((el) => {
        el.addEventListener("click", () => {
          const idx = Number(el.dataset.traceIdx);
          if (idx >= 0) selectTrace(idx);
        });
      });
    } else {
      errBox.classList.add("hidden");
    }

    // Live Token-Highlighted Source Preview
    const hlBox = $("#highlighted-code");
    const fragments = [];
    data.traces.forEach((tr, idx) => {
      const cat = tr.kind === "ERROR" ? "error" : (data.tokens.find((t) => t.start_pos === tr.start_pos)?.category || "other");
      const title = tr.kind === "ERROR"
        ? `LEXICAL_ERROR tại ${tr.line}:${tr.col} (${formatLexeme(tr.lexeme)})`
        : `${tr.token_type} (${tr.line}:${tr.col}) · Trạng thái D${tr.final_accept_state}` + (tr.backtrack_steps > 0 ? ` · Quay lui ${tr.backtrack_steps}` : "");
      if (cat === "whitespace") {
        fragments.push(`<span class="hl-tok hl-cat-whitespace" data-trace-idx="${idx}" title="${escHtml(title)}">${escHtml(tr.lexeme)}</span>`);
      } else {
        fragments.push(`<span class="hl-tok hl-cat-${cat}" data-trace-idx="${idx}" title="${escHtml(title)}">${escHtml(tr.lexeme)}</span>`);
      }
    });
    hlBox.innerHTML = fragments.join("") || '<span class="muted">(Mã nguồn trống)</span>';
    hlBox.querySelectorAll(".hl-tok").forEach((el) => {
      el.addEventListener("click", () => selectTrace(Number(el.dataset.traceIdx)));
    });

    // Token Table
    const tbody = $("#token-tbody");
    const rows = [];
    let displayNum = 0;
    data.traces.forEach((tr, idx) => {
      if (tr.kind === "TOKEN" && tr.skipped && !showSkipped) return;
      displayNum += 1;
      const tokObj = data.tokens.find((t) => t.start_pos === tr.start_pos);
      const cat = tr.kind === "ERROR" ? "error" : (tokObj?.category || "other");
      const btHtml = tr.backtrack_steps > 0
        ? `<span class="tok-badge badge-operator">↩ ${tr.backtrack_steps}</span>`
        : `<span class="muted">0</span>`;
      const stateHtml = tr.final_accept_state !== null ? `<code>D${tr.final_accept_state}</code>` : `<span class="tok-badge badge-error">DEAD</span>`;
      rows.push(`
        <tr data-trace-idx="${idx}">
          <td>${displayNum}</td>
          <td><span class="tok-badge ${categoryBadgeClass(cat)}">${escHtml(tr.token_type)}</span></td>
          <td><code>${escHtml(formatLexeme(tr.lexeme))}</code></td>
          <td>${tr.line}:${tr.col}</td>
          <td>${stateHtml}</td>
          <td>${btHtml}</td>
        </tr>
      `);
    });
    tbody.innerHTML = rows.join("") || '<tr><td colspan="6" class="muted" style="text-align:center">Không có token nào</td></tr>';
    tbody.querySelectorAll("tr[data-trace-idx]").forEach((row) => {
      row.addEventListener("click", () => selectTrace(Number(row.dataset.traceIdx)));
    });
  }

  function selectTrace(traceIdx) {
    stopAnimation();
    const traces = AppState.scanData?.traces || [];
    if (traces.length === 0) {
      $("#anim-tape").innerHTML = "";
      $("#anim-path-svg").innerHTML = "";
      return;
    }
    traceIdx = Math.max(0, Math.min(traces.length - 1, traceIdx));
    AppState.selectedTraceIdx = traceIdx;
    const tr = traces[traceIdx];
    // Show final step by default so user sees the complete path immediately, or can hit Play from step 0!
    AppState.animStepIdx = tr.steps.length - 1;

    // Highlight selected row & highlighted span
    $$("#token-tbody tr").forEach((r) => r.classList.toggle("row-selected", Number(r.dataset.traceIdx) === traceIdx));
    $$("#highlighted-code .hl-tok").forEach((s) => s.classList.toggle("selected", Number(s.dataset.traceIdx) === traceIdx));

    renderAnimator();
  }

  function renderAnimator() {
    const traces = AppState.scanData?.traces || [];
    const tr = traces[AppState.selectedTraceIdx];
    if (!tr) return;

    const steps = tr.steps || [];
    const curStepIdx = Math.max(0, Math.min(steps.length - 1, AppState.animStepIdx));
    const curStep = steps[curStepIdx];

    $("#anim-subtitle").innerHTML =
      `Đang mô phỏng #${tr.index + 1}: <strong>${escHtml(tr.token_type)}</strong> = <code>${escHtml(formatLexeme(tr.lexeme))}</code> ` +
      `(dòng ${tr.line}, cột ${tr.col})` +
      (tr.backtrack_steps > 0 ? ` · <strong style="color:var(--warning)">Maximal Munch quay lui ${tr.backtrack_steps} ký tự!</strong>` : "");

    $("#anim-step-badge").textContent = `Bước ${curStepIdx} / ${steps.length - 1}`;

    // Build character tape (all steps > 0 represent characters examined by DFA)
    const charSteps = steps.slice(1);
    const acceptCharLen = tr.kind === "TOKEN" ? tr.end_pos - tr.start_pos : 0;

    const tapeHtml = charSteps
      .map((st, idx) => {
        const stepPos = idx + 1;
        let cls = "tape-cell";
        if (stepPos === curStepIdx) {
          cls += " cell-active";
        } else if (stepPos < curStepIdx) {
          if (st.status === "dead") cls += " cell-dead";
          else if (idx < acceptCharLen) cls += " cell-accepted";
          else cls += " cell-backtrack";
        }
        const tag = st.status === "dead" ? "DEAD" : (idx >= acceptCharLen && tr.kind === "TOKEN" ? "↩" : `#${st.pos}`);
        return `<div class="${cls}" title="Ký tự '${escHtml(st.char_display)}' tại vị trí ${st.pos}">
          <span>${escHtml(st.char_display)}</span>
          <span class="cell-idx">${tag}</span>
        </div>`;
      })
      .join("");
    $("#anim-tape").innerHTML = tapeHtml || '<span class="muted">EOF</span>';

    // Narration
    const narr = $("#anim-narration");
    narr.className = "anim-narration";
    if (curStep.status === "start") {
      narr.innerHTML = `Khởi đầu tại trạng thái <code>D${curStep.to_state}</code> (vị trí ${curStep.pos}). Sẵn sàng đọc ký tự đầu tiên theo nguyên tắc Maximal Munch (Reps O(n)).`;
    } else if (curStep.status === "accept") {
      narr.classList.add("narr-accept");
      narr.innerHTML =
        `Đọc ký tự <code>${escHtml(curStep.char_display)}</code>: chuyển <code>D${curStep.from_state} → D${curStep.to_state}</code>. ` +
        `<strong>Đạt trạng thái kết thúc [${escHtml(curStep.accept_token)}]!</strong> Cập nhật <code>last_accept = D${curStep.to_state}</code> và tiếp tục thử đọc dài hơn.`;
    } else if (curStep.status === "move") {
      narr.innerHTML =
        `Đọc ký tự <code>${escHtml(curStep.char_display)}</code>: chuyển <code>D${curStep.from_state} → D${curStep.to_state}</code> ` +
        `(trạng thái trung gian, chưa kết thúc — tiếp tục nhìn trước).`;
    } else if (curStep.status === "dead") {
      if (tr.kind === "TOKEN") {
        narr.classList.add("narr-warn");
        narr.innerHTML =
          `Gặp ký tự <code>${escHtml(curStep.char_display)}</code> tại <code>D${curStep.from_state}</code>: <strong>không có chuyển tiếp δ (DEAD)</strong>. ` +
          (tr.backtrack_steps > 0
            ? `Áp dụng <strong>Maximal Munch</strong>: quay lui <b>${tr.backtrack_steps}</b> ký tự về <code>last_accept = D${tr.final_accept_state}</code> → xuất <strong>${escHtml(tr.token_type)}</strong>(<code>${escHtml(formatLexeme(tr.lexeme))}</code>)!`
            : `Dừng và xuất token dài nhất tại <code>D${tr.final_accept_state}</code> → <strong>${escHtml(tr.token_type)}</strong>(<code>${escHtml(formatLexeme(tr.lexeme))}</code>)!`);
      } else {
        narr.classList.add("narr-err");
        const recMode = AppState.scanData?.stats?.error_recovery_mode === "smart_sync"
          ? `phục hồi <strong>Smart-Sync</strong> (thu hồi <code>${escHtml(formatLexeme(tr.lexeme))}</code>)`
          : `phục hồi <strong>Panic-mode</strong> (bỏ qua 1 ký tự <code>${escHtml(formatLexeme(tr.lexeme))}</code>)`;
        narr.innerHTML =
          `Gặp ký tự <code>${escHtml(curStep.char_display)}</code> tại <code>D${curStep.from_state}</code>: <strong>DEAD</strong> và chưa từng đi qua trạng thái kết thúc nào! ` +
          `Báo <strong>LEXICAL_ERROR</strong> tại (${tr.line}:${tr.col}) và ${recMode}.`;
      }
    }

    // Draw linear step-by-step path SVG
    renderPathSVG(tr, curStepIdx);
  }

  function renderPathSVG(tr, curStepIdx) {
    const svg = $("#anim-path-svg");
    svg.innerHTML = "";
    const steps = tr.steps || [];
    if (steps.length === 0) return;

    const stepGap = 118;
    const totalW = Math.max(720, steps.length * stepGap + 90);
    svg.setAttribute("viewBox", `0 0 ${totalW} 175`);

    const defs = svgEl("defs");
    const mk = (id, col) => {
      const m = svgEl("marker", { id, viewBox: "0 0 10 10", refX: "9", refY: "5", markerWidth: "7", markerHeight: "7", orient: "auto" });
      m.appendChild(svgEl("path", { d: "M 0 1 L 9.5 5 L 0 9 z", fill: col }));
      return m;
    };
    defs.appendChild(mk("pa-ok", "#2563eb"));
    defs.appendChild(mk("pa-dead", "#dc2626"));
    defs.appendChild(mk("pa-dim", "#cbd5e1"));
    svg.appendChild(defs);

    const cy = 84;
    const R = 24;

    steps.forEach((st, idx) => {
      const x = 62 + idx * stepGap;
      const isReached = idx <= curStepIdx;
      const isCurrent = idx === curStepIdx;
      const isDead = st.status === "dead";

      // Edge from previous step
      if (idx > 0) {
        const prevX = 62 + (idx - 1) * stepGap;
        const col = !isReached ? "#cbd5e1" : isDead ? "#dc2626" : "#2563eb";
        const mkUrl = !isReached ? "url(#pa-dim)" : isDead ? "url(#pa-dead)" : "url(#pa-ok)";
        svg.appendChild(svgEl("line", {
          x1: prevX + R + 2, y1: cy, x2: x - R - 4, y2: cy,
          stroke: col, "stroke-width": isCurrent ? 3 : 2, "marker-end": mkUrl,
        }));

        const midX = (prevX + x) / 2;
        const lbl = st.char_display;
        const bw = Math.max(24, lbl.length * 8 + 10);
        svg.appendChild(svgEl("rect", {
          x: midX - bw / 2, y: cy - 26, width: bw, height: 19, rx: 5,
          fill: isDead ? "#fef2f2" : isCurrent ? "#dbeafe" : "#f8fafc",
          stroke: col, "stroke-width": 1.2,
        }));
        svg.appendChild(svgEl("text", {
          x: midX, y: cy - 13, "text-anchor": "middle",
          "font-family": "var(--mono)", "font-size": 11.5, "font-weight": 800,
          fill: isDead ? "#dc2626" : "#0f172a",
        }, lbl));
      }

      // Node circle
      let fill = "#ffffff", stroke = "#94a3b8", txtCol = "#0f172a";
      if (!isReached) {
        fill = "#f8fafc"; stroke = "#cbd5e1"; txtCol = "#94a3b8";
      } else if (isDead) {
        fill = "#fee2e2"; stroke = "#dc2626"; txtCol = "#dc2626";
      } else if (st.is_accept) {
        fill = isCurrent ? "#059669" : "#ecfdf5";
        stroke = "#059669";
        txtCol = isCurrent ? "#ffffff" : "#065f46";
      } else if (isCurrent) {
        fill = "#2563eb"; stroke = "#1d4ed8"; txtCol = "#ffffff";
      } else {
        fill = "#eff6ff"; stroke = "#2563eb"; txtCol = "#1e3a8a";
      }

      if (isCurrent) {
        svg.appendChild(svgEl("circle", {
          cx: x, cy, r: R + 6, fill: "none", stroke, "stroke-width": 2, opacity: 0.4,
        }));
      }

      svg.appendChild(svgEl("circle", {
        cx: x, cy, r: R, fill, stroke, "stroke-width": isCurrent ? 3 : 2,
      }));

      if (st.is_accept && !isDead) {
        svg.appendChild(svgEl("circle", {
          cx: x, cy, r: R - 4.5, fill: "none",
          stroke: isCurrent ? "#ffffff" : "#059669", "stroke-width": 1.5,
        }));
      }

      svg.appendChild(svgEl("text", {
        x, y: cy + 4.5, "text-anchor": "middle",
        "font-family": "var(--mono)", "font-size": 12.5, "font-weight": 800, fill: txtCol,
      }, isDead ? "✗" : `D${st.to_state}`));

      if (st.is_accept && st.accept_token && isReached) {
        svg.appendChild(svgEl("text", {
          x, y: cy + R + 17, "text-anchor": "middle",
          "font-family": "var(--mono)", "font-size": 10.5, "font-weight": 700, fill: "#059669",
        }, st.accept_token));
      } else if (isDead && isReached) {
        svg.appendChild(svgEl("text", {
          x, y: cy + R + 17, "text-anchor": "middle",
          "font-family": "var(--mono)", "font-size": 10.5, "font-weight": 700, fill: "#dc2626",
        }, "DEAD"));
      }
    });

    // Backtrack arc if at final step and backtrack_steps > 0
    if (tr.kind === "TOKEN" && tr.backtrack_steps > 0 && curStepIdx === steps.length - 1) {
      const deadIdx = steps.length - 1;
      const lastAcceptIdx = tr.end_pos - tr.start_pos;
      if (lastAcceptIdx >= 1 && lastAcceptIdx < deadIdx) {
        const xFrom = 62 + deadIdx * stepGap;
        const xTo = 62 + lastAcceptIdx * stepGap;
        const midX = (xFrom + xTo) / 2;
        svg.appendChild(svgEl("path", {
          d: `M ${xFrom} ${cy - R - 4} Q ${midX} 6 ${xTo} ${cy - R - 4}`,
          fill: "none", stroke: "#d97706", "stroke-width": 2.2, "stroke-dasharray": "6,3",
        }));
        svg.appendChild(svgEl("text", {
          x: midX, y: 18, "text-anchor": "middle",
          "font-size": 11.5, "font-weight": 800, fill: "#d97706",
        }, `↩ Quay lui ${tr.backtrack_steps} ký tự về D${tr.final_accept_state} (${tr.token_type})`));
      }
    }
  }

  function stopAnimation() {
    if (AppState.animTimer) {
      clearInterval(AppState.animTimer);
      AppState.animTimer = null;
    }
    const btn = $("#btn-step-play");
    if (btn) btn.textContent = "▶ Chạy";
  }

  function togglePlayAnimation() {
    if (AppState.animTimer) {
      stopAnimation();
      return;
    }
    const tr = AppState.scanData?.traces?.[AppState.selectedTraceIdx];
    if (!tr || !tr.steps.length) return;
    if (AppState.animStepIdx >= tr.steps.length - 1) {
      AppState.animStepIdx = 0;
      renderAnimator();
    }
    $("#btn-step-play").textContent = "⏸ Dừng";
    const delay = 1350 - Number($("#anim-speed").value);
    AppState.animTimer = setInterval(() => {
      const curTr = AppState.scanData?.traces?.[AppState.selectedTraceIdx];
      if (!curTr || AppState.animStepIdx >= curTr.steps.length - 1) {
        stopAnimation();
        return;
      }
      AppState.animStepIdx += 1;
      renderAnimator();
    }, delay);
  }

  // ==================== TAB 2: COMBINED AUTOMATA & MINIMIZATION ====================
  function updateTopPipelinePill() {
    const s = AppState.automataData?.summary;
    if (!s) return;
    const eqMark = s.equivalence.equivalent ? "✓ Eq" : "✗ Eq";
    const epsFree = s.eps_free_nfa_states ? ` → NFA(${s.eps_free_nfa_states})` : "";
    $("#pipeline-pill").textContent =
      `RE(${s.token_count}) → ε-NFA(${s.nfa_states})${epsFree} → DFA(${s.subset_dfa_states}) → Min(${s.minimized_dfa_states}, -${s.state_reduction_percent}%) · ${eqMark}`;
  }

  function renderAutomataTab() {
    const data = AppState.automataData;
    if (!data) return;
    const s = data.summary;

    // Equivalence & Minimality Proof Banner
    const eq = s.equivalence;
    const mhEq = s.moore_vs_hopcroft?.equivalent !== false;
    const minProof = s.minimality;
    const banner = $("#eq-proof-banner");
    banner.style.background = eq.equivalent && mhEq ? "var(--success-soft)" : "var(--danger-soft)";
    banner.style.color = eq.equivalent && mhEq ? "var(--success)" : "var(--danger)";
    banner.innerHTML = `
      <span>${eq.equivalent && mhEq ? "✅" : "❌"} <strong>Kiểm chứng Toán học:</strong> Subset DFA ≡ Moore Min-DFA ≡ Hopcroft Min-DFA (${s.minimized_dfa_states} trạng thái) · <strong>Myhill-Nerode:</strong> ${minProof ? `${minProof.distinguishable_pairs}/${minProof.total_pairs} cặp phân biệt (100% tối giản)` : escHtml(eq.message)}</span>
      <span>Biên dịch: <strong>${s.timings_ms.total_ms.toFixed(2)} ms</strong> · Lớp Σ: <strong>${s.char_class_count}</strong></span>
    `;

    // Warnings (shadowed rules or nullable tokens)
    if (s.warnings && s.warnings.length > 0) {
      showGlobalAlert(s.warnings.join(" | "), "warn");
    } else {
      showGlobalAlert("");
    }

    // Inspector Stats
    $("#auto-stats-list").innerHTML = `
      <div class="stat-chip"><div class="sc-val">${s.token_count}</div><div class="sc-lbl">Quy tắc Token</div></div>
      <div class="stat-chip"><div class="sc-val">${s.nfa_states}</div><div class="sc-lbl">Trạng thái ε-NFA</div></div>
      <div class="stat-chip"><div class="sc-val">${s.eps_free_nfa_states || "—"}</div><div class="sc-lbl">NFA Khử ε (ĐL 2)</div></div>
      <div class="stat-chip"><div class="sc-val">${s.subset_dfa_states}</div><div class="sc-lbl">Subset DFA</div></div>
      <div class="stat-chip"><div class="sc-val">${s.minimized_dfa_states}</div><div class="sc-lbl">Min-DFA (-${s.state_reduction_percent}%)</div></div>
      <div class="stat-chip"><div class="sc-val">${s.char_class_count}</div><div class="sc-lbl">Lớp tương đương Σ</div></div>
    `;

    // Priority conflicts resolved & shadowed warnings
    const confBox = $("#conflicts-list");
    const confs = s.priority_conflicts_resolved || [];
    const shad = data.shadowed_rules || [];
    let confHtml = "";
    if (shad.length > 0) {
      confHtml += shad
        .map(
          (sr) =>
            `<div class="conflict-item" style="border-left:3px solid var(--danger);background:var(--danger-soft)">⚠ <strong>LUẬT BỊ CHE KHUẤT:</strong> <code>${escHtml(sr.token_name || sr.rule_name)}</code> bị che khuất hoàn toàn bởi [${(sr.shadowed_by || []).map(escHtml).join(", ")}]</div>`
        )
        .join("");
    }
    confHtml += confs.length
      ? confs
          .map(
            (c) =>
              `<div class="conflict-item"><code>${c.state}</code>: <strong>${escHtml(c.winner)}</strong> thắng [${c.all_matched.map(escHtml).join(", ")}]</div>`
          )
          .join("")
      : '<p class="muted">Không có xung đột ưu tiên token.</p>';
    confBox.innerHTML = confHtml;

    renderActiveAutoSubView();
  }

  function renderActiveAutoSubView() {
    const data = AppState.automataData;
    if (!data) return;
    const view = AppState.currentAutoView;

    const isGraph = view === "min_dfa" || view === "subset_dfa" || view === "eps_free_nfa" || view === "combined_nfa";
    $("#auto-graph-layout").classList.toggle("hidden", !isGraph);
    $("#graph-cat-filter-bar")?.classList.toggle("hidden", !isGraph);
    $("#auto-table-view").classList.toggle("hidden", view !== "table");
    $("#auto-min-view").classList.toggle("hidden", view !== "minimization");
    ["#btn-zoom-in", "#btn-zoom-out", "#btn-zoom-fit", "#btn-export-svg"].forEach((sel) => {
      $(sel)?.classList.toggle("hidden", !isGraph);
    });

    if (isGraph) {
      const graph =
        view === "min_dfa"
          ? data.minimized_dfa
          : view === "subset_dfa"
          ? data.subset_dfa
          : view === "eps_free_nfa"
          ? data.eps_free_nfa
          : data.combined_nfa;
      renderAutomataSVG(
        $("#main-automata-svg"),
        $("#main-graph-viewport"),
        graph,
        "main",
        (node, g) => {
          const outEdges = g.edges.filter((e) => e.from === node.id);
          let html = `<div><strong>Trạng thái:</strong> <code>${node.label}</code> ${node.is_start ? '<span class="tok-badge badge-identifier">START</span>' : ""} ${node.is_accept ? `<span class="tok-badge badge-pass">ACCEPT: ${escHtml(node.accept_token)}</span>` : ""}</div>`;
          if (node.conflicts && node.conflicts.length > 1) {
            html += `<div style="margin-top:5px"><strong>Xung đột đã giải quyết:</strong> ${node.conflicts.map((x) => `<code>${escHtml(x)}</code>`).join(" &gt; ")}</div>`;
          }
          if (node.subset && node.subset.length) {
            html += `<div style="margin-top:5px"><strong>Tập con NFA:</strong> <code>{${node.subset.slice(0, 20).join(", ")}${node.subset.length > 20 ? ", …" : ""}}</code></div>`;
          }
          if (node.merged_from && node.merged_from.length) {
            html += `<div style="margin-top:5px"><strong>Gộp từ Subset DFA:</strong> <code>{${node.merged_from.map((x) => "D" + x).join(", ")}}</code></div>`;
          }
          html +=
            `<div style="margin-top:6px"><strong>Chuyển tiếp ra (${outEdges.length}):</strong><br/>` +
            (outEdges.slice(0, 12).map((e) => `<code>${escHtml(e.label)}</code> → <code>${g.kind === "NFA" ? "q" : "D"}${e.to}</code>`).join("<br/>") || '<span class="muted">Không có</span>') +
            (outEdges.length > 12 ? `<br/><span class="muted">… và ${outEdges.length - 12} cạnh khác</span>` : "") +
            `</div>`;
          $("#node-inspector").innerHTML = html;
        },
        AppState.graphCategoryFilter
      );
    } else if (view === "table") {
      renderTransitionMatrix();
    } else if (view === "minimization") {
      renderMinimizationView();
    }
  }

  function renderTransitionMatrix() {
    const data = AppState.automataData;
    if (!data) return;
    const src = document.querySelector('input[name="table-source"]:checked')?.value || "min";
    const tbl = src === "min" ? data.minimized_table : data.subset_table;
    const filter = ($("#table-search").value || "").trim().toLowerCase();

    const cols = tbl.columns || [];
    const rows = (tbl.rows || []).filter((r) => {
      if (!filter) return true;
      return (
        r.label.toLowerCase().includes(filter) ||
        (r.accept_token || "").toLowerCase().includes(filter)
      );
    });

    const thead = `<thead><tr><th>Trạng thái</th><th>Token kết thúc</th>${cols
      .map((c) => `<th title="${c.size} ký tự">${escHtml(c.label)}</th>`)
      .join("")}</tr></thead>`;

    const tbody = `<tbody>${rows
      .map((r) => {
        const prefix = (r.is_start ? "→ " : "") + (r.is_accept ? "★ " : "");
        const tokBadge = r.accept_token ? `<span class="tok-badge badge-pass">${escHtml(r.accept_token)}</span>` : `<span class="muted">—</span>`;
        const cells = cols
          .map((c) => {
            const v = r.transitions[c.id];
            return v === "—" ? `<td class="muted">—</td>` : `<td><strong>${v}</strong></td>`;
          })
          .join("");
        return `<tr><td><strong>${prefix}${r.label}</strong></td><td>${tokBadge}</td>${cells}</tr>`;
      })
      .join("")}</tbody>`;

    $("#transition-matrix").innerHTML = thead + tbody;
  }

  function renderMinimizationView() {
    const data = AppState.automataData;
    const m = data?.minimization;
    if (!m) return;
    const hop = data?.hopcroft_minimization;
    const minProof = data?.summary?.minimality;
    const mhEq = data?.summary?.moore_vs_hopcroft;

    $("#min-summary-cards").innerHTML = `
      <div class="kpi-box"><div class="kpi-val">${m.original_state_count}</div><div class="kpi-lbl">Trạng thái trước tối giản</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${m.minimized_state_count}</div><div class="kpi-lbl">Moore Min-DFA (${m.iterations} vòng)</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${hop ? hop.minimized_state_count : m.minimized_state_count}</div><div class="kpi-lbl">Hopcroft O(E·|Q|log|Q|)</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-warn">-${m.reduction_count} (-${m.reduction_percent}%)</div><div class="kpi-lbl">Giảm được</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${minProof ? `${minProof.distinguishable_pairs}/${minProof.total_pairs}` : "100%"}</div><div class="kpi-lbl">Myhill-Nerode cặp phân biệt</div></div>
    `;

    const mnBox = $("#min-myhill-nerode-box");
    if (mnBox && minProof) {
      const witnesses = (minProof.sample_witnesses || [])
        .slice(0, 6)
        .map((w) => {
          const pairLabel = Array.isArray(w.pair) ? `(${w.pair[0]}, ${w.pair[1]})` : `(D${w.state_p}, D${w.state_q})`;
          const wDisp = !w.witness ? "ε" : `"${formatLexeme(w.witness)}"`;
          return `<code>${escHtml(pairLabel)}</code> phân biệt bởi chuỗi <code>${escHtml(wDisp)}</code>`;
        })
        .join(" · ");
      mnBox.innerHTML = `
        <div><strong>✅ Định lý Myhill-Nerode & Đối chiếu Song song Moore ≡ Hopcroft:</strong> ${escHtml(minProof.message)} (${mhEq?.equivalent ? "Moore Min-DFA ≡ Hopcroft Min-DFA: 0 phản ví dụ" : "Không khớp"})</div>
        <div style="margin-top:4px;font-size:12px" class="muted"><strong>Mẫu chuỗi nhân chứng phân tách cặp trạng thái (Distinguishing Witnesses):</strong> ${witnesses}</div>
      `;
    }

    $("#min-partitions-container").innerHTML = (m.partition_history || [])
      .map((step) => {
        const groupsHtml = step.groups
          .map((g) => {
            const cls = g.token ? "p-group p-accept" : "p-group";
            const tag = g.token ? ` <strong>[${escHtml(g.token)}]</strong>` : "";
            return `<span class="${cls}">{${g.states.join(", ")}}${tag}</span>`;
          })
          .join("");
        return `
          <div class="partition-step">
            <div class="partition-step-header">
              <span>Π<sub>${step.iteration}</sub> — ${escHtml(step.note)}</span>
              <span class="step-badge">${step.group_count} nhóm</span>
            </div>
            <div class="partition-groups">${groupsHtml}</div>
          </div>
        `;
      })
      .join("");
  }

  // ==================== TAB 3: SINGLE-RE DUAL PIPELINE LAB ====================
  function renderQuickReButtons() {
    const bar = $("#quick-re-buttons");
    bar.innerHTML = AppState.singleExamples
      .map(
        (ex, idx) =>
          `<button class="pill-btn" data-re-idx="${idx}" title="${escHtml(ex.note)}">${escHtml(ex.name)}</button>`
      )
      .join("");
    bar.querySelectorAll(".pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const ex = AppState.singleExamples[Number(btn.dataset.reIdx)];
        $("#re-input").value = ex.pattern;
        $("#re-name").value = ex.name.split(":")[0].replace(/[^A-Za-z0-9_]/g, "_").slice(0, 14) || "TOKEN";
        $("#re-test-strings").value = ex.sample_inputs.join(", ");
        runSingleRegexInspect();
      });
    });
  }

  async function runSingleRegexInspect() {
    const pattern = $("#re-input").value;
    const tokenName = $("#re-name").value || "TOKEN";
    const rawTests = $("#re-test-strings").value;
    const testStrings = rawTests.trim() === "" ? [] : rawTests.split(",").map((s) => s.trim());

    const errBox = $("#re-error-box");
    errBox.classList.add("hidden");

    try {
      const info = await apiPost("/api/inspect-regex", {
        pattern,
        token_name: tokenName,
        test_strings: testStrings,
      });
      AppState.singleReData = info;
      renderSingleReOverview();
      renderSingleReStage();
    } catch (err) {
      errBox.className = "alert-inline alert-err";
      errBox.textContent = err.message;
      errBox.classList.remove("hidden");
    }
  }

  function renderSingleReOverview() {
    const info = AppState.singleReData;
    if (!info) return;
    const eq1 = info.equivalence.subset_vs_minimized.equivalent;
    const eq2 = info.equivalence.subset_vs_direct.equivalent;
    const eq3 = info.equivalence.moore_vs_hopcroft?.equivalent !== false;
    const epsFreeCount = info.eps_free_nfa ? info.eps_free_nfa.state_count : info.nfa.state_count;

    $("#re-summary-strip").innerHTML = `
      <div class="kpi-box"><div class="kpi-val" style="font-size:13px">${escHtml(info.postfix)}</div><div class="kpi-lbl">Hậu tố (Postfix)</div></div>
      <div class="kpi-box"><div class="kpi-val">${info.nfa.state_count}</div><div class="kpi-lbl">Thompson ε-NFA</div></div>
      <div class="kpi-box"><div class="kpi-val">${epsFreeCount}</div><div class="kpi-lbl">NFA Khử ε (ĐL 2)</div></div>
      <div class="kpi-box"><div class="kpi-val">${info.subset_dfa.state_count}</div><div class="kpi-lbl">Subset DFA</div></div>
      <div class="kpi-box"><div class="kpi-val">${info.direct_dfa.dfa.state_count}</div><div class="kpi-lbl">Direct DFA (r#)</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${info.minimized_dfa.state_count}</div><div class="kpi-lbl">Min-DFA (Moore/Hopcroft)</div></div>
      <div class="kpi-box"><div class="kpi-val ${eq1 && eq2 && eq3 ? "kpi-ok" : "kpi-err"}">${eq1 && eq2 && eq3 ? "✓ 100%" : "✗"}</div><div class="kpi-lbl">Tương đương & Tối giản</div></div>
    `;

    $("#re-string-tests").innerHTML = (info.string_tests || [])
      .map((st) => {
        const disp = st.input === "" ? "ε (rỗng)" : `"${st.input}"`;
        const ok = st.min_dfa_accepted;
        return `<span class="str-pill ${ok ? "acc" : "rej"}" title="NFA=${st.nfa_accepted}, MinDFA=${st.min_dfa_accepted}, DirectDFA=${st.direct_dfa_accepted}">
          <span>${escHtml(disp)}</span> → <strong>${ok ? "ACCEPT" : "REJECT"}</strong> ${st.consistent ? "✓" : "⚠"}
        </span>`;
      })
      .join("");
  }

  function renderSingleReStage() {
    const info = AppState.singleReData;
    if (!info) return;
    const v = AppState.singleReView;

    $("#re-stage-graph").classList.toggle("hidden", v === "direct");
    $("#re-stage-direct").classList.toggle("hidden", v !== "direct");

    if (v === "direct") {
      renderSyntaxTreeSVG($("#direct-tree-svg"), $("#direct-tree-svg").parentElement, info.direct_dfa.syntax_tree);
      $("#followpos-tbody").innerHTML = (info.direct_dfa.followpos_table || [])
        .map(
          (row) =>
            `<tr><td><strong>${row.position}</strong></td><td><code>${escHtml(row.symbol)}</code>${row.is_end_marker ? " (kết thúc)" : ""}</td><td><code>{${row.followpos.join(", ")}}</code></td></tr>`
        )
        .join("");
      renderAutomataSVG($("#direct-dfa-svg"), $("#direct-dfa-viewport"), info.direct_dfa.dfa, "direct-dfa");
      return;
    }

    const extra = $("#re-extra-panel");
    if (v === "nfa") {
      $("#re-stage-caption").textContent = `Thompson ε-NFA (Định lý 1): ${info.nfa.state_count} trạng thái, ${info.nfa.edge_count} cung (${info.nfa.epsilon_edge_count} ε-chuyển tiếp)`;
      renderAutomataSVG($("#re-automata-svg"), $("#re-graph-viewport"), info.nfa, "single-re");
      extra.innerHTML = `<div class="muted">Biểu thức trung tố tường minh: <code>${escHtml(info.explicit_infix)}</code> · Hậu tố: <code>${escHtml(info.postfix)}</code></div>`;
    } else if (v === "eps_free") {
      const ef = info.eps_free_nfa || info.nfa;
      $("#re-stage-caption").textContent = `NFA Không ε (Định lý 2 Slide 21-22): ${ef.state_count} trạng thái, ${ef.edge_count} cung (0 ε-chuyển tiếp)`;
      renderAutomataSVG($("#re-automata-svg"), $("#re-graph-viewport"), ef, "single-re");
      extra.innerHTML = `<div class="muted">Khử toàn bộ ε-chuyển tiếp bằng bao đóng ε-closure(q) và tích hợp trạng thái kết thúc theo đúng Định lý 2 (Chương 3.1).</div>`;
    } else if (v === "subset") {
      $("#re-stage-caption").textContent = `Subset Construction DFA (Định lý 3): ${info.subset_dfa.state_count} trạng thái từ ε-closure & Move`;
      renderAutomataSVG($("#re-automata-svg"), $("#re-graph-viewport"), info.subset_dfa, "single-re");
      extra.innerHTML = `
        <h4 style="margin-bottom:6px;font-size:13px">Nhật ký xây dựng tập con (Subset Construction Steps):</h4>
        <div class="table-scroll" style="max-height:190px">
          <table class="data-table">
            <thead><tr><th>#</th><th>Bước tính toán ε-closure / Move</th></tr></thead>
            <tbody>${(info.subset_steps || [])
              .map((s, i) => `<tr><td>${i + 1}</td><td><code>${escHtml(s.description)}</code></td></tr>`)
              .join("")}</tbody>
          </table>
        </div>
      `;
    } else if (v === "min") {
      const mp = info.minimality;
      $("#re-stage-caption").textContent = `Minimized DFA (Định lý 4 — Moore & Hopcroft): ${info.minimized_dfa.state_count} trạng thái (giảm từ ${info.subset_dfa.state_count} trạng thái)`;
      renderAutomataSVG($("#re-automata-svg"), $("#re-graph-viewport"), info.minimized_dfa, "single-re");
      const witnessHtml = mp && mp.sample_witnesses && mp.sample_witnesses.length
        ? `<div style="margin-top:6px;font-size:12px" class="muted"><strong>Chứng minh tối giản Myhill-Nerode (${mp.distinguishable_pairs}/${mp.total_pairs} cặp phân biệt):</strong> ` +
          mp.sample_witnesses
            .map((w) => {
              const pLbl = Array.isArray(w.pair) ? `(${w.pair[0]}, ${w.pair[1]})` : `(D${w.state_p}, D${w.state_q})`;
              return `<code>${escHtml(pLbl)}</code> bởi <code>"${escHtml(w.witness || "ε")}"</code>`;
            })
            .join(" · ") +
          `</div>`
        : "";
      extra.innerHTML = `
        <div class="proof-banner" style="margin-bottom:8px">
          <span>✅ Subset ≡ Moore Min ≡ Hopcroft Min: ${escHtml(info.equivalence.subset_vs_minimized.message)}</span>
          <span>✅ Subset ≡ Direct (r#): ${escHtml(info.equivalence.subset_vs_direct.message)}</span>
        </div>
        <div class="partitions-list">${(info.minimization.partition_history || [])
          .map(
            (st) =>
              `<div class="partition-step"><strong>Π<sub>${st.iteration}</sub>:</strong> ${st.groups
                .map((g) => `<span class="p-group ${g.token ? "p-accept" : ""}">{${g.states.join(",")}}</span>`)
                .join(" ")}</div>`
          )
          .join("")}</div>
        ${witnessHtml}
      `;
    }
  }

  async function runRegexCompare() {
    const patA = $("#cmp-re-a").value.trim();
    const patB = $("#cmp-re-b").value.trim();
    const box = $("#cmp-re-result");
    if (!patA || !patB) return;
    try {
      const res = await apiPost("/api/compare-regex", { pattern_a: patA, pattern_b: patB });
      box.classList.remove("hidden");
      if (res.equivalent) {
        box.className = "alert-inline alert-ok";
        box.innerHTML = `✅ <strong>TƯƠNG ĐƯƠNG TOÁN HỌC:</strong> <code>L(${escHtml(patA)}) ≡ L(${escHtml(patB)})</code> (Product DFA đã duyệt ${res.visited_pairs ?? res.checked_pairs} cặp trạng thái; Min-DFA: ${res.min_dfa_a_states ?? res.pattern_a_min_states} vs ${res.min_dfa_b_states ?? res.pattern_b_min_states} trạng thái, 0 phản ví dụ).`;
      } else {
        box.className = "alert-inline alert-err";
        const ce = res.counterexample === "" ? "ε (chuỗi rỗng)" : `"${res.counterexample}"`;
        box.innerHTML = `❌ <strong>KHÔNG TƯƠNG ĐƯƠNG:</strong> <code>L(${escHtml(patA)}) ≠ L(${escHtml(patB)})</code> — Phản ví dụ ngắn nhất (BFS): <code>w = ${escHtml(ce)}</code> (${escHtml(res.message)}).`;
      }
    } catch (err) {
      box.classList.remove("hidden");
      box.className = "alert-inline alert-err";
      box.textContent = `Lỗi kiểm tra tương đương: ${err.message}`;
    }
  }

  // ==================== TAB 4: LIVE TOKEN SPEC EDITOR ====================
  function renderSpecEditor() {
    const tbody = $("#spec-editor-tbody");
    const cats = ["keyword", "identifier", "literal", "operator", "delimiter", "comment", "whitespace", "other"];
    const shadowedMap = new Map();
    (AppState.automataData?.shadowed_rules || []).forEach((sr) => {
      shadowedMap.set(sr.token_name || sr.rule_name, sr);
    });

    // Update shadowed warning box in Tab 4
    const shBox = $("#shadowed-warning-box");
    if (shBox) {
      if (shadowedMap.size > 0) {
        shBox.classList.remove("hidden");
        shBox.innerHTML =
          `<strong>⚠ CẢNH BÁO PHÁT HIỆN ${shadowedMap.size} QUY TẮC BỊ CHE KHUẤT (SHADOWED / DEAD RULES):</strong><br/>` +
          Array.from(shadowedMap.values())
            .map((sr) => `• ${escHtml(sr.message)}`)
            .join("<br/>");
      } else {
        shBox.classList.add("hidden");
      }
    }

    tbody.innerHTML = AppState.editorSpecs
      .map((sp, idx) => {
        const isShadowed = shadowedMap.has(sp.name);
        const shInfo = shadowedMap.get(sp.name);
        return `
      <tr data-idx="${idx}" class="${isShadowed ? "row-shadowed" : ""}" title="${isShadowed ? escHtml(shInfo.message) : ""}">
        <td><input type="number" class="ed-prio" value="${sp.priority}" min="1" /></td>
        <td><input type="text" class="ed-name mono-cell" value="${escHtml(sp.name)}" /></td>
        <td><input type="text" class="ed-pat mono-cell" value="${escHtml(sp.pattern)}" /></td>
        <td>
          <select class="ed-cat">
            ${cats.map((c) => `<option value="${c}" ${sp.category === c ? "selected" : ""}>${c}</option>`).join("")}
          </select>
        </td>
        <td style="text-align:center"><input type="checkbox" class="ed-skip" ${sp.skip ? "checked" : ""} /></td>
        <td><input type="text" class="ed-desc" value="${escHtml(sp.description || "")}" /></td>
        <td>
          <button class="btn btn-outline btn-sm ed-up" title="Tăng ưu tiên">↑</button>
          <button class="btn btn-outline btn-sm ed-down" title="Giảm ưu tiên">↓</button>
          <button class="btn-danger-sm ed-del" title="Xóa">✕</button>
        </td>
      </tr>
    `;
      })
      .join("");

    tbody.querySelectorAll("tr").forEach((tr) => {
      const idx = Number(tr.dataset.idx);
      tr.querySelector(".ed-up").addEventListener("click", () => {
        syncEditorFromDOM();
        if (idx > 0) {
          [AppState.editorSpecs[idx - 1], AppState.editorSpecs[idx]] = [AppState.editorSpecs[idx], AppState.editorSpecs[idx - 1]];
          renumberPriorities();
          renderSpecEditor();
        }
      });
      tr.querySelector(".ed-down").addEventListener("click", () => {
        syncEditorFromDOM();
        if (idx < AppState.editorSpecs.length - 1) {
          [AppState.editorSpecs[idx + 1], AppState.editorSpecs[idx]] = [AppState.editorSpecs[idx], AppState.editorSpecs[idx + 1]];
          renumberPriorities();
          renderSpecEditor();
        }
      });
      tr.querySelector(".ed-del").addEventListener("click", () => {
        syncEditorFromDOM();
        AppState.editorSpecs.splice(idx, 1);
        renumberPriorities();
        renderSpecEditor();
      });
    });
  }

  function syncEditorFromDOM() {
    const rows = $$("#spec-editor-tbody tr");
    AppState.editorSpecs = rows.map((tr, i) => ({
      priority: Number(tr.querySelector(".ed-prio").value) || i + 1,
      name: tr.querySelector(".ed-name").value.trim(),
      pattern: tr.querySelector(".ed-pat").value,
      category: tr.querySelector(".ed-cat").value,
      skip: tr.querySelector(".ed-skip").checked,
      description: tr.querySelector(".ed-desc").value,
    }));
  }

  function renumberPriorities() {
    AppState.editorSpecs.forEach((s, i) => { s.priority = i + 1; });
  }

  async function recompileCustomSpecs() {
    syncEditorFromDOM();
    const fb = $("#editor-feedback");
    fb.classList.add("hidden");
    try {
      const compiled = await apiPost("/api/compile", { specs: AppState.editorSpecs });
      AppState.automataData = compiled;
      AppState.activePreset = "custom";
      AppState.editorSpecs = compiled.specs.map((s) => ({ ...s }));
      renderSpecEditor();
      updateTopPipelinePill();
      renderAutomataTab();
      await runScan();

      const s = compiled.summary;
      const shCount = (compiled.shadowed_rules || []).length;
      fb.className = shCount > 0 ? "alert-inline alert-warn" : "alert-inline alert-ok";
      fb.textContent =
        `✅ Biên dịch thành công ${s.token_count} quy tắc token trong ${s.timings_ms.total_ms.toFixed(2)} ms! ` +
        `ε-NFA (${s.nfa_states}) → NFA Khử ε (${s.eps_free_nfa_states}) → Subset DFA (${s.subset_dfa_states}) → Minimized DFA (${s.minimized_dfa_states}, -${s.state_reduction_percent}%).` +
        (shCount > 0 ? ` ⚠ Phát hiện ${shCount} quy tắc bị che khuất!` : "");
      fb.classList.remove("hidden");
    } catch (err) {
      fb.className = "alert-inline alert-err";
      fb.textContent = `❌ Lỗi biên dịch: ${err.message}`;
      fb.classList.remove("hidden");
    }
  }

  // ==================== TAB 5: TEST SUITE & BENCHMARK ====================
  async function runTestSuiteUI() {
    try {
      const report = await apiGet("/api/tests");
      AppState.testReport = report;
      renderTestReport();
    } catch (err) {
      showGlobalAlert(`Lỗi chạy bộ test: ${err.message}`, "err");
    }
  }

  function renderTestReport() {
    const r = AppState.testReport;
    if (!r) return;
    $("#test-kpis").innerHTML = `
      <div class="kpi-box"><div class="kpi-val">${r.total}</div><div class="kpi-lbl">Tổng Test Cases</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${r.passed}</div><div class="kpi-lbl">Đạt (PASSED)</div></div>
      <div class="kpi-box"><div class="kpi-val ${r.failed ? "kpi-err" : "kpi-ok"}">${r.failed}</div><div class="kpi-lbl">Thất bại (FAILED)</div></div>
      <div class="kpi-box"><div class="kpi-val kpi-ok">${r.pass_rate}%</div><div class="kpi-lbl">Tỷ lệ chính xác</div></div>
    `;

    const filtered = r.results.filter((item) => AppState.testFilter === "all" || item.category === AppState.testFilter);
    $("#tests-tbody").innerHTML = filtered
      .map(
        (it) => `
      <tr>
        <td><code>${escHtml(it.id)}</code></td>
        <td>${escHtml(it.group)}</td>
        <td><span class="tok-badge ${it.category === "valid" ? "badge-literal" : it.category === "edge" ? "badge-operator" : "badge-error"}">${escHtml(it.category)}</span></td>
        <td><strong>${escHtml(it.name)}</strong></td>
        <td><code>${escHtml(formatLexeme(it.input).slice(0, 38))}</code></td>
        <td><span class="tok-badge ${it.passed ? "badge-pass" : "badge-fail"}">${it.passed ? "✓ PASS" : "✗ FAIL"}</span></td>
        <td class="muted">${escHtml(it.detail)}</td>
      </tr>
    `
      )
      .join("");
  }

  async function runBenchmarkUI() {
    try {
      const data = await apiGet("/api/benchmark");
      $("#bench-tbody").innerHTML = (data.benchmarks || [])
        .map(
          (b) => `
        <tr>
          <td><strong>${escHtml(b.preset.toUpperCase())}</strong></td>
          <td>${b.tokens}</td>
          <td>${b.nfa_states}</td>
          <td>${b.eps_free_nfa_states}</td>
          <td>${b.subset_dfa_states}</td>
          <td>${b.combined_direct_dfa_states}</td>
          <td><strong>${b.minimized_dfa_states} / ${b.hopcroft_dfa_states}</strong> <span class="tok-badge badge-pass">-${b.reduction_percent}%</span></td>
          <td>${b.moore_ms.toFixed(2)} / ${b.hopcroft_ms.toFixed(2)} ms</td>
          <td>${b.scan_10kb_ms.toFixed(2)} ms (${b.scan_10kb_tokens} tok)</td>
          <td><span class="tok-badge ${b.equivalent && b.is_minimal ? "badge-pass" : "badge-fail"}">${b.equivalent && b.is_minimal ? `✓ 6-Chiều (${b.minimality_pairs})` : "✗"}</span></td>
        </tr>
      `
        )
        .join("");

      const stressTbody = $("#stress-tbody");
      if (stressTbody && data.stress_tests) {
        stressTbody.innerHTML = data.stress_tests
          .map((st) => {
            const pMs = Number(st.panic_ms ?? st.panic_char_ms ?? 0);
            const sMs = Number(st.smart_ms ?? st.smart_sync_ms ?? 0);
            const ok = Boolean(st.passed ?? st.linear_verified);
            return `
          <tr>
            <td><strong>${escHtml(st.name)}</strong></td>
            <td><code>${st.length.toLocaleString()} ký tự</code></td>
            <td><strong>${pMs.toFixed(2)} ms</strong> (${st.panic_errors} lỗi)</td>
            <td><strong>${sMs.toFixed(2)} ms</strong> (${st.smart_errors} lỗi)</td>
            <td><code>${st.memoized_cutoffs.toLocaleString()} lần cắt tỉa</code></td>
            <td><span class="tok-badge ${ok ? "badge-pass" : "badge-fail"}">${ok ? "✓ O(n) Tuyến tính" : "✗"}</span></td>
          </tr>
        `;
          })
          .join("");
      }
    } catch (err) {
      showGlobalAlert(`Lỗi benchmark: ${err.message}`, "err");
    }
  }

  // ==================== PRESET SWITCHING & INITIALIZATION ====================
  async function loadPreset(presetId) {
    try {
      const data = await apiPost("/api/compile", { preset_id: presetId });
      AppState.activePreset = presetId;
      AppState.lastPresetId = presetId;
      AppState.automataData = data;
      AppState.editorSpecs = data.specs.map((s) => ({ ...s }));
      $("#preset-select").value = presetId;

      // Load default valid sample into editor
      const p = AppState.presets[presetId];
      if (p?.samples?.valid) {
        $("#source-input").value = p.samples.valid.code;
        $$(".sample-pills .pill-btn").forEach((b) => b.classList.toggle("active", b.dataset.sample === "valid"));
      }

      updateTopPipelinePill();
      renderSpecEditor();
      renderAutomataTab();
      await runScan();
    } catch (err) {
      showGlobalAlert(`Không thể nạp preset '${presetId}': ${err.message}`, "err");
    }
  }

  function bindEvents() {
    // Theme toggle
    $("#btn-theme").addEventListener("click", () => {
      const isDark = document.documentElement.dataset.theme === "dark";
      document.documentElement.dataset.theme = isDark ? "" : "dark";
      $("#btn-theme").textContent = isDark ? "🌙" : "☀️";
    });

    // Main Tabs
    $$(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const target = btn.dataset.tab;
        $$(".tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
        $$(".tab-panel").forEach((p) => p.classList.toggle("active", p.id === `tab-${target}`));

        // Refit visible SVG on tab activation
        if (target === "automata") {
          setTimeout(() => renderActiveAutoSubView(), 30);
        } else if (target === "single-re") {
          if (!AppState.singleReData) runSingleRegexInspect();
          else setTimeout(() => renderSingleReStage(), 30);
        } else if (target === "tests") {
          if (!AppState.testReport) runTestSuiteUI();
          runBenchmarkUI();
        }
      });
    });

    // Preset selector
    $("#preset-select").addEventListener("change", (e) => loadPreset(e.target.value));

    // Topbar JFLAP export
    $("#btn-export-jff-top").addEventListener("click", () => {
      window.location.href = "/api/export-jflap?stage=min_dfa";
    });

    // Tab 1 controls
    $$(".sample-pills .pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const p = AppState.presets[AppState.activePreset] || AppState.presets[AppState.lastPresetId] || AppState.presets.minilang;
        const sampleKey = btn.dataset.sample;
        if (p?.samples?.[sampleKey]) {
          $("#source-input").value = p.samples[sampleKey].code;
          $$(".sample-pills .pill-btn").forEach((b) => b.classList.toggle("active", b === btn));
          runScan();
        }
      });
    });

    $("#btn-scan").addEventListener("click", runScan);
    $("#chk-use-min").addEventListener("change", runScan);
    $("#sel-error-recovery")?.addEventListener("change", runScan);
    $("#chk-show-skipped").addEventListener("change", renderScanResults);
    $("#btn-export-tokens").addEventListener("click", () => {
      if (!AppState.scanData) return;
      downloadBlob(JSON.stringify(AppState.scanData, null, 2), `tokens_${AppState.activePreset}.json`, "application/json");
    });

    // Animator controls
    $("#btn-tok-prev").addEventListener("click", () => {
      const traces = AppState.scanData?.traces || [];
      let i = AppState.selectedTraceIdx - 1;
      while (i > 0 && traces[i].skipped && !$("#chk-show-skipped").checked) i--;
      if (i >= 0) selectTrace(i);
    });
    $("#btn-tok-next").addEventListener("click", () => {
      const traces = AppState.scanData?.traces || [];
      let i = AppState.selectedTraceIdx + 1;
      while (i < traces.length - 1 && traces[i].skipped && !$("#chk-show-skipped").checked) i++;
      if (i < traces.length) selectTrace(i);
    });
    $("#btn-step-first").addEventListener("click", () => { stopAnimation(); AppState.animStepIdx = 0; renderAnimator(); });
    $("#btn-step-prev").addEventListener("click", () => { stopAnimation(); AppState.animStepIdx = Math.max(0, AppState.animStepIdx - 1); renderAnimator(); });
    $("#btn-step-next").addEventListener("click", () => {
      stopAnimation();
      const max = (AppState.scanData?.traces?.[AppState.selectedTraceIdx]?.steps?.length || 1) - 1;
      AppState.animStepIdx = Math.min(max, AppState.animStepIdx + 1);
      renderAnimator();
    });
    $("#btn-step-last").addEventListener("click", () => {
      stopAnimation();
      const max = (AppState.scanData?.traces?.[AppState.selectedTraceIdx]?.steps?.length || 1) - 1;
      AppState.animStepIdx = max;
      renderAnimator();
    });
    $("#btn-step-play").addEventListener("click", togglePlayAnimation);

    // Global keyboard shortcuts for Tab 1
    document.addEventListener("keydown", (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        runScan();
        return;
      }
      const tag = (e.target?.tagName || "").toUpperCase();
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
      const isScannerTab = $("#tab-scanner")?.classList.contains("active");
      if (!isScannerTab) return;
      if (e.key === " ") {
        e.preventDefault();
        togglePlayAnimation();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        stopAnimation();
        AppState.animStepIdx = Math.max(0, AppState.animStepIdx - 1);
        renderAnimator();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        stopAnimation();
        const max = (AppState.scanData?.traces?.[AppState.selectedTraceIdx]?.steps?.length || 1) - 1;
        AppState.animStepIdx = Math.min(max, AppState.animStepIdx + 1);
        renderAnimator();
      }
    });

    // Tab 2 Automata subtabs, category filter & zoom
    $$("#auto-subtabs .subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#auto-subtabs .subtab-btn").forEach((b) => b.classList.toggle("active", b === btn));
        AppState.currentAutoView = btn.dataset.view;
        renderActiveAutoSubView();
      });
    });
    $$("#graph-cat-filter-bar .pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#graph-cat-filter-bar .pill-btn").forEach((b) => b.classList.toggle("active", b === btn));
        AppState.graphCategoryFilter = btn.dataset.gcat || "all";
        renderActiveAutoSubView();
      });
    });
    $("#btn-zoom-in").addEventListener("click", () => AppState.panZoomControllers.main?.zoomBy(1.25));
    $("#btn-zoom-out").addEventListener("click", () => AppState.panZoomControllers.main?.zoomBy(0.8));
    $("#btn-zoom-fit").addEventListener("click", () => AppState.panZoomControllers.main?.fit());
    $("#btn-export-svg").addEventListener("click", () => {
      const svgText = new XMLSerializer().serializeToString($("#main-automata-svg"));
      downloadBlob(svgText, `${AppState.activePreset}_${AppState.currentAutoView}.svg`, "image/svg+xml");
    });
    $("#btn-export-jff-view").addEventListener("click", () => {
      const stage =
        AppState.currentAutoView === "combined_nfa"
          ? "nfa"
          : AppState.currentAutoView === "eps_free_nfa"
          ? "eps_free_nfa"
          : AppState.currentAutoView === "subset_dfa"
          ? "subset_dfa"
          : "min_dfa";
      window.location.href = `/api/export-jflap?stage=${stage}`;
    });
    $("#table-search").addEventListener("input", renderTransitionMatrix);
    $$('input[name="table-source"]').forEach((r) => r.addEventListener("change", renderTransitionMatrix));

    // Tab 3 Single-RE Lab & Equivalence Checker
    $("#btn-inspect-re").addEventListener("click", runSingleRegexInspect);
    $("#re-input").addEventListener("keydown", (e) => { if (e.key === "Enter") runSingleRegexInspect(); });
    $$("#re-subtabs .subtab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#re-subtabs .subtab-btn").forEach((b) => b.classList.toggle("active", b === btn));
        AppState.singleReView = btn.dataset.review;
        renderSingleReStage();
      });
    });
    $("#btn-re-jff").addEventListener("click", () => {
      const pat = encodeURIComponent($("#re-input").value);
      const stage =
        AppState.singleReView === "nfa"
          ? "nfa"
          : AppState.singleReView === "eps_free"
          ? "eps_free_nfa"
          : AppState.singleReView === "subset"
          ? "subset_dfa"
          : "min_dfa";
      window.location.href = `/api/export-jflap?pattern=${pat}&stage=${stage}&expand=true`;
    });
    $("#btn-compare-re")?.addEventListener("click", runRegexCompare);
    $$("[data-cmp-a]").forEach((btn) => {
      btn.addEventListener("click", () => {
        $("#cmp-re-a").value = btn.dataset.cmpA;
        $("#cmp-re-b").value = btn.dataset.cmpB;
        runRegexCompare();
      });
    });

    // Tab 4 Spec Editor
    $("#btn-add-rule").addEventListener("click", () => {
      syncEditorFromDOM();
      AppState.editorSpecs.push({
        priority: AppState.editorSpecs.length + 1,
        name: `NEW_TOKEN_${AppState.editorSpecs.length + 1}`,
        pattern: "abc",
        category: "other",
        skip: false,
        description: "Quy tắc mới",
      });
      renderSpecEditor();
    });
    $("#btn-add-hex-demo").addEventListener("click", () => {
      syncEditorFromDOM();
      if (!AppState.editorSpecs.some((s) => s.name === "HEX_LIT")) {
        const intIdx = AppState.editorSpecs.findIndex((s) => s.name.includes("INT") || s.name.includes("FLOAT"));
        const insertAt = intIdx >= 0 ? intIdx : 2;
        AppState.editorSpecs.splice(insertAt, 0, {
          priority: insertAt + 1,
          name: "HEX_LIT",
          pattern: "0[xX][0-9a-fA-F]+",
          category: "literal",
          skip: false,
          description: "Hằng số thập lục phân (0xFF)",
        });
        renumberPriorities();
        renderSpecEditor();
      }
    });
    $("#btn-demo-shadow")?.addEventListener("click", async () => {
      syncEditorFromDOM();
      const idIdx = AppState.editorSpecs.findIndex((s) => s.name === "IDENTIFIER");
      const kwIdx = AppState.editorSpecs.findIndex((s) => s.name.startsWith("KW_"));
      if (idIdx >= 0 && kwIdx >= 0 && idIdx > kwIdx) {
        const [idSpec] = AppState.editorSpecs.splice(idIdx, 1);
        AppState.editorSpecs.splice(kwIdx, 0, idSpec);
        renumberPriorities();
        renderSpecEditor();
        await recompileCustomSpecs();
      }
    });
    $("#btn-reset-preset")?.addEventListener("click", async () => {
      await loadPreset(AppState.lastPresetId || "minilang");
    });
    $("#btn-recompile").addEventListener("click", recompileCustomSpecs);
    $("#btn-export-spec").addEventListener("click", () => {
      syncEditorFromDOM();
      downloadBlob(JSON.stringify({ tokens: AppState.editorSpecs }, null, 2), `spec_${AppState.activePreset}.json`, "application/json");
    });

    // Tab 5 Tests & Benchmark
    $("#btn-run-tests").addEventListener("click", runTestSuiteUI);
    $("#btn-run-bench").addEventListener("click", runBenchmarkUI);
    $$("#test-filter-bar .pill-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        $$("#test-filter-bar .pill-btn").forEach((b) => b.classList.toggle("active", b === btn));
        AppState.testFilter = btn.dataset.tfilter;
        renderTestReport();
      });
    });
  }

  async function init() {
    bindEvents();
    try {
      const meta = await apiGet("/api/presets");
      AppState.presets = meta.presets;
      AppState.singleExamples = meta.single_regex_examples || [];
      renderQuickReButtons();
      const qs = new URLSearchParams(window.location.search);
      const initPreset = qs.get("preset") || "minilang";
      await loadPreset(initPreset);
      const initSample = qs.get("sample");
      if (initSample && AppState.presets[initPreset]?.samples?.[initSample]) {
        $("#source-input").value = AppState.presets[initPreset].samples[initSample].code;
        $$(".sample-pills .pill-btn").forEach((b) => b.classList.toggle("active", b.dataset.sample === initSample));
        await runScan();
      }
      const focusLex = qs.get("focus");
      if (focusLex && AppState.scanData?.traces) {
        const idx = AppState.scanData.traces.findIndex((t) => t.lexeme === focusLex);
        if (idx >= 0) selectTrace(idx);
      }
      const initTab = qs.get("tab");
      if (initTab) {
        const btn = document.querySelector(`.tab-btn[data-tab="${initTab}"]`);
        if (btn) btn.click();
      }
      const initReview = qs.get("review");
      if (initTab === "single-re" && initReview) {
        AppState.singleReView = initReview;
        $$("#re-subtabs .subtab-btn").forEach((b) => b.classList.toggle("active", b.dataset.review === initReview));
        await runSingleRegexInspect();
      }
    } catch (err) {
      showGlobalAlert(`Không kết nối được máy chủ Python backend: ${err.message}`, "err");
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
