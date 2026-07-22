*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene2

	

[resetlaypos]
[bg_show storage="教室昼" bg_x="0.5" bg_y="0.5" bg_zoom="1.1"]
[se se="学校のチャイム" volume="1" frequency="1" block="false"]
	//生徒//
	「気を付けー、礼。」

[se se="高校の教室" volume="5" frequency="1" block="false"]
	//純一//
	「（ようやっと終わったぜ、疲れた……）」
	「（しかし腹が減った、昼時は空腹すぎて集中できないな……）」
	「（さて、学食へ向かうとしよう。）」
	「（まずは増田と合流しなければ。今日の定食は何だろうな。）」

[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
[BGM bgm="Mok_Lap1" volume="5" loop="true"]
	//桃子//
	「ねえねえ、ちょっと聞いてよぉ。」
	//純一//
	「ん？桃子か。どうしたんだ、そんな深刻な顔して。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「あのね、あんまりおなかペコペコだったから、」
	「さっきの休み時間にシュークリームをつい食べちゃったの……」
	//純一//
	「あぁ、購買のやつだろ。クリームたっぷりの。」
	「あのシュークリームおいしいもんな。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「そう、そうなの！」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE00_00" fade="0.3"]
	//桃子//
	「……でもね。」
	「シュークリームの上にお弁当まで食べちゃったら・・・」
	//純一//
	「確かにあのクリームは腹に溜まるよなあ……」
	「……なるほど、おなか一杯になっちゃったのか！」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「違うの！」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE01_00" fade="0.3"]
	//桃子//
	「まだ食べれちゃうんだけど・・・」
	//純一//
	「じゃあ問題無いじゃないか。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE01_00" fade="0.3"]
	//桃子//
	「いや、その・・・」
　	//純一//
	「？」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" fade="0.3"]
	//桃子//
	「……体重が、」
	//純一//
	「へ？」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU05_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" fade="0.3"]
	//桃子//
	「……体重が気になったりとかあるの！」
	//純一//
	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" fade="0.3"]
	//桃子//
	「・・・」
	//純一//
	「……あっはっはっは！」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「ちょっと！！」
	//純一//
	「難儀なもんだなあ、女っていうのは。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「女子のコトぜんっぜん分かってないんだから！」
	//純一//
	「いやいや、すまないすまない……ふふッ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「もー、と・に・か・く！」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「せっかく作ったお弁当が宙ぶらりんになっちゃったの……！」
	//純一//
	「お手製とは結構な事で。」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//桃子//
	「持って帰ってもしょうがないでしょう？」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//桃子//
	「どーしましょ・・・」
	//純一//
　	「早いうちに食べないと弁当ダメになっちゃうもんな。」
　　　　	「だんだん暑くなってきたし。」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE01_02" mouth="MMK_F02_MOU01_00" brow="MMK_F02_BRO01_00" cheek="MMK_F02_CHE00_00" fade="0.3"]
	//桃子//
	「う～ん・・・」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE01_00" mouth="MMK_F02_MOU04_02" brow="MMK_F02_BRO03_00" cheek="MMK_F02_CHE00_00" fade="0.3"]
	//桃子//
	「あ、そうだ！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「あなた、このお弁当食べない！？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//純一//
	「なッ！？」
	「（……まずい、まずいぞ、」
　　　　	「桃子の手作り弁当を食うのは男子からの視線が痛い！……）」
　　　　	「……いやー僕は普段 増田と学食で＿＿＿」

[SE 走る足音（近づく・大きくなっていく）]
[SE　大きく教室のドアを開ける音]

[chara_show name="増田"　eye="eye1" mouth="mouth1" x="0.5" y="0.5"]
[桃子　驚き顔に変化]
　　　　 	//純一//
　　　　	「おっ！増田、良いところに来た！」
　　　　	「学食行こうぜ！」
	//増田//
　　　　	「ごめん！それがさ、マエケンに呼ばれちった！」
　　　　	「飯は各自済ませるという事で、じゃ！」
[chara_hide name="増田"　eye="eye1" mouth="mouth1" x="0.5" y="0.5"]

[SE 走る足音（遠ざかる・小さくなっていく）]

　　　　 	//純一//
　　　　	「あっ、おい！」
　　　　	「（……軽音楽部の鬼顧問、」
　　　　	「前山田健吾郎に呼ばれたんじゃ仕方無いか……）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU03_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「えーと、どうかな？」
　　　　 	//純一//
　　　　	「……ほら、あれだよ、女友達とかに分けて＿＿＿」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「皆ダイエットしてて頼めないよぉ。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「いいでしょ、親友のためだと思って！」
　　　　 	//純一//
　　　　	「（桃子にはファンクラブまであるとかないとか・・・」
　　　　	「確かに食べたいが、事なかれ主義の僕には荷が重すぎ＿＿＿」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「おねがい！」
　　　　 	//純一//
　　　　	「・・・」
　　　　	「・・・」
　　　　	「・・・まぁ、学食代も浮くしな！」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//桃子//
	「ほんと？やったー！」
　　　　 	//純一//
　　　　	「（もうどうにでもなれだ……」
　　　　	「……これで明日からいじめられたらどうしよ……）」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//桃子//
	「はいこれっ！」
	「お口に合うかわからないけど！」
　　　　 	//純一//
　　　　	「で、では早速……」
　　　　	「桃弁、拝見させていただきます……」


[SE お弁当を開ける音　パカ]
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//純一//
	「・・・」
　　　　	「（ゴクリ・・・）」
　　　　	「（これは相当・・・」
　　　　	「相当美味しそうだぞ・・・！）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" fade="0.3"]
	//桃子//
	「ふふーん、どう？」
　　　　 	//純一//
　　　	「（運動部らしく からあげ弁当か。ご飯にはおかか海苔が。」
　　　　	「茶色いラインナップを野菜の彩りが中和している。）」
　　　　	「……中々に美味しそうだ。」
	//桃子//
　　　　	「最近ね、お母さんと料理作り頑張ってるんだー。」
　　　　 	//純一//
　　　　	「……昔はあんなにやんちゃだったのに、随分と女の子らしくなったもんだな。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「えへへ……そうかな。」
　　　　 	//純一//
　　　　	「じゃあ、いただきます。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「は～い。」
　　　　 	//純一//
　　　　	「（モグモグ・・・）」
　　　　	「（モグモグ・・・）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//純一//
	「（なるほど、オーソドックスなお弁当だが……」
　　　　	「それぞれの具材の調和が絶妙で……うまいぞ！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「どう、かな・・・？」
　　　　 	//純一//
　　　　	「（特にこのきんぴらごぼうが絶品だな……」
　　　　	「どこか懐かしい味がする。）」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「ちょっとぉ、そんな真剣な顔でたべないでよぉ……」
　　　　 	//純一//
　　　　	「（そうか、思い出したぞ！」
　　　　	「これは昔、桃子のお母さんが作ってくれたきんぴらの味だ。）」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE03_01" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「ねーーえーー。」
　　　　 	//純一//
　　　　	「（旨い……」
　　　　	「こういうのでいいんだよ、こういうので……）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「どう、ですか・・・？」

[choice_1 option1="ちょっとからかう" option2="素直に褒める"]
[if condition="choice_1==1"]
　　　　 	//純一//
　　　　	「（うーん、ここで素直に褒めるのはどこか悔しい……）」
　　　　	「……まあ、」
　　　　	「……意外に……悪くはなかった。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「・・・」
　　　　 	//純一//
　　　　	「なかなか楽しませて頂いたよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「えー、もっと素直に褒めてよぉ。」
　　　　 	//純一//
　　　　	「僕を満足させるには あれだな、」
　　　　	「人生経験がちっと足りなかったな。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「ちょっとー。」
　　　　 	//純一//
　　　　	「美味しかった、美味しかったよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「もー！」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_02" mouth="MMK_F02_MOU05_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE01_00" fade="0.3"]
	//桃子//
	「別にいいもん、今度はぎゃふんと言わせるから！」
　　　　 	//純一//
　　　　	「はっはっは、これからの成長が楽しみだ。」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE03_01" mouth="MMK_F02_MOU02_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE01_00" fade="0.3"]
	//桃子//
	「なにそれー。」
[endif]

[if condition="choice_1==2"]
　　　　 	//純一//
　　　　	「（こんなうまい弁当、なかなか無かったな。）」
　　　　	「・・・桃子よ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「はい・・・」
　　　　 	//純一//
　　　　	「めちゃくちゃうまかった！」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//純一//
　　　　	「これは店が出せる味だぞ！」
	//桃子//
　　　　	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE01_00" fade="0.3"]
	//桃子//
	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" fade="0.3"]
	//桃子//
	「……えへへ、ほんと？」
　　　　 	//純一//
　　　　	「ほんと、毎日だって食べたいくらいさ！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「もう、言い過ぎだってばーー。」
[endif]


[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//純一//
	「あっはっはっは！」
	「（休み時間はこうして桃子の桃弁を食べて過ごした。）」
	「（男子陣からの白い視線を感じながら＿＿＿）」
	[scroll-stop]