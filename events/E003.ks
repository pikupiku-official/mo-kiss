*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene3|
[resetlaypos]

[bg_show storage="school"  bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[BGM bgm="MmkBgm1" volume="0" loop="true"]
	
　　　　	//純一//
　　　　	「（ぼちぼち下校するか。」
　　　　	「今日は特に何もないからまっすぐ帰ろう。）」

[bg_show storage="商店街"  bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]

	//純一//
	「（駅前の商店街はずっと変わらないな。）」
[SE 自転車のベル音　チリンチリン]
	//純一//
	「ん？なんだ？」

[chara_show name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_09" mouth="NOK_F00_MOU_12" brow="NOK_F00_BRO_02" blink="true" x="0.5" y="0.9" size="1.8" fade="0.15"]
	//？？//
	「よっ！純くん！」
　　　　 	//純一//
　　　　	「あ、おじさん！こんにちは。」
　　　　	「（この人は桃子のお父さんの愛沼直樹さんだ。）」
　　　　	「（家によく遊びに行っていた僕は、彼との付き合いも長い。）」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「こんにちは。どうだい、最近の調子は。」
　　　　 	//純一//
　　　　	「元気にやってます。でも近頃は蒸し暑くて敵いません。」
[chara_shift name="直樹" torso="NOK_T00_ARM02_CLO00" eye="NOK_F00_EYE_09" mouth="NOK_F00_MOU_12" brow="NOK_F00_BRO_02" fade="0.15"]
	//直樹//
	「ははは、同感だ。梅雨の時期は仕方ない。」
　　　　	「綺麗な紫陽花と父の日があることを除けば、六月は好かん。ははは。」
　　　　	//純一//
　　　　	「（直樹おじさんは街の警察官として勤めていて交友関係が広い。」
　　　　	「最近は愛沼家に顔を出していないので、会うのは久方ぶりだ。）」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_12" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「おっと、そいつは夏服だな。」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_04" fade="0.15"]
	//直樹//
	「そうだ、学校の方は上手くいってるか？」
	//純一//
　　　　	「どうでしょう。」
　　　　	「特に代わり映えしない毎日ですが……」
　　　　	「ぼちぼちやってますかね。」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「ぼちぼち、ね……」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_01" mouth="NOK_F01_MOU_04" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「ふん、君も大人びたもんだな。」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_09" mouth="NOK_F01_MOU_11" brow="NOK_F01_BRO_02" fade="0.15"]
	//直樹//
	「やんちゃ坊主だった頃が懐かしいよ。」
　　　　 	//純一//
　　　　	「やんちゃ坊主って。」
[chara_shift name="直樹" torso="NOK_T01_ARM02_CLO00" eye="NOK_F01_EYE_05" mouth="NOK_F01_MOU_11" brow="NOK_F01_BRO_02" fade="0.15"]
	//直樹//
	「桃子と毎日泥だらけになるまで遊んでさ。」
　　　　 	//純一//
　　　　	「いつの話ですか。」
[chara_shift name="直樹" torso="NOK_T00_ARM02_CLO00" eye="NOK_F00_EYE_02" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「覚えてるか？ある時君らを公園まで迎えに行ったら、かくれんぼしてた桃子が全然見当たらなくて。」
　　　　 	//純一//
　　　　	「……？」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_03" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「日が落ち込んでもどこにもいなくて二人でそこら中探して。」
　　　　 	//純一//
　　　　	「……あったあった、遊んでたら忽然と消えちゃったんだ。」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_04" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「いよいよ大事になるかってところで純くんがようやく見つけたと思ったら。」
　　　　 	//純一//
　　　　	「スパゲッティ食べてた。喫茶店で。」
　　　　	「小学生のくせに大盛り。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_03" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「長いこと隠れ続けて、おなか減っちゃったんだろな。」
　　　　 	//純一//
　　　　	「懐かしいな……ありましたね、そんな事。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_05" fade="0.15"]
	//直樹//
	「この年まで生きてきて、あの日ほど焦った時は無いな。」
　　　　	//純一//
　　　　	「ホントですよ。」
　　　　	「僕より桃子の方がよっぽど問題児でしたよ。」
[chara_shift name="直樹" torso="NOK_T00_ARM02_CLO00" eye="NOK_F00_EYE_02" mouth="NOK_F00_MOU_04" brow="NOK_F00_BRO_02" fade="0.15"]
	//直樹//
	「どうだか。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_03" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_02" fade="0.15"]
	//直樹//
	「君の恥ずかしーい思い出や痴態を沢山覚えているけど。」
