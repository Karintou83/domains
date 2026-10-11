"""Wikidata 取得まわりの共通部品。build_data.py / validate.py から使う。

ここに共通化する理由: SPARQL のリトライ・User-Agent・キャッシュの規約を1か所に集めておくと、
「節度あるリクエスト数」というルールを全スクリプトで同じように守れるため。
"""
import http.client
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"

ENDPOINT = "https://query.wikidata.org/sparql"
API = "https://www.wikidata.org/w/api.php"
# 連絡先は GitHub の URL のみ。公開リポジトリに個人のメールアドレスを残さないため。
UA = "domains/0.1 (https://github.com/Karintou83/domains; Wikidata editor tool)"


def qid(uri):
    """'http://www.wikidata.org/entity/Q123' → 'Q123'。None はそのまま None。"""
    return uri.rsplit("/", 1)[-1] if uri else None


def year(s):
    """'1607-01-01T00:00:00Z' → 1607。年のみの精度なので月日は捨てる。"""
    m = re.match(r"^(-?\d{1,4})-", s or "")
    return int(m.group(1)) if m else None


def parse_point(s):
    """WKT 'Point(経度 緯度)' → (緯度, 経度)。WKT は lon, lat の順なので入れ替える。"""
    m = re.match(r"^Point\((-?[\d.]+) (-?[\d.]+)\)$", s or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


def chunks(seq, n):
    seq = list(seq)
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


# Wikimedia は WDQS の障害対応などで「1分に1回」のような強い制限をかけることがある(429 と Retry-After で知らせる)。
# 制限は回避せずに守る: 429 を一度受けたら、以後の SPARQL の間隔を LIMITED_PAUSE に延ばし、取り直しも1分以上空ける。
# 全国版は問い合わせが東北版の数倍になるため、この待ち方を入れた(touhoku-domains では 4 回で諦めていた)。
LIMITED_PAUSE = 65
_limited = [False]


def _get(url, timeout=120):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(20):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except (http.client.IncompleteRead, ConnectionError, TimeoutError) as e:
            # WDQS はクエリが時間切れになると、200 を返したあとで応答の途中で接続を切ることがある(IncompleteRead)。
            # 回線の一時的な切断も同じ扱いにして、少し待って取り直す。何度も続くなら、クエリの分割を細かくする。
            wait = (5, 20, 60, 120)[min(attempt, 3)]
            print(f"  {type(e).__name__}(応答が途中で切れました): {wait}秒待ってリトライ", flush=True)
            time.sleep(wait)
            continue
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504):
                raise
            wait = (5, 20, 60, 120)[min(attempt, 3)]
            if e.code == 429:
                # サーバーが Retry-After で示した秒数を守る(最低70秒、長すぎる値は20分で打ち切って取り直す)。
                _limited[0] = True
                try:
                    wait = min(max(70, int(e.headers.get("Retry-After") or 0)), 1200)
                except ValueError:
                    wait = 70
            print(f"  HTTP {e.code}: {wait}秒待ってリトライ", flush=True)
            time.sleep(wait)
        except urllib.error.URLError as e:
            # HTTP の応答が無い接続の失敗(名前解決・接続拒否など)。一時的なことが多いので取り直す。
            wait = (5, 20, 60, 120)[min(attempt, 3)]
            print(f"  接続エラー({e.reason}): {wait}秒待ってリトライ", flush=True)
            time.sleep(wait)
    raise RuntimeError("リトライ上限に達しました: " + url[:120])


def sparql(query, pause=3):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
    rows = _get(url)["results"]["bindings"]
    time.sleep(LIMITED_PAUSE if _limited[0] else pause)  # 連続リクエストを避ける
    return [{k: v["value"] for k, v in row.items()} for row in rows]


COMMONS_API = "https://commons.wikimedia.org/w/api.php"


def api(_endpoint=None, **params):
    """MediaWiki API (既定は Wikidata)。Commons を呼ぶときは _endpoint=COMMONS_API を渡す。"""
    params["format"] = "json"
    return _get((_endpoint or API) + "?" + urllib.parse.urlencode(params), timeout=60)


def cached(name, producer):
    """data/raw/<name> があればそれを使い、無ければ producer() で取得して保存する。
    取得し直したいときは、そのファイルを消す。"""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    rows = producer()
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[fetch] {name}: {len(rows) if hasattr(rows, '__len__') else ''}")
    return rows


def cached_by_id(name, ids, fetch, size, key):
    """ID(QID やファイル名)ごとに取得済みかを控えるキャッシュ。data/raw/<name> に
    {"done": [取得済みのID], "rows": [行]} を保存し、まだ取得していない ID だけを size 件ずつ fetch(ids) で取りに行く。

    cached() との違い: 人物や藩の集合が変わっても、増えた分だけを取りに行く(既存分は取り直さない)。
    touhoku-domains の family_chunks/ は「人物リストの何番目の塊か」をキーにしていたため、人物が1人増えると
    以降の塊がずれて、別人の結果を読んでしまう問題があった。ID そのものをキーにすれば、ずれは起きない。
    行が無かった ID(例: 実父の登録が無い人物)も done に入るので、毎回問い合わせ直すことはない。
    key: 行のどの列がその ID か(例: "person")。返すのは今回の ids に当たる行だけにする
    (人物の集合が減ったとき、もう対象でない人物の行が混ざって余計な線ができないように)。
    取得し直したいときは、ファイルを消す。"""
    RAW.mkdir(parents=True, exist_ok=True)
    path = RAW / name
    store = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"done": [], "rows": []}
    done = set(store["done"])
    todo = sorted(set(ids) - done)
    for ch in chunks(todo, size):
        store["rows"] += fetch(ch)
        done |= set(ch)
        store["done"] = sorted(done)
        # 塊ごとに保存する: 取得が途中で止まっても(制限・回線断)、次回は続きから再開できる。
        path.write_text(json.dumps(store, ensure_ascii=False, indent=1), encoding="utf-8")
    if todo:
        print(f"[fetch] {name}: +{len(todo)} 件(計 {len(done)} 件、{len(store['rows'])} 行)", flush=True)
    want = set(ids)
    return [r for r in store["rows"] if _key_id(r.get(key)) in want]


def _key_id(v):
    """行の値(URI またはそのままの ID)を、ids と比べられる形にそろえる。"""
    return v.rsplit("/", 1)[-1] if v and v.startswith("http://www.wikidata.org/entity/") else v


def dump(name, obj):
    DATA.mkdir(parents=True, exist_ok=True)
    # 並び順を固定し、indent を付ける: git の差分が小さく、レビューしやすい。
    (DATA / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
