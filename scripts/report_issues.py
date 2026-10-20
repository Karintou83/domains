"""Wikidata 側で直すとよい点の一覧(docs/wikidata_issues.md)を、data/*.json から作る。

build_data.py がデータを作るたびに呼ぶ(単独でも `python scripts/report_issues.py` で作り直せる)。
手書きの一覧は、データを取り直すたびに古くなるため、warnings.json から機械的に作る。
"""
import json
from collections import defaultdict

from wdlib import DATA, RAW, ROOT

# 載せる警告の種類と見出し。上から順に並べる(Wikidata を直すときに効果の大きいものを先に)。
# ここに無い種類は「その他」にまとめる。info のうち、直す必要の薄いもの(概略位置で代用した、など)は IGNORE で外す。
SECTIONS = [
    ("province_missing", "旧国が決まらない(地方不明として表示)",
     "藩の項目に所在地(P131)の令制国か郡を入れる、または本部所在地(P159)の城・陣屋に所在地を入れると決まります。"
     "郡は config.json の district_to_province でも補えます。"),
    ("province_district_unlisted", "旧国の対応表に無い所在地",
     "config.json の district_to_province に、この所在地(郡など)の旧国を指定すると、挙げた藩を地方に振り分けられます。"),
    ("province_multiple", "旧国が複数あり、城のある国を決められない",
     "本部所在地(P159)の城・陣屋の所在地(P131)をたどって国に届くようにするか、config.json の province_overrides で指定します。"),
    ("coord_missing", "座標が無く地図に出ない",
     "本部所在地(P159)に城・陣屋を入れ、その項目に座標(P625)を入れるのが確実です。"
     "所在地(P131)が令制国だけの藩は、国の中心では粗すぎるため座標に使っていません。"),
    ("multiple_fathers", "実父が2人以上いる",
     "子の P22 か、父の項目の P40 のどちらかが誤りです(P40 で拾った人物が母の場合もあります)。"),
    ("lord_no_father", "藩主に実父(P22)が無い",
     "実父が分かれば P22 を入れると、家系図でほかの藩主とつながることがあります。"),
    ("p40_without_p22", "父の P40 にあるが、子の側に P22 が無い", ""),
    ("p22_without_p40", "子の P22 にあるが、父の側に P40 が無い", ""),
    ("p1039_missing", "親族(P1038)に関係(P1039)が無く、向きが分からない", ""),
    ("p1039_unlisted", "養子関係らしいが、扱っていない関係(P1039)",
     "向きが分かる関係なら config.json の p1039_roles に追加します。"),
    ("tenure_no_start", "在任(P39)に開始年(P580)が無い", ""),
    ("extra_no_start", "征夷大将軍の在任に開始年が無い", ""),
    ("p39_p1308_mismatch", "在任の年が P39 と P1308 で食い違う", ""),
    ("p1308_count_mismatch", "P39 と P1308 で在任の数が違う", ""),
    ("domain_position_mismatch", "役職の P2389 と藩の P2388 が一致しない", ""),
    ("lord_female", "藩主の性別(P21)が女性", ""),
    ("parent_gender_unknown", "性別(P21)が無い(母の可能性)", ""),
    ("domain_duplicate_name", "同名の藩項目が複数", ""),
    ("image_license_unclear", "肖像のライセンスを確認できない", ""),
]
# 行ごとの文が同じ説明の繰り返しになる種類。行には「今の所在地」だけを載せる
BRIEF = {"coord_missing", "province_missing"}
IGNORE = {"coord_approx", "coord_seat_override", "coord_branch", "p1039_skipped", "multiple_stints", "seat_ambiguous",
          "position_no_holders", "province_override_redundant"}


def link(q, label=None):
    if not q or not str(q).startswith("Q"):
        return label or str(q)
    return f"[{label or q}](https://www.wikidata.org/wiki/{q}) ({q})"


def main():
    load = lambda name: json.loads((DATA / name).read_text(encoding="utf-8"))
    warnings, meta = load("warnings.json"), load("meta.json")
    names = {d["id"]: d["name"] for d in load("domains.json")}
    names.update({l["id"]: l["name"] for l in load("lords.json")})
    # 座標の無い藩に「今入っている所在地」を添えるため(取得していなければ添えない)
    locs = defaultdict(list)
    p = RAW / "domain_locations.json"
    if p.exists():
        for r in json.loads(p.read_text(encoding="utf-8"))["rows"]:
            locs[r["domain"].rsplit("/", 1)[-1]].append(r.get("locLabel") or r["loc"].rsplit("/", 1)[-1])

    by_kind = defaultdict(list)
    for w in warnings:
        if w["kind"] not in IGNORE:
            by_kind[w["kind"]].append(w)
    known = {k for k, _, _ in SECTIONS}
    out = ["# Wikidata 側で直すとよい点の一覧", "",
           f"このファイルは `scripts/report_issues.py` が `data/warnings.json` から自動で作ります(手で直さない)。"
           f"データ生成: {meta['generated_at'][:10]}。リンクは Wikidata の項目です。",
           "Wikidata を直したあと、生データ(`data/raw/`)を消して `python scripts/build_data.py` を実行すると反映されます。", ""]
    toc = []
    body = []
    for kind, title, hint in SECTIONS + [("_other", "その他", "")]:
        ws = by_kind.get(kind, []) if kind != "_other" else [w for k, v in by_kind.items() if k not in known for w in v]
        if not ws:
            continue
        toc.append(f"- {title}({len(ws)}件)")
        body += [f"## {title}({len(ws)}件)", ""]
        if hint:
            body += [hint, ""]
        for w in sorted(ws, key=lambda w: (names.get(w["subject"]) or w["subject"])):
            name = names.get(w["subject"])
            msg = w["message"]
            if name and msg.startswith(name + ": "):
                msg = msg[len(name) + 2:]   # 行の先頭のリンクと名前が重なるので外す
            if kind in BRIEF:               # 説明は見出しの下に1回だけ書く。行には、今入っている所在地だけを添える
                msg = f"今の所在地 P131: {'・'.join(locs[w['subject']])}" if locs.get(w["subject"]) else "所在地 P131 なし"
            body.append(f"- {link(w['subject'], name)}: {msg}")
        body.append("")
    out += ["## 目次", ""] + toc + [""] + body
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "wikidata_issues.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main()
