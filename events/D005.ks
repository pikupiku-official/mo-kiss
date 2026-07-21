*start

;----------------------------------------------
;◆デモシナリオ
;----------------------------------------------

*sceneD005|


[resetlaypos]
[bg_show storage="教室昼" bg_x="0.5" bg_y="0.5" bg_zoom="1.1"]
[chara_show name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	//純一//
	「（うーん……）」
	「（どれにしようかな……）」
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.2" size="2.7" fade="0.3"]
	//桃子//
	「それでそれで、あなたのお好みは？」[female]

[choice_1 option1="ソース" option2="塩"　option3="醤油"　option4="マヨネーズ"　option5="ケチャップ"]
	//桃子//
	「言うと思ったぁ……ほんとあなたってって味濃いの好きよね。」
	「これは表層寄りに感じます。」
[scroll-stop]