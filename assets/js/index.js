/* トップページ: meta.json の地方別の集計(by_region)を表にする。地方の順は meta.regions(config.json の regions)。 */
(async function () {
  const { el, showError } = Han;
  let meta;
  try {
    const res = await fetch("data/meta.json");
    if (!res.ok) throw new Error("meta.json を読み込めません (HTTP " + res.status + ")");
    meta = await res.json();
  } catch (err) { showError(String(err)); return; }
  const by = meta.by_region || {};
  const rows = (meta.regions || []).concat(by.unknown && by.unknown.domains ? ["unknown"] : []);
  const tbody = document.querySelector("#regions tbody");
  rows.forEach((r) => {
    const c = by[r];
    if (!c || !c.domains) return;
    const q = r === "unknown" ? "" : "?region=" + encodeURIComponent(r);
    tbody.append(el("tr", {}, [
      el("th", { scope: "row", text: r === "unknown" ? "地方不明" : r }),
      el("td", { text: String(c.domains) }), el("td", { text: String(c.lords) }), el("td", { text: String(c.tenures) }),
      el("td", {}, [el("a", { href: "map.html" + q, text: "地図" }), " ・ ", el("a", { href: "all.html" + q, text: "系図" })]),
    ]));
  });
  const n = meta.counts || {};
  tbody.append(el("tr", { class: "total" }, [el("th", { scope: "row", text: "計" }),
    el("td", { text: String(n.domains) }), el("td", { text: String(n.rulers) }), el("td", { text: String(n.tenures) }), el("td", {})]));
  const g = document.getElementById("generated");
  if (g && meta.generated_at) g.textContent = "データ生成: " + meta.generated_at.slice(0, 10);
})();
