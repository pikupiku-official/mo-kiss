*start
;@expression-status: human_confirmed

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*GDscene2


[resetlaypos]
[bg_show storage="改教室昼" bg_x="0.5" bg_y="0.5" bg_zoom="1.1" fade="0.0"]
[bgm bgm="MokLap1" volume="0.5" loop="true"]
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.3"]
	//{name}//
	「俺がこの弁当、食べていいのか・・・？」
[chara_shift name="桃子" torso="MMK_T00_ARM18_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「だ～か～ら～。さっきから良いって言ってるでしょー！」
	「私はもうお腹いっぱいになっちゃったの！」
[chara_shift name="桃子" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU06_00" effect="MMK_E00_01" fade="0.15" move="linear"]
	//{name}//
	「分かったよ。食べるよ。食べるからさ。」
	「・・・じゃ、じゃあ。いただきます。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO03_00" effect="" fade="0.15"]
	//桃子//
	「は～い。」
　　　　 	//{name}//
　　　　	「（モグモグ・・・）」
　　　　	「（モグモグ・・・）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	//{name}//
	「（なるほど、オーソドックスなお弁当だが・・・」
　　　　	「それぞれの具材の調和が絶妙で・・・うまいぞ！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「どう、かな・・・？」
　　　　 	//{name}//
　　　　	「（特にこのきんぴらごぼうが絶品だな・・・」
　　　　	「どこか懐かしい味がする。）」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「ちょっとぉ、そんな真剣な顔でたべないでよぉ。」
　　　　 	//{name}//
　　　　	「（そうか、思い出したぞ！」
　　　　	「これは昔、桃子のお母さんが作ってくれたきんぴらの味だ。）」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE03_01" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「ね～え～！」
　　　　 	//{name}//
　　　　	「（旨い・・・）」
　　　　	「（こういうのでいいんだよ、こういうので。）」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「それで、その・・・」
	「どう、ですか・・・？」

[choice_1 option1="ちょっとからかう" option2="素直に褒める"]
[if condition="choice_1==1"]
　　　　 	//{name}//
　　　　	「（うーん、ここで素直に褒めるのはどこか悔しい・・・）」
　　　　	「・・・まあ、」
　　　　	「意外に悪くはなかった。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「・・・」
　　　　 	//{name}//
　　　　	「なかなか楽しませて頂いたよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="" fade="0.3"]
	//桃子//
	「えー、もっと素直に褒めてよぉ。」
　　　　 	//{name}//
　　　　	「僕を満足させるにはあれだな、」
　　　　	「人生経験がちっと足りなかったな。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「ちょっとー。」
　　　　 	//{name}//
	「あはは。」
　　　　	「美味しかった、美味しかったよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「もー！」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE00_02" mouth="MMK_F02_MOU05_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE01_00" fade="0.3"]
	//桃子//
	「別にいいもん、今度はぎゃふんと言わせるから！」
　　　　 	//{name}//
　　　　	「はっはっは、これからの成長が楽しみだ。」
[chara_shift name="桃子" torso="MMK_T02_ARM00_CLO00" eye="MMK_F02_EYE03_01" mouth="MMK_F02_MOU02_00" brow="MMK_F02_BRO02_00" cheek="MMK_F02_CHE01_00" fade="0.3"]
	//桃子//
	「なにそれ～。」
[endif]

[if condition="choice_1==2"]
　　　　 	//{name}//
　　　　	「（こんなうまい弁当、なかなか無かったな。）」
　　　　	「・・・桃子よ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	//桃子//
	「はい・・・」
　　　　 	//{name}//
　　　　	「めちゃくちゃうまかった！」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	//{name}//
　　　　	「これは店が出せる味だぞ！」
	//桃子//
　　　　	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE01_00" effect="" fade="0.3"]
	//桃子//
	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" fade="0.3"]
	//桃子//
	「・・・へへ、ほんと？」
　　　　 	//{name}//
　　　　	「ほんと、毎日だって食べたいくらいさ！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	//桃子//
	「もう、言い過ぎだってば～。」
[endif]


[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" effect="" fade="0.3"]
	//{name}//
	「あっはっはっは！」
	「（休み時間はこうして桃子の桃弁を食べて過ごした。）」
	「（男子陣からの白い視線を感じながら――）」
	[scroll-stop]