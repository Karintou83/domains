# Wikidata 側で直すとよい点の一覧

このファイルは `scripts/report_issues.py` が `data/warnings.json` から自動で作ります(手で直さない)。データ生成: 2026-10-30。リンクは Wikidata の項目です。
Wikidata を直したあと、生データ(`data/raw/`)を消して `python scripts/build_data.py` を実行すると反映されます。

## 目次

- 旧国が決まらない(地方不明として表示)(24件)
- 座標が無く地図に出ない(117件)
- 実父が2人以上いる(40件)
- 藩主に実父(P22)が無い(131件)
- 父の P40 にあるが、子の側に P22 が無い(8件)
- 子の P22 にあるが、父の側に P40 が無い(5件)
- 親族(P1038)に関係(P1039)が無く、向きが分からない(3件)
- 養子関係らしいが、扱っていない関係(P1039)(1件)
- 在任(P39)に開始年(P580)が無い(5件)
- 征夷大将軍の在任に開始年が無い(3件)
- 在任の年が P39 と P1308 で食い違う(9件)
- P39 と P1308 で在任の数が違う(12件)
- 役職の P2389 と藩の P2388 が一致しない(3件)
- 藩主の性別(P21)が女性(2件)
- 性別(P21)が無い(母の可能性)(1件)
- 同名の藩項目が複数(4件)
- 肖像のライセンスを確認できない(2件)
- その他(2件)

## 旧国が決まらない(地方不明として表示)(24件)

藩の項目に所在地(P131)の令制国か郡を入れる、または本部所在地(P159)の城・陣屋に所在地を入れると決まります。郡は config.json の district_to_province でも補えます。