　　　　 	//純一//
　　　　	「勘弁してくださいよ。」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_09" mouth="NOK_F00_MOU_11" brow="NOK_F00_BRO_03" fade="0.15"]
	//直樹//
	「ははは、いや悪い悪い、ずっと子供のままのイメージなんだ。」
　　　　	//純一//
　　　　	「おじさんの方はどうですか、お変わりありませんか。」
[chara_shift name="直樹" torso="NOK_T00_ARM02_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_07" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「それがさ、聞いてくれよ、純くん。」
　　　　 	//純一//
　　　　	「なんです？」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_02" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「知ってるか？最近ね、あちこちで動物がくたばっちまってんだ。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_03" mouth="NOK_F00_MOU_02" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「やれスズメとか猫とかがさ。その数が変に多くてだな。」
	//純一//
　　　　	「おっかないですね、原因は何ですか。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_02" mouth="NOK_F00_MOU_05" brow="NOK_F00_BRO_03" fade="0.15"]
	//直樹//
	「それが一切判らない。」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_06" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「だが、よく判らないモノはワタシらの出番。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「だから、体は元気なんだけど、その回収に追われてるんだ、最近は。」
　　　　 	//純一//
　　　　	「この平和な街で、どういう事なんでしょうね。」
　　　　	「お勤めご苦労様です。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_04" mouth="NOK_F01_MOU_04" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「お陰で街中行ったり来たりだ、学生時代の特訓を思い出すよ。」
	//純一//
　　　　	「そっか、おじさんも桃子と同じテニス部でしたもんね。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_01" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「ああ。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_01" mouth="NOK_F01_MOU_08" brow="NOK_F01_BRO_02" fade="0.15"]
	//直樹//
	「部活といえば、純くんはまだ帰宅部なのかい？」
　　　　	//純一//
　　　　	「なっ！ え、ええ、まぁ。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_02" mouth="NOK_F01_MOU_11" brow="NOK_F01_BRO_05" fade="0.15"]
	//直樹//
	「感心しないなあ、彼女は？」
　　　　 	//純一//
　　　　	「いえ、残念ながら。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_03" mouth="NOK_F01_MOU_12" brow="NOK_F01_BRO_03" fade="0.15"]
	//直樹//
	「かーっ！ こんな時間に一人で帰ってきてるもんなぁ。そりゃそうか。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_02" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_05" fade="0.15"]
	//直樹//
	「おじさんの頃の男児は皆ガンガンいってたけどな。」
　　　　 	//純一//
　　　　	「……僕は黙っててもモテますから！」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_09" mouth="NOK_F00_MOU_12" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「ははは、ま、学生は勉学に励みなさい。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_01" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「ほら、これでアイスでも買うといい。」
　　　　 	//純一//
　　　　	「あっ、ありがとうございます。」
[chara_shift name="直樹" torso="NOK_T00_ARM03_CLO00" eye="NOK_F00_EYE_03" mouth="NOK_F00_MOU_01" brow="NOK_F00_BRO_01" fade="0.15"]
	//直樹//
	「でも、青春は今しかないぞ、青年。」
　　　　	//純一//
　　　　	「……はい、頑張ります。」
[chara_shift name="直樹" torso="NOK_T00_ARM01_CLO00" eye="NOK_F00_EYE_09" mouth="NOK_F00_MOU_11" brow="NOK_F00_BRO_05" fade="0.15"]
	//直樹//
	「応援してるよ。相手が桃子だった場合は話が変わるがね。」
[chara_shift name="直樹" torso="NOK_T01_ARM01_CLO00" eye="NOK_F01_EYE_09" mouth="NOK_F01_MOU_01" brow="NOK_F01_BRO_01" fade="0.15"]
	//直樹//
	「それじゃ！」


[chara_hide name="直樹" fade="0.15"]
[SE 自転車のベル音　チリンチリン]
	//純一//
	「(……)」
　　　　	「（行ってしまった。相変わらずフランクな人だ。）」
　　　　	「（ふぅ……なんだか暑いな。」
　　　　	「折角だ、アイスでも買って帰ろう。）」

	[scroll-stop]