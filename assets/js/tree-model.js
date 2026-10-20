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

    // ---------- 全体の系図(島の一覧) ----------
    // 実父子の線でつながった人の集まり(連結成分 connected component)を「島」と呼ぶ。大きい島を先頭に返す。
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
      return out.sort((a, b) => b.length - a.length);
    }

    // 世代の段: 島全体で共通の段数(家系図で上から何段目か)。実父は子の1段上、子は実父の1段下として、
    // 島の誰か1人から線をたどって順に決め、最後に最上段を 0 にそろえる。
    // 「その人の上に何代の祖先が記録されているか」で数えると、祖先が未入力の藩主がどこにいても最上段に見えてしまうため。
    // 実父が2人いるなど段が食い違う箇所は、先に決まった段を優先する(要確認として warnings に出ているもの)。
    function ranks(comp) {
      const inComp = new Set(comp);
      const rank = new Map([[comp[0], 0]]);
      const queue = [comp[0]];
      while (queue.length) {
        const x = queue.shift();
        const r = rank.get(x);
        (parents.get(x) || []).forEach((p) => { if (inComp.has(p.id) && !rank.has(p.id)) { rank.set(p.id, r - 1); queue.push(p.id); } });
        (children.get(x) || []).forEach((c) => { if (inComp.has(c.id) && !rank.has(c.id)) { rank.set(c.id, r + 1); queue.push(c.id); } });
      }
      const min = Math.min(...rank.values());
      rank.forEach((v, k) => rank.set(k, v - min));
      return rank;
    }

    function firstStart(id) {
      return Math.min(...(tenuresByLord.get(id) || []).map((t) => t.start || 9999), 9999);
    }

    // 島の中で、その人から実子・孫…とたどれる人数(島の外の人は数えない)。
    function descendantCount(id, inComp) {
      const seen = new Set();
      const stack = [id];
      while (stack.length) {
        const x = stack.pop();
        (children.get(x) || []).forEach((c) => { if (inComp.has(c.id) && !seen.has(c.id)) { seen.add(c.id); stack.push(c.id); } });
      }
      return seen.size;
    }

    // 島の一覧。代表者 = 島の中で子孫が最も多い藩主(その島の本流の祖)。
    // 同点なら世代が上の人、次に在任の始まりが早い人。
    // 「家系図の一番上の藩主」で選ぶと、徳川・松平の島で子孫4人の松平信一が選ばれるなど、分家の祖や子孫の少ない兄弟が出やすかったため。
    // 藩主のいない島は無い(藩主でない人物は、藩主の実父・祖先としてだけ載っているため)が、念のため島の全員から選ぶ。
    // regions: 島の藩主が在任した藩の地方。地方で一覧を絞るときに使う。
    function islands() {
      return components(new Set(data.lords.map((l) => l.id))).map((comp) => {
        const inComp = new Set(comp);
        const rank = ranks(comp);
        const rulers = comp.filter(isRuler);
        const pool = rulers.length ? rulers : comp;
        const desc = new Map(pool.map((id) => [id, descendantCount(id, inComp)]));
        const rep = pool.slice().sort((a, b) => desc.get(b) - desc.get(a) || rank.get(a) - rank.get(b)
          || firstStart(a) - firstStart(b) || lords.get(a).name.localeCompare(lords.get(b).name, "ja"))[0];
        const regions = new Set();
        rulers.forEach((id) => (tenuresByLord.get(id) || []).forEach((t) => {
          const d = domains.get(t.domain);
          if (d && d.region) regions.add(d.region);
        }));
        return { id: rep, rep, members: comp, rulers: rulers.length, regions };
      });
    }

    // 円を渦巻き(アルキメデスの螺旋)に沿って、大きい順に重ならない最初の位置へ置く。戻り値は各円の中心。
    // 大きい島が中央に、小さい島が周りや隙間に集まり、「島の大きさ」を見比べやすい。
    // 円の数は数百なので、重なりの判定は総当たりで十分(厳密な最密充填は求めない)。
    function packCircles(circles, gap) {
      gap = gap === undefined ? 12 : gap;
      const placed = [];
      const b = 6 / (2 * Math.PI);      // 螺旋の1周ごとに半径が 6px 増える
      // 同じ大きさの円は、前の円を置いた位置の続きから探す(内側はもう埋まっているので)。
      // 1人だけの島など同じ大きさの円が数百あるため、毎回中心から探すと遅い。
      const resume = new Map();
      return circles.map((c) => {
        let x = 0, y = 0;
        if (placed.length) {
          for (let th = resume.get(c.r) || 0; ; ) {
            const rad = b * th;
            x = rad * Math.cos(th); y = rad * Math.sin(th);
            if (placed.every((p) => (p.x - x) ** 2 + (p.y - y) ** 2 >= (p.r + c.r + gap) ** 2)) { resume.set(c.r, th); break; }
            th += Math.min(0.5, 4 / Math.max(rad, 1));   // 弧の長さがおよそ 4px ずつ進むように角度を刻む
          }
        }
        placed.push({ x, y, r: c.r });
        return { id: c.id, x, y };
      });
    }

    function search(query, limit) {
      const q = String(query || "").trim();
      if (!q) return [];
      return data.lords.filter((l) => l.name.includes(q) || (l.gen_label || "").includes(q)).slice(0, limit || 12);
    }

    return { thumbUrl, lords, domains, colors, tenuresByLord, tenuresByDomain, parents, children, clans, holders, neighbors,
             warningsFor, ancestors, nodeLabel, elements, components, islands, packCircles, primaryTenure,
             isRuler, ruledDomain, regionOfLord, search };
  }

  const api = { build, NON_RULER_COLOR };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.TreeModel = api;
})(typeof window !== "undefined" ? window : globalThis);
