*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene5|


[resetlaypos]
[bg_show storage="classroomBack" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[se se="学校のチャイム" volume="0.5" frequency="1" block="false"]
[chara_show name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
[bgm bgm="MokLap1" volume="0.5" loop="true"]
	//桃子//
	「じゅんいちー！」
	//純一//
	「ん？どうした桃子。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「ねね、橘は目玉焼きに何をかける？」
	//純一//
	「なんだい藪から棒に。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「あのね、今朝の話なんだけど。」
	//純一//
	「うん。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「うちの朝食は大体、マーガリンを塗ったトーストなんだけどね。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「食パンを切らしちゃってたから、今朝はご飯と目玉焼きだったの。」
	//純一//
	「ほう。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「そしたらね、なんと＿＿！」

[fadeout color="black" time="1.0"]
[bgm bgm="◎_26_Shin_Nichijo A" volume="0.5" loop="true"]
[bg_show storage="桃子の部屋" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_hide name="桃子" fade="0.15"]
[fadein time="1.0"]
[chara_show name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_show name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
[chara_show name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_02" mouth="NOK_F01_MOU_02" brow="NOK_F01_BRO_01" blink="true" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//静//
	「は～い、出来たわよ～。」
	「ほら運んで運んで。」
	//桃子//
	「はーい。」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" blink="true" x="0.5" y="0.75" size="1.6" fade="0.15"]
	//杏//
	「ほらパパ、これ今朝の新聞。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_13" brow="NOK_F01_BRO_02" effect="NOK_F01_E00_01" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「ふわぁ～あ。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_05" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_02" effect="NOK_F01_E00_01" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「ん、ありがとう。」
[se se="お皿を置く" volume="0.5" frequency="1" block="false"]
	//桃子//
	「おー！なんだか新鮮だね～目玉焼き。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_01" mouth="NOK_F01_MOU_07" brow="NOK_F01_BRO_02" effect="" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「あれ？今日はトーストじゃないのか。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0010" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「そうよ、誰かさんが頼んだパンを買い忘れたからね。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_05" mouth="NOK_F01_MOU_02" brow="NOK_F01_BRO_01" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「……」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
	//杏//
	「もーいいから早く食べようよ、おねぇが死んじゃうよ。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_01" mouth="NOK_F01_MOU_08" brow="NOK_F01_BRO_02" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0003" mouth="ANZ_F00_MOU_0002" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
	//桃子//
	「お腹減ったよ～。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_02" effect="" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「……はいはい、それじゃあ＿＿」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_04" brow="NOK_F01_BRO_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0011" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
	//四人//
	「いただきま～す。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_04" mouth="NOK_F01_MOU_04" brow="NOK_F01_BRO_01" x="0.8" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[se se="お箸で食べる" volume="0.5" frequency="1" block="false"]
	//直樹//
	「よし、母さん、ソースを取ってくれ。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「ソース？一体何に使うのかしら？」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_04" mouth="NOK_F01_MOU_07" brow="NOK_F01_BRO_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「何っておまえ……そりゃ目玉焼きにかけるに決まってるだろう。」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0009" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0008" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「…………」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_04" mouth="NOK_F01_MOU_06" brow="NOK_F01_BRO_02" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「…………？」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0008" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「あなた……目玉焼きにソースをかけるの……？」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_06" brow="NOK_F01_BRO_02" effect="" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「そりゃあ、ソースが一番美味いだろう。」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0009" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「何言ってんのよ！塩よ、し・お！」
	//桃子//
	「えぇー、お醤油がベストだよ！」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_04" brow="NOK_F01_BRO_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「ソースはね、コクが増して食べてる感がイチバン出るんだ！」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0002" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「素材の味を一番引き出せるのは塩なのよ。」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0009" mouth="ANZ_F00_MOU_0010" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「きっと足立区のお生まれだから繊細な味がわからないのね。」
	//桃子//
　	「素材が同じたまごかけご飯には醤油かけてるじゃん！」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" x="0.5" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_05" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//直樹//
	「なんだったらソースでご飯を食べたっていいくらいなんだから。」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//静//
	「ちょっと、それが毎日献立を考える人の前でいうこと？」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_02" mouth="NOK_F01_MOU_05" brow="NOK_F01_BRO_01" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
	//静//
	「お話にならないわ。」
	//桃子//
	「たまごかけご飯には醤油かけてるじゃん！！」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_02" brow="NOK_F01_BRO_04" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//三人//
	「むむむ……」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0002" x="0.5" y="0.75" size="1.6" fade="0.15"]
	//杏//
	「ーーふふふ、やっぱり目玉焼きにはマヨネーズが一番ね。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_13" brow="NOK_F01_BRO_05" effect="NOK_F01_E00_02" x="0.8" y="0.75" size="1.6" fade="0.15"]
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0013" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" x="0.2" y="0.75" size="1.6" fade="0.15"]
	//三人//
	「それはない！！！」



[fadeout color="black" time="1.0"]
[bgm bgm="MokLap1" volume="0.5" loop="true"]
[chara_hide name="直樹" fade="0.15"]
[chara_hide name="杏" fade="0.15"]
[chara_hide name="静" fade="0.15"]
[bg_show storage="classroomBack" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
[fadein time="1.0"]
	//桃子//
	「＿＿って感じでね、みーんなバラバラなの！」
	//純一//
	「（朝っぱらから随分微笑ましい話だな……）」
	「（それに比べて家では独り、学校では冴えない友人と食べてる僕は＿＿）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「純一？どうしたの？」
　	//純一//
　　　	「ん！？あ、いや、トホホだよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「とほ……？」
　　　　	//純一//
　　　	「（しまった！！）」
　　　	「いや、いいんだ、何でも無いよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「ふ～ん……」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「それでそれで、貴方はどうするの？」
　　　　	//純一//
　　　	「……え？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「目玉焼きだよー！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「あなたのお好みは？」
　　　　	//純一//
　　　	「僕か……僕は……」


[choice_1 option1="ソース" option2="塩"　option3="醤油"　option4="マヨネーズ"　option5="ケチャップ"]
[if condition="choice_1==1"]
	//純一//
	「僕はソースかなあ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「言うと思ったぁ……」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「ほんとあなたってって味濃いの好きよね。」
[endif]

[if condition="choice_1==2"]
	//純一//
　　　	「僕は塩かな。」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「塩……！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU00_01" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「貴方もなかなか通なとこあるのね……」
[endif]

[if condition="choice_1==3"]
　　　　	//純一//
　　　	「僕は醤油派だな。」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「えー私と一緒だ！」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「やったぁ……えへへ……」
[endif]

[if condition="choice_1==4"]
　　　　	//純一//
　　　	「無難にマヨネーズかなあ。」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
　　　　	「＿＿マヨネーズ！？」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「あなたにそんな趣味があったとは……」
[endif]

[if condition="choice_1==5"]
　　　　	//純一//
　　　	「僕はケチャップかな。」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「＿＿けちゃっぷ！？」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「えへへ、あなたも可愛らしいところあるんだねえ。」
[endif]


	[scroll-stop]