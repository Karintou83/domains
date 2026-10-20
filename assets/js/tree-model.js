/* 家系図のデータモデル(DOM にも Cytoscape にも依存しない純粋関数)。
   分けた理由: 「どのノード・辺をどこに置くか」は表示ライブラリと無関係なので、Node.js 単体でテストできるようにするため。 */
(function (root) {
  function push(map, key, value) {
    if (!map.has(key)) map.set(key, []);
    map.get(key).push(value);
  }

  // 藩ごとの色。黄金角(約137.5°)ずつ色相をずらすと、藩の数が増えても隣り合う色が似にくい。
  // 彩度・明度を固定して「くすんだ淡色」にそろえる(派手にならず、文字が読める)。
  function domainColors(domains) {
    const sorted = domains.slice().sort((a, b) => a.name.localeCompare(b.name, "ja"));
    const out = new Map();
    sorted.forEach((d, i) => {
      const h = Math.round((i * 137.508) % 360);
      out.set(d.id, { fill: "hsl(" + h + ",34%,93%)", border: "hsl(" + h + ",28%,48%)", head: "hsl(" + h + ",30%,32%)" });
    });
    return out;
  }
  // 藩主でない人物(藩主の実父・祖先)の色。どの藩の色とも紛れない灰色にする。
  const NON_RULER_COLOR = { fill: "#efede8", border: "#9a968c", head: "#6a665c" };

  function build(data) {
    const lords = new Map(data.lords.map((l) => [l.id, l]));
    const domains = new Map(data.domains.map((d) => [d.id, d]));
    const colors = domainColors(data.domains);
    const tenuresByLord = new Map();
    const tenuresByDomain = new Map();
    data.tenures.forEach((t) => { push(tenuresByLord, t.lord, t); push(tenuresByDomain, t.domain, t); });

    // 辺: 親 → 子 の向きで保持する(実親子も養子も source=親, target=子)。
    const parents = new Map();   // 子 → [{id: 親, edge}]
    const children = new Map();  // 親 → [{id: 子, edge}]
    data.relations.forEach((e) => {
      if (!lords.has(e.source) || !lords.has(e.target)) return;
      push(children, e.source, { id: e.target, edge: e });
      push(parents, e.target, { id: e.source, edge: e });
    });

    const warningsBySubject = new Map();
    data.warnings.forEach((w) => push(warningsBySubject, w.subject, w));

    // 氏 → 所属する人物。推定(inferred_name / inherited_father)は別に数える。
    const clans = new Map();
    data.lords.forEach((l) => {
      l.clans.forEach((c) => {
        if (!clans.has(c.id)) clans.set(c.id, { id: c.id, name: c.name, members: new Set(), certain: new Set() });
        const rec = clans.get(c.id);
        rec.members.add(l.id);
        if (l.clan_source === "wikidata") rec.certain.add(l.id);
      });
    });

    function holders(domainId) {
      const seen = new Set();
      return (tenuresByDomain.get(domainId) || [])
        .slice()
        .sort((a, b) => (a.start || 0) - (b.start || 0) || (a.ord || 0) - (b.ord || 0))
        .map((t) => t.lord)
        .filter((id) => lords.has(id) && !seen.has(id) && seen.add(id));
    }

    // 人物の「主たる藩」(primary_domain: 最も早い在任の藩)はビルド時に決めてある。ここではその藩での最初の在任を返す。
    // 色分け、藩での強調、他ページへのリンク先の基準になる。
    function primaryTenure(id) {
      const l = lords.get(id);
      const dom = l && l.primary_domain;
      if (!dom || !domains.has(dom)) return null;
      const ts = (tenuresByLord.get(id) || []).filter((t) => t.domain === dom);
      return ts.slice().sort((a, b) => (a.start || 9999) - (b.start || 9999) || (a.ord || 0) - (b.ord || 0))[0] || null;
    }
    function ruledDomain(id, domainId) { return (tenuresByLord.get(id) || []).some((t) => t.domain === domainId); }
    function isRuler(id) { const l = lords.get(id); return !!(l && l.has_tenure); }
    // 人物の地方 = 主たる藩の地方。藩主でない人物は null(どの地方にも属させない)。
    function regionOfLord(id) {
      const l = lords.get(id);
      const d = l && l.primary_domain && domains.get(l.primary_domain);
      return d ? (d.region || null) : null;
    }
    function colorOf(id) {
      const t = primaryTenure(id);
      if (!t) return NON_RULER_COLOR;
      return colors.get(t.domain) || NON_RULER_COLOR;
    }

    function neighbors(id, opts) {
      const bloodOnly = !!(opts && opts.bloodOnly);
      const out = new Set();
      [...(parents.get(id) || []), ...(children.get(id) || [])].forEach((n) => {
        if (bloodOnly && n.edge.type !== "blood") return;
        if (lords.has(n.id)) out.add(n.id);
      });
      return out;
    }

    // 実父をたどる(養子関係は無視)。ids の人物から gens 世代前まで、blood の辺だけをさかのぼった人物の集合を返す。
    function ancestors(ids, gens) {
      const out = new Set();
      let frontier = [...ids];
      for (let g = 0; g < gens && frontier.length; g++) {
        const next = [];
        frontier.forEach((id) => (parents.get(id) || []).forEach((p) => {
          if (p.edge.type !== "blood" || !lords.has(p.id) || out.has(p.id)) return;
          out.add(p.id); next.push(p.id);
        }));
        frontier = next;
      }
      return out;
    }

    function warningsFor(id) { return warningsBySubject.get(id) || []; }
    function hasWarn(id) { return warningsFor(id).some((w) => w.level === "warn"); }

    // 藩別ページのラベル: 「藩・代」+名前(在任期間は載せない)
    function nodeLabel(l, hiddenCount) {
      let text = l.gen_label ? l.gen_label.split("・").join("\n") + "\n" + l.name : l.name;
      if (!l.has_tenure) text += "\n(藩主以外)";
      if (hasWarn(l.id)) text += " ⚠";
      if (hiddenCount > 0) text += "\n[+" + hiddenCount + "]";
      return text;
    }

    // 画像(Wikimedia Commons)のサムネイルURL。ライセンスを確認できたもの(display=true)だけをノードに使う。
    // Special:FilePath?width=N は Commons が縮小版を返す(原寸を読み込まないので軽い)。
    function thumbUrl(l, width) {
      const im = l.image;
      if (!im || !im.display) return null;
      if (im.thumb) return im.thumb;   // ビルド時に解決した縮小版URL(common.js の imageUrl と同じ規則。Node でも動くようここに複製)
      return "https://commons.wikimedia.org/wiki/Special:FilePath/" + encodeURIComponent(im.file) + "?width=" + (width || 240);
    }

    function baseData(l, opts) {
      const c = colorOf(l.id);
      const img = opts && opts.images ? thumbUrl(l) : null;
      const d = { id: l.id, nonRuler: !l.has_tenure, warn: hasWarn(l.id), fill: c.fill, border: c.border,
                  clanIds: l.clans.map((x) => x.id), clanSource: l.clan_source || "none", hasImg: !!img };
      if (img) d.img = img;
      return d;
    }

    function edgeData(e) {
      return { group: "edges", data: { id: e.id, source: e.source, target: e.target, type: e.type, flagged: e.flags.length > 0 } };
    }

    // visible: 表示中の人物 ID の Set。→ Cytoscape に渡す elements を返す(藩別の家系図用)。
    function elements(visible, opts) {
      const nodes = [];
      visible.forEach((id) => {
        const l = lords.get(id);
        if (!l) return;
        const hidden = [...neighbors(id, opts)].filter((n) => !visible.has(n)).length;
        nodes.push({ group: "nodes", data: Object.assign(baseData(l, opts), { label: nodeLabel(l, hidden), hidden }) });
      });
      const ids = new Set(nodes.map((n) => n.data.id));
      const edges = data.relations.filter((e) => ids.has(e.source) && ids.has(e.target) && !(opts && opts.bloodOnly && e.type !== "blood")).map(edgeData);
      return nodes.concat(edges);
    }

    // ---------- 全体系図(1本の巨大グラフ) ----------
    // 血縁・養子でつながった人の集まり(連結成分 connected component)を求める。
    // dagre をそのまま全体にかけると、つながりのない一族が横一列に並んで極端に横長になる。
    // そこで一族ごとに階層レイアウトを作り、あとで2次元に敷き詰める(packRects)ために使う。
    function components(idSet) {
      const ids = [...idSet].filter((id) => lords.has(id));
      const inSet = new Set(ids);
      const seen = new Set();
      const out = [];
      ids.forEach((start) => {
        if (seen.has(start)) return;
        const comp = [];
        const stack = [start];
        while (stack.length) {
          const x = stack.pop();
          if (seen.has(x)) continue;
          seen.add(x);
          comp.push(x);
          [...(parents.get(x) || []), ...(children.get(x) || [])].forEach((n) => { if (inSet.has(n.id) && !seen.has(n.id)) stack.push(n.id); });
        }
        out.push(comp);
      });
      return out.sort((a, b) => b.length - a.length);   // 大きい一族を先頭に置く
    }

    // 矩形を段(shelf)に左から詰めていく簡易パッキング。戻り値は各矩形の左上座標。
    // 厳密な最小面積は求めない(速く・結果が予測しやすいことを優先)。
    function packRects(rects, rowWidth, gap) {
      gap = gap === undefined ? 40 : gap;
      const width = Math.max(rowWidth || 0, ...rects.map((r) => r.w));
      const out = [];
      let x = 0, y = 0, rowH = 0;
      rects.forEach((r) => {
        if (x > 0 && x + r.w > width) { x = 0; y += rowH + gap; rowH = 0; }
        out.push({ id: r.id, x, y });
        x += r.w + gap;
        rowH = Math.max(rowH, r.h);
      });
      return { positions: out, width, height: y + rowH };
    }

    // 全体表示用。ids を省くと全員。
    function allElements(opts, ids) {
      return elements(ids || new Set(data.lords.map((l) => l.id)), opts);
    }

    // 地方で絞り込むときに描く人物: その地方の藩に一度でも在任した藩主と、その実父の系統(祖先)。
    // 一族(連結成分)を丸ごと残すと、遠い祖先を介して全国の家がつながった大きな一族が、どの地方を選んでも入ってしまう。
    // 祖先だけを足せば、藩主から上へのつながりは切れず、他地方の無関係な分家は入らない。
    function idsInRegion(region) {
      if (!region) return new Set(data.lords.map((l) => l.id));
      const rulers = new Set();
      data.tenures.forEach((t) => { const d = domains.get(t.domain); if (d && d.region === region && lords.has(t.lord)) rulers.add(t.lord); });
      ancestors([...rulers], Infinity).forEach((id) => rulers.add(id));
      return rulers;
    }

    function search(query, limit) {
      const q = String(query || "").trim();
      if (!q) return [];
      return data.lords.filter((l) => l.name.includes(q) || (l.gen_label || "").includes(q)).slice(0, limit || 12);
    }

    return { thumbUrl, lords, domains, colors, tenuresByLord, tenuresByDomain, parents, children, clans, holders, neighbors,
             warningsFor, ancestors, nodeLabel, elements, allElements, components, idsInRegion, packRects, primaryTenure,
             isRuler, ruledDomain, regionOfLord, search };
  }

  const api = { build, NON_RULER_COLOR };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.TreeModel = api;
})(typeof window !== "undefined" ? window : globalThis);
