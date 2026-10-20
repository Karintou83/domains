/* 全体の系図ページ。2つの画面を切り替える。
   - 島の一覧: 実父子の線でつながった人の集まり(島)を、代表者1人のアイコンで並べる。アイコンの面積は島の人数に比例。
   - 島の家系図: 一覧で選んだ島の全員を、階層レイアウト(dagre)で名前が読める大きさに描く。
   全員を1枚に敷き詰める描き方では、全国 4000 人余りが点の集まりにしかならず、どこまで拡大しても読めなかったため。 */
(function () {
  const { el, showError, domainsByRegion } = Han;
  const UI = Han.GraphUI;
  let model, data, cy, islands, islandById, islandOf;
  const state = { mode: "islands", island: null };
  const $ = (id) => document.getElementById(id);

  // アイコンの直径。面積を人数に比例させる(直径は人数の平方根に比例)。1人の島でも名前が読める大きさを足しておく。
  const diameter = (n) => 26 + 11 * Math.sqrt(n);

  // ---------- 島の一覧 ----------
  function visibleIslands() {
    const region = $("region").value;
    return islands.filter((isl) => !region || isl.regions.has(region));
  }

  function islandElements(list) {
    const images = $("showImages").checked;
    const pos = model.packCircles(list.map((isl) => ({ id: isl.id, r: diameter(isl.members.length) / 2 })));
    return list.map((isl, i) => {
      const l = model.lords.get(isl.rep);
      const t = model.primaryTenure(isl.rep);
      const c = (t && model.colors.get(t.domain)) || { fill: "#efede8", border: "#9a968c" };
      const n = isl.members.length;
      const img = images ? model.thumbUrl(l) : null;
      const d = { id: isl.id, label: l.name + (n > 1 ? "\n" + n + "人" : ""), size: diameter(n), font: Math.min(30, 11 + Math.sqrt(n) * 0.8),
                  fill: c.fill, border: c.border, hasImg: !!img };
      if (img) d.img = img;
      return { group: "nodes", data: d, position: { x: pos[i].x, y: pos[i].y } };
    });
  }

  function islandStyle() {
    return [
      { selector: "node", style: {
        "shape": "ellipse", "width": "data(size)", "height": "data(size)", "background-color": "data(fill)",
        "border-width": 2, "border-color": "data(border)", "label": "data(label)", "text-wrap": "wrap", "text-max-width": 160,
        "font-size": "data(font)", "text-valign": "bottom", "text-halign": "center", "text-margin-y": 4, "color": "#2a2622",
        "font-family": "'Yu Mincho','Hiragino Mincho ProN','Noto Serif JP',serif", "font-weight": 600, "line-height": 1.25,
        "text-background-color": "#fffdf8", "text-background-opacity": 0.8, "text-background-padding": 1.5,
        "text-background-shape": "roundrectangle", "min-zoomed-font-size": 7 } },
      { selector: "node[?hasImg]", style: { "background-image": "data(img)", "background-fit": "cover", "background-position-y": "0%",
                                           "background-image-crossorigin": "null", "border-width": 3 } },
      { selector: "node.hl", style: { "border-color": "#a8801f", "border-width": 6 } },
      { selector: "node.dim", style: { "opacity": 0.15 } },
      { selector: "node:active, node:selected", style: { "overlay-opacity": 0, "border-color": "#223a5e", "border-width": 5 } },
    ];
  }

  // 一覧での強調: 選んだ藩に在任した人、選んだ氏の人を含む島を金の縁にし、ほかを薄くする。
  function highlightIslands() {
    const clan = $("clan").value, dom = $("domain").value;
    cy.nodes().removeClass("hl dim");
    if (!clan && !dom) return;
    const c = clan && model.clans.get(clan);
    cy.nodes().forEach((n) => {
      const isl = islandById.get(n.id());
      const ok = isl.members.some((id) => (!c || c.members.has(id)) && (!dom || model.ruledDomain(id, dom)));
      n.addClass(ok ? "hl" : "dim");
    });
  }

  function showIslands() {
    state.mode = "islands"; state.island = null;
    const list = visibleIslands();
    cy.style(islandStyle());
    cy.elements().remove();
    cy.add(islandElements(list));
    cy.fit(cy.elements(), 30);
    highlightIslands();
    const people = list.reduce((s, isl) => s + isl.members.length, 0);
    $("count").textContent = list.length + " 島 / " + people + " 人";
    $("islandInfo").hidden = true;
    $("islandsHelp").hidden = false;
    $("info").replaceChildren(el("p", { class: "sub", text: "島(アイコン)をクリックすると、その島の全員を家系図で表示します。" }));
    syncUrl();
  }

  // ---------- 島の家系図 ----------
  function showIsland(id, focus) {
    const isl = islandById.get(id);
    if (!isl) return;
    state.mode = "family"; state.island = id;
    cy.style(UI.style({ round: true }));
    cy.elements().remove();
    cy.add(model.elements(new Set(isl.members), { images: $("showImages").checked, bloodOnly: true }));
    try {
      cy.layout({ name: "dagre", rankDir: "TB", nodeSep: 22, rankSep: 70, nodeDimensionsIncludeLabels: true, animate: false, fit: false }).run();
    } catch (err) {
      showError("階層レイアウト(dagre)を読み込めなかったため、簡易レイアウトで表示しています。");
      cy.layout({ name: "breadthfirst", directed: true, fit: false }).run();
    }
    cy.fit(cy.elements(), 30);
    // 大きな島は全体を収めると名前が読めない縮尺になるので、代表者(最上段)の周りから見せる。
    if (cy.zoom() < 0.5) { cy.zoom(0.8); cy.center(cy.getElementById(isl.rep)); }
    highlight();
    const rep = model.lords.get(isl.rep);
    $("count").textContent = cy.nodes().length + " 人 / " + cy.edges().length + " 本";
    $("islandTitle").textContent = rep.name + " の島(" + isl.members.length + "人・藩主 " + isl.rulers + "人)";
    $("islandInfo").hidden = false;
    $("islandsHelp").hidden = true;
    if (focus) focusNode(focus, true);
    else { clearFocus(); syncUrl(); }
  }

  function highlight() {
    if (state.mode === "islands") highlightIslands();
    else UI.applyHighlight(cy, model, { clanId: $("clan").value, domainId: $("domain").value });
  }

  // 選んだ人物とその直接の親族以外を薄くして、つながりを追いやすくする
  function focusNode(id, center) {
    const n = cy.getElementById(id);
    if (!n || n.empty()) return;
    cy.elements().removeClass("faded");
    cy.elements().not(n.closedNeighborhood()).addClass("faded");
    cy.nodes().unselect();
    n.select();
    // 拡大してから中央に寄せる(先に寄せると、拡大の基準点がずれてその人が画面から外れる)。
    if (center) { cy.zoom(Math.max(cy.zoom(), 0.9)); cy.center(n); }
    const l = model.lords.get(id);
    const t = model.primaryTenure(id);
    UI.renderInfo($("info"), model, id, {
      onClan: (clanId) => { $("clan").value = clanId; highlight(); },
      links: [{ text: "藩別の家系図で見る", href: "tree.html?" + (t ? "domain=" + encodeURIComponent(t.domain) + "&" : "") + "lord=" + encodeURIComponent(l.id) },
             ].concat(t ? [{ text: "地図で見る", href: "map.html?lord=" + encodeURIComponent(l.id) }] : []),
    });
    syncUrl(id);
  }

  function clearFocus() {
    cy.elements().removeClass("faded");
    cy.nodes().unselect();
    $("info").replaceChildren(el("p", { class: "sub", text: "人物をクリックすると、その人と親族だけが濃く表示されます。" }));
  }

  // ---------- 共通 ----------
  function onRegion() {
    const region = $("region").value;
    UI.fillDomainSelect(model, data, $("domain"), true, region);
    renderDomainLegend(region);
    showIslands();
  }

  function renderDomainLegend(region) {
    const legend = $("domainLegend");
    legend.replaceChildren();
    domainsByRegion(data).forEach((g) => {
      if (region && g.region !== region) return;
      legend.append(el("li", { class: "region-head", text: g.region }));
      g.domains.forEach((d) => {
        const c = model.colors.get(d.id);
        legend.append(el("li", {}, [el("span", { class: "chip", style: "background:" + c.fill + ";border-color:" + c.border }), d.name]));
      });
    });
  }

  function syncUrl(focus) {
    const p = new URLSearchParams();
    if ($("region").value) p.set("region", $("region").value);
    if (state.island) p.set("island", state.island);
    if (focus) p.set("lord", focus);
    history.replaceState(null, "", "?" + p.toString());
  }

  async function init() {
    try { data = await Han.loadData("data/"); } catch (err) { showError(String(err)); return; }
    if (typeof cytoscape === "undefined") { showError("Cytoscape.js を読み込めませんでした(ネットワークを確認してください)。"); return; }
    model = TreeModel.build(data);
    islands = model.islands();
    islandById = new Map(islands.map((isl) => [isl.id, isl]));
    islandOf = new Map();
    islands.forEach((isl) => isl.members.forEach((id) => islandOf.set(id, isl.id)));
    UI.syncAdoptionUI(data);
    UI.fillRegionSelect(data, $("region"));
    UI.fillClanSelect(model, $("clan"));

    cy = cytoscape({ container: $("cy"), elements: [], style: islandStyle(), wheelSensitivity: 0.3,
                     minZoom: 0.03, maxZoom: 2.5, boxSelectionEnabled: false, textureOnViewport: true });
    cy.on("tap", "node", (ev) => {
      if (state.mode === "islands") showIsland(ev.target.id());
      else focusNode(ev.target.id(), false);
    });
    cy.on("tap", (ev) => { if (ev.target === cy && state.mode === "family") { clearFocus(); syncUrl(); } });

    $("clan").addEventListener("change", highlight);
    $("domain").addEventListener("change", () => {
      highlight();
      const dom = $("domain").value;
      if (!dom || state.mode !== "family") return;
      const hit = cy.nodes().filter((n) => model.ruledDomain(n.id(), dom));
      if (!hit.empty()) cy.fit(hit, 60);
    });
    $("region").addEventListener("change", onRegion);
    $("showImages").addEventListener("change", () => (state.mode === "islands" ? showIslands() : showIsland(state.island)));
    $("fit").addEventListener("click", () => cy.fit(cy.elements(), 30));
    $("back").addEventListener("click", showIslands);
    UI.bindSearch(model, $("q"), $("results"), (l) => showIsland(islandOf.get(l.id), l.id));

    // URL: ?region=地方名 / ?island=代表者のQID / ?lord=人物のQID(その人の島を開いて、その人に寄せる)
    const p = new URLSearchParams(location.search);
    const region = p.get("region") || "";
    if ([...$("region").options].some((o) => o.value === region)) $("region").value = region;
    onRegion();
    const focus = model.lords.has(p.get("lord")) ? p.get("lord") : null;
    if (focus) showIsland(islandOf.get(focus), focus);
    else if (islandById.has(p.get("island"))) showIsland(p.get("island"));
    $("generated").textContent = (data.meta && data.meta.generated_at) ? "データ生成: " + data.meta.generated_at.slice(0, 10) : "";
  }

  document.addEventListener("DOMContentLoaded", init);
})();
