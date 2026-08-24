*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene11|

[resetlaypos]
[bg_show storage="test.bg.schoolGate" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[bgm bgm="MokLap1.mp3" volume="0.5" loop="true" fade="0.0"]
[chara_show name="桃子" torso="MMK_T00_ARM07_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「おまたせーっ！」
	//純一//
	「おう。」
	「それじゃ早速、行きますか。」
[chara_shift name="桃子" torso="MMK_T00_ARM07_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.5" y="0.9" size="2.3" fade="0.15"]
	//桃子//
	「よっしゃ！いこいこ～！」


[fadeout color="black" time="1.0"]
[chara_shift name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE03_00" x="0.76548673" y="0.8159292" size="1.73265413" fade="0.15"]
[bg_show storage="イタリアン店前" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[fadein time="1.0"]
	//純一//
	「着いたな。」
[chara_shift name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_01" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE03_00" x="0.76548673" y="0.8159292" size="1.73265413" fade="0.15"]
	//桃子//
	「着いたね。」
	//純一//
	「ここであってるよな？」
[chara_shift name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE03_00" x="0.76548673" y="0.8159292" size="1.73265413" fade="0.15"]
	//桃子//
	「ここであってるね。」
	//純一//
	「あれ、店やってるかな？」
[chara_shift name="桃子" eye="MMK_F01_EYE04_00" fade="0.15"]
	//桃子//
	「やってるね。」
	//純一//
	「・・・おいおい、ここ、高校生が入っても大丈夫なの？」
	「ちょっと、オトナすぎやしないか？」
[chara_shift name="桃子" torso="MMK_T01_ARM07_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_01" fade="0.15"]
	//桃子//
	「大丈夫。ドレスコードもないし、価格もそんなに高くない。」
[chara_shift name="桃子" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU00_02" fade="0.15"]
	//桃子//
	「緊張しなくたって全然平気だよ。」
	//純一//
	「そう言う割に僕の後ろに隠れてるじゃないか・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE02_00" mouth="MMK_F01_MOU00_00" cheek="MMK_F01_CHE01_00" effect="MMK_E01_01" fade="0.15"]
	//桃子//
	「・・・。」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「だって純一、どこへでも連れてくって言ってたでしょ！」
[chara_shift name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE00_01" mouth="MMK_F01_MOU02_02" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE01_00" effect="MMK_E01_01" fade="0.15"]
	//桃子//
	「いいからほら、早く入ろうよ～！」
[chara_show name="桃子" torso="MMK_T01_ARM06_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU04_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE01_00" effect="MMK_E01_01" blink="true"fade="0.15"]
	//純一//
	「わかったわかった。」
	「・・・よし、じゃあ、行くぜ？」
[chara_shift name="桃子" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO01_00" fade="0.15"]
	//桃子//
	「・・・うん！」

[bg_move storage="school" bg_left="0.1" bg_top="0.1" time="1000" bg_zoom="1.5"]
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" effect="" fade="0.15"]
[fadeout color="black" time="1.0"]
[bg_show storage="イタリアン店内" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_shift name="桃子" x="0.5" y="0.85" size="2.1" fade="0.15"]
;@standalone-step
[fadein time="1.0"]
	//店員//
	「いらっしゃいませ。後ほど注文をお伺いしますね。」
	//純一//
	「はいっ、アリガトウゴザイマス。」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" fade="0.15"]
	//桃子//
	「凄いお洒落なお店だね～！」
[chara_shift name="桃子" mouth="MMK_F00_MOU00_00" fade="0.15"]
	//純一//
	「まったくだな、芸能人も結構来てるらしいって噂は伊達じゃなさそうだ。」
	「店内は薄暗くてムーディーな感じなのに、店員さんは朗らかで落ち着くね。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU00_02" fade="0.15"]
	//桃子//
	「でしょでしょ～！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE06_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO02_00" fade="0.15"]
	//桃子//
	「お店選びのセンスには自信あるんだ〜！お母さん譲りですから！」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO03_00" fade="0.15"]
	//桃子//
	「ずっと来たかったんだけど、家族で来るにはちょっとこぢんまりしてるでしょ？」
	//純一//
	「確かに、ふたりくらいが丁度いいかもな。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" mouth="MMK_F00_MOU00_00" fade="0.15"]
	//純一//
	「実際客も僕らを含めて男女ペアが三組だ。」
[chara_shift name="桃子" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO00_00" fade="0.15"]
	//桃子//
	「そうだねー。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" fade="0.15"]
	//桃子//
	「けど、流石に私達と同世代じゃないか、どっちも三十代以上だね～。」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" fade="0.15"]
	//桃子//
	「二組とも素敵！」
	//純一//
	「ああ。確かに。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE06_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO01_00" size="2.2" fade="0.5"]
[chara_move left="0.0" top="0.0" zoom="1.4" time="0.5"]
	//桃子//
	「ねね、やっぱりカップルなのかな？」
	//純一//
	「そりゃこんな店に来るくらいだし、そうでしょう。」
[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" size="2.1" fade="0.15"]
	//桃子//
	「だよね～、ここはカップルで来るよねー！」
	「あ・・・」
	「・・・」

	//あ//
	「あ」
	[scroll-stop]