/* 家系図ページ・地図ページで共有する部品。グローバル名前空間 Han に載せる。
   ES modules ではなく単純な <script> にしている理由: file:// ではなく http サーバ経由でも、
   GitHub Pages でも、ビルド工程なしでそのまま動くようにするため。 */
(function (root) {
  const DATA_FILES = ["domains", "lords", "tenures", "relations", "warnings", "meta"];

  async function loadData(base) {
    base = base || "data/";
    const parts = await Promise.all(DATA_FILES.map(async (name) => {
      const res = await fetch(base + name + ".json");
      if (!res.ok) throw new Error(name + ".json を読み込めません (HTTP " + res.status + ")");
      return res.json();
    }));
    const data = {};
    DATA_FILES.forEach((name, i) => { data[name] = parts[i]; });
    return data;
  }

  // 日本語版Wikipediaへのリンクは出典として必ず残す(Wikidata は CC0 だが、記事への導線は明示する方針)。
  function wikipediaUrl(title) {
    return "https://ja.wikipedia.org/wiki/" + encodeURIComponent(String(title).replace(/ /g, "_"));
  }
  function wikidataUrl(id) {
    return "https://www.wikidata.org/wiki/" + encodeURIComponent(id);
  }

  // 氏の出所。推定値は確定値と区別して画面に出す(中立性・出典の明確さのため)。
  const CLAN_SOURCE_LABEL = {
    wikidata: "Wikidata (P53)",
    inferred_name: "名前から推定",
    inherited_father: "実父から継承",
  };

  // 肖像のURL。ビルド時に解決した upload.wikimedia.org のサムネイル(im.thumb)があればそれを使う。
  // 無い場合だけ Special:FilePath(リダイレクト+その場での縮小生成が入るので遅い)にフォールバックする。
  // 全画面で同じ1サイズを使うのは、同じURLならブラウザのキャッシュが効くため。
  function imageUrl(im, width) {
    if (im.thumb) return im.thumb;
    return "https://commons.wikimedia.org/wiki/Special:FilePath/" + encodeURIComponent(im.file) + "?width=" + (width || 240);
  }

  // 地方の並び順は config.json の regions(meta.json に写してある)に従う。画面ごとに順序を持たないため。
  // 旧国が分からない藩(region が null)は最後に「地方不明」としてまとめる。
  const UNKNOWN_REGION = "地方不明";
  function regionOf(d) { return d.region || UNKNOWN_REGION; }
  function regionsOf(data) {
    const order = ((data.meta && data.meta.regions) || []).slice();
    data.domains.forEach((d) => { if (!order.includes(regionOf(d))) order.push(regionOf(d)); });
    return order.filter((r) => data.domains.some((d) => regionOf(d) === r));
  }
  // [{region, domains}]。地方の中は藩名の五十音順(藩名で探すことが多いので、旧国順より見つけやすい)。
  function domainsByRegion(data) {
    return regionsOf(data).map((region) => ({
      region,
      domains: data.domains.filter((d) => regionOf(d) === region).sort((a, b) => a.name.localeCompare(b.name, "ja")),
    }));
  }
  function provinceName(d) { return d.province && d.province.name ? d.province.name : ""; }

  function el(tag, attrs, children) {
    const node = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => {
      if (v === null || v === undefined || v === false) return;
      if (k === "class") node.className = v;
      else if (k === "text") node.textContent = v;
      else if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v === true ? "" : v);
    });
    (children || []).forEach((c) => node.append(c));
    return node;
  }

  function showError(message) {
    const box = document.getElementById("error");
    if (box) { box.textContent = message; box.hidden = false; }
    console.error(message);
  }

  root.Han = Object.assign(root.Han || {}, {
    loadData, imageUrl, wikipediaUrl, wikidataUrl, CLAN_SOURCE_LABEL, el, showError,
    UNKNOWN_REGION, regionOf, regionsOf, domainsByRegion, provinceName,
  });
})(typeof window !== "undefined" ? window : globalThis);
