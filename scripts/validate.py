#!/usr/bin/env python3
"""data/*.json の整合性チェック。 python scripts/validate.py

build_data.py が「Wikidata の欠落・食い違い」を warnings.json に書くのに対し、
こちらは「生成した JSON 自体がサイトで安全に使えるか」を確かめる(参照切れ・循環・範囲外など)。
  error  → 終了コード 1(サイトに載せてはいけない)
  warn   → 表示のみ(データ側の確認事項。画面上の警告アイコンの元になる)
"""
import json
import sys
from collections import Counter, defaultdict

from wdlib import DATA, ROOT

CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
Y0, Y1 = CONFIG["year_range"]
BB = CONFIG["japan_bbox"]


def load(n):
    return json.loads((DATA / n).read_text(encoding="utf-8"))


def main():
    domains, lords = load("domains.json"), load("lords.json")
    tenures, rels, warns = load("tenures.json"), load("relations.json"), load("warnings.json")
    D = {d["id"]: d for d in domains}
    L = {l["id"]: l for l in lords}
    errors, notes = [], []

    # 1. ID の重複・参照切れ(Cytoscape や Leaflet に渡すと実行時エラーになるため、ここで止める)
    for name, items in (("domains", domains), ("lords", lords), ("tenures", tenures), ("relations", rels)):
        dup = [k for k, v in Counter(i["id"] for i in items).items() if v > 1]
        if dup:
            errors.append(f"{name}: ID重複 {dup[:5]}")
    for t in tenures:
        if t["lord"] not in L:
            errors.append(f"tenure {t['id']}: 藩主 {t['lord']} が lords.json にありません")
        if t["domain"] not in D:
            errors.append(f"tenure {t['id']}: 藩 {t['domain']} が domains.json にありません")
        if t["start"] and t["end"] and t["start"] > t["end"]:
            errors.append(f"tenure {t['id']}: 開始年 > 終了年")
        for y in (t["start"], t["end"]):
            if y and not Y0 <= y <= Y1:
                notes.append(f"tenure {t['id']}: 年 {y} が想定範囲 {Y0}–{Y1} の外です")
    for e in rels:
        for k in ("source", "target"):
            if e[k] not in L:
                errors.append(f"relation {e['id']}: {k} {e[k]} が lords.json にありません")

    # 2. 家系の循環(階層レイアウト dagre は有向非循環グラフ DAG を前提とするため)
    graph = defaultdict(list)
    for e in rels:
        if e["type"] != "adoption_unknown":
            graph[e["source"]].append(e["target"])
    state = {}

    def dfs(u, path):
        state[u] = 1
        for v in graph.get(u, []):
            if state.get(v) == 1:
                errors.append("家系に循環: " + " → ".join(L[x]["name"] for x in path[path.index(v):] + [v] if x in L)
                              if v in path else f"家系に循環: {u} → {v}")
            elif v not in state:
                dfs(v, path + [v])
        state[u] = 2
    for n in list(graph):
        if n not in state:
            dfs(n, [n])

    # 2b. 実父は1人のはず(母を「実父」として拾っていないかの検査。build_data.py が女性を除いている)
    nfather = Counter(e["target"] for e in rels if e["type"] == "blood")
    multi = [L[c]["name"] for c, n in nfather.items() if n > 1 and c in L]
    for n in multi[:10]:
        notes.append(f"{n}: 実父(blood の辺)が複数あります")

    # 3. 座標の範囲(緯度経度の入れ替え・桁の誤りを検出)
    for d in domains:
        c = d.get("coord")
        if c and not (BB["lat"][0] <= c["lat"] <= BB["lat"][1] and BB["lon"][0] <= c["lon"] <= BB["lon"][1]):
            errors.append(f"domain {d['name']}: 座標 ({c['lat']}, {c['lon']}) が日本の範囲外です")

    # 4. 同一藩の在任の重なり・空白・代数の重複(別人の在任が複数年にわたって重なる場合のみ。交代年の重なりは許容)
    by_dom = defaultdict(list)
    for t in tenures:
        if t["start"]:
            by_dom[t["domain"]].append(t)
    overlap = gaps = dup_ord = 0
    for d, ts in by_dom.items():
        ts.sort(key=lambda t: (t["start"], t["end"] or 9999))
        for a, b in zip(ts, ts[1:]):
            if a["lord"] != b["lord"] and a["end"] and b["start"] < a["end"]:
                overlap += 1
                notes.append(f"{D[d]['name']}: {L[a['lord']]['name']}({a['start']}–{a['end']}) と "
                             f"{L[b['lord']]['name']}({b['start']}–{b['end']}) が重なっています")
            elif a["end"] and b["start"] > a["end"] + 1:
                gaps += 1
                notes.append(f"{D[d]['name']}: {a['end']}–{b['start']} 年に在任者の空白があります")
        ords = Counter((t["ord"]) for t in ts if t["ord"])
        for o, n in ords.items():
            if n > 1 and len({t["lord"] for t in ts if t["ord"] == o}) > 1:
                dup_ord += 1
                notes.append(f"{D[d]['name']}: {o}代が複数の人物に付いています")

    # 5. 旧国・地方の参照(画面の「地方 → 旧国 → 藩」の選択欄と絞り込みが、この対応に頼っているため)
    p2r = CONFIG["province_to_region"]
    regions = set(CONFIG["regions"])
    for q, v in p2r.items():
        if v.get("region") not in regions:
            errors.append(f"config province_to_region {q}({v.get('name')}): 地方 {v.get('region')} が regions にありません")
    for d in domains:
        pr, r = d.get("province"), d.get("region")
        if r is not None and r not in regions:
            errors.append(f"domain {d['name']}: 地方 {r} が config の regions にありません")
        if pr and pr["id"] not in p2r and r is not None:
            errors.append(f"domain {d['name']}: 旧国 {pr['id']} が province_to_region に無いのに地方 {r} が付いています")
        if pr and pr["id"] in p2r and p2r[pr["id"]]["region"] != r:
            errors.append(f"domain {d['name']}: 地方 {r} が旧国 {pr['name']} の地方 {p2r[pr['id']]['region']} と食い違います")
        if pr is None and r is not None:
            errors.append(f"domain {d['name']}: 旧国が無いのに地方 {r} が付いています")
        if pr is None:
            notes.append(f"{d['name']}: 旧国が決まっていません(地方不明)")
        elif pr["id"] not in p2r:
            notes.append(f"{d['name']}: 旧国 {pr['name']} が province_to_region にありません(地方不明)")
    # config に書いた藩の QID が、実際のデータに無い(書き間違い、または Wikidata 側で藩主職が消えた)
    for key in ("province_overrides", "seat_overrides", "branch_domains"):
        for q in CONFIG.get(key, {}):
            if q not in D:
                errors.append(f"config {key}: {q} が domains.json にありません")
    for q, v in CONFIG.get("province_overrides", {}).items():
        if v["province"] not in p2r:
            errors.append(f"config province_overrides {q}: 旧国 {v['province']} が province_to_region にありません")
    for l in lords:
        if l.get("primary_domain") and l["primary_domain"] not in D:
            errors.append(f"lord {l['name']}: primary_domain {l['primary_domain']} が domains.json にありません")
        if l["has_tenure"] and not l.get("primary_domain"):
            errors.append(f"lord {l['name']}: 在任があるのに primary_domain がありません")

    # 6. 表示まわり(地方別に集計する。全国版では「東北か外部か」を持たないため)
    rulers = [l for l in lords if l["has_tenure"]]
    region_of = {d["id"]: d.get("region") or "(地方不明)" for d in domains}
    no_wp = [l["name"] for l in rulers if "no_wikipedia" in l["flags"]]

    print(f"domains={len(domains)} lords={len(lords)}(藩主 {len(rulers)} / 藩主以外 {len(lords) - len(rulers)}) "
          f"tenures={len(tenures)} relations={len(rels)}")
    print("地方別(藩 / 藩主 / 座標なし):")
    for r in CONFIG["regions"] + ["(地方不明)"]:
        ds = [d for d in domains if region_of[d["id"]] == r]
        ls = {t["lord"] for t in tenures if region_of.get(t["domain"]) == r}
        nc = [d["name"] for d in ds if not d.get("coord")]
        print(f"  {r}: {len(ds)} / {len(ls)} / {len(nc)}" + (f"({'・'.join(nc[:8])}{'…' if len(nc) > 8 else ''})" if nc else ""))
    print("旧国の出所:", dict(Counter(d.get("province_source") or "none" for d in domains)))
    print("氏の出所(藩主):", dict(Counter(l["clan_source"] or "none" for l in rulers)))
    approx = [d["name"] for d in domains if (d.get("coord") or {}).get("precision") == "approx"]
    print(f"座標なし: {sum(1 for d in domains if not d.get('coord'))}  概略位置: {len(approx)}")
    print(f"実父が複数ある人物: {len(multi)}")
    print(f"在任の重なり: {overlap} / 空白: {gaps} / 代数の重複: {dup_ord}")
    print("警告の内訳:", dict(Counter(f"{w['level']}/{w['kind']}" for w in warns)))
    if no_wp:
        print(f"日本語版Wikipedia記事なし(藩主): {len(no_wp)}人")
    for n in notes[:30]:
        print("  [注意]", n)
    if len(notes) > 30:
        print(f"  …ほか {len(notes) - 30} 件")
    for e in errors:
        print("  [ERROR]", e)
    print("結果:", "NG" if errors else "OK(errorなし)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
