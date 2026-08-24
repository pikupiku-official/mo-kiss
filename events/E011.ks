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
[chara_move name="桃子" time="1000" left="-0.2" top="0" zoom="0.3"]

	//桃子//
	「言葉は想像力を運ぶ電車です。」
	「日本中どこまでも想像力を運ぶ『私たち』という路線図。」
	「一個の私は想像力が乗り降りする一つ一つの駅みたいなもので、どんな小さな駅にも止まる各停みたいな言葉もあれば、仕事をしやすくしてくれる、急行みたいな言葉もあるし。」
	[scroll-stop]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="classroom"  bg_x="0.6" bg_y="0.4" bg_zoom="1.8"]
[BGM bgm="classroom" volume="0" loop="true"]

	//桃子//
	「別の場面に移動しました。」
	[scroll-stop]

[chara_show name="サナコ"　eye="eye2" mouth="mouth2" x="0.2" y="0.2"]

	//桃子//
	「わかる人にしかわからない、快速みたいな言葉もあって、一番言葉の集まる駅にしか止まらない、新幹線みたいな言葉もあります。」
	「地下の暗闇を走る言葉もあります。」
	「地下から地下へ受け渡されるよこしまな想像力たち。」
	[scroll-stop]

	//サナコ//
	「でも時折、地下から地上に顔を出してビルの谷間をくぐるとき、不意の太陽が無理矢理たてじまに変えようとするから、想像力は眉をしかめたりします。」
	[scroll-stop]

[chara_hide name="桃子"]

[bg_move storage="classroom" bg_left="0.0" bg_top="0.0" time="1000" bg_zoom="1.0"]
[chara_move name="サナコ" time="600" left="0.1" top="0.1" zoom="1.7"]

	//サナコ//
	「ときどき、届くのが速いほど言葉は便利な、大事なものに思えます。」
	「だけどほんとうに大事なのは、想像力が降りるべき駅で降りること。」
	「次に乗り込むべき言葉に乗ること。」
	「ただそれだけです。」
	「だから、ダイアグラムの都合から、ぎゅうぎゅう詰めの急行と、すっかすかの各停が同じ時刻に出発して、」
	「ほんの一瞬同じ速さで走るとき、急行の中の想像力がうらやましげに各停をながめることもあるのです。」
	「２０１２年には東京メトロ副都心線と東急東横線がつながるみたいに、今まではつながれなかったあれもこれもつながるんだろうか。」
	「そんなことを想像しています。」
	「これは最後のテキストです。」
	[scroll-stop]