[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.90767825" size="2.50528314" fade="0.15"]
[bg_show storage="教室昼" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[bgm bgm="MokLap1.mp3" volume="0.55" loop="true" fade="0.0"]
	//純一//
	「行ってないだろ、部活」
[chara_shift name="桃子" template="驚き" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_02" fade="0.15"]
	//桃子//
	「…………」
	//純一//
	「それでも学校に残ってる訳はなんだ」
	「……こんな時間まで」
[chara_shift name="桃子" template="本当かなあ？斜め" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_00" brow="MMK_F01_BRO04_00" cheek="MMK_F01_CHE03_00" effect="MMK_E01_01" fade="0.15"]
	//桃子//
	「…………」
	//純一//
	「…………家」
	「家に……帰れないのか？」
[chara_shift name="桃子" eye="MMK_F01_EYE03_00" fade="0.15"]
	//桃子//
	「…………」
; 表情の変化で演出したい
[chara_shift name="桃子" left="0.03976234" top="0.0" zoom="2.50528314"]
	//桃子//
	「…………なんで」
	//純一//
	「…………」


[chara_shift name="桃子" template="何言ってんだこいつ" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" x="0.40334528" size="2.50528314" fade="0.15"]
	//純一//
	「（天真爛漫な桃子が、最近はどこか上の空で元気がない。）」
[chara_shift name="桃子" template="拗ねる・ぷくー斜め" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU04_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE03_00" x="0.54731237" y="0.90767825" size="2.50528314" fade="0.15"]
	//純一//
	「（何か大きなことに頭を悩ませているみたいに。）」
	//純一//
	「（[seed id="MOMOKO_TP1_001"]そして、家族の話題を避けているようだ。[/seed]）」
[chara_shift name="桃子" x="0.65251502" fade="0.15" move="linear" time="600"]
	//純一//
	「（普段は嬉々として話していたけど、今は触れられないように立ち回っている。）」
	//純一//
	「（[seed id="MOMOKO_TP1_002"]最後に、こんな時間まで部活にもいかずに時間を潰している。[/seed]）」
	「（[seed id="MOMOKO_TP1_003"]これは桃子に家に帰りたくない事情があるとみていいだろう。[/seed]）」
[chara_shift name="桃子" template="聞き上手" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO05_00" cheek="MMK_F00_CHE04_00" x="0.5" fade="0.15"]
	//純一//
	「（この三つをつなげれば、桃子が隠していることが分かるはずだ。）」

; ～種システム発動！入力！収束～

[seed_answer turning_point="MOMOKO_TP1" prompt="桃子が家に帰りたくない理由は何だろう？"]
[chara_shift name="桃子" template="驚き" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.15"]
	「・・・そうだろ？」

	//桃子//
	「！！」
[chara_shift name="桃子" eye="MMK_F00_EYE00_01" brow="MMK_F00_BRO04_00" fade="0.15"]
	//桃子//
	「・・・なんで。」
	//純一//
	「……知ってるから、僕」
[chara_shift name="桃子" template="照れ提案斜め" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE01_00" fade="0.15"]
	//桃子//
	「………え…」
	//純一//
	「桃子がずっと頑張ってること、」
[chara_shift name="桃子" eye="MMK_F01_EYE01_01" fade="0.15"]
	//純一//
	「僕は知ってる。」
	//桃子//
	「…………」
[chara_shift name="桃子" eye="MMK_F01_EYE00_00" fade="0.15"]
	//純一//
	「だから話してくれ」
	「好きなこと、楽しいこと、辛いこと、悲しいこと。」
; --- new step ---
//speaker//
「セリフ」

[chara_shift name="桃子" effect="MMK_E01_02" fade="0.15"]
	//純一//
	「何でも話して欲しいんだ。」
[chara_shift name="桃子" mouth="MMK_F01_MOU04_00" fade="0.15"]
	//桃子//
	「・・・」
	//純一//
	「僕は、いつだって、君の味方だから。」
[chara_shift name="桃子" template="ドヤ顔" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_00" fade="0.15"]
	//桃子//
	「――！」
[chara_shift name="桃子" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//桃子//
	「・・・」
	「・・・ダメなんだよ、ほんとは。」
	//純一//
	「ははは、そんなの知るもんか。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" brow="MMK_F00_BRO05_00" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="疑い照れ斜め" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE01_00" fade="0.15"]
	//桃子//
	「・・・あのね、星が現れた日の夜――」


; 中略。


[fadeout color="black" time="1.0"]
[cg_show storage="MMK_03_011" fade="0.3"]
[bgm bgm="◎_12_A Voyage to the center of the cosmos ２楽.mp3" volume="0.5" loop="true" fade="0.0" start="37.76"]
[fadein time="1.0"]
	//桃子//
	「ふたりとも、大好き。」
[cg_shift storage="MMK_03_010" time="600" fade="0.3"]
	//桃子//
	「どっちかなんて、選べない。」
	「それでも・・・それでも私は・・・」
[cg_shift storage="MMK_03_000" time="600" fade="0.3"]
	//純一//
	「・・・」
	//桃子//
	「私は、お姉ちゃんだから・・・」
[cg_shift storage="MMK_03_003" time="600" fade="0.3"]
	//桃子//
	「杏のことを守らなくちゃいけないの。」
	「だって、杏は、まだ中学に入ったばっかりで、」
[cg_shift storage="MMK_03_004" time="600" fade="0.3"]
	//桃子//
	「やっぱり、まだまだ危なっかしいし、私がいないと駄目だもの。」
	//純一//
	「桃子・・・」
[cg_shift storage="MMK_03_005" time="600" fade="0.3"]
	//桃子//
	「お母さんから教わってないこと、まだまだいっぱいあるの。」
	「でもね、お父さんみたいな人は・・・」
[cg_shift storage="MMK_03_006" time="600" fade="0.3"]
	//桃子//
	「ひとりにしたら、きっと駄目になっちゃうよ・・・」
	//純一//
	「・・・」
[cg_shift storage="MMK_03_001" time="600" fade="0.3"]
	//桃子//
	「ねぇ、純一。」
	「私、一体、どうしたらいいんだろう？」