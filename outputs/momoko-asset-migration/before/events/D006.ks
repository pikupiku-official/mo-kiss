*start

;----------------------------------------------
;◆デモシナリオ
;----------------------------------------------

*sceneD006|


[resetlaypos]
[bg_show storage="純一部屋" bg_x="0.5" bg_y="0.5" bg_zoom="1.1"]
[chara_show name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE02_02" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//純一//
	「できたよー。」
	「じゃあ、食べようか。」
[chara_show name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「目玉焼きナポリタン・・・？」
[chara_show name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//桃子//
	「ありがとう。いただきます。」[female]

[choice_1 option1="ソース" option2="塩"　option3="醤油"　option4="マヨネーズ"　option5="ケチャップ"]
[if condition="choice_1==1"]
	//桃子//
	「言うと思ったぁ……ほんとあなたってって味濃いの好きよね。」
[endif]

[if condition="choice_1==2"]
	//桃子//
	「これは表層寄りに感じます。」
[endif]

	「hyo-sou」
[scroll-stop]