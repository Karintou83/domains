#!/usr/bin/env python3
"""フェーズ0: 全国版にする前の Wikidata 実データ調査。サイトの生成には使わない。

  python scripts/survey_nationwide.py            # 取得(足りない分だけ) → 集計を表示し、report.json に保存
  python scripts/survey_nationwide.py --offline  # 取得せず、保存済みの分だけで集計

調べること(タスクのフェーズ0):
  1. 藩主職がある藩・在任・人物の数(全国の合計と、旧国別)
  2. 藩項目に旧国が入っているか。どのプロパティで、何割の藩か。値が都道府県・市町村の場合の内訳
  3. 旧国が決まらない藩の一覧(補い方を考える材料: P131 の値、座標)
  4. 祖先8世代を含めたときの人数 → lords.json などのサイズの見積もり
  5. 親藩の候補: 徳川家康の子孫(実父の系統 / 母を経由する系統を区別)が藩主になった藩

作りの方針(touhoku-domains の explore_*.py と同じ):
  - 標準ライブラリだけ。1クエリごとに待つ(PAUSE)。人物・藩のリストは分割(chunks)して問い合わせる。
  - 生の結果は data/raw/survey/ に保存し、あるファイルは再取得しない(問い合わせを増やさないため)。
  - QID を記憶で決め打ちしない。旧国のクラスは「陸奥国」などのラベルから実データで求め、
    徳川家康の QID もラベルで引いて確かめる(記憶違いがそのまま調査結果の誤りになるため)。
  - Wikidata は読むだけ。
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "survey"
ENDPOINT = "https://query.wikidata.org/sparql"
# 連絡先は GitHub の URL のみ(公開リポジトリに個人のメールアドレスを残さないため)。
UA = "domains-survey/0.1 (https://github.com/Karintou83/domains; read-only research script)"
PAUSE = 3                      # 秒。連続リクエストを避ける(wdlib.sparql と同じ値)
KINSEI = "Q24887524"           # 近世大名。build_data.py の position_class と同じ
POSITION_CLASS = "Q114962596"  # 藩主職の P31。build_data.py の SPARQL と同じ
FEMALE = "Q6581072"
ANCESTOR_GENS = 8
DESCENT_GENS = 14              # 家康(1543生)から幕末まで実際は 10〜11 世代。余裕を見て 14 で打ち切る

# 旧国クラスを求めるための見本。ラベルで引き、全員に共通する P31 を旧国のクラスとみなす。
# 明治の分割後の国(陸前・羽前・渡島)も入れて、同じクラスで表されているかも確かめる。
PROVINCE_SAMPLES = ["陸奥国", "出羽国", "武蔵国", "薩摩国", "山城国", "陸前国", "羽前国", "渡島国"]

# ---- 地方の区分(案)。フェーズ0の報告で地方別の数字を出すためだけに使う。----
# 確定したら、フェーズ1で config.json の province_to_region(旧国の QID → 地方)に移す。
# ここでラベルを使うのは、まだ旧国の QID を確かめていないため。
REGION_DRAFT = {
    "北海道・東北": ["蝦夷", "渡島", "後志", "胆振", "石狩", "天塩", "北見", "日高", "十勝", "釧路", "根室", "千島",
                 "陸奥", "陸中", "陸前", "磐城", "岩代", "出羽", "羽前", "羽後"],
    "関東": ["上野", "下野", "常陸", "上総", "下総", "武蔵", "安房", "相模", "甲斐"],
    "北陸": ["越後", "佐渡", "越中", "能登", "加賀", "越前", "若狭"],
    "東海・甲信": ["信濃", "飛騨", "美濃", "尾張", "三河", "遠江", "駿河", "伊豆"],
    "近畿": ["伊勢", "伊賀", "志摩", "近江", "山城", "大和", "河内", "和泉", "摂津", "紀伊",
           "丹波", "丹後", "但馬", "播磨", "淡路"],
    "中国": ["因幡", "伯耆", "出雲", "石見", "隠岐", "美作", "備前", "備中", "備後", "安芸", "周防", "長門"],
    "四国": ["阿波", "讃岐", "伊予", "土佐"],
    "九州": ["豊前", "豊後", "筑前", "筑後", "肥前", "肥後", "日向", "大隅", "薩摩", "対馬", "壱岐"],
}
REGION_OF = {p: r for r, ps in REGION_DRAFT.items() for p in ps}


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def sparql(query):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for wait in (5, 20, 60, 120):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                rows = json.load(r)["results"]["bindings"]
            time.sleep(PAUSE)
            return [{k: v["value"] for k, v in row.items()} for row in rows]
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            print(f"  HTTP {e.code}: {wait}秒待ってリトライ")
            time.sleep(wait)
    raise RuntimeError("リトライ上限に達しました")


OFFLINE = False


def cached(name, producer):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    if OFFLINE:
        print(f"  (offline) {name} が無いので空として扱います")
        return []
    rows = producer()
    p.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fetch] {name}: {len(rows)}")
    return rows


def values(ids):
    return " ".join(f"wd:{i}" for i in ids)


# ---------------------------------------------------------------------------- 取得
def fetch():
    pos = cached("positions.json", lambda: sparql(f"""
