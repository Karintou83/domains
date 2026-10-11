# Wikidata 側の食い違い・欠落の一覧

生成元: data/warnings.json(build_data.py)と validate.py の注意。リンクは Wikidata の項目。
2026-10-11 取得のデータ時点の一覧(Wikidata を直したあと `python scripts/build_data.py` を、該当する生データを消してから実行すると反映される)。

## 実父が2人以上いる(13件)

P22(子の側)か P40(父の側)のどちらかが誤り。P40 で拾った人物が母(性別 P21 未入力)の場合もある。

- [松平親清 (大給松平家)](https://www.wikidata.org/wiki/Q108056290) (Q108056290): [松平乗正](https://www.wikidata.org/wiki/Q106313638) (Q106313638)、[松平乗元](https://www.wikidata.org/wiki/Q10729465) (Q10729465)
- [戸田宗光](https://www.wikidata.org/wiki/Q10862100) (Q10862100): [戸田綱光](https://www.wikidata.org/wiki/Q110284102) (Q110284102)、[戸田実光](https://www.wikidata.org/wiki/Q110284147) (Q110284147)、[正親町三条実興](https://www.wikidata.org/wiki/Q11545674) (Q11545674)
- [林政秀](https://www.wikidata.org/wiki/Q110249784) (Q110249784): [林通政 (織田信長の家臣)](https://www.wikidata.org/wiki/Q11107033) (Q11107033)、[林通政 (駿河守)](https://www.wikidata.org/wiki/Q20042364) (Q20042364)
- [松平信光](https://www.wikidata.org/wiki/Q11239114) (Q11239114): [松平泰親](https://www.wikidata.org/wiki/Q11239151) (Q11239151)、[松平親氏](https://www.wikidata.org/wiki/Q11239169) (Q11239169)
- [奥平昌邁](https://www.wikidata.org/wiki/Q11445780) (Q11445780): [伊達宗敦](https://www.wikidata.org/wiki/Q7224597) (Q7224597)、[伊達宗城](https://www.wikidata.org/wiki/Q862949) (Q862949)
- [秋月種春](https://www.wikidata.org/wiki/Q11595122) (Q11595122): [忠宥](https://www.wikidata.org/wiki/Q108957773) (Q108957773)、[秋月種貞](https://www.wikidata.org/wiki/Q11595127) (Q11595127)
- [菅沼定則](https://www.wikidata.org/wiki/Q11619293) (Q11619293): [菅沼定忠 (菅沼定信の子)](https://www.wikidata.org/wiki/Q106680492) (Q106680492)、[菅沼定成 (菅沼定忠の子)](https://www.wikidata.org/wiki/Q106680510) (Q106680510)
- [黒田職隆](https://www.wikidata.org/wiki/Q11678682) (Q11678682): [黒田重隆](https://www.wikidata.org/wiki/Q11678698) (Q11678698)、[小寺則職](https://www.wikidata.org/wiki/Q17216220) (Q17216220)
- [水野忠政](https://www.wikidata.org/wiki/Q1188498) (Q1188498): [水野賢勝](https://www.wikidata.org/wiki/Q106680073) (Q106680073)、[水野清忠](https://www.wikidata.org/wiki/Q106680332) (Q106680332)
- [得川親季](https://www.wikidata.org/wiki/Q22130053) (Q22130053): [新田義宗](https://www.wikidata.org/wiki/Q3342232) (Q3342232)、[世良田政義](https://www.wikidata.org/wiki/Q60989729) (Q60989729)
- [德川家達](https://www.wikidata.org/wiki/Q672741) (Q672741): [徳川家茂](https://www.wikidata.org/wiki/Q348466) (Q348466)、[徳川慶頼](https://www.wikidata.org/wiki/Q7813724) (Q7813724)
- [内藤信成](https://www.wikidata.org/wiki/Q6959828) (Q6959828): [松平広忠](https://www.wikidata.org/wiki/Q1064935) (Q1064935)、[嶋田景信](https://www.wikidata.org/wiki/Q108453479) (Q108453479)
- [松平頼純](https://www.wikidata.org/wiki/Q6993673) (Q6993673): [徳川頼宣](https://www.wikidata.org/wiki/Q1045763) (Q1045763)、[father of 松平頼純](https://www.wikidata.org/wiki/Q141640638) (Q141640638)

## 藩主に実父(P22)がない(5件)

- [久世広明](https://www.wikidata.org/wiki/Q10859999) (Q10859999): 実父(P22)がありません
- [小笠原吉次](https://www.wikidata.org/wiki/Q10860025) (Q10860025): 実父(P22)がありません
- [牧野成春](https://www.wikidata.org/wiki/Q10860114) (Q10860114): 実父(P22)がありません
- [増山正同](https://www.wikidata.org/wiki/Q11429189) (Q11429189): 実父(P22)がありません
- [徳永寿昌](https://www.wikidata.org/wiki/Q11490349) (Q11490349): 実父(P22)がありません

## 父の P40 にあるが、子の側に P22 がない(2件)

- [奥平昌邁](https://www.wikidata.org/wiki/Q11445780) (Q11445780): 伊達宗敦 の子として P40 にありますが、奥平昌邁 側に P22 がありません
- [德川家達](https://www.wikidata.org/wiki/Q672741) (Q672741): 徳川家茂 の子として P40 にありますが、德川家達 側に P22 がありません

## 子の P22 にあるが、父の側に P40 がない(2件)

- [康雄 松平](https://www.wikidata.org/wiki/Q141640432) (Q141640432): 松平康納 の実父 康雄 松平 側に P40 がありません
- [father of 松平頼純](https://www.wikidata.org/wiki/Q141640638) (Q141640638): 松平頼純 の実父 father of 松平頼純 側に P40 がありません

## P1038(親族)に P1039(関係の種類)がない(3件)

- [徳川秀忠](https://www.wikidata.org/wiki/Q314464) (Q314464): P1038 に P1039(関係)がなく、向きを判定できません
- [徳川家継](https://www.wikidata.org/wiki/Q366722) (Q366722): P1038 に P1039(関係)がなく、向きを判定できません
- [鍋島直興](https://www.wikidata.org/wiki/Q6956822) (Q6956822): P1038 に P1039(関係)がなく、向きを判定できません

## 在任(P39)に開始年(P580)がない(1件)

- [松前慶広](https://www.wikidata.org/wiki/Q844035) (Q844035): 松前藩主 の開始年がありません

## 征夷大将軍(P39)の在任に開始年がない(3件)

徳川宗家・足利将軍家は「家」の項目に P39 が付いている(人物ではない)。懐良親王は南北朝期の人物で、開始年が無いだけ。どれも江戸時代の在任ではないので、全国版には載せておらず、直さなくても表示には影響しない。

- [徳川宗家](https://www.wikidata.org/wiki/Q11071640) (Q11071640): 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません
- [懐良親王](https://www.wikidata.org/wiki/Q11074321) (Q11074321): 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません
- [足利将軍家](https://www.wikidata.org/wiki/Q28692536) (Q28692536): 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません

## 役職の P2389 と藩の P2388 が一致しない(1件)

- [小城藩](https://www.wikidata.org/wiki/Q3034399) (Q3034399): 役職側P2389と藩側P2388が一致しません (役職→藩: ['Q141529979'] / 藩→役職: [])

## P39 と P1308 で在任の数が違う(13件)

- [松平勝成](https://www.wikidata.org/wiki/Q10729337) (Q10729337): 伊予松山藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平定昭](https://www.wikidata.org/wiki/Q10729366) (Q10729366): 伊予松山藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平康福](https://www.wikidata.org/wiki/Q10791086) (Q10791086): 浜田藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [久世重之](https://www.wikidata.org/wiki/Q10860008) (Q10860008): 関宿藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平忠弘](https://www.wikidata.org/wiki/Q11239138) (Q11239138): 山形藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平武元](https://www.wikidata.org/wiki/Q11239141) (Q11239141): 館林藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [徳川慶喜](https://www.wikidata.org/wiki/Q287657) (Q287657): 一橋徳川家当主 の在任声明数が P39=2 / P1308=1 で異なります
- [織田信敏](https://www.wikidata.org/wiki/Q5370072) (Q5370072): 天童藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平頼位](https://www.wikidata.org/wiki/Q6638162) (Q6638162): 常陸宍戸藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平昌親](https://www.wikidata.org/wiki/Q6788037) (Q6788037): 福井藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [阿部正静](https://www.wikidata.org/wiki/Q8012981) (Q8012981): 白河藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [阿部正静](https://www.wikidata.org/wiki/Q8012981) (Q8012981): 棚倉藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松前章広](https://www.wikidata.org/wiki/Q8514326) (Q8514326): 松前藩主 の在任声明数が P39=1 / P1308=2 で異なります

## 同じ藩に在任声明が複数(2件)

再任なら正しい。重複入力なら1つにまとめる。

- [徳川慶喜](https://www.wikidata.org/wiki/Q287657) (Q287657): 一橋徳川家当主 に在任声明が2件(再任、または重複入力)
- [徳川慶頼](https://www.wikidata.org/wiki/Q7813724) (Q7813724): 田安徳川家当主 に在任声明が2件(再任、または重複入力)

## 性別(P21)がない(母の可能性)(1件)

- [Q141641625](https://www.wikidata.org/wiki/Q141641625) (Q141641625): 性別(P21)がなく、子1人には別に実父(P22)がいるため、実父として扱っていません(母の可能性)

## 同名の藩項目が複数(2件)

- [高田藩](https://www.wikidata.org/wiki/Q10863417) (Q10863417): 高田藩
- [高田藩](https://www.wikidata.org/wiki/Q839422) (Q839422): 高田藩

## 座標がない(藩 P625・城 P159・行政中心地 P36 のいずれにも座標なし)(29件)

- [窪田藩](https://www.wikidata.org/wiki/Q10855529) (Q10855529)
- [仁賀保藩](https://www.wikidata.org/wiki/Q10856283) (Q10856283)
- [石川藩](https://www.wikidata.org/wiki/Q10863280) (Q10863280)
- [大久保藩](https://www.wikidata.org/wiki/Q10863309) (Q10863309)
- [出羽丸岡藩](https://www.wikidata.org/wiki/Q10863431) (Q10863431)
- [陸奥下村藩](https://www.wikidata.org/wiki/Q10863528) (Q10863528)
- [吉江藩](https://www.wikidata.org/wiki/Q10863532) (Q10863532)
- [村山藩](https://www.wikidata.org/wiki/Q10863541) (Q10863541)
- [矢島藩](https://www.wikidata.org/wiki/Q10863546) (Q10863546)
- [松崎藩](https://www.wikidata.org/wiki/Q109359686) (Q109359686)
- [下手渡藩](https://www.wikidata.org/wiki/Q111655770) (Q111655770)
- [小倉新田藩](https://www.wikidata.org/wiki/Q12111537) (Q12111537)
- [平戸新田藩](https://www.wikidata.org/wiki/Q12168152) (Q12168152)
- [肥後新田藩](https://www.wikidata.org/wiki/Q12168171) (Q12168171)
- [鶴田藩](https://www.wikidata.org/wiki/Q123150770) (Q123150770)
- [岩崎藩](https://www.wikidata.org/wiki/Q141654715) (Q141654715)
- [大山藩](https://www.wikidata.org/wiki/Q141654758) (Q141654758)
- [松山藩](https://www.wikidata.org/wiki/Q141654775) (Q141654775)
- [左沢藩](https://www.wikidata.org/wiki/Q141654806) (Q141654806)
- [湯本藩](https://www.wikidata.org/wiki/Q141661613) (Q141661613)
- [斗南藩](https://www.wikidata.org/wiki/Q16180027) (Q16180027)
- [豊後高松藩](https://www.wikidata.org/wiki/Q24900616) (Q24900616)
- [三池藩](https://www.wikidata.org/wiki/Q27506184) (Q27506184)
- [蓮池藩](https://www.wikidata.org/wiki/Q3034444) (Q3034444)
- [常陸宍戸藩](https://www.wikidata.org/wiki/Q3034528) (Q3034528)
- [中津山藩](https://www.wikidata.org/wiki/Q844227) (Q844227)
- [湯長谷藩](https://www.wikidata.org/wiki/Q844425) (Q844425)
- [亀田藩](https://www.wikidata.org/wiki/Q847258) (Q847258)
- [泉藩](https://www.wikidata.org/wiki/Q909946) (Q909946)

## 在任の年が重なる(別人が複数年重複)(4件)

- [小倉藩](https://www.wikidata.org/wiki/Q1140943) (Q1140943): [細川忠利](https://www.wikidata.org/wiki/Q3140918) (Q3140918)(1620–1633)と [小笠原忠真](https://www.wikidata.org/wiki/Q7079842) (Q7079842)(1632–1667)
- [鹿島藩](https://www.wikidata.org/wiki/Q3034464) (Q3034464): [鍋島直宜](https://www.wikidata.org/wiki/Q11650666) (Q11650666)(1770–1801)と [鍋島直彜](https://www.wikidata.org/wiki/Q11650670) (Q11650670)(1800–1820)
- [川越藩](https://www.wikidata.org/wiki/Q3034465) (Q3034465): [松平直克](https://www.wikidata.org/wiki/Q11530518) (Q11530518)(1861–1867)と [松平康英](https://www.wikidata.org/wiki/Q6526602) (Q6526602)(1866–1869)
- [高田藩](https://www.wikidata.org/wiki/Q839422) (Q839422): [酒井忠勝](https://www.wikidata.org/wiki/Q5367620) (Q5367620)(1618–1619)と [松平忠昌](https://www.wikidata.org/wiki/Q2814515) (Q2814515)(1618–1623)

## 同じ代数が複数の人物に付いている(P1545)(1件)

- [岩崎藩](https://www.wikidata.org/wiki/Q141654715) (Q141654715): 1代 = [佐竹義理](https://www.wikidata.org/wiki/Q5370062) (Q5370062)、[佐竹義長](https://www.wikidata.org/wiki/Q8514455) (Q8514455)
