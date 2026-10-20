#!/usr/bin/env python3
"""Wikidata (SPARQL) → data/*.json を作る。

  python scripts/build_data.py            # 足りない生データだけ取得 → JSON を生成
  python scripts/build_data.py --offline  # 取得せず、data/raw/ にある分だけで JSON を生成

2段構成にしている理由:
  fetch  (ネットワーク): 結果を data/raw/ に保存。存在するファイルは再取得しない(節度ある取得)。
  build  (純粋な変換):   data/raw/ → data/*.json。ネット無しで何度でも再実行でき、テストしやすい。
取得し直したいときは、data/raw/ の該当ファイルを消してから再実行する。

出力: domains.json / lords.json / tenures.json / relations.json / warnings.json / meta.json

全国版(touhoku-domains から作り替え)での主な変更:
  - 「東北 / 東北外」の二択(external_domains, scope)をやめ、藩ごとに旧国(province)と地方(region)を持たせる。
    旧国は Wikidata から決め、決まらない藩は config.json の province_overrides で補う。旧国 → 地方は
    config.json の province_to_region で決める(判断が入る部分をコードに埋めないため)。
  - 人物には主たる藩(primary_domain = 最も早い在任の藩)を持たせる。「外部」かどうかは画面側で、
    表示中の範囲に対して相対的に決める(データに固定しない)。
  - 近世大名の藩主職のほかに、config.json の extra_positions(征夷大将軍)も在任として取り込む。
  - 取得のキャッシュを ID ごとにした(wdlib.cached_by_id)。人物の集合が変わっても、増えた分だけ取得する。
"""
import argparse
import datetime
import json
import sys
from collections import Counter, defaultdict

import re
import urllib.parse
from html.parser import HTMLParser

from wdlib import (COMMONS_API, DATA, RAW, ROOT, api, cached, cached_by_id, chunks, dump, parse_point, qid, sparql,
                   year)

CONFIG = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
KINSEI = CONFIG["position_class"]            # 近世大名 (Q24887524)
# 近世大名の藩主職以外に取り込む役職(征夷大将軍)。藩の代わりに domain(江戸幕府)へ結びつける。
EXTRA_POSITIONS = {e["position"]: e for e in CONFIG.get("extra_positions", [])}
PROVINCE_CLASSES = CONFIG["province_classes"]   # 旧国の P31(令制国 Q860290 と、北海道の旧国名 Q1541735)
FEMALE = "Q6581072"                          # 性別(P21) = 女性。系図には載せない方針(実父の系統だけを描く)

# ----------------------------------------------------------------------------
# fetch: SPARQL
# 列名は、最初の調査(explore_*.py)で保存した data/raw/*.json と同じにしてある。
# → 調査で取得済みのファイルをそのまま再利用でき、取得リクエストを増やさずに済む。
# ----------------------------------------------------------------------------
# 藩主職の選び方: 上位クラス(P279)が近世大名で、日本語ラベルが「〇〇藩主」のもの。
# 以前は P31 = Q114962596 も条件にしていたが、P31 の入れ方は職によってまちまちなので、ラベルで選ぶ。
# 近世大名の下位クラスには「〇〇藩主」以外(大名家の当主など)もあり得るので、ラベルの末尾で藩主職に限る。
POS_FILTER = f"""?pos wdt:P279 wd:{KINSEI} ; rdfs:label ?posJa .
  FILTER(LANG(?posJa) = "ja" && STRENDS(?posJa, "藩主"))"""