SELECT ?pos ?domain ?domainLabel ?coord WHERE {{
  ?pos wdt:P31 wd:{POSITION_CLASS} ; wdt:P279 wd:{KINSEI} .
  OPTIONAL {{ ?pos wdt:P2389 ?domain . OPTIONAL {{ ?domain wdt:P625 ?coord }} }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""))
    domains = sorted({qid(r["domain"]) for r in pos if r.get("domain")})

    # 在任: 声明(?st)単位で数える。ラベルは要らないので取らない(軽くするため)。
    p39 = cached("p39.json", lambda: sparql(f"""
SELECT ?st ?person ?pos ?start WHERE {{
  ?pos wdt:P31 wd:{POSITION_CLASS} ; wdt:P279 wd:{KINSEI} .
  ?person p:P39 ?st . ?st ps:P39 ?pos .
  OPTIONAL {{ ?st pq:P580 ?start }}
}}"""))
    persons = sorted({qid(r["person"]) for r in p39})

    # 旧国のクラス: 見本の旧国の P31 を集める。
    labels = " ".join(f'"{s}"@ja' for s in PROVINCE_SAMPLES)
    samples = cached("province_samples.json", lambda: sparql(f"""
SELECT ?item ?label ?cls ?clsLabel WHERE {{
  VALUES ?label {{ {labels} }}
  ?item rdfs:label ?label ; wdt:P31 ?cls .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""))
    classes = province_classes(samples)
    print("旧国のクラス(見本全員に共通する P31):", classes)
    if not classes:
        sys.exit("旧国のクラスを決められません。province_samples.json を確認してください")
    cls_vals = values(classes)
    cached("provinces.json", lambda: sparql(f"""
SELECT DISTINCT ?prov ?provLabel WHERE {{
  VALUES ?c {{ {cls_vals} }} ?prov wdt:P31 ?c .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""))

    # 藩 → 旧国。3通りの経路を別々に取り、どれが使われているかを数える。
    #   direct: 藩項目の文(プロパティを問わない)の値が旧国
    #   p131:   藩項目の P131(所在地)を上にたどって旧国に届く
    #   seat:   本拠地(P159、城・陣屋)の P131 を上にたどって旧国に届く
    def prov_rows(kind, pattern):
        rows = []
        for ch in chunks(domains, 80):
            rows += sparql(f"""
SELECT ?domain ?prop ?prov WHERE {{
  VALUES ?domain {{ {values(ch)} }} VALUES ?c {{ {cls_vals} }}
  {pattern}
  ?prov wdt:P31 ?c .
}}""")
        for r in rows:
            r["kind"] = kind
        return rows
    cached("domain_prov_direct.json", lambda: prov_rows("direct", """
  ?domain ?p ?prov . FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
  BIND(REPLACE(STR(?p), "^.*/", "") AS ?prop)"""))
    cached("domain_prov_p131.json", lambda: prov_rows("p131", """
  ?domain wdt:P131/wdt:P131* ?prov . BIND("P131+" AS ?prop)"""))
    cached("domain_prov_seat.json", lambda: prov_rows("seat", """
  ?domain wdt:P159 ?seat . ?seat wdt:P131/wdt:P131* ?prov . BIND("P159/P131+" AS ?prop)"""))

    # P131 の直接の値と、その種類(都道府県・市町村など)。旧国でない値の扱いを考える材料。
    cached("domain_p131.json", lambda: [r for ch in chunks(domains, 80) for r in sparql(f"""
SELECT ?domain ?loc ?locLabel ?type ?typeLabel WHERE {{
  VALUES ?domain {{ {values(ch)} }}
  ?domain wdt:P131 ?loc . OPTIONAL {{ ?loc wdt:P31 ?type }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}""")])
    # 本拠地(P159)・行政中心地(P36)とその座標。旧国が決まらない藩を座標や所在市町村で補う案の材料。
    cached("domain_seats.json", lambda: [r for ch in chunks(domains, 80) for r in sparql(f"""
SELECT ?domain ?prop ?seat ?seatLabel ?coord ?loc ?locLabel WHERE {{
  VALUES ?domain {{ {values(ch)} }} VALUES ?p {{ wdt:P159 wdt:P36 }}
  ?domain ?p ?seat . BIND(REPLACE(STR(?p), "^.*/", "") AS ?prop)
  OPTIONAL {{ ?seat wdt:P625 ?coord }} OPTIONAL {{ ?seat wdt:P131 ?loc }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}""")])

    # 祖先: build_data.py の q_parents と同じ条件(P22、または女性でない父の P40)で 8 世代さかのぼる。
    # 行の形も build_data.py の ancestors.json と同じにしてある。
    def ancestors():
        rows, queried, frontier = [], set(), set(persons)
        for g in range(ANCESTOR_GENS):
            todo = sorted(frontier - queried)
            if not todo:
                break
            queried |= set(todo)
            gen_rows = [r for ch in chunks(todo, 80) for r in sparql(f"""
SELECT ?person ?father ?via WHERE {{
  VALUES ?person {{ {values(ch)} }}
  {{ ?person wdt:P22 ?father . BIND("P22" AS ?via) }}
  UNION {{ ?father wdt:P40 ?person . FILTER NOT EXISTS {{ ?father wdt:P21 wd:{FEMALE} }} BIND("P40" AS ?via) }}
}}""")]
            for r in gen_rows:
                r["gen"] = g + 1
            rows += gen_rows
            frontier = {qid(r["father"]) for r in gen_rows}
            print(f"  ancestors gen{g + 1}: queried={len(todo)} rows={len(gen_rows)}")
        return rows
    cached("ancestors.json", ancestors)

    # 徳川家康: ラベルで引いて、人間(Q5)であることを確かめる。
    ie = cached("ieyasu.json", lambda: sparql("""
SELECT ?item ?birth WHERE { ?item rdfs:label "徳川家康"@ja ; wdt:P31 wd:Q5 . OPTIONAL { ?item wdt:P569 ?birth } }"""))
    if len(ie) < 1:
        sys.exit("徳川家康の項目が見つかりません")
    root = qid(ie[0]["item"])

    # 家康の子孫を世代ごとに下へたどる。P40(親→子)と、子の P22(父)・P25(母)の両方から拾う。
    # 性別も取り、「実父の系統だけで届く」か「母(娘)を経由して届く」かを区別できるようにする
    # (鷹司松平家のように母方でつながる家を、候補として落とさず、かつ区別して示すため)。
    def descendants():
        rows, seen, frontier = [], {root}, [root]
        for g in range(DESCENT_GENS):
            if not frontier:
                break
            gen_rows = [r for ch in chunks(frontier, 80) for r in sparql(f"""
SELECT ?parent ?child ?g WHERE {{
  VALUES ?parent {{ {values(ch)} }}
  {{ ?parent wdt:P40 ?child }} UNION {{ ?child wdt:P22 ?parent }} UNION {{ ?child wdt:P25 ?parent }}
  OPTIONAL {{ ?child wdt:P21 ?g }}
}}""")]
            rows += gen_rows
            nxt = {qid(r["child"]) for r in gen_rows} - seen
            seen |= nxt
            frontier = sorted(nxt)
            print(f"  descendants gen{g + 1}: new={len(nxt)}")
        return rows
    cached("ieyasu_descendants.json", descendants)


def province_classes(samples):
    by_item = defaultdict(set)
    for r in samples:
        by_item[r["label"]].add(qid(r["cls"]))
    found = [s for s in PROVINCE_SAMPLES if by_item.get(s)]
    if not found:
        return []
    # 古代の国(陸奥・出羽…)と明治の国(陸前・渡島…)でクラスが違う可能性があるので、
    # 共通部分が空なら、2つ以上の見本に付いているクラスを採る。
    common = set.intersection(*(by_item[s] for s in found))
    if common:
        return sorted(common)
    cnt = Counter(c for s in found for c in by_item[s])
    return sorted(c for c, n in cnt.items() if n >= 2)


# ---------------------------------------------------------------------------- 集計
def load(name, default=None):
    p = OUT / name
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else (default if default is not None else [])


def stem(label):
    return (label or "").removesuffix("国")


def analyze():
    pos = load("positions.json")
    domain_name = {qid(r["domain"]): r.get("domainLabel") for r in pos if r.get("domain")}
    pos_domain = {qid(r["pos"]): qid(r["domain"]) for r in pos if r.get("domain")}
    has_coord = {qid(r["domain"]) for r in pos if r.get("coord")}
    p39 = [r for r in load("p39.json") if qid(r["pos"]) in pos_domain]
    prov_name = {qid(r["prov"]): r.get("provLabel") for r in load("provinces.json")}
    report = {"positions": len({qid(r["pos"]) for r in pos}),
              "positions_without_domain": sorted({qid(r["pos"]) for r in pos if not r.get("domain")})}

    # --- 1. 規模
    st_by_dom = defaultdict(set)
    person_by_dom = defaultdict(set)
    for r in p39:
        d = pos_domain[qid(r["pos"])]
        st_by_dom[d].add(r["st"])
        person_by_dom[d].add(qid(r["person"]))
    persons = {qid(r["person"]) for r in p39}
    with_tenure = set(st_by_dom)
    report["totals"] = {"domains_with_position": len(domain_name), "domains_with_tenure": len(with_tenure),
                        "tenures": len({r["st"] for r in p39}), "lords": len(persons)}

    # --- 2. 旧国
    paths = {}
    for kind in ("direct", "p131", "seat"):
        rows = load(f"domain_prov_{kind}.json")
        m = defaultdict(set)
        props = Counter()
        for r in rows:
            m[qid(r["domain"])].add(qid(r["prov"]))
            props[r["prop"]] += 1
        paths[kind] = m
        report[f"province_via_{kind}"] = {"domains": len(m), "share": round(len(m) / max(1, len(domain_name)), 3),
                                         "properties": dict(props)}
    resolved, source, multi = {}, {}, {}
    for d in domain_name:
        for kind in ("direct", "p131", "seat"):     # 藩項目に直接ある値を最優先(人が明示した値のため)
            ps = paths[kind].get(d)
            if ps:
                resolved[d], source[d] = sorted(ps), kind
                if len(ps) > 1:
                    multi[d] = [prov_name.get(p, p) for p in sorted(ps)]
                break
    report["province_resolved"] = {"domains": len(resolved), "by_source": dict(Counter(source.values())),
                                   "multiple": {f"{domain_name[d]} ({d})": v for d, v in sorted(multi.items())}}

    # P131 の直接の値の種類(旧国が決まらない藩について)
    p131 = defaultdict(list)
    for r in load("domain_p131.json"):
        p131[qid(r["domain"])].append((r.get("locLabel"), r.get("typeLabel")))
    unresolved = sorted(d for d in domain_name if d not in resolved)
    types = Counter()
    for d in unresolved:
        for t in {t for _, t in p131.get(d, [])} or {"(P131なし)"}:
            types[t] += 1
    seats = defaultdict(list)
    for r in load("domain_seats.json"):
        seats[qid(r["domain"])].append(f"{r['prop']}:{r.get('seatLabel')}" + ("" if r.get("coord") else "(座標なし)"))
    report["unresolved"] = {
        "count": len(unresolved), "with_tenure": len(set(unresolved) & with_tenure),
        "p131_types": dict(types.most_common()),
        "list": [{"id": d, "name": domain_name[d], "tenures": len(st_by_dom.get(d, ())),
                  "p131": sorted({l for l, _ in p131.get(d, []) if l}), "seats": sorted(set(seats.get(d, []))),
                  "coord": d in has_coord} for d in unresolved]}

    # --- 1'. 旧国別・地方(案)別
    def first_prov(d):
        return prov_name.get(resolved[d][0], resolved[d][0]) if d in resolved else None
    by_prov = defaultdict(lambda: {"domains": 0, "tenures": 0, "lords": set()})
    for d in domain_name:
        k = first_prov(d) or "(旧国不明)"
        by_prov[k]["domains"] += 1
        by_prov[k]["tenures"] += len(st_by_dom.get(d, ()))
        by_prov[k]["lords"] |= person_by_dom.get(d, set())
    report["by_province"] = {k: {"domains": v["domains"], "tenures": v["tenures"], "lords": len(v["lords"])}
                             for k, v in sorted(by_prov.items(), key=lambda kv: -kv[1]["domains"])}
    by_reg = defaultdict(lambda: {"domains": 0, "tenures": 0, "lords": set(), "provinces": set()})
    unmapped = set()
    for k, v in by_prov.items():
        r = REGION_OF.get(stem(k)) if k != "(旧国不明)" else "(地方不明)"
        if r is None:
            unmapped.add(k)
            r = "(区分案に無い旧国)"
        by_reg[r]["domains"] += v["domains"]
        by_reg[r]["tenures"] += v["tenures"]
        by_reg[r]["lords"] |= v["lords"]
        by_reg[r]["provinces"].add(k)
    report["by_region_draft"] = {r: {"domains": v["domains"], "tenures": v["tenures"], "lords": len(v["lords"]),
                                     "provinces": sorted(v["provinces"])} for r, v in by_reg.items()}
    report["provinces_not_in_draft"] = sorted(unmapped)
    report["all_province_labels"] = sorted(set(prov_name.values()) - {None})

    # --- 4. 祖先とサイズ
    anc = load("ancestors.json")
    nodes = set(persons) | {qid(r["father"]) for r in anc}
    gens = Counter(r.get("gen") for r in anc)
    # 1人・1本あたりのバイト数は、touhoku-domains の現行 data/*.json の実測値
    # (lords 476B/人, relations 132B/本, tenures 255B/件, domains 352B/藩)。
    est_edges = len({(qid(r["father"]), qid(r["person"])) for r in anc})
    report["size_estimate"] = {
        "nodes_lords_plus_ancestors": len(nodes), "ancestor_rows_by_gen": dict(sorted(gens.items())),
        "lords_json_MB": round(len(nodes) * 476 / 1e6, 2), "relations_json_MB": round(est_edges * 132 / 1e6, 2),
        "tenures_json_MB": round(report["totals"]["tenures"] * 255 / 1e6, 2),
        "domains_json_MB": round(len(domain_name) * 352 / 1e6, 2)}

    # --- 5. 親藩の候補(家康の子孫が藩主になった藩)。確定はユーザーが config で行う。
    ie = load("ieyasu.json")
    root = qid(ie[0]["item"]) if ie else None
    desc = load("ieyasu_descendants.json")
    gender = {}
    kids = defaultdict(set)
    for r in desc:
        p, c = qid(r["parent"]), qid(r["child"])
        kids[p].add(c)
        if r.get("g"):
            gender[c] = qid(r["g"])
    male_line, any_line = set(), set()
    if root:
        # 実父の系統: 女性を親として通らない。母方を含む系統: 誰でも通る。
        stack = [root]
        male_line.add(root)
        while stack:
            p = stack.pop()
            if gender.get(p) == FEMALE:
                continue
            for c in kids.get(p, ()):
                if c not in male_line:
                    male_line.add(c)
                    stack.append(c)
        stack = [root]
        any_line.add(root)
        while stack:
            p = stack.pop()
            for c in kids.get(p, ()):
                if c not in any_line:
                    any_line.add(c)
                    stack.append(c)
    cands = []
    for d in domain_name:
        lords = person_by_dom.get(d, set())
        m, a = lords & male_line, lords & any_line
        if a:
            cands.append({"id": d, "name": domain_name[d], "province": first_prov(d), "lords": len(lords),
                          "male_line_lords": len(m), "via_female_only_lords": len(a - m),
                          "share": round(len(a) / len(lords), 2)})
    cands.sort(key=lambda c: (-c["share"], c["name"] or ""))
    report["shinpan_candidates"] = {"ieyasu": root, "descendants_male_line": len(male_line),
                                    "descendants_any_line": len(any_line), "domains": cands}

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("unresolved", "shinpan_candidates", "by_province")},
                     ensure_ascii=False, indent=1))
    print(f"旧国不明: {report['unresolved']['count']} 藩 / 親藩候補: {len(cands)} 藩 → 詳細は {OUT / 'report.json'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    OFFLINE = a.offline
    if not a.offline:
        fetch()
    analyze()