- [三次藩](https://www.wikidata.org/wiki/Q109359691) (Q109359691): 所在地 P131 なし
- [上有知藩](https://www.wikidata.org/wiki/Q10863297) (Q10863297): 所在地 P131 なし
- [下総三浦藩](https://www.wikidata.org/wiki/Q10863364) (Q10863364): 所在地 P131 なし
- [下総飯田藩](https://www.wikidata.org/wiki/Q10863231) (Q10863231): 所在地 P131 なし
- [中村藩](https://www.wikidata.org/wiki/Q18710354) (Q18710354): 所在地 P131 なし
- [伊予吉田藩](https://www.wikidata.org/wiki/Q114397604) (Q114397604): 所在地 P131 なし
- [佐野藩](https://www.wikidata.org/wiki/Q10863374) (Q10863374): 所在地 P131 なし
- [児島藩](https://www.wikidata.org/wiki/Q109358278) (Q109358278): 所在地 P131 なし
- [吉永藩](https://www.wikidata.org/wiki/Q109356827) (Q109356827): 所在地 P131 なし
- [土佐新田藩](https://www.wikidata.org/wiki/Q12162100) (Q12162100): 所在地 P131 なし
- [多度津藩](https://www.wikidata.org/wiki/Q109356835) (Q109356835): 所在地 P131 なし
- [大聖寺新田藩](https://www.wikidata.org/wiki/Q10863382) (Q10863382): 所在地 P131 なし
- [山城長岡藩](https://www.wikidata.org/wiki/Q12589487) (Q12589487): 所在地 P131 なし
- [平福藩](https://www.wikidata.org/wiki/Q10863493) (Q10863493): 所在地 P131 なし
- [広島新田藩](https://www.wikidata.org/wiki/Q109359721) (Q109359721): 所在地 P131 なし
- [彦根新田藩](https://www.wikidata.org/wiki/Q12626275) (Q12626275): 所在地 P131 なし
- [新谷藩](https://www.wikidata.org/wiki/Q109357353) (Q109357353): 所在地 P131 なし
- [深谷藩](https://www.wikidata.org/wiki/Q10863507) (Q10863507): 所在地 P131 なし
- [清末藩](https://www.wikidata.org/wiki/Q613073) (Q613073): 所在地 P131 なし
- [生坂藩](https://www.wikidata.org/wiki/Q123110957) (Q123110957): 所在地 P131 なし
- [西江原藩](https://www.wikidata.org/wiki/Q10856274) (Q10856274): 所在地 P131 なし
- [阿保藩](https://www.wikidata.org/wiki/Q10863294) (Q10863294): 所在地 P131 なし
- [高島藩](https://www.wikidata.org/wiki/Q16282184) (Q16282184): 所在地 P131 なし
- [鴨方藩](https://www.wikidata.org/wiki/Q123110960) (Q123110960): 所在地 P131 なし

## 座標が無く地図に出ない(117件)

本部所在地(P159)に城・陣屋を入れ、その項目に座標(P625)を入れるのが確実です。所在地(P131)が令制国だけの藩は、国の中心では粗すぎるため座標に使っていません。

- [三次藩](https://www.wikidata.org/wiki/Q109359691) (Q109359691): 所在地 P131 なし
- [三河中島藩](https://www.wikidata.org/wiki/Q10863477) (Q10863477): 今の所在地 P131: 三河国
- [三草藩](https://www.wikidata.org/wiki/Q10863479) (Q10863479): 今の所在地 P131: 播磨国
- [上総苅谷藩](https://www.wikidata.org/wiki/Q10854976) (Q10854976): 今の所在地 P131: 上総国
- [上里見藩](https://www.wikidata.org/wiki/Q10854996) (Q10854996): 今の所在地 P131: 上野国
- [下手渡藩](https://www.wikidata.org/wiki/Q111655770) (Q111655770): 所在地 P131 なし
- [下松藩](https://www.wikidata.org/wiki/Q141737697) (Q141737697): 今の所在地 P131: 周防国
- [下総三浦藩](https://www.wikidata.org/wiki/Q10863364) (Q10863364): 所在地 P131 なし
- [下総飯田藩](https://www.wikidata.org/wiki/Q10863231) (Q10863231): 所在地 P131 なし
- [下野上田藩](https://www.wikidata.org/wiki/Q10863368) (Q10863368): 今の所在地 P131: 下野国
- [下野富田藩](https://www.wikidata.org/wiki/Q10863369) (Q10863369): 今の所在地 P131: 下野国
- [中津山藩](https://www.wikidata.org/wiki/Q844227) (Q844227): 今の所在地 P131: 陸奥国
- [亀田藩](https://www.wikidata.org/wiki/Q847258) (Q847258): 今の所在地 P131: 出羽国
- [五井藩](https://www.wikidata.org/wiki/Q369285) (Q369285): 今の所在地 P131: 上総国
- [仁賀保藩](https://www.wikidata.org/wiki/Q10856283) (Q10856283): 所在地 P131 なし
- [伊予吉田藩](https://www.wikidata.org/wiki/Q114397604) (Q114397604): 所在地 P131 なし
- [伊保藩](https://www.wikidata.org/wiki/Q10863235) (Q10863235): 今の所在地 P131: 三河国
- [伊勢岩手藩](https://www.wikidata.org/wiki/Q10863238) (Q10863238): 今の所在地 P131: 伊勢国
- [保内藩](https://www.wikidata.org/wiki/Q10863484) (Q10863484): 今の所在地 P131: 常陸国
- [信濃中村藩](https://www.wikidata.org/wiki/Q10863375) (Q10863375): 今の所在地 P131: 信濃国
- [児島藩](https://www.wikidata.org/wiki/Q109358278) (Q109358278): 所在地 P131 なし
- [八木藩](https://www.wikidata.org/wiki/Q10863529) (Q10863529): 今の所在地 P131: 但馬国
- [八田藩](https://www.wikidata.org/wiki/Q10863430) (Q10863430): 今の所在地 P131: 伊勢国
- [出羽丸岡藩](https://www.wikidata.org/wiki/Q10863431) (Q10863431): 所在地 P131 なし
- [加納藩](https://www.wikidata.org/wiki/Q3034458) (Q3034458): 今の所在地 P131: 美濃国
- [原市藩](https://www.wikidata.org/wiki/Q10863433) (Q10863433): 今の所在地 P131: 武蔵国
- [吉永藩](https://www.wikidata.org/wiki/Q109356827) (Q109356827): 所在地 P131 なし
- [吉江藩](https://www.wikidata.org/wiki/Q10863532) (Q10863532): 今の所在地 P131: 越前国
- [埴科藩](https://www.wikidata.org/wiki/Q10863435) (Q10863435): 今の所在地 P131: 信濃国
- [多度津藩](https://www.wikidata.org/wiki/Q109356835) (Q109356835): 所在地 P131 なし
- [大久保藩](https://www.wikidata.org/wiki/Q10863309) (Q10863309): 今の所在地 P131: 陸奥国
- [大山藩](https://www.wikidata.org/wiki/Q141654758) (Q141654758): 所在地 P131 なし
- [大聖寺新田藩](https://www.wikidata.org/wiki/Q10863382) (Q10863382): 所在地 P131 なし
- [大聖寺藩](https://www.wikidata.org/wiki/Q3034431) (Q3034431): 今の所在地 P131: 加賀国
- [大輪藩](https://www.wikidata.org/wiki/Q10863323) (Q10863323): 今の所在地 P131: 下総国
- [奥仁科藩](https://www.wikidata.org/wiki/Q10863326) (Q10863326): 今の所在地 P131: 安曇郡
- [安志藩](https://www.wikidata.org/wiki/Q10863256) (Q10863256): 今の所在地 P131: 播磨国
- [安房三枝藩](https://www.wikidata.org/wiki/Q10863257) (Q10863257): 今の所在地 P131: 安房国
- [安房勝山藩](https://www.wikidata.org/wiki/Q3034384) (Q3034384): 今の所在地 P131: 安房国
- [小久保藩](https://www.wikidata.org/wiki/Q10863383) (Q10863383): 今の所在地 P131: 上総国
- [小張藩](https://www.wikidata.org/wiki/Q10855302) (Q10855302): 今の所在地 P131: 常陸国
- [山城長岡藩](https://www.wikidata.org/wiki/Q12589487) (Q12589487): 所在地 P131 なし
- [岩崎藩](https://www.wikidata.org/wiki/Q141654715) (Q141654715): 所在地 P131 なし
- [岩村田藩](https://www.wikidata.org/wiki/Q10863260) (Q10863260): 今の所在地 P131: 信濃国
- [岩滝藩](https://www.wikidata.org/wiki/Q10863263) (Q10863263): 今の所在地 P131: 美濃国
- [川成島藩](https://www.wikidata.org/wiki/Q10855037) (Q10855037): 今の所在地 P131: 駿河国
- [左沢藩](https://www.wikidata.org/wiki/Q141654806) (Q141654806): 所在地 P131 なし
- [布市藩](https://www.wikidata.org/wiki/Q10863438) (Q10863438): 今の所在地 P131: 新川郡
- [庭瀬藩](https://www.wikidata.org/wiki/Q3034514) (Q3034514): 今の所在地 P131: 備中国
- [徳美藩](https://www.wikidata.org/wiki/Q10863449) (Q10863449): 今の所在地 P131: 甲斐国
- [徳野藩](https://www.wikidata.org/wiki/Q11490464) (Q11490464): 今の所在地 P131: 美濃国
- [揖斐藩](https://www.wikidata.org/wiki/Q10863264) (Q10863264): 今の所在地 P131: 美濃国
- [摂津中島藩](https://www.wikidata.org/wiki/Q10863420) (Q10863420): 今の所在地 P131: 摂津国
- [斗南藩](https://www.wikidata.org/wiki/Q16180027) (Q16180027): 所在地 P131 なし
- [新谷藩](https://www.wikidata.org/wiki/Q109357353) (Q109357353): 所在地 P131 なし
- [木本藩](https://www.wikidata.org/wiki/Q10863393) (Q10863393): 今の所在地 P131: 越前国
- [村山藩](https://www.wikidata.org/wiki/Q10863541) (Q10863541): 今の所在地 P131: 村山郡
- [東方藩](https://www.wikidata.org/wiki/Q141732683) (Q141732683): 今の所在地 P131: 武蔵国
- [松山藩](https://www.wikidata.org/wiki/Q141654775) (Q141654775): 所在地 P131 なし
- [松長藩](https://www.wikidata.org/wiki/Q10863501) (Q10863501): 今の所在地 P131: 駿河国
- [板橋藩](https://www.wikidata.org/wiki/Q10863265) (Q10863265): 今の所在地 P131: 下野国
- [林藩](https://www.wikidata.org/wiki/Q11533304) (Q11533304): 今の所在地 P131: 伊勢国
- [栗原藩](https://www.wikidata.org/wiki/Q10863338) (Q10863338): 今の所在地 P131: 下総国
- [櫛羅藩](https://www.wikidata.org/wiki/Q10863339) (Q10863339): 今の所在地 P131: 大和国
- [武蔵小室藩](https://www.wikidata.org/wiki/Q10863502) (Q10863502): 今の所在地 P131: 武蔵国
- [泉藩](https://www.wikidata.org/wiki/Q909946) (Q909946): 所在地 P131 なし
- [清富藩](https://www.wikidata.org/wiki/Q30925922) (Q30925922): 今の所在地 P131: 但馬国
- [湯本藩](https://www.wikidata.org/wiki/Q141661613) (Q141661613): 所在地 P131 なし
- [湯長谷藩](https://www.wikidata.org/wiki/Q844425) (Q844425): 所在地 P131 なし
- [潤井戸藩](https://www.wikidata.org/wiki/Q10863278) (Q10863278): 今の所在地 P131: 上総国
- [片野藩](https://www.wikidata.org/wiki/Q10855066) (Q10855066): 今の所在地 P131: 常陸国
- [玉取藩](https://www.wikidata.org/wiki/Q10856335) (Q10856335): 今の所在地 P131: 常陸国
- [生坂藩](https://www.wikidata.org/wiki/Q123110957) (Q123110957): 所在地 P131 なし
- [生実藩](https://www.wikidata.org/wiki/Q3034406) (Q3034406): 今の所在地 P131: 下総国
- [矢作藩](https://www.wikidata.org/wiki/Q10863545) (Q10863545): 今の所在地 P131: 下総国
- [窪田藩](https://www.wikidata.org/wiki/Q10855529) (Q10855529): 所在地 P131 なし
- [篠塚藩](https://www.wikidata.org/wiki/Q10863400) (Q10863400): 今の所在地 P131: 上野国
- [美作宮川藩](https://www.wikidata.org/wiki/Q141737724) (Q141737724): 今の所在地 P131: 美作国
- [美濃脇坂藩](https://www.wikidata.org/wiki/Q10863516) (Q10863516): 今の所在地 P131: 美濃国
- [美濃長谷川藩](https://www.wikidata.org/wiki/Q10863517) (Q10863517): 今の所在地 P131: 美濃国
- [美濃高松藩](https://www.wikidata.org/wiki/Q10863523) (Q10863523): 今の所在地 P131: 美濃国
- [能登下村藩](https://www.wikidata.org/wiki/Q10863457) (Q10863457): 今の所在地 P131: 能登国
- [興留藩](https://www.wikidata.org/wiki/Q10863353) (Q10863353): 今の所在地 P131: 大和国
- [花房藩](https://www.wikidata.org/wiki/Q3034442) (Q3034442): 今の所在地 P131: 安房国
- [菊間藩](https://www.wikidata.org/wiki/Q10855751) (Q10855751): 今の所在地 P131: 上総国
- [蔵王堂藩](https://www.wikidata.org/wiki/Q10863403) (Q10863403): 今の所在地 P131: 越後国
- [西江原藩](https://www.wikidata.org/wiki/Q10856274) (Q10856274): 所在地 P131 なし
- [西谷藩](https://www.wikidata.org/wiki/Q10863462) (Q10863462): 今の所在地 P131: 能登国
- [谷田部藩](https://www.wikidata.org/wiki/Q10863553) (Q10863553): 今の所在地 P131: 常陸国
- [豊後高松藩](https://www.wikidata.org/wiki/Q24900616) (Q24900616): 所在地 P131 なし
- [赤沼藩](https://www.wikidata.org/wiki/Q10863285) (Q10863285): 今の所在地 P131: 武蔵国
- [足守藩](https://www.wikidata.org/wiki/Q10863289) (Q10863289): 今の所在地 P131: 備中国
- [近江宮川藩](https://www.wikidata.org/wiki/Q10863290) (Q10863290): 今の所在地 P131: 近江国
- [近江小室藩](https://www.wikidata.org/wiki/Q10863292) (Q10863292): 今の所在地 P131: 近江国
- [近江高島藩](https://www.wikidata.org/wiki/Q10863293) (Q10863293): 今の所在地 P131: 近江国
- [遠江久野藩](https://www.wikidata.org/wiki/Q10863464) (Q10863464): 今の所在地 P131: 遠江国
- [那波藩](https://www.wikidata.org/wiki/Q10863466) (Q10863466): 今の所在地 P131: 上野国
- [那須藩](https://www.wikidata.org/wiki/Q10863467) (Q10863467): 今の所在地 P131: 下野国
- [野本藩](https://www.wikidata.org/wiki/Q141732613) (Q141732613): 今の所在地 P131: 武蔵国
- [長尾藩](https://www.wikidata.org/wiki/Q3034503) (Q3034503): 今の所在地 P131: 安房国
- [長峰藩](https://www.wikidata.org/wiki/Q10855946) (Q10855946): 今の所在地 P131: 越後国
- [阿保藩](https://www.wikidata.org/wiki/Q10863294) (Q10863294): 所在地 P131 なし
- [陶器藩](https://www.wikidata.org/wiki/Q10863472) (Q10863472): 今の所在地 P131: 和泉国
- [陸奥下村藩](https://www.wikidata.org/wiki/Q10863528) (Q10863528): 今の所在地 P131: 陸奥国
- [青柳藩](https://www.wikidata.org/wiki/Q10863295) (Q10863295): 今の所在地 P131: 上野国
- [青野藩](https://www.wikidata.org/wiki/Q3034383) (Q3034383): 今の所在地 P131: 美濃国
- [高井藩](https://www.wikidata.org/wiki/Q10863408) (Q10863408): 今の所在地 P131: 信濃国
- [高井野藩](https://www.wikidata.org/wiki/Q10863409) (Q10863409): 今の所在地 P131: 高井郡
- [高島藩](https://www.wikidata.org/wiki/Q16282184) (Q16282184): 所在地 P131 なし
- [高徳藩](https://www.wikidata.org/wiki/Q10863414) (Q10863414): 今の所在地 P131: 下野国
- [高柳藩](https://www.wikidata.org/wiki/Q10856398) (Q10856398): 今の所在地 P131: 越後国
- [高森藩](https://www.wikidata.org/wiki/Q10856390) (Q10856390): 今の所在地 P131: 越前国
- [鴨方藩](https://www.wikidata.org/wiki/Q123110960) (Q123110960): 所在地 P131 なし
- [鶴田藩](https://www.wikidata.org/wiki/Q123150770) (Q123150770): 所在地 P131 なし
- [麻生藩](https://www.wikidata.org/wiki/Q10863296) (Q10863296): 今の所在地 P131: 常陸国
- [麻田藩](https://www.wikidata.org/wiki/Q1073005) (Q1073005): 今の所在地 P131: 摂津国
- [黒羽藩](https://www.wikidata.org/wiki/Q3034477) (Q3034477): 今の所在地 P131: 下野国

## 実父が2人以上いる(40件)

子の P22 か、父の項目の P40 のどちらかが誤りです(P40 で拾った人物が母の場合もあります)。

- [Q110816643](https://www.wikidata.org/wiki/Q110816643) (Q110816643): 井伊忠直: 実父が複数あります(井伊景直、井伊成直)
- [Q22130053](https://www.wikidata.org/wiki/Q22130053) (Q22130053): 得川親季: 実父が複数あります(新田義宗、世良田政義)
- [丹羽氏明](https://www.wikidata.org/wiki/Q11368647) (Q11368647): 実父が複数あります(一色氏宗、丹羽氏純)
- [内藤信成](https://www.wikidata.org/wiki/Q6959828) (Q6959828): 実父が複数あります(松平広忠、嶋田景信)
- [別所吉治](https://www.wikidata.org/wiki/Q11245090) (Q11245090): 実父が複数あります(別所重宗、別所長治)
- [加藤泰秋](https://www.wikidata.org/wiki/Q6378611) (Q6378611): 実父が複数あります(加藤泰幹、加藤泰祉)
- [大久保忠礼](https://www.wikidata.org/wiki/Q8081574) (Q8081574): 実父が複数あります(大久保教義、松平頼恕)
- [大内持盛](https://www.wikidata.org/wiki/Q11432526) (Q11432526): 実父が複数あります(大内弘世、大内義弘)
- [大内教幸](https://www.wikidata.org/wiki/Q11432530) (Q11432530): 実父が複数あります(大内持盛、大内盛見)
- [奥平昌邁](https://www.wikidata.org/wiki/Q11445780) (Q11445780): 実父が複数あります(伊達宗敦、伊達宗城)
- [小堀政峯](https://www.wikidata.org/wiki/Q11459502) (Q11459502): 実父が複数あります(小堀政恒、小堀政養)
- [德川家達](https://www.wikidata.org/wiki/Q672741) (Q672741): 実父が複数あります(徳川家茂、徳川慶頼)
- [戸田宗光](https://www.wikidata.org/wiki/Q10862100) (Q10862100): 実父が複数あります(戸田綱光、戸田実光、正親町三条実興)
- [戸田忠時](https://www.wikidata.org/wiki/Q10862120) (Q10862120): 実父が複数あります(戸田忠継、Q141794049)
- [村上忠勝](https://www.wikidata.org/wiki/Q11522794) (Q11522794): 実父が複数あります(戸田勝隆、戸田内記)
- [松平乗穏](https://www.wikidata.org/wiki/Q10729488) (Q10729488): 実父が複数あります(松平盈乗、馬込興承)
- [松平信光](https://www.wikidata.org/wiki/Q11239114) (Q11239114): 実父が複数あります(松平泰親、松平親氏)
- [松平親清 (大給松平家)](https://www.wikidata.org/wiki/Q108056290) (Q108056290): 実父が複数あります(松平乗正、松平乗元)
- [松平頼純](https://www.wikidata.org/wiki/Q6993673) (Q6993673): 実父が複数あります(徳川頼宣、father of 松平頼純)
- [林政秀](https://www.wikidata.org/wiki/Q110249784) (Q110249784): 実父が複数あります(林通政 (織田信長の家臣)、林通政 (駿河守))
- [森川重信](https://www.wikidata.org/wiki/Q11539646) (Q11539646): 実父が複数あります(森川重名、森川重政)
- [水野忠寛](https://www.wikidata.org/wiki/Q10565523) (Q10565523): 実父が複数あります(水野忠鼎、水野忠紹)
- [水野忠政](https://www.wikidata.org/wiki/Q1188498) (Q1188498): 実父が複数あります(水野賢勝、水野清忠)
- [池田政恭](https://www.wikidata.org/wiki/Q11551920) (Q11551920): 実父が複数あります(池田政弼、池田治政)
- [池田輝名](https://www.wikidata.org/wiki/Q11069924) (Q11069924): 実父が複数あります(松平忠順、池田喜生)
- [秋月種春](https://www.wikidata.org/wiki/Q11595122) (Q11595122): 実父が複数あります(忠宥、秋月種貞)
- [稲葉通兼](https://www.wikidata.org/wiki/Q109122992) (Q109122992): 実父が複数あります(稲葉通高、河野通春)
- [細川興隆](https://www.wikidata.org/wiki/Q11605992) (Q11605992): 実父が複数あります(細川興元、細川興昌)
- [織田久長](https://www.wikidata.org/wiki/Q11608249) (Q11608249): 実父が複数あります(織田常松、織田常竹、勝久 織田)
- [織田信定](https://www.wikidata.org/wiki/Q11608277) (Q11608277): 実父が複数あります(織田敏定、織田良信)
- [織田常松](https://www.wikidata.org/wiki/Q11608367) (Q11608367): 実父が複数あります(織田常勝、藤原将広)
- [織田常竹](https://www.wikidata.org/wiki/Q11608368) (Q11608368): 実父が複数あります(織田常勝、藤原将広)
- [織田良信](https://www.wikidata.org/wiki/Q11608420) (Q11608420): 実父が複数あります(織田敏信、織田敏定)
- [菅沼定則](https://www.wikidata.org/wiki/Q11619293) (Q11619293): 実父が複数あります(菅沼定忠 (菅沼定信の子)、菅沼定成 (菅沼定忠の子))
- [西尾吉次](https://www.wikidata.org/wiki/Q11627721) (Q11627721): 実父が複数あります(吉良持広、西尾信光)
- [足利義明](https://www.wikidata.org/wiki/Q11636811) (Q11636811): 実父が複数あります(足利政氏、足利義晴)
- [里見実堯](https://www.wikidata.org/wiki/Q11644642) (Q11644642): 実父が複数あります(里見成義、里見義実)
- [阿部正長](https://www.wikidata.org/wiki/Q111131074) (Q111131074): 実父が複数あります(阿部正春、阿部正晴)
- [青山成重](https://www.wikidata.org/wiki/Q11069279) (Q11069279): 実父が複数あります(服部正信、青山忠重)
- [黒田職隆](https://www.wikidata.org/wiki/Q11678682) (Q11678682): 実父が複数あります(黒田重隆、小寺則職)

## 藩主に実父(P22)が無い(131件)

実父が分かれば P22 を入れると、家系図でほかの藩主とつながることがあります。

- [三宅康保](https://www.wikidata.org/wiki/Q10523842) (Q10523842): 実父(P22)がありません
- [三宅康友](https://www.wikidata.org/wiki/Q10523862) (Q10523862): 実父(P22)がありません
- [三宅康明](https://www.wikidata.org/wiki/Q10523924) (Q10523924): 実父(P22)がありません
- [三宅康直](https://www.wikidata.org/wiki/Q10523993) (Q10523993): 実父(P22)がありません
- [三宅康貞](https://www.wikidata.org/wiki/Q10524017) (Q10524017): 実父(P22)がありません
- [中山信守](https://www.wikidata.org/wiki/Q6638010) (Q6638010): 実父(P22)がありません
- [中山信宝](https://www.wikidata.org/wiki/Q11364056) (Q11364056): 実父(P22)がありません
- [中山信徴](https://www.wikidata.org/wiki/Q11364059) (Q11364059): 実父(P22)がありません
- [中山信情](https://www.wikidata.org/wiki/Q11364060) (Q11364060): 実父(P22)がありません
- [中山信成](https://www.wikidata.org/wiki/Q11364062) (Q11364062): 実父(P22)がありません
- [中山信政](https://www.wikidata.org/wiki/Q11364063) (Q11364063): 実父(P22)がありません
- [中山信敏](https://www.wikidata.org/wiki/Q11364064) (Q11364064): 実父(P22)がありません
- [中山信昌](https://www.wikidata.org/wiki/Q11364065) (Q11364065): 実父(P22)がありません
- [中山信治](https://www.wikidata.org/wiki/Q11364067) (Q11364067): 実父(P22)がありません
- [中山信順](https://www.wikidata.org/wiki/Q11364069) (Q11364069): 実父(P22)がありません
- [久世広明](https://www.wikidata.org/wiki/Q10859999) (Q10859999): 実父(P22)がありません
- [井上正健](https://www.wikidata.org/wiki/Q11373068) (Q11373068): 実父(P22)がありません
- [井上正兼](https://www.wikidata.org/wiki/Q11373069) (Q11373069): 実父(P22)がありません
- [井上正巳](https://www.wikidata.org/wiki/Q3151480) (Q3151480): 実父(P22)がありません
- [井上正広](https://www.wikidata.org/wiki/Q11373079) (Q11373079): 実父(P22)がありません
- [井上正建](https://www.wikidata.org/wiki/Q11373080) (Q11373080): 実父(P22)がありません
- [井上正意](https://www.wikidata.org/wiki/Q11373081) (Q11373081): 実父(P22)がありません
- [井上正敦](https://www.wikidata.org/wiki/Q11373082) (Q11373082): 実父(P22)がありません
- [井上正棠](https://www.wikidata.org/wiki/Q11373083) (Q11373083): 実父(P22)がありません
- [井上正民](https://www.wikidata.org/wiki/Q11373086) (Q11373086): 実父(P22)がありません
- [井上正辰](https://www.wikidata.org/wiki/Q11373094) (Q11373094): 実父(P22)がありません
- [井伊直朝](https://www.wikidata.org/wiki/Q11161327) (Q11161327): 実父(P22)がありません
- [井伊直武](https://www.wikidata.org/wiki/Q11161337) (Q11161337): 実父(P22)がありません
- [佐久間安次](https://www.wikidata.org/wiki/Q11382701) (Q11382701): 実父(P22)がありません
- [佐久間安長](https://www.wikidata.org/wiki/Q11382702) (Q11382702): 実父(P22)がありません
- [加納久慎](https://www.wikidata.org/wiki/Q11398747) (Q11398747): 実父(P22)がありません
- [土方雄豊](https://www.wikidata.org/wiki/Q11423550) (Q11423550): 実父(P22)がありません
- [堀之敏](https://www.wikidata.org/wiki/Q11427207) (Q11427207): 実父(P22)がありません
- [堀之美](https://www.wikidata.org/wiki/Q11427205) (Q11427205): 実父(P22)がありません
- [堀田正民](https://www.wikidata.org/wiki/Q11427644) (Q11427644): 実父(P22)がありません
- [堀田正穀](https://www.wikidata.org/wiki/Q11427646) (Q11427646): 実父(P22)がありません
- [堀田正誠](https://www.wikidata.org/wiki/Q11427649) (Q11427649): 実父(P22)がありません
- [堀田正養](https://www.wikidata.org/wiki/Q11427656) (Q11427656): 実父(P22)がありません
- [堀直佑](https://www.wikidata.org/wiki/Q11427680) (Q11427680): 実父(P22)がありません
- [堀直哉](https://www.wikidata.org/wiki/Q10565588) (Q10565588): 実父(P22)がありません
- [堀直喜](https://www.wikidata.org/wiki/Q11427685) (Q11427685): 実父(P22)がありません
- [堀直堅](https://www.wikidata.org/wiki/Q11427686) (Q11427686): 実父(P22)がありません
- [堀直央 (椎谷藩主)](https://www.wikidata.org/wiki/Q11427690) (Q11427690): 実父(P22)がありません
- [堀直宣](https://www.wikidata.org/wiki/Q11427692) (Q11427692): 実父(P22)がありません
- [堀直寛](https://www.wikidata.org/wiki/Q11427696) (Q11427696): 実父(P22)がありません
- [堀直旧](https://www.wikidata.org/wiki/Q11427703) (Q11427703): 実父(P22)がありません
- [堀直武](https://www.wikidata.org/wiki/Q11427708) (Q11427708): 実父(P22)がありません
- [堀直皓](https://www.wikidata.org/wiki/Q11427714) (Q11427714): 実父(P22)がありません
- [堀直興](https://www.wikidata.org/wiki/Q11427715) (Q11427715): 実父(P22)がありません
- [堀直著](https://www.wikidata.org/wiki/Q11427718) (Q11427718): 実父(P22)がありません
- [堀直輝](https://www.wikidata.org/wiki/Q11427720) (Q11427720): 実父(P22)がありません
- [堀直郷](https://www.wikidata.org/wiki/Q11427722) (Q11427722): 実父(P22)がありません
- [堀著朝](https://www.wikidata.org/wiki/Q11427750) (Q11427750): 実父(P22)がありません
- [堀親庸](https://www.wikidata.org/wiki/Q11427757) (Q11427757): 実父(P22)がありません
- [堀親民](https://www.wikidata.org/wiki/Q11427760) (Q11427760): 実父(P22)がありません
- [堀通周](https://www.wikidata.org/wiki/Q11427811) (Q11427811): 実父(P22)がありません
- [増山正同](https://www.wikidata.org/wiki/Q11429189) (Q11429189): 実父(P22)がありません
- [大久保忠喜](https://www.wikidata.org/wiki/Q11431968) (Q11431968): 実父(P22)がありません
- [大久保忠愨](https://www.wikidata.org/wiki/Q8081567) (Q8081567): 実父(P22)がありません
- [大久保忠胤](https://www.wikidata.org/wiki/Q11431982) (Q11431982): 実父(P22)がありません
- [大久保忠順](https://www.wikidata.org/wiki/Q11431985) (Q11431985): 実父(P22)がありません
- [大河内輝声](https://www.wikidata.org/wiki/Q11437058) (Q11437058): 実父(P22)がありません
- [岡部長住](https://www.wikidata.org/wiki/Q11473877) (Q11473877): 実父(P22)がありません
- [岡部長修](https://www.wikidata.org/wiki/Q11473878) (Q11473878): 実父(P22)がありません
- [岡部長職](https://www.wikidata.org/wiki/Q7400591) (Q7400591): 実父(P22)がありません
- [市橋信直](https://www.wikidata.org/wiki/Q11480545) (Q11480545): 実父(P22)がありません
- [市橋直挙](https://www.wikidata.org/wiki/Q11480556) (Q11480556): 実父(P22)がありません
- [市橋長昭](https://www.wikidata.org/wiki/Q11480569) (Q11480569): 実父(P22)がありません
- [成瀬正典](https://www.wikidata.org/wiki/Q11495562) (Q11495562): 実父(P22)がありません
- [成瀬正幸](https://www.wikidata.org/wiki/Q11495569) (Q11495569): 実父(P22)がありません
- [新庄直ハツ](https://www.wikidata.org/wiki/Q11502209) (Q11502209): 実父(P22)がありません
- [本多正武](https://www.wikidata.org/wiki/Q11520069) (Q11520069): 実父(P22)がありません
- [本多正矩](https://www.wikidata.org/wiki/Q10522845) (Q10522845): 実父(P22)がありません
- [本庄道利](https://www.wikidata.org/wiki/Q11520310) (Q11520310): 実父(P22)がありません
- [本庄道堅](https://www.wikidata.org/wiki/Q10860072) (Q10860072): 実父(P22)がありません
- [本庄道昌](https://www.wikidata.org/wiki/Q11520312) (Q11520312): 実父(P22)がありません
- [本郷泰固](https://www.wikidata.org/wiki/Q11520893) (Q11520893): 実父(P22)がありません
- [村上頼勝](https://www.wikidata.org/wiki/Q11522938) (Q11522938): 実父(P22)がありません
- [松平忠誠 (武蔵国忍藩主)](https://www.wikidata.org/wiki/Q11530449) (Q11530449): 実父(P22)がありません
- [松平輝徳](https://www.wikidata.org/wiki/Q11530597) (Q11530597): 実父(P22)がありません
- [柳沢保卓](https://www.wikidata.org/wiki/Q11534365) (Q11534365): 実父(P22)がありません
- [柳沢信有](https://www.wikidata.org/wiki/Q11534376) (Q11534376): 実父(P22)がありません
- [柳沢光被](https://www.wikidata.org/wiki/Q11534386) (Q11534386): 実父(P22)がありません
- [柳沢里世](https://www.wikidata.org/wiki/Q11534420) (Q11534420): 実父(P22)がありません
- [柳沢里旭](https://www.wikidata.org/wiki/Q11534423) (Q11534423): 実父(P22)がありません
- [柳生俊則](https://www.wikidata.org/wiki/Q11534508) (Q11534508): 実父(P22)がありません
- [柳生俊平](https://www.wikidata.org/wiki/Q10729347) (Q10729347): 実父(P22)がありません
- [柳生俊方](https://www.wikidata.org/wiki/Q11534512) (Q11534512): 実父(P22)がありません
- [柳生俊章](https://www.wikidata.org/wiki/Q11534514) (Q11534514): 実父(P22)がありません
- [柳生俊能](https://www.wikidata.org/wiki/Q6636035) (Q6636035): 実父(P22)がありません
- [柳生宗在](https://www.wikidata.org/wiki/Q11534524) (Q11534524): 実父(P22)がありません
- [桑山重晴](https://www.wikidata.org/wiki/Q11537542) (Q11537542): 実父(P22)がありません
- [水野元綱](https://www.wikidata.org/wiki/Q10565602) (Q10565602): 実父(P22)がありません
- [水野忠定](https://www.wikidata.org/wiki/Q10565518) (Q10565518): 実父(P22)がありません
- [水野忠昭](https://www.wikidata.org/wiki/Q10565540) (Q10565540): 実父(P22)がありません
- [水野忠興](https://www.wikidata.org/wiki/Q10565556) (Q10565556): 実父(P22)がありません
- [水野忠見](https://www.wikidata.org/wiki/Q10565559) (Q10565559): 実父(P22)がありません
- [水野忠韶](https://www.wikidata.org/wiki/Q10565566) (Q10565566): 実父(P22)がありません
- [水野忠順](https://www.wikidata.org/wiki/Q11549385) (Q11549385): 実父(P22)がありません
- [水野重上](https://www.wikidata.org/wiki/Q10565571) (Q10565571): 実父(P22)がありません
- [水野重期](https://www.wikidata.org/wiki/Q10565576) (Q10565576): 実父(P22)がありません
- [永井尚備](https://www.wikidata.org/wiki/Q11549747) (Q11549747): 実父(P22)がありません
- [永井直哉](https://www.wikidata.org/wiki/Q11549795) (Q11549795): 実父(P22)がありません
- [永井直壮](https://www.wikidata.org/wiki/Q11549798) (Q11549798): 実父(P22)がありません
- [永井直矢](https://www.wikidata.org/wiki/Q11549810) (Q11549810): 実父(P22)がありません
- [浅野長勲](https://www.wikidata.org/wiki/Q4803532) (Q4803532): 実父(P22)がありません
- [片桐為元](https://www.wikidata.org/wiki/Q11569867) (Q11569867): 実父(P22)がありません
- [片桐為次](https://www.wikidata.org/wiki/Q11569866) (Q11569866): 実父(P22)がありません
- [片桐貞中](https://www.wikidata.org/wiki/Q11569878) (Q11569878): 実父(P22)がありません
- [片桐貞信](https://www.wikidata.org/wiki/Q11569877) (Q11569877): 実父(P22)がありません
- [片桐貞利](https://www.wikidata.org/wiki/Q11569879) (Q11569879): 実父(P22)がありません
- [片桐貞彰](https://www.wikidata.org/wiki/Q11569880) (Q11569880): 実父(P22)がありません
- [片桐貞照](https://www.wikidata.org/wiki/Q11569884) (Q11569884): 実父(P22)がありません
- [片桐貞篤](https://www.wikidata.org/wiki/Q6637937) (Q6637937): 実父(P22)がありません
- [稲葉正善](https://www.wikidata.org/wiki/Q6013303) (Q6013303): 実父(P22)がありません
- [米倉昌寿](https://www.wikidata.org/wiki/Q8054929) (Q8054929): 実父(P22)がありません
- [織田信就](https://www.wikidata.org/wiki/Q11608282) (Q11608282): 実父(P22)がありません
- [蒔田定安](https://www.wikidata.org/wiki/Q141734621) (Q141734621): 実父(P22)がありません
- [蒔田定庸](https://www.wikidata.org/wiki/Q141734625) (Q141734625): 実父(P22)がありません
- [蒔田定祥](https://www.wikidata.org/wiki/Q141734622) (Q141734622): 実父(P22)がありません
- [蒔田定英](https://www.wikidata.org/wiki/Q141734620) (Q141734620): 実父(P22)がありません
- [蒔田定邦](https://www.wikidata.org/wiki/Q141734623) (Q141734623): 実父(P22)がありません
- [蒔田広運](https://www.wikidata.org/wiki/Q141734627) (Q141734627): 実父(P22)がありません
- [遠山友随](https://www.wikidata.org/wiki/Q11642019) (Q11642019): 実父(P22)がありません
- [酒井忠経](https://www.wikidata.org/wiki/Q11644157) (Q11644157): 実父(P22)がありません
- [酒井忠藎](https://www.wikidata.org/wiki/Q11644092) (Q11644092): 実父(P22)がありません
- [阿部正能](https://www.wikidata.org/wiki/Q10565452) (Q10565452): 実父(P22)がありません
- [高木正善](https://www.wikidata.org/wiki/Q11670089) (Q11670089): 実父(P22)がありません
- [高木正坦](https://www.wikidata.org/wiki/Q11670091) (Q11670091): 実父(P22)がありません
- [高木正恒](https://www.wikidata.org/wiki/Q11670099) (Q11670099): 実父(P22)がありません
- [高木正直](https://www.wikidata.org/wiki/Q11670105) (Q11670105): 実父(P22)がありません

## 父の P40 にあるが、子の側に P22 が無い(8件)

- [別所吉治](https://www.wikidata.org/wiki/Q11245090) (Q11245090): 別所長治 の子として P40 にありますが、別所吉治 側に P22 がありません
- [加藤泰秋](https://www.wikidata.org/wiki/Q6378611) (Q6378611): 加藤泰祉 の子として P40 にありますが、加藤泰秋 側に P22 がありません
- [奥平昌邁](https://www.wikidata.org/wiki/Q11445780) (Q11445780): 伊達宗敦 の子として P40 にありますが、奥平昌邁 側に P22 がありません
- [德川家達](https://www.wikidata.org/wiki/Q672741) (Q672741): 徳川家茂 の子として P40 にありますが、德川家達 側に P22 がありません
- [戸田忠時](https://www.wikidata.org/wiki/Q10862120) (Q10862120): 戸田忠継 の子として P40 にありますが、戸田忠時 側に P22 がありません
- [水野忠寛](https://www.wikidata.org/wiki/Q10565523) (Q10565523): 水野忠鼎 の子として P40 にありますが、水野忠寛 側に P22 がありません
- [細川興隆](https://www.wikidata.org/wiki/Q11605992) (Q11605992): 細川興元 の子として P40 にありますが、細川興隆 側に P22 がありません
- [青山成重](https://www.wikidata.org/wiki/Q11069279) (Q11069279): 青山忠重 の子として P40 にありますが、青山成重 側に P22 がありません

## 子の P22 にあるが、父の側に P40 が無い(5件)

- [Q141794049](https://www.wikidata.org/wiki/Q141794049) (Q141794049): 戸田忠時 の実父 Q141794049 側に P40 がありません
- [father of 松平頼純](https://www.wikidata.org/wiki/Q141640638) (Q141640638): 松平頼純 の実父 father of 松平頼純 側に P40 がありません
- [小堀政養](https://www.wikidata.org/wiki/Q11459507) (Q11459507): 小堀政峯 の実父 小堀政養 側に P40 がありません
- [有馬徳純](https://www.wikidata.org/wiki/Q11516784) (Q11516784): 三浦朗次 の実父が 有馬徳純 ですが、父側に P40 がありません
- [藤堂高清](https://www.wikidata.org/wiki/Q29410909) (Q29410909): 藤堂高英 の実父 藤堂高清 側に P40 がありません

## 親族(P1038)に関係(P1039)が無く、向きが分からない(3件)

- [徳川家継](https://www.wikidata.org/wiki/Q366722) (Q366722): P1038 に P1039(関係)がなく、向きを判定できません
- [徳川秀忠](https://www.wikidata.org/wiki/Q314464) (Q314464): P1038 に P1039(関係)がなく、向きを判定できません
- [鍋島直興](https://www.wikidata.org/wiki/Q6956822) (Q6956822): P1038 に P1039(関係)がなく、向きを判定できません

## 養子関係らしいが、扱っていない関係(P1039)(1件)

向きが分かる関係なら config.json の p1039_roles に追加します。

- [Q180472](https://www.wikidata.org/wiki/Q180472) (Q180472): P1039 Q180472(養子縁組)は養子関係らしいラベルですが、config.json の p1039_roles に無いため養子関係として扱っていません(扱うなら p1039_roles に追加)

## 在任(P39)に開始年(P580)が無い(5件)

- [朽木元綱](https://www.wikidata.org/wiki/Q6448558) (Q6448558): 朽木藩主 の開始年がありません
- [松前慶広](https://www.wikidata.org/wiki/Q844035) (Q844035): 松前藩主 の開始年がありません
- [根津信直](https://www.wikidata.org/wiki/Q16482495) (Q16482495): 上野豊岡藩主 の開始年がありません
- [根津政次](https://www.wikidata.org/wiki/Q16482486) (Q16482486): 上野豊岡藩主 の開始年がありません
- [足利国朝](https://www.wikidata.org/wiki/Q11636757) (Q11636757): 喜連川藩主 の開始年がありません

## 征夷大将軍の在任に開始年が無い(3件)

- [Q11071640](https://www.wikidata.org/wiki/Q11071640) (Q11071640): 徳川宗家: 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません
- [Q11074321](https://www.wikidata.org/wiki/Q11074321) (Q11074321): 懐良親王: 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません
- [Q28692536](https://www.wikidata.org/wiki/Q28692536) (Q28692536): 足利将軍家: 征夷大将軍 の在任に開始年が無いため、江戸時代の在任か判断できず載せていません

## 在任の年が P39 と P1308 で食い違う(9件)

- [中山信徴](https://www.wikidata.org/wiki/Q11364059) (Q11364059): 常陸松岡藩主 の在任年が P39=1861–1871 / P1308=1861–1868 で食い違います(要文献確認)
- [井伊直勝](https://www.wikidata.org/wiki/Q5994900) (Q5994900): 彦根藩主 の在任年が P39=1608–1615 / P1308=1606–1615 で食い違います(要文献確認)
- [井伊直幸](https://www.wikidata.org/wiki/Q11161255) (Q11161255): 彦根藩主 の在任年が P39=1755–1789 / P1308=1754–1755 で食い違います(要文献確認)
- [吉川経幹](https://www.wikidata.org/wiki/Q11413061) (Q11413061): 岩国藩主 の在任年が P39=1844–1868 / P1308=1868–1868 で食い違います(要文献確認)
- [池田徳定](https://www.wikidata.org/wiki/Q11551873) (Q11551873): 鳥取新田藩主 の在任年が P39=1862–1869 / P1308=1862–1870 で食い違います(要文献確認)
- [渡辺基綱](https://www.wikidata.org/wiki/Q11562165) (Q11562165): 伯太藩主 の在任年が P39=1698–1728 / P1308=1698–1727 で食い違います(要文献確認)
- [細川興元](https://www.wikidata.org/wiki/Q11605976) (Q11605976): 谷田部藩主 の在任年が P39=1610–1616 / P1308=1616–1619 で食い違います(要文献確認)
- [蒔田広孝](https://www.wikidata.org/wiki/Q11621238) (Q11621238): 浅尾藩主 の在任年が P39=1858–1863 / P1308=1863–1871 で食い違います(要文献確認)
- [関一政](https://www.wikidata.org/wiki/Q7447188) (Q7447188): 黒坂藩主 の在任年が P39=1610–1618 / P1308=1611–1618 で食い違います(要文献確認)

## P39 と P1308 で在任の数が違う(12件)

- [中山信徴](https://www.wikidata.org/wiki/Q11364059) (Q11364059): 常陸松岡藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [井伊直定](https://www.wikidata.org/wiki/Q11161221) (Q11161221): 彦根藩主 の在任声明数が P39=2 / P1308=1 で異なります
- [井伊直幸](https://www.wikidata.org/wiki/Q11161255) (Q11161255): 彦根藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [吉川経幹](https://www.wikidata.org/wiki/Q11413061) (Q11413061): 岩国藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [大給恒](https://www.wikidata.org/wiki/Q6788054) (Q6788054): 奥殿藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [安部信発](https://www.wikidata.org/wiki/Q11451595) (Q11451595): 岡部藩主 の在任声明数が P39=2 / P1308=1 で異なります
- [徳川慶喜](https://www.wikidata.org/wiki/Q287657) (Q287657): 一橋徳川家当主 の在任声明数が P39=2 / P1308=1 で異なります
- [松前章広](https://www.wikidata.org/wiki/Q8514326) (Q8514326): 松前藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [松平乗真](https://www.wikidata.org/wiki/Q10729485) (Q10729485): 奥殿藩主 の在任声明数が P39=1 / P1308=2 で異なります
- [細川興元](https://www.wikidata.org/wiki/Q11605976) (Q11605976): 谷田部藩主 の在任声明数が P39=2 / P1308=1 で異なります
- [細川興貫](https://www.wikidata.org/wiki/Q11605990) (Q11605990): 谷田部藩主 の在任声明数が P39=2 / P1308=1 で異なります
- [蒔田広孝](https://www.wikidata.org/wiki/Q11621238) (Q11621238): 浅尾藩主 の在任声明数が P39=1 / P1308=2 で異なります

## 役職の P2389 と藩の P2388 が一致しない(3件)

- [東方藩](https://www.wikidata.org/wiki/Q141732683) (Q141732683): 役職側P2389と藩側P2388が一致しません (役職→藩: ['Q141732700'] / 藩→役職: [])
- [野本藩](https://www.wikidata.org/wiki/Q141732613) (Q141732613): 役職側P2389と藩側P2388が一致しません (役職→藩: ['Q141732701'] / 藩→役職: [])
- [鹿奴藩](https://www.wikidata.org/wiki/Q123997456) (Q123997456): 役職側P2389と藩側P2388が一致しません (役職→藩: ['Q141737845'] / 藩→役職: ['Q141733594'])

## 藩主の性別(P21)が女性(2件)

- [岡部長住](https://www.wikidata.org/wiki/Q11473877) (Q11473877): 藩主ですが性別(P21)が女性です(藩主なので系図には残しています)
- [松平信書](https://www.wikidata.org/wiki/Q11530348) (Q11530348): 藩主ですが性別(P21)が女性です(藩主なので系図には残しています)

## 性別(P21)が無い(母の可能性)(1件)

- [Q141641625](https://www.wikidata.org/wiki/Q141641625) (Q141641625): 中村吉兵衛: 性別(P21)がなく、子1人には別に実父(P22)がいるため、実父として扱っていません(母の可能性)

## 同名の藩項目が複数(4件)

- [高田藩](https://www.wikidata.org/wiki/Q10863417) (Q10863417): 同名の藩項目が複数あります: 高田藩
- [高田藩](https://www.wikidata.org/wiki/Q839422) (Q839422): 同名の藩項目が複数あります: 高田藩
- [鳥取新田藩](https://www.wikidata.org/wiki/Q141737782) (Q141737782): 同名の藩項目が複数あります: 鳥取新田藩
- [鳥取新田藩](https://www.wikidata.org/wiki/Q141737862) (Q141737862): 同名の藩項目が複数あります: 鳥取新田藩

## 肖像のライセンスを確認できない(2件)

- [大久保忠真](https://www.wikidata.org/wiki/Q8081583) (Q8081583): 画像 Ōkubo Tadazane.gif はライセンスを確認できないため、画像を表示せずリンクのみにしています
- [牧野忠雅](https://www.wikidata.org/wiki/Q6739716) (Q6739716): 画像 Toku fig03.jpg はライセンスを確認できないため、画像を表示せずリンクのみにしています

## その他(2件)

- [大垣新田藩](https://www.wikidata.org/wiki/Q10863312) (Q10863312): 本部所在地(P159)に陣屋 大垣新田藩畠村陣屋 があるため、本藩 大垣藩 の座標には合わせていません(合わせるなら config.json の branch_domains に指定)
- [大聖寺新田藩](https://www.wikidata.org/wiki/Q10863382) (Q10863382): 本藩 大聖寺藩 に座標が無いため、地図に出せません