Q_POSITIONS = f"""
SELECT ?pos ?posLabel ?p279 ?domain ?domainLabel ?back ?coord WHERE {{
  {POS_FILTER}
  BIND(wd:{KINSEI} AS ?p279)
  OPTIONAL {{ ?pos wdt:P2389 ?domain .
             OPTIONAL {{ ?domain wdt:P2388 ?back }}
             OPTIONAL {{ ?domain wdt:P625 ?coord }} }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""

# 座標の取得元は P159(本拠地=城・陣屋) と P36(首都=市町村) に限る(実データで使われていたのはこの2つ)。
Q_SEATS = f"""
SELECT ?domain ?prop ?seat ?seatLabel ?coord WHERE {{
  {POS_FILTER}
  ?pos wdt:P2389 ?domain .
  VALUES ?p {{ wdt:P159 wdt:P36 }}
  ?domain ?p ?seat . ?seat wdt:P625 ?coord .
  BIND(REPLACE(STR(?p), "^.*/", "") AS ?prop)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""

# 在任は statement ノード(p:/ps:/pq:)で取る。修飾子(年・前任・後任)は声明に付いているため。
Q_P39 = f"""
SELECT ?st ?person ?personLabel ?pos ?start ?end ?prev ?next ?clan ?clanLabel WHERE {{
  {POS_FILTER}
  ?person p:P39 ?st . ?st ps:P39 ?pos .
  OPTIONAL {{ ?st pq:P580 ?start }}  OPTIONAL {{ ?st pq:P582 ?end }}
  OPTIONAL {{ ?st pq:P1365 ?prev }}  OPTIONAL {{ ?st pq:P1366 ?next }}
  OPTIONAL {{ ?person wdt:P53 ?clan }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""

Q_P1308 = f"""
SELECT ?st ?pos ?person ?ord ?start ?end WHERE {{
  {POS_FILTER}
  ?pos p:P1308 ?st . ?st ps:P1308 ?person .
  OPTIONAL {{ ?st pq:P1545 ?ord }}
  OPTIONAL {{ ?st pq:P580 ?start }}  OPTIONAL {{ ?st pq:P582 ?end }}
}}"""


def q_family(ids):
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"""
SELECT ?person ?kind ?other ?otherLabel ?rel
       (GROUP_CONCAT(DISTINCT STR(?opos); separator="|") AS ?otherPos)
       (GROUP_CONCAT(DISTINCT STR(?oclan); separator="|") AS ?otherClan) WHERE {{
  VALUES ?person {{ {vals} }}
  {{ ?person wdt:P22 ?other . BIND("P22" AS ?kind) }}
  UNION {{ ?person wdt:P40 ?other . BIND("P40" AS ?kind) }}
  UNION {{ ?person p:P1038 ?st . ?st ps:P1038 ?other . OPTIONAL {{ ?st pq:P1039 ?rel }} BIND("P1038" AS ?kind) }}
  OPTIONAL {{ ?other wdt:P39 ?opos }}
  OPTIONAL {{ ?other wdt:P53 ?oclan }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}} GROUP BY ?person ?kind ?other ?otherLabel ?rel"""


def q_parents(ids):
    """実父をたどる用。P22(本人側)と P40(父側に子として載っている)の両方から実父を拾う。
    片側しか入力されていないデータでも、つながりを落とさないため。
    P40 は母の項目にも入っているので、女性(P21)は除く。母を実父として拾うと、母方の祖先まで
    「実父の系統」としてたどってしまうため(build 側でも gender.json で同じ除外をする=二重の安全策)。"""
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"""
SELECT ?person ?father ?fatherLabel ?via WHERE {{
  VALUES ?person {{ {vals} }}
  {{ ?person wdt:P22 ?father . BIND("P22" AS ?via) }}
  UNION {{ ?father wdt:P40 ?person . FILTER NOT EXISTS {{ ?father wdt:P21 wd:{FEMALE} }} BIND("P40" AS ?via) }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""


def q_meta(ids):
    """日本語版Wikipedia記事名 (sitelink) と氏 (P53)。GROUP BY を使わず行を返し、Python側で畳む
    (ラベルサービスと集約の組み合わせは WDQS で不安定なため)。"""
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"""
SELECT ?item ?itemLabel ?title ?clan ?clanLabel WHERE {{
  VALUES ?item {{ {vals} }}
  OPTIONAL {{ ?article schema:about ?item ; schema:isPartOf <https://ja.wikipedia.org/> ; schema:name ?title }}
  OPTIONAL {{ ?item wdt:P53 ?clan }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""


def q_images(ids):
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"SELECT ?item ?img WHERE {{ VALUES ?item {{ {vals} }} ?item wdt:P18 ?img }}"


def commons_file_name(url):
    """'http://commons.wikimedia.org/wiki/Special:FilePath/Xxx%20yyy.jpg' → 'Xxx yyy.jpg'"""
    return urllib.parse.unquote(url.rsplit("/", 1)[-1]).replace("_", " ")


class _Text(HTMLParser):
    """Commons の作者欄は HTML(リンク付き)なので、プレーンテキストに直す。"""
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, d):
        self.parts.append(d)


def plain(html):
    p = _Text()
    p.feed(html or "")
    return re.sub(r"\s+", " ", "".join(p.parts)).strip()


def q_gender(ids):
    """性別(P21)。女性を系図から除くために使う。"""
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"SELECT ?item ?g WHERE {{ VALUES ?item {{ {vals} }} ?item wdt:P21 ?g }}"


def q_children(ids):
    vals = " ".join(f"wd:{i}" for i in ids)
    return f"SELECT ?parent ?child WHERE {{ VALUES ?parent {{ {vals} }} ?parent wdt:P40 ?child }}"


THUMB_WIDTH = 240   # 肖像のサムネイル幅(px)。系図・地図・詳細パネルで同じURLを使い回し、ブラウザのキャッシュを効かせる
# 実父を何世代さかのぼって取得・掲載するか(config.json の ancestor_generations)。
# 全体の系図(all.html)に出る祖先の深さと、藩別の家系図でさかのぼれる上限がこれで決まる。
ANCESTOR_GENS = int(CONFIG.get("ancestor_generations", 5))


def q_p39_extra(position):
    """extra_positions(征夷大将軍)の在任。列は Q_P39 と同じにして、build で同じように扱えるようにする。
    役職は ps:P39 に直接書く(BIND で先に ?pos を決めると、WDQS がすべての P39 声明を走査して重くなるため)。"""
    return f"""
SELECT ?st ?person ?personLabel ?pos ?start ?end ?prev ?next ?clan ?clanLabel WHERE {{
  ?person p:P39 ?st . ?st ps:P39 wd:{position} .
  BIND(wd:{position} AS ?pos)
  OPTIONAL {{ ?st pq:P580 ?start }}  OPTIONAL {{ ?st pq:P582 ?end }}
  OPTIONAL {{ ?st pq:P1365 ?prev }}  OPTIONAL {{ ?st pq:P1366 ?next }}
  OPTIONAL {{ ?person wdt:P53 ?clan }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""


def extra_row_ok(r):
    """征夷大将軍の在任のうち、config の year_from〜year_to に始まるものだけを使う(鎌倉・室町の将軍を除く)。
    開始年が無い声明は、どの時代か判断できないので使わない(build で警告に残す)。"""
    e = EXTRA_POSITIONS.get(qid(r["pos"]))
    y = year(r.get("start"))
    return bool(e) and y is not None and e.get("year_from", -9999) <= y <= e.get("year_to", 9999)


# 藩 → 旧国。3通りの経路を別々のクエリで取り、kind で区別する(調査 survey_nationwide.py と同じ経路)。
#   direct: 藩項目の文の値が旧国(実データでは P131 がほとんど。P1001・P361 もある)
#   p131:   藩項目の P131 を上にたどって旧国に届く
#   seat:   本拠地(P159、城・陣屋)の P131 を上にたどって旧国に届く。旧国が複数ある藩で「城のある国」を選ぶのに使う
# 1つのクエリに UNION でまとめると、P131 をたどる部分が重く WDQS の時間切れ(応答の途中切断)になったため分けた。
PROVINCE_PATTERNS = {
    "direct": '''?domain ?p ?prov . FILTER(STRSTARTS(STR(?p), "http://www.wikidata.org/prop/direct/"))
  BIND(REPLACE(STR(?p), "^.*/", "") AS ?prop)''',
    "p131": '''?domain wdt:P131/wdt:P131* ?prov . BIND("P131+" AS ?prop)''',
    "seat": '''?domain wdt:P159 ?seat . ?seat wdt:P131/wdt:P131* ?prov . BIND("P159/P131+" AS ?prop)''',
}


def domain_provinces(ids):
    cls = " ".join(f"wd:{c}" for c in PROVINCE_CLASSES)
    rows = []
    for kind, pattern in PROVINCE_PATTERNS.items():
        part = sparql(f"""
SELECT ?domain ?prop ?prov WHERE {{
  VALUES ?domain {{ {" ".join(f"wd:{i}" for i in ids)} }} VALUES ?c {{ {cls} }}
  {pattern}
  ?prov wdt:P31 ?c .
}}""")
        for r in part:
            r["kind"] = kind
        rows += part
    return rows


def q_coords(ids):
    """config の seat_overrides で指定した城(江戸城)などの座標とラベル。"""
    return f"""
SELECT ?item ?itemLabel ?coord WHERE {{
  VALUES ?item {{ {" ".join(f"wd:{i}" for i in ids)} }} OPTIONAL {{ ?item wdt:P625 ?coord }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""


def fetch_all():
    pos = cached("positions.json", lambda: sparql(Q_POSITIONS))
    cached("domain_seats.json", lambda: sparql(Q_SEATS))
    kinsei = {qid(r["pos"]) for r in pos if qid(r.get("p279")) == KINSEI}
    p39 = cached("p39.json", lambda: sparql(Q_P39))
    cached("p1308.json", lambda: sparql(Q_P1308))
    extra = []
    for p in EXTRA_POSITIONS:
        extra += cached(f"p39_extra_{p}.json", lambda p=p: sparql(q_p39_extra(p)))
    persons = sorted({qid(r["person"]) for r in p39 if qid(r["pos"]) in kinsei}
                     | {qid(r["person"]) for r in extra if extra_row_ok(r)})

    # 藩の旧国。旧国の一覧(ラベル)は、config に無い旧国が出てきたときに名前を出すため。
    domains = sorted({qid(r["domain"]) for r in pos if r.get("domain")})
    cached("provinces.json", lambda: sparql(f"""
SELECT DISTINCT ?prov ?provLabel ?cls WHERE {{
  VALUES ?cls {{ {" ".join(f"wd:{c}" for c in PROVINCE_CLASSES)} }} ?prov wdt:P31 ?cls .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "ja,en". }}
}}"""))
    cached_by_id("domain_provinces.json", domains, domain_provinces, 100, key="domain")
    seats = sorted({v["seat"] for v in CONFIG.get("seat_overrides", {}).values()})
    cached_by_id("seat_overrides.json", seats, lambda ch: sparql(q_coords(ch)), 200, key="item")

    # 分割の大きさ(何件ずつ問い合わせるか)は touhoku-domains と同じ。大きくすると時間切れ(応答の途中切断)になりやすい。
    # 親族(実父・子・養子関係)。人物の QID ごとにキャッシュする(cached_by_id の説明を参照)。
    fam = cached_by_id("family.json", persons, lambda ch: sparql(q_family(ch)), 60, key="person")

    # 実父を ANCESTOR_GENS 世代さかのぼる(養子は無視)。世代ごとに「まだ父を問い合わせていない人」だけを問い合わせる。
    # 問い合わせ済みかどうかは ancestors.json の done に人物ごとに控えるので、藩主が増えたときや
    # 世代数を増やしたときも、足りない分だけを取得する(touhoku-domains の ancestors_gens.json の仕組みを置き換えた)。
    anc, seen, frontier = [], set(persons), set(persons)
    for g in range(ANCESTOR_GENS):
        if not frontier:
            break
        rows = cached_by_id("ancestors.json", frontier, lambda ch: sparql(q_parents(ch)), 100, key="person")
        anc += rows
        frontier = {qid(r["father"]) for r in rows} - seen
        seen |= frontier

    fathers = sorted({qid(r["other"]) for r in fam if r["kind"] == "P22"} | {qid(r["father"]) for r in anc})
    outside = [f for f in fathers if f not in set(persons)]
    meta_ids = sorted(set(persons) | set(fathers) | set(domains) | {e["domain"] for e in EXTRA_POSITIONS.values()})
    cached_by_id("meta.json", meta_ids, lambda ch: sparql(q_meta(ch)), 80, key="item")
    cached_by_id("outside_children.json", outside, lambda ch: sparql(q_children(ch)), 60, key="parent")

    rels = sorted({qid(r["rel"]) for r in fam if r["kind"] == "P1038" and r.get("rel")})

    def labels(ch):
        ents = api(action="wbgetentities", ids="|".join(ch), props="labels|descriptions", languages="ja|en")["entities"]
        return [{"id": i,
                 "ja": ents.get(i, {}).get("labels", {}).get("ja", {}).get("value"),
                 "en": ents.get(i, {}).get("labels", {}).get("en", {}).get("value"),
                 "desc_ja": ents.get(i, {}).get("descriptions", {}).get("ja", {}).get("value")} for i in ch]
    cached_by_id("p1039_labels.json", rels, labels, 50, key="id")

    # 画像: Wikidata の P18 (画像) → Commons のファイル → ライセンス・作者(extmetadata)
    # 画像そのものは保存せず、サイトは Commons のサムネイルを直接参照する。出典・ライセンス表示のため、
    # ここで作者とライセンスを取得して JSON に残す。
    people = sorted(set(persons) | set(fathers))
    # 性別(P21): 「実父」として拾った人物に母が混ざっていないかを確かめるため(P40 は母の項目にもある)。
    cached_by_id("gender.json", people, lambda ch: sparql(q_gender(ch)), 150, key="item")
    imgs = cached_by_id("images.json", people, lambda ch: sparql(q_images(ch)), 80, key="item")
    files = sorted({commons_file_name(r["img"]) for r in imgs})

    def commons_meta(ch):
        out = []
        res = api(COMMONS_API, action="query", prop="imageinfo", iiprop="extmetadata|url|mime", iiurlwidth=THUMB_WIDTH,
                  iiextmetadatafilter="LicenseShortName|LicenseUrl|Artist|Credit|AttributionRequired|Copyrighted",
                  titles="|".join("File:" + f for f in ch))
        norm = {n["to"]: n["from"] for n in res.get("query", {}).get("normalized", [])}
        for page in res.get("query", {}).get("pages", {}).values():
            title = page.get("title", "")
            info = (page.get("imageinfo") or [{}])[0]
            md = info.get("extmetadata", {})
            g = lambda k: (md.get(k) or {}).get("value")
            name = norm.get(title, title)[len("File:"):]
            out.append({"file": name, "license": g("LicenseShortName"), "license_url": g("LicenseUrl"),
                        "artist": plain(g("Artist")), "credit": plain(g("Credit")),
                        "attribution_required": g("AttributionRequired"), "copyrighted": g("Copyrighted"),
                        "page_url": info.get("descriptionurl"), "mime": info.get("mime"), "thumb": info.get("thumburl"),
                        "missing": "missing" in page})
        return out
    cached_by_id("commons_meta.json", files, commons_meta, 40, key="file")


# ----------------------------------------------------------------------------
# build: raw → JSON
# ----------------------------------------------------------------------------
def load(name, default=None):
    """data/raw/<name> を読む。cached_by_id の形({"done": [...], "rows": [...]})なら行だけを返す。"""
    p = RAW / name
    if not p.exists():
        return default
    obj = json.loads(p.read_text(encoding="utf-8"))
    return obj["rows"] if isinstance(obj, dict) and "rows" in obj and "done" in obj else obj


def load_labels():
    """P1039 のラベル。取得は ID ごとの行(cached_by_id)なので、ここで {QID: {...}} に直す。"""
    return {r["id"]: r for r in load("p1039_labels.json", [])}


# P1039 (主題から見て P1038 の値が何にあたるか) のラベル → 役割。
# ラベル文字列で分類する理由: QID を決め打ちすると、記憶違いがそのままデータの誤りになるため。
# P1038 は「親族 (relative)」全般なので、兄弟・甥・祖父なども入っている。養親/養子に当たらないものは
# "other"(家系図には描かない)として除外し、warnings(info)に一度だけ列挙する。
# 判定を変えたいときは config.json の p1039_roles で "parent" / "child" / "other" を指定する。
PARENT_KW = ("養父", "養母", "義父", "義母", "養親", "adoptive father", "adoptive mother", "adoptive parent",
             "foster father", "foster mother")
CHILD_KW = ("養子", "養女", "婿", "養嗣子", "adopted son", "adopted daughter", "adopted child", "son-in-law",
            "foster son")


def classify_role(qid_, labels):
    forced = CONFIG["p1039_roles"].get(qid_)
    if forced:
        return forced
    lab = labels.get(qid_) or {}
    text = " ".join(filter(None, [lab.get("ja"), lab.get("en")])).lower()
    # 「養父」を先に判定: 「養子」を含む語より優先する理由は特になく、短いキーワードの誤爆を避けるため。
    if any(k in text for k in PARENT_KW):
        return "parent"
    if any(k in text for k in CHILD_KW):
        return "child"
    return "other"


def is_son_in_law(qid_, labels):
    lab = labels.get(qid_) or {}
    text = " ".join(filter(None, [lab.get("ja"), lab.get("en")])).lower()
    return "婿" in text or "son-in-law" in text


def build():
    warnings = []

    def warn(level, kind, subject, message, **extra):
        warnings.append({"level": level, "kind": kind, "subject": subject, "message": message, **extra})

    # ---------------- domains ----------------
    pos_rows = load("positions.json", [])
    pos_rows = [r for r in pos_rows if qid(r.get("p279")) == KINSEI]   # 近世大名の役職だけ(他国・他時代の役職を除く)
    pos_label, pos_domain = {}, {}
    domains = {}
    for r in pos_rows:
        p = qid(r["pos"])
        pos_label[p] = r.get("posLabel")
        d = qid(r.get("domain"))
        if not d:
            warn("warn", "position_no_domain", p, f"{pos_label[p]} に P2389(藩)がありません")
            continue
        pos_domain[p] = d
        dom = domains.setdefault(d, {"id": d, "name": r.get("domainLabel"), "positions": set(), "back": set(),
                                     "p625": None})
        dom["positions"].add(p)
        if r.get("back"):
            dom["back"].add(qid(r["back"]))
        if r.get("coord") and not dom["p625"]:
            dom["p625"] = parse_point(r["coord"])
    # 征夷大将軍(config の extra_positions)。藩ではないが、江戸幕府の項目を「藩」の代わりにして同じ形で持つ。
    # 役職と藩の相互参照(P2389/P2388)は藩主職のための仕組みなので、ここでは確かめない(back = positions)。
    for p, e in EXTRA_POSITIONS.items():
        pos_label[p] = e["name"]
        pos_domain[p] = e["domain"]
        domains[e["domain"]] = {"id": e["domain"], "name": e["domain_name"], "positions": {p}, "back": {p}, "p625": None,
                                "gen_name": e.get("gen_name")}
    for d, dom in domains.items():
        if dom["back"] != dom["positions"]:
            warn("warn", "domain_position_mismatch", d,
                 f"{dom['name']}: 役職側P2389と藩側P2388が一致しません "
                 f"(役職→藩: {sorted(dom['positions'])} / 藩→役職: {sorted(dom['back'])})",
                 positions=sorted(dom["positions"]), back=sorted(dom["back"]))
    names = Counter(dom["name"] for dom in domains.values())
    for d, dom in domains.items():
        if names[dom["name"]] > 1:
            warn("info", "domain_duplicate_name", d, f"同名の藩項目が複数あります: {dom['name']}")

    # 座標: 藩P625 → 城(P159) → 市町村(P36, 概略)
    seats = defaultdict(dict)
    for r in load("domain_seats.json", []):
        if r["prop"] not in ("P159", "P36"):
            continue
        pt = parse_point(r["coord"])
        if pt:
            seats[qid(r["domain"])][(r["prop"], qid(r["seat"]))] = (r.get("seatLabel"), pt)
    for d, dom in domains.items():
        stem = (dom["name"] or "").removesuffix("藩")
        coord = None
        if dom["p625"]:
            coord = {"lat": dom["p625"][0], "lon": dom["p625"][1], "source": "P625", "source_item": d,
                     "precision": "exact"}
        else:
            for prop, precision in (("P159", "exact"), ("P36", "approx")):
                cands = sorted((s for s in seats.get(d, {}).items() if s[0][0] == prop), key=lambda s: s[0][1])
                if not cands:
                    continue
                hit = [c for c in cands if stem and stem in (c[1][0] or "")] or cands
                if len(hit) > 1:
                    warn("info", "seat_ambiguous", d, f"{dom['name']}: 座標候補が複数あり先頭を採用 "
                         f"({', '.join(c[1][0] or c[0][1] for c in hit)})")
                (_, sid), (slabel, pt) = hit[0]
                coord = {"lat": pt[0], "lon": pt[1], "source": prop, "source_item": sid, "source_label": slabel,
                         "precision": precision}
                if precision == "approx":
                    warn("info", "coord_approx", d, f"{dom['name']}: 市町村(P36)の座標で代用した概略位置です")
                break
        if coord is None:
            warn("warn", "coord_missing", d, f"{dom['name']}: 座標を取得できません(藩P625・城P159・P36のいずれも無し)")
        else:
            coord["lat"], coord["lon"] = round(coord["lat"], 5), round(coord["lon"], 5)
        dom["coord"] = coord

    # config の seat_overrides: 藩としての所在地を持たない御三卿と江戸幕府(将軍)を、江戸城の位置に置く(ユーザーの判断)。
    # Wikidata に座標があっても上書きする。同じ城に複数を置くとマーカーが完全に重なるので、2つ目以降は約400m ずつずらし、
    # precision="seat_override" として画面でも「江戸城の位置に置いています」と示す。
    seat_rows = {qid(r["item"]): r for r in load("seat_overrides.json", [])}
    on_seat = Counter()
    for d, ov in CONFIG.get("seat_overrides", {}).items():
        dom, sr = domains.get(d), seat_rows.get(ov["seat"])
        pt = parse_point((sr or {}).get("coord"))
        if not dom or not pt:
            continue
        k = on_seat[ov["seat"]]
        on_seat[ov["seat"]] += 1
        dlat, dlon = [(0, 0), (0.004, -0.004), (-0.004, -0.004), (0.004, 0.004), (-0.004, 0.004)][k % 5]
        dom["coord"] = {"lat": round(pt[0] + dlat, 5), "lon": round(pt[1] + dlon, 5), "source": "seat_override",
                        "source_item": ov["seat"], "source_label": sr.get("itemLabel"), "precision": "seat_override"}
        warnings[:] = [w for w in warnings if not (w["kind"] in ("coord_missing", "coord_approx") and w["subject"] == d)]
        warn("info", "coord_seat_override", d, f"{dom['name']}: config.json の seat_overrides により {sr.get('itemLabel')} の位置に置いています")

    # ---------------- 旧国・地方 ----------------
    # 決め方(優先順):
    #   1. config.json の province_overrides(Wikidata から決まらない藩、旧国が複数ある藩をユーザーが確認して手で指定)
    #   2. Wikidata: 藩項目の文の値が旧国(direct) → 藩の P131 をたどって旧国(p131) → 城の P131 をたどって旧国(seat)
    #      旧国が複数あるときは「城(陣屋)のある国」を採る(ユーザーの判断)。城の P131 から国にたどれないときは、
    #      どれか1つに決める根拠が無いので先頭を仮に採り、警告に残す(config で指定してもらう)。
    #   3. どれも無ければ province = null、region = null(画面では「地方不明」)
    # 旧国 → 地方は config.json の province_to_region。表に無い旧国は region = null にして警告に残す。
    prov_label = {qid(r["prov"]): r.get("provLabel") for r in load("provinces.json", [])}
    p2r = CONFIG["province_to_region"]
    found = defaultdict(lambda: defaultdict(set))   # 藩 → kind → {旧国}
    props = defaultdict(set)
    for r in load("domain_provinces.json", []):
        found[qid(r["domain"])][r["kind"]].add(qid(r["prov"]))
        if r["kind"] == "direct":
            props[qid(r["domain"])].add(r["prop"])
    overrides = CONFIG.get("province_overrides", {})

    def prov_name(q):
        return (p2r.get(q) or {}).get("name") or prov_label.get(q) or q

    for d, dom in domains.items():
        f = found.get(d, {})
        wd = None
        for kind in ("direct", "p131", "seat"):
            if f.get(kind):
                wd = (kind, sorted(f[kind]))
                break
        chosen, source = None, None
        if d in overrides:
            chosen, source = overrides[d]["province"], "config"
            if wd and len(wd[1]) == 1:
                if wd[1][0] == chosen:
                    warn("info", "province_override_redundant", d, f"{dom['name']}: config の province_overrides と同じ旧国が"
                         f" Wikidata にもあります({prov_name(chosen)})。config の指定は外せます")
                else:
                    warn("warn", "province_override_conflict", d, f"{dom['name']}: config の province_overrides は"
                         f"{prov_name(chosen)}ですが、Wikidata では{prov_name(wd[1][0])}です(要確認)")
        elif wd:
            kind, cands = wd
            if len(cands) == 1:
                chosen, source = cands[0], "wikidata_" + kind
            else:
                at_seat = [c for c in cands if c in f.get("seat", set())]
                if len(at_seat) == 1:
                    chosen, source = at_seat[0], "wikidata_seat"
                else:
                    chosen, source = cands[0], "wikidata_" + kind
                    warn("warn", "province_multiple", d, f"{dom['name']}: 旧国が複数あり({'・'.join(map(prov_name, cands))})、"
                         f"城のある国を Wikidata から決められないため{prov_name(chosen)}を仮に採っています"
                         "(config.json の province_overrides で指定してください)")
        if chosen is None:
            warn("warn", "province_missing", d, f"{dom['name']}: 旧国を決められません(Wikidata に旧国が無く、"
                 "config.json の province_overrides にもありません)。地方不明として表示します")
        dom["province"] = {"id": chosen, "name": prov_name(chosen)} if chosen else None
        dom["province_source"] = source
        if source and source.startswith("wikidata_direct"):
            dom["province_property"] = sorted(props.get(d, ()))   # どのプロパティに入っていたか(P131 / P1001 / P361)
        region = (p2r.get(chosen) or {}).get("region") if chosen else None
        if chosen and region is None:
            warn("warn", "province_no_region", d, f"{dom['name']}: 旧国 {prov_name(chosen)} ({chosen}) が"
                 " config.json の province_to_region にありません。地方不明として表示します")
        dom["region"] = region

    # 新田藩(固有の領地・陣屋を持たない分家藩)は、本藩の陣屋の近くに仮置きする(config.json の branch_domains)。
    # 本藩と完全に同じ座標だと地図上でマーカーが重なって見えなくなるので、約1.3km ずつずらす。
    # 位置の根拠が弱いので precision="branch" とし、画面上でも「本藩の陣屋付近に仮置き」と示す。
    placed = Counter()
    for d, parent in CONFIG.get("branch_domains", {}).items():
        dom, par = domains.get(d), domains.get(parent)
        if not dom or not par or not par.get("coord") or dom.get("coord"):
            continue
        k = placed[parent]
        placed[parent] += 1
        dlat, dlon = [(0.012, 0.012), (-0.012, 0.012), (0.012, -0.012), (-0.012, -0.012)][k % 4]
        dom["coord"] = {"lat": round(par["coord"]["lat"] + dlat, 5), "lon": round(par["coord"]["lon"] + dlon, 5),
                        "source": "branch_of", "source_item": parent, "source_label": par["name"],
                        "precision": "branch"}
        warnings[:] = [w for w in warnings if not (w["kind"] == "coord_missing" and w["subject"] == d)]
        warn("info", "coord_branch", d, f"{dom['name']}: 固有の陣屋が無いため、本藩 {par['name']} の陣屋付近に仮置きしています")

    # ---------------- tenures ----------------
    p39 = [r for r in load("p39.json", []) if qid(r["pos"]) in pos_domain]
    for p in EXTRA_POSITIONS:
        rows = load(f"p39_extra_{p}.json", [])
        p39 += [r for r in rows if extra_row_ok(r)]
        nostart = {qid(r["person"]): r.get("personLabel") for r in rows if year(r.get("start")) is None}
        for person, lab in sorted(nostart.items()):
            warn("info", "extra_no_start", person, f"{lab}: {EXTRA_POSITIONS[p]['name']} の在任に開始年が無いため、"
                 "江戸時代の在任か判断できず載せていません")
    labels_of = {}                       # 人物ラベル
    for r in p39:
        labels_of[qid(r["person"])] = r.get("personLabel")

    def pair_dates(starts, ends):
        """statement ID が無い旧データ用の復元。SPARQLの行は「開始年 × 終了年」の直積になるため、
        開始年と終了年が同数なら、昇順に並べて1対1で組み直す(再任=複数の在任は時系列順なので成り立つ)。"""
        starts, ends = sorted(starts, key=lambda x: (x is None, x or 0)), sorted(ends, key=lambda x: (x is None, x or 0))
        return list(zip(starts, ends)) if len(starts) == len(ends) else [(a, b) for a in starts for b in ends]

    def collapse(rows, extra=()):
        """声明(statement)単位に畳む。新しい取得では ?st(声明ID)で一意になる。
        戻り値: {(pos, person): [{'start','end', 'prev','next','ord'}...]}"""
        out = defaultdict(list)
        if rows and "st" in rows[0]:
            g = {}
            for r in rows:
                k = (qid(r["pos"]), qid(r["person"]), r["st"])
                s = g.setdefault(k, {"start": year(r.get("start")), "end": year(r.get("end")), "prev": set(),
                                     "next": set(), "ord": None})
                if r.get("prev"):
                    s["prev"].add(qid(r["prev"]))
                if r.get("next"):
                    s["next"].add(qid(r["next"]))
                o = r.get("ord")
                if o and o.isdigit():
                    s["ord"] = int(o)
            for (p, person, _), s in g.items():
                out[(p, person)].append(s)
            return out
        tmp = defaultdict(lambda: {"starts": set(), "ends": set(), "prev": set(), "next": set(), "ord": None})
        for r in rows:
            o = r.get("ord")
            k = (qid(r["pos"]), qid(r["person"]), int(o) if o and o.isdigit() else None)
            t = tmp[k]
            t["starts"].add(year(r.get("start")))
            t["ends"].add(year(r.get("end")))
            t["ord"] = k[2]
            if r.get("prev"):
                t["prev"].add(qid(r["prev"]))
            if r.get("next"):
                t["next"].add(qid(r["next"]))
        for (p, person, _), t in tmp.items():
            for st, en in pair_dates(t["starts"], t["ends"]):
                out[(p, person)].append({"start": st, "end": en, "prev": t["prev"], "next": t["next"], "ord": t["ord"]})
        return out

    p39c = collapse(p39)
    p1308c = collapse([r for r in load("p1308.json", []) if qid(r["pos"]) in pos_domain])
    p1308 = {k: sorted(v, key=lambda x: (x["ord"] is None, x["ord"] or 0, x["start"] or 0)) for k, v in p1308c.items()}
    by_pair = {k: [(x["start"], x["end"], x) for x in v] for k, v in p39c.items()}
    tenures = []
    for (p, person), lst in by_pair.items():
        lst.sort(key=lambda x: (x[0] is None, x[0] or 0, x[1] or 0))
        ords = p1308.get((p, person), [])
        if len(lst) > 1:
            warn("info", "multiple_stints", person,
                 f"{labels_of.get(person)}: {pos_label[p]} に在任声明が{len(lst)}件(再任、または重複入力)",
                 spans=[[a, b] for a, b, _ in lst])
        if ords and len(ords) != len(lst):
            warn("info", "p1308_count_mismatch", person,
                 f"{labels_of.get(person)}: {pos_label[p]} の在任声明数が P39={len(lst)} / P1308={len(ords)} で異なります")
        for i, (st, en, s) in enumerate(lst):
            flags = []
            o = ords[i] if i < len(ords) else None
            if st is None:
                flags.append("no_start")
                warn("warn", "tenure_no_start", person, f"{labels_of.get(person)}: {pos_label[p]} の開始年がありません")
            if o and o["start"] and o["end"] and st and en and (o["start"] != st or o["end"] != en):
                flags.append("p39_p1308_mismatch")
                o_s, o_e = o["start"], o["end"]   # f-string内で同じ種類の引用符を使うと Python 3.11 以前で構文エラーになるため
                warn("warn", "p39_p1308_mismatch", person,
                     f"{labels_of.get(person)}: {pos_label[p]} の在任年が P39={st}–{en} / P1308={o_s}–{o_e} で食い違います(要文献確認)")
            tenures.append({"id": f"{p}:{person}:{st or ''}-{en or ''}", "lord": person, "domain": pos_domain[p], "position": p,
                            "start": st, "end": en, "ord": o["ord"] if o else None, "flags": flags,
                            "prev": sorted(s["prev"]), "next": sorted(s["next"])})
    # 征夷大将軍には P1308(在任者)の代数が無いので、開始年の順に 1代, 2代…と数える(江戸時代の在任に絞った後の順)。
    # Wikidata の値ではなく数えた値なので、flags に ord_by_start を付けて区別する。
    for p in EXTRA_POSITIONS:
        order = []
        for t in sorted((t for t in tenures if t["position"] == p), key=lambda t: (t["start"] or 9999, t["end"] or 9999)):
            if t["lord"] not in order:
                order.append(t["lord"])
            if t["ord"] is None:
                t["ord"] = order.index(t["lord"]) + 1
                t["flags"].append("ord_by_start")
    tenures.sort(key=lambda t: (t["domain"], t["start"] or 0, t["lord"]))
    for p in pos_label:
        if p in pos_domain and not any(t["position"] == p for t in tenures):
            warn("info", "position_no_holders", p, f"{pos_label[p]}: P39の在任者がいません"
                 + ("(P1308側には在任者あり)" if any(k[0] == p for k in p1308) else ""))

    # ---------------- family / nodes ----------------
    fam = load("family.json", [])
    # 祖先(ancestors.json)を family と同じ形の行にして足す。P22由来は「子→実父」、P40由来は「父が子を持つ」の行になる。
    for r in load("ancestors.json", []):
        if r["via"] == "P22":
            fam.append({"person": r["person"], "kind": "P22", "other": r["father"], "otherLabel": r.get("fatherLabel")})
        else:
            fam.append({"person": r["father"], "kind": "P40", "other": r["person"], "otherLabel": None,
                        "personLabel": r.get("fatherLabel")})
    lords_p39 = {t["lord"] for t in tenures}
    for r in fam:                        # 下で行を除く前にラベルを控える(警告文に名前を出すため)
        labels_of.setdefault(qid(r["other"]), r.get("otherLabel"))
        if r.get("personLabel"):
            labels_of.setdefault(qid(r["person"]), r["personLabel"])

    # ---------------- 女性は載せない(方針) ----------------
    # P40(子)は母の項目にも入っているため、何もしないと「母→子」が実父子の辺になり、母方の祖先まで
    # 実父の系統としてたどってしまう。次の3段で除く。
    #   (1) 性別(P21)が女性の人物が関わる行を、すべて除く(母・娘・養女)。
    #   (2) 子に P22(実父)があるのに、別の人物が P40 でその子を挙げている場合:
    #       その人物の性別が不明なら実父とはみなさない(P21 未入力の母の可能性が高い)。
    #       性別が分かっていて女性でない場合は、本当の食い違いなので残し、あとで警告する(multiple_fathers)。
    #   (3) 藩主から実父をさかのぼって届く人物だけをノードにする(母を除いたあとに孤立する母方の祖父などを落とす)。
    gender = defaultdict(set)
    for r in load("gender.json", []):
        gender[qid(r["item"])].add(qid(r["g"]))
    have_gender = (RAW / "gender.json").exists()
    female = {p for p, gs in gender.items() if FEMALE in gs}
    for p in sorted(female & lords_p39):
        warn("warn", "lord_female", p, f"{labels_of.get(p)}: 藩主ですが性別(P21)が女性です(藩主なので系図には残しています)")
    female -= lords_p39
    if not have_gender:
        warn("warn", "gender_missing", "-", "gender.json が未取得のため、性別による除外ができていません"
             "(build_data.py を --offline なしで一度実行すると取得します)")
    fam = [r for r in fam if qid(r["person"]) not in female and qid(r["other"]) not in female]
    p22_father = defaultdict(set)
    for r in fam:
        if r["kind"] == "P22":
            p22_father[qid(r["person"])].add(qid(r["other"]))
    kept, gender_unknown = [], Counter()
    for r in fam:
        if r["kind"] == "P40":
            par, fs = qid(r["person"]), p22_father.get(qid(r["other"]))
            if fs and par not in fs and not gender.get(par):
                gender_unknown[par] += 1
                continue
        kept.append(r)
    fam = kept
    if have_gender:
        for par, n in sorted(gender_unknown.items()):
            warn("info", "parent_gender_unknown", par,
                 f"{labels_of.get(par)}: 性別(P21)がなく、子{n}人には別に実父(P22)がいるため、実父として扱っていません(母の可能性)")
    up = defaultdict(set)                # 子 → 実父
    for r in fam:
        if r["kind"] == "P22":
            up[qid(r["person"])].add(qid(r["other"]))
        elif r["kind"] == "P40":
            up[qid(r["other"])].add(qid(r["person"]))
    # 藩主から1世代ずつ、ANCESTOR_GENS 世代まで(藩主でない祖先だけを数える。途中に藩主がいれば、そこから数え直しになる)。
    nodes, level = set(lords_p39), set(lords_p39)
    for _ in range(ANCESTOR_GENS):
        level = {par for c in level for par in up.get(c, ())} - nodes
        nodes |= level
    for r in fam:
        labels_of.setdefault(qid(r["other"]), r.get("otherLabel"))
        if r.get("personLabel"):
            labels_of.setdefault(qid(r["person"]), r["personLabel"])
    meta = defaultdict(lambda: {"title": None, "clans": {}, "label": None})
    for r in load("meta.json", []):
        m = meta[qid(r["item"])]
        m["label"] = r.get("itemLabel")
        m["title"] = m["title"] or r.get("title")
        if r.get("clan"):
            m["clans"][qid(r["clan"])] = r.get("clanLabel")
    have_meta = bool(meta)
    if not have_meta:
        # meta 未取得でも動くように、P39側の氏(P53)で代用する(Wikipedia記事名は無し)
        for r in p39:
            if r.get("clan"):
                meta[qid(r["person"])]["clans"][qid(r["clan"])] = r.get("clanLabel")
        warn("warn", "meta_missing", "-", "meta.json が未取得のため、Wikipedia記事名と実父の氏が欠けています")

    # ---------------- relations ----------------
    labels = load_labels()
    blood = defaultdict(set)             # (親, 子) → {'P22','P40'}
    adoption = {}
    unclassified = Counter()
    skipped_rel = Counter()
    for r in fam:
        person, other = qid(r["person"]), qid(r["other"])
        if r["kind"] == "P22":
            blood[(other, person)].add("P22")
        elif r["kind"] == "P40":
            if other in nodes:
                blood[(person, other)].add("P40")
        else:
            rel = qid(r.get("rel"))
            role = classify_role(rel, labels) if rel else "unknown"   # P1039 自体が無い場合だけ unknown
            if role == "other":
                skipped_rel[rel] += 1    # 兄弟・甥・祖父など。養子関係ではないので辺にしない
                continue
            if other not in nodes or person not in nodes:
                continue                 # グラフ外の人物との養子関係は描かない
            if role == "parent":
                parent, child = other, person
            elif role == "child":
                parent, child = person, other
            else:
                parent, child = person, other
            typ = "adoption_unknown" if role == "unknown" else ("son_in_law" if is_son_in_law(rel, labels) else "adoption")
            # 同じ(親,子)を双方の項目が記述する(養親/養子)ので、1本に統合する。
            # 種類が食い違うときは 婿養子 > 養子 > 不明 の優先順位で、情報の多いほうを残す。
            rank = {"son_in_law": 2, "adoption": 1, "adoption_unknown": 0}
            key = (parent, child)
            if key not in adoption or rank[typ] > rank[adoption[key]["type"]]:
                adoption[key] = {"id": f"{typ}:{parent}:{child}", "source": parent, "target": child, "type": typ,
                                 "rel": rel, "rel_label": (labels.get(rel) or {}).get("ja")}
            if role == "unknown":
                unclassified[person] += 1
    for rel, n in skipped_rel.items():
        warn("info", "p1039_skipped", rel or "-",
             f"P1038の関係 {rel}({(labels.get(rel) or {}).get('ja')}) {n}件は養子関係ではないため辺にしていません"
             "(養子関係として扱うなら config.json の p1039_roles で指定)")
    for person, n in unclassified.items():
        warn("warn", "p1039_missing", person, f"{labels_of.get(person)}: P1038 に P1039(関係)がなく、向きを判定できません")
    outside_children = defaultdict(set)
    have_outside = (RAW / "outside_children.json").exists()
    for r in load("outside_children.json", []):
        outside_children[qid(r["parent"])].add(qid(r["child"]))
    relations = []
    for (parent, child), src in sorted(blood.items()):
        if parent not in nodes or child not in nodes:
            continue
        flags = []
        if src == {"P40"}:
            flags.append("p40_only")
            # 子が藩主(P22を取得済み)の場合だけ「P22が無い」と言える。子が実父として載っただけの人物は
            # P22 を取得していないので、判定できない(誤警告になる)。
            if child in lords_p39:
                warn("warn", "p40_without_p22", child,
                     f"{labels_of.get(parent)} の子として P40 にありますが、{labels_of.get(child)} 側に P22 がありません")
        elif src == {"P22"} and parent in lords_p39:
            flags.append("p22_only")
            warn("warn", "p22_without_p40", parent, f"{labels_of.get(child)} の実父が {labels_of.get(parent)} ですが、父側に P40 がありません")
        elif src == {"P22"} and have_outside and child not in outside_children.get(parent, set()):
            flags.append("p22_only")
            warn("info", "p22_without_p40", parent, f"{labels_of.get(child)} の実父 {labels_of.get(parent)} 側に P40 がありません")
        relations.append({"id": f"blood:{parent}:{child}", "source": parent, "target": child, "type": "blood",
                          "flags": flags})
    # 実父子の循環(A の父が B、B の父が A など)は Wikidata 側の誤りで、どちらが正しいか判断できない。
    # 階層レイアウト(dagre)は循環を扱えないので、循環をつくる線はすべて描かず、関わる人物を警告に残す(隠さない方針)。
    kids = defaultdict(list)
    for e in relations:
        kids[e["source"]].append(e["target"])
    color, cyc_edges = {}, set()

    def visit(u, stack):
        color[u] = 1
        stack.append(u)
        for v in kids.get(u, ()):
            if color.get(v) == 1:
                path = stack[stack.index(v):] + [v]
                cyc_edges.update(zip(path, path[1:]))
            elif v not in color:
                visit(v, stack)
        stack.pop()
        color[u] = 2
    sys.setrecursionlimit(max(10000, sys.getrecursionlimit()))
    for u in sorted(kids):
        if u not in color:
            visit(u, [])
    if cyc_edges:
        relations = [e for e in relations if (e["source"], e["target"]) not in cyc_edges]
        for a in sorted({x for ed in cyc_edges for x in ed}):
            warn("warn", "father_cycle", a, f"{labels_of.get(a)}: 実父(P22/P40)が循環しています("
                 + "、".join(f"{labels_of.get(x)}→{labels_of.get(y)}" for x, y in sorted(cyc_edges) if a in (x, y))
                 + ")。Wikidata 側の誤りと考えられるため、この線は描いていません")
    blood_parents = defaultdict(list)
    for e in relations:
        blood_parents[e["target"]].append(e["source"])
    for child, ps in sorted(blood_parents.items()):
        if len(ps) > 1:                  # 実父は1人のはず。2人以上は Wikidata 側の食い違い(または性別未入力の母)
            warn("warn", "multiple_fathers", child,
                 f"{labels_of.get(child)}: 実父が複数あります({'、'.join(str(labels_of.get(x)) for x in sorted(ps))})")
    # 養子関係の辺を出力に含めるか(config.json の include_adoption)。false のあいだは実父子の辺だけを出す。
    # 判定そのもの(adoption)は続ける: 「養子は実父の氏を継がない」という氏の推定で使うため。
    include_adoption = CONFIG.get("include_adoption", True)
    if include_adoption:
        relations += sorted(adoption.values(), key=lambda e: e["id"])
    skipped_total = dict(skipped_rel)
    for e in relations:
        e.setdefault("flags", [])
    adoptees = {e["target"] for e in adoption.values() if e["type"] in ("adoption", "son_in_law")}

    # ---------------- lords (氏: Wikidata → 名前推定 → 実父から継承) ----------------
    clan_names = {}
    for p in nodes:
        for c, lab in meta[p]["clans"].items():
            clan_names[c] = lab
    stem_of = {c: (lab or "").removesuffix("氏").removesuffix("家") for c, lab in clan_names.items()}
    by_stem = defaultdict(Counter)
    for p in nodes:
        for c in meta[p]["clans"]:
            by_stem[stem_of[c]][c] += 1
    stems = sorted((s for s in by_stem if s), key=lambda s: -len(s))

    def infer_by_name(name, exclude=None):
        """名前の先頭が既知の氏の語幹と一致すれば、その氏を返す(最長一致)。
        exclude: 自己採点用。その人物自身が与えた氏の情報は除いて判定する(leave-one-out)。"""
        own = Counter(list(meta[exclude]["clans"])) if exclude else Counter()
        for s in stems:
            cnt = by_stem[s] - own
            if cnt and (name or "").startswith(s):
                return cnt.most_common(1)[0][0]
        return None

    # 推定の精度を、氏が Wikidata にある人物で自己採点する。
    # 自分自身が根拠になる「カンニング」を避けるため、leave-one-out で評価する。
    known = [(p, set(meta[p]["clans"])) for p in nodes if meta[p]["clans"]]
    hit = sum(1 for p, cs in known if infer_by_name(labels_of.get(p), exclude=p) in cs)
    infer_stats = {"evaluated": len(known), "correct": hit}

    father_of = {}
    for (parent, child), _ in blood.items():
        father_of.setdefault(child, parent)
    # 画像: P18 にある画像は、肖像かどうかを問わず使う(像・墓・旗なども可、という方針)。
    # 条件はライセンスだけ: 「再利用可」と確認できるものを display=True にする(config の image_license_prefixes)。
    # それ以外(不明・非自由)は、画像は出さずに Commons のファイルページへのリンクだけ残す。
    # 個別に出したくない画像は、config.json の image_exclude に人物のQIDを書く。
    cm = {r["file"]: r for r in load("commons_meta.json", [])}
    prefixes = tuple(x.lower() for x in CONFIG.get("image_license_prefixes", []))
    exclude = set(CONFIG.get("image_exclude", []))
    image_of = {}
    for r in load("images.json", []):
        person, fname = qid(r["item"]), commons_file_name(r["img"])
        m = cm.get(fname)
        if not m or m.get("missing"):
            continue
        lic = (m.get("license") or "")
        licensed = bool(lic) and lic.lower().startswith(prefixes) and (m.get("mime") or "").startswith("image/")
        ok = licensed and person not in exclude
        image_of[person] = {"file": fname, "page_url": m.get("page_url"), "license": lic or None,
                            "license_url": m.get("license_url"), "author": m.get("artist") or m.get("credit") or None,
                            "display": ok, "thumb": m.get("thumb")}
        if person not in nodes:
            continue                     # 系図に載せない人物(女性など)の画像については警告しない
        if not licensed:
            warn("info", "image_license_unclear", person,
                 f"{labels_of.get(person)}: 画像 {fname} はライセンスを確認できないため、画像を表示せずリンクのみにしています")
        elif not ok:
            warn("info", "image_excluded", person,
                 f"{labels_of.get(person)}: 画像 {fname} は config.json の image_exclude により表示していません")

    lords = {}
    tenure_by_lord = defaultdict(list)
    for t in tenures:
        tenure_by_lord[t["lord"]].append(t)
    for p in sorted(nodes):
        clans = [{"id": c, "name": lab} for c, lab in meta[p]["clans"].items()]
        source = "wikidata" if clans else None
        if not clans:
            c = infer_by_name(labels_of.get(p))
            if c:
                clans, source = [{"id": c, "name": clan_names[c]}], "inferred_name"
        if not clans and p not in adoptees and father_of.get(p):
            fc = meta[father_of[p]]["clans"]
            if fc:
                clans, source = [{"id": c, "name": lab} for c, lab in fc.items()], "inherited_father"
        ts = sorted(tenure_by_lord.get(p, []), key=lambda t: (t["start"] or 9999, t["ord"] or 0))

        def gname(t):
            dom = domains[t["domain"]]
            return dom.get("gen_name") or dom["name"]
        gen = "・".join(f"{gname(t)}{t['ord']}代" if t["ord"] else gname(t) for t in ts if t["domain"] in domains)
        # 主たる藩: 最も早い在任の藩(開始年が同じなら代数の小さい方)。色分けと、全体系図でどのブロックに置くかの基準。
        # touhoku-domains では「東北の藩を優先」していたが、全国版では地域を優先しない(どこを表示するかは画面側で決める)。
        primary = next((t["domain"] for t in ts if t["domain"] in domains), None)
        lords[p] = {"id": p, "name": labels_of.get(p) or meta[p]["label"] or p, "wikipedia": meta[p]["title"],
                    "primary_domain": primary, "has_tenure": bool(ts),
                    "gen_label": gen, "clans": clans, "clan_source": source, "flags": []}
        lords[p]["image"] = image_of.get(p)
        if source in ("inferred_name", "inherited_father"):
            lords[p]["flags"].append("clan_" + source)
        if not clans:
            lords[p]["flags"].append("clan_missing")
        if not father_of.get(p) and p in lords_p39:
            lords[p]["flags"].append("no_father")
            warn("warn", "lord_no_father", p, f"{lords[p]['name']}: 実父(P22)がありません")
        if have_meta and not meta[p]["title"]:
            lords[p]["flags"].append("no_wikipedia")
    for d, dom in domains.items():
        dom.pop("gen_name", None)
        dom["positions"], dom["back"] = sorted(dom["positions"]), sorted(dom["back"])
        dom["wikipedia"] = meta[d]["title"] if have_meta else None
        dom.pop("p625")
        ts = [t for t in tenures if t["domain"] == d]
        dom["first_year"] = min((t["start"] for t in ts if t["start"]), default=None)
        dom["last_year"] = max((t["end"] for t in ts if t["end"]), default=None)

    nclan = Counter(l["clan_source"] or "none" for l in lords.values())
    # 地方別の藩数・藩主数(index.html に載せる数字)。藩主は「その地方の藩に在任したことがある人」で数えるので、
    # 転封で複数の地方に在任した人は、それぞれの地方に数える(地方の合計は全体の人数より多くなる)。
    regions = CONFIG["regions"] + [None]
    by_region = {}
    for r in regions:
        ds = {d for d, dom in domains.items() if dom["region"] == r}
        by_region[r or "unknown"] = {"domains": len(ds), "lords": len({t["lord"] for t in tenures if t["domain"] in ds}),
                                     "tenures": sum(1 for t in tenures if t["domain"] in ds)}
    dump("domains.json", sorted(domains.values(), key=lambda d: d["id"]))
    dump("lords.json", sorted(lords.values(), key=lambda l: l["id"]))
    dump("tenures.json", tenures)
    dump("relations.json", sorted(relations, key=lambda e: e["id"]))
    warnings.sort(key=lambda w: ({"error": 0, "warn": 1, "info": 2}[w["level"]], w["kind"], w["subject"]))
    dump("warnings.json", warnings)
    dump("meta.json", {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "source": "Wikidata (CC0). 日本語版Wikipediaへのリンクを出典として残す",
        "counts": {"domains": len(domains), "lords": len(lords), "tenures": len(tenures), "relations": len(relations),
                   "rulers": len({t["lord"] for t in tenures}),
                   "warnings": dict(Counter(w["level"] for w in warnings))},
        "regions": CONFIG["regions"], "by_region": by_region,
        "province_source": dict(Counter(dom["province_source"] or "none" for dom in domains.values())),
        "clan_source": dict(nclan), "clan_inference_selfcheck": infer_stats,
        "p1038_skipped_non_adoption": skipped_total,
        "p1039_roles": {q: {"label": (labels.get(q) or {}).get("ja"), "role": classify_role(q, labels)} for q in labels},
        "fetched": {"meta": have_meta, "outside_children": have_outside, "gender": have_gender},
        "excluded": {"female": len(female), "parent_gender_unknown": len(gender_unknown),
                     "adoption_edges": 0 if include_adoption else len(adoption)},
        "include_adoption": include_adoption,
        "ancestor_generations": ANCESTOR_GENS,
    })
    print(f"domains={len(domains)} lords={len(lords)} tenures={len(tenures)} relations={len(relations)}")
    print("氏の出所:", dict(nclan), "/ 名前推定の自己採点:", infer_stats)
    print("地方別:", {k: v["domains"] for k, v in by_region.items()})
    print("警告:", dict(Counter(w["level"] for w in warnings)))
    for q, v in sorted(labels.items()):
        print("  P1039", q, v.get("ja"), "→", classify_role(q, labels))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="取得せず data/raw/ の既存分だけで生成")
    a = ap.parse_args()
    if not a.offline:
        fetch_all()
    build()
