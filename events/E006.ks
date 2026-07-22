*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene6

	

[resetlaypos]
[bg_show storage="教室昼" bg_x="0.5" bg_y="0.5" bg_zoom="1.1"]
[se se="学校のチャイム" volume="0.5" frequency="1" block="false"]
	//生徒//
	「気を付けー、礼。」
[se se="高校の教室" volume="1" frequency="1" block="false"]
	//純一//
	「（さてと、今日はなんだか気分が乗っているから、予習でもしようか。）」
	「（よし、そうしよう……うん、苦手な数学をやろう。）」
　　　　	「（二年生から難しくなってきて、もう何が何だかわからんぞ……）」
　　　　	「（molってなんだモルって……頑張らねば！）」

[BGM bgm="MokMas42654" volume="5" loop="true"]
[chara_show name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.3"]
	//増田//
	「よお！遊ぼうぜ！」
　　　　 	//純一//
　　　　	「・・・」
　　　　	「・・・・・・」
[chara_show name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0005" brow="MST_F00_BRO_0008" blink="true" x="0.5" y="1.0" size="2.3" fade="0.3"]
	//増田//
	「おいおい無視スンナ！もくもくと教科書を開くな！」
　　　　 	//純一//
　　　　	「・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0007" effect="MST_E00_01" blink="true" x="0.5" y="1.0" size="2.3" fade="0.3"]
	//増田//
	「なんだよ～、かまってよ～、俺の最新ギャグ見てくれよ～。」
　　　　 	//純一//
　　　　	「…………まったく、折角やる気が出てきたってのに邪魔してくれちゃって。」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「何殊勝なことやってんのよ！」
[chara_shift name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「もういい、全力鬼ごっこだ、鬼はおれ。」
　　　　 	//純一//
　　　　	「おい。」
[chara_shift name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「捕まったら"ももてん"奢りな、桃の天然水！」
　　　　 	//純一//
　　　　	「ちょっとま——」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「"なっちゃん"でもいいぜ。」
　　　　 	//純一//
　　　　	「いやだから——」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「はい始めるぞ～はいいくよ～、さーん……にーい……」
　　　　　	//純一//
　　　　	「やらないぞ。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0003" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「・・・」
　　　　 	//純一//
　　　　	「・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0012" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0007" effect="MST_E00_01" fade="0.3"]
	//増田//
	「おぉいぃィ～～。」
　　　　 	//純一//
　　　　	「あのね、お前も少しは勉強に時間を充てろよ。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0004" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0007" effect="MST_E00_01" fade="0.3"]
	//増田//
	「そんなの家でやるよー。」
　　　　 	//純一//
　　　　	「（…………家ではやるんだ。）」
　　　　	「（大体、１０分だけの中休みで全力鬼ごっこって……）」
　　　　	「増田よ、君は高校卒業したらどうするつもりだ？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0003" brow="MST_F00_BRO_0005" fade="0.3"]
	//増田//
	「んお？」
　　　　 	//純一//
　　　　	「早いやつはそろそろ勉強に本腰入れる時期だぜ。」
　　　　	「どこの大学を志望するかとか、ちゃんと考えてるかい？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「うん！」
[chara_shift name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「俺はバンド一本でいくから、空いた時間は全部、」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0008" fade="0.3"]
	//増田//
	「歌の練習と曲作りに費やしてる！」
　　　　 	//純一//
　　　　	「…………おぉ……」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0011" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0005" fade="0.3"]
	//増田//	
	「すげえ楽しいんだけど、だからさ、中々遊びに行けなくてさ～。」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0011" mouth="MST_F00_MOU_0001" brow="MST_F00_BRO_0004" fade="0.3"]
	//増田//
	「あ、モチロンちゃんと勉強も最低限はやってるよ！！」
　　　　　	//純一//
　　　　	「（…………何だろうか、この気持ちは。）」
　　　　	「（眩しいぜ、増田…………）」
　　　　	「た、確かにそんだけアクティブなら、気を休める暇さえ惜しいか。」
[chara_shift name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0004" fade="0.3"]
	//増田//
	「そうそう、だからしようや全力鬼ごっこ！」
　　　　 	//純一//
　　　　	「……ってオイオイ、勘弁しろよ。」
　　　　	「腐っても元野球部の増田と帰宅部一筋の僕じゃ、結果は明らかだ！」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0007" x="0.5" y="1.0"]
	//増田//
	「なんだよォ……」
　　　　 	//純一//
　　　　	「足も速くて売るほど暇を持て余してる坂西とかを誘えって。」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0008" x="0.5" y="1.0" fade="0.3"]
	//増田//
	「あいつ逃げ足だけは早いからなぁ・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.5" y="1.0" fade="0.3"]
	//増田//
	「・・・ってオイ！」
	//純一//
	「（一人でボケてツッコんでるよ……）」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.5" y="1.0" fade="0.3"]
	//増田//
	「え～、じゃあ放課後に校庭でキャッチボールは？」
　　　　 	//純一//
　　　　	「・・・・・・」
　　　　	「・・・まあ、それ位なら・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.5" y="1.0" fade="0.3"]
	//増田//
	「反応、渋ッ！？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0004" x="0.5" y="1.0" fade="0.3"]
	//増田//
	「お前なぁ、少しは運動したり日の光を浴びたりしろよ。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0012" brow="MST_F00_BRO_0004" x="0.5" y="1.0" fade="0.3"]
	//純一//
	「余計なお世話だ。」
　　　　	「僕は体じゃなくて頭を動かすタイプなんだ。」

[bgmstop time="1.0"]
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「なになに？何のはなし？」
[BGM bgm="Mok1_Lap1" volume="5" loop="true"]
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0006" x="0.725" y="1.0" fade="0.3"]
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//増田//
	「よー桃子！」
[chara_shift name="増田" torso="MST_T00_ARM_0003" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0006" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「純一がインドアすぎて幸せホルモン不足ってハナシ。」
	//純一//
　　　　	「逆だ逆。増田が元気すぎるんだ。」
　　　　	「あと僕はビタミンもセロトニンも足りている。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「あはは、でも運動はぜったい大事だよね～。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0006" x="0.725" y="1.0" fade="0.3"]
	//桃子//
	「あんまり怠けてると、将来階段が登れなくなっちゃうよー？」
　　　　 	//純一//
　　　　	「そんな親戚みたいなお説教なんか聞きたくないよ。」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0006" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「お前さんもテニス部に入って桃子にしごかれなさい。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「あ～！そうだそうだ。」
　　　　	「ふたりに聞きたかったんだけど。」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0002" brow="MST_F00_BRO_0005" x="0.725" y="1.0" fade="0.3"]
	//純一//
	「ん、なんだ？」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「今日の放課後って空いてる？」
	//純一//
　　　　	「うん。」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「えっ、キャッチボールは……」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0011" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//桃子//
	「よかった〜！！じゃあね、」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「駅前の喫茶店、みんなで行かない？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0005" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「おー！めっちゃいいじゃん！」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0005" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「行くべ行くべ！」
	//純一//
	「いいね、何かお目当てでもあるの？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0012" brow="MST_F00_BRO_0005" x="0.725" y="1.0" fade="0.3"]
	//桃子//
	「お目当てはね～・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「ジャンボパフェ～！」
　　　　 	//純一//
　　　　	「ジャンボパフェ？」
[chara_shift name="増田" torso="MST_T00_ARM_0001" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「ジャンボパフェ！？」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0004" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//桃子//
	「最近メニューに新しく追加されてね、ずっと気になってたんだー。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.275" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//桃子//
	「いいでしょ？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//純一//
	「僕は別に構わな――」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0005" brow="MST_F00_BRO_0008" x="0.65" y="1.0" fade="0.3"]
	//増田//
	「ちょっと待った！！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.225" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「！？」
　	//純一//
　　　　	「うん？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0008" x="0.65" y="1.0" fade="0.3"]
	//増田//
	「おい桃子…………」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0008" x="0.65" y="1.0" fade="0.3"]
	//増田//
	「…………ダイエットはどうなった？」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「うぅ…………」
	//純一//
　　　　	「なんだ、お前、ダイエット始めたのか。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0005" brow="MST_F00_BRO_0008" x="0.65" y="1.0" fade="0.3"]
	//増田//
	「夏に向けて本格的に痩せようって、誓ったよな！？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0005" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//増田//
　　　　	「――――ふたりで一緒に！！」
　　　　　	//純一//
　　　　	「（…………お前もかよ。）」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「……でもでも、部活の大会もあるし……」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.25" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「ちょっとだけ！ちょっとだけご褒美を――」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「いいのか？本当に。」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「その少しの気の緩みが成否を分かつのだ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//桃子//
	「・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0010" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「このまま夏になってみろォ、たまげるぜ？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0008" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「俺のお腹は引っ込んでも……桃子、お前はどうかな……？」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「・・・」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0004" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「誰かさんがもぐもぐ食べ続けてる間も、俺は大好物のラーメンを我慢。」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0004" x="0.625" y="1.0" fade="0.3"]
	//増田//
	「今をとるか未来をとるか。まさにアリとキリギリスのように――」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.2" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「でも増田、昨日ラーメン食べたでしょ。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.725" y="1.0" fade="0.3"]
	//増田//
	「――――なッ！？」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.25" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「楽しそうに話してたよね、吉祥寺に評判のラーメン屋があるって。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0006" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//増田//
	「・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU03_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" x="0.25" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「ラーメン二郎の支店なんでしょ？」
　　　　	「不良が落書きして、ラーメン{boten:生}郎になってるんだよね。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0007" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//増田//
	「・・・」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_01" mouth="MMK_F02_MOU04_02" brow="MMK_F02_BRO00_00" cheek="MMK_F02_CHE00_00" x="0.25" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「何だっけ、マシマシ？にんにくとか野菜とか、」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_01" mouth="MMK_F02_MOU00_01" brow="MMK_F02_BRO03_00" cheek="MMK_F02_CHE00_00" x="0.25" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「それはそれは凄い量を注文できるんだって、言ってたよね～？」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_02" mouth="MMK_F02_MOU03_00" brow="MMK_F02_BRO00_00" cheek="MMK_F02_CHE00_00" x="0.25" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0007" mouth="MST_F00_MOU_0018" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//増田//
	「・・・」
	//純一//
　　　　	「……おい、どうなんだ？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//増田//
	「…………ははっ、嘘だよ嘘、うそっぱち！」
　　　　	「そうだよ、そうに決まって――」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" x="0.35" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「嘘じゃないよ～。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0004" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//増田//
	「！？」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" x="0.35" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「だって・・・」
	//純一//
	「・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" x="0.35" y="1.1" size="2.3" fade="0.3"]
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0004" effect="MST_E00_02" x="0.75" y="1.0" fade="0.3"]
	//桃子//
	「だって増田・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" x="0.4" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「口がまだにんにくクサいもん！！」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.8" y="1.0" fade="0.3"]
	//増田//
	「…………！！」
	//純一//
　　　　	「……言われてみれば、確かに。」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_02" mouth="MMK_F02_MOU04_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE00_00" x="0.35" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「………………」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0005" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.8" y="1.0" fade="0.3"]
	//増田//
	「…………ち、」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0005" brow="MST_F00_BRO_0008" effect="MST_E00_02" x="0.8" y="1.0" fade="0.3"]
	//増田//
	「ちきしょぉお～～！！」
[chara_hide name="増田"　eye="eye1" mouth="mouth1" x="0.5" y="0.5"]
[se se="学校の廊下を走る" volume="0.5" frequency="1" block="false"]
	//純一//
	「あっ、おい！」
　　　　	「結局どうするんだよ！……ったく。」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE01_00" mouth="MMK_F02_MOU00_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE00_00" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「ふふふ、まったく余計な事言うから。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「私は何としてもジャンボパフェを食べるのよ。ね、純一？」
　　　　 	//純一//
　　　　	「……お、おう。」
　　　　	「そうだな……」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「きまり～！」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「じゃあ今日の放課後、正門前で集合ね～！」

[chara_hide name="桃子" fade="0.3"]
[bgmstop time="5"]
[se se="学校の廊下を走る" volume="0.5" frequency="1" block="false"]
	//純一//
	「ああ・・・」
　　　　	「行っちゃった・・・」
　　　　	「（こんな感じで、桃子と喫茶店へ行く約束をした。）」
　　　　	「（あいつ、食べ物のことになると目の色が変わるな……）」
	[scroll-stop]