*start
;@expression-status: human_confirmed

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene8|

[resetlaypos]
[bg_show storage="classroomBack" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[se se="学校のチャイム" volume="0.5" frequency="1" block="false"]
	//純一//
	「（…………）」
	「（……………………）」
	「（なんだか授業に身が入らないな…………）」
;@memo: 空のカットとか入れたいな
[bgm bgm="◎_12_A Voyage to the center of the cosmos ２楽" volume="0.5" loop="true"]
	//純一//
	「（…………そりゃあそうだ。空が、先週のそれとは全く違う様相を呈しているのだから。）」
	「（それに……）」
	//坂西//
	「こっからもフツーに授業らしいよ、オカシクない？」
	//伊藤//
	「は？だる！こんな状況なのに！？」
	//中島//
	「おいおい、どうなるんだ、これ。」
	//純一//
	「（僕だけじゃない、皆も浮足立っている。）」
	//坂西//
	「やっぱりノストラダムスの大予言と関係あるんじゃない？」
	//中島//
	「馬鹿馬鹿しい、オカルトだろ、あんなの。」
	「業界が仕掛けたムーヴメントなんだよ、バレンタイン然り。」
	//伊藤//
	「ケツかゆ！誰か掻いてくれ。」
	//坂西//
	「でもムーにも書いてあったよ、7月に向けて破滅が始まるって。」
	//中島//
	「一番のオカルトじゃん！踊らされるなって、あほくさい。」
	//伊藤//
	「悪いんだけど誰かケツ掻いてくれないか。」
	//坂西//
	「だって実際ありえない事が起きてるし。」
	//中島//
	「バカ、ただの気象現象だよ。そのうち収まるに決まってる。」
	//伊藤//
	「誰かケ・・・」
	//中島//
	「お前はいつまでそれ言ってるんだ。」
	//純一//
	「（即座の危険はないし通常通り登校、か。）」
	「（大人達も突然の異変に対応できていない、というのが実情だろう。）」
	「（ただ、この状況で学業に集中しろってのが土台無理な話だな。）」
	「（タイタニック号のオーケストラならいざ知らず。）」
	「（…………しかし騒々しいな、場所を変えよう。）」

[se se="静かな一人の足音" volume="0.9" frequency="1" block="false"]
[fadeout color="black" time="1.0"]
[bg_show storage="connectingCorridor" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO01_00" blink="true" x="0.35" y="0.5" size="0.7" fade="0.15"]
[fadein time="1.0"]
	//純一//
	「（お、桃子。）」
	「（……ん？なんだアイツ、珍しく所在なげに。）」
	「おーい桃子。」
	//桃子//
	「…………」
	//純一//
	「（……聞こえてないのか？）」
	「桃子さ～ん？」
	//桃子//
	「…………」
	//純一//
	「（…………？）」
	「（ちょっと話しに行ってみるか。）」
[bg_move storage="connectingCorridor" bg_left="0.0" bg_top="0.0" bg_zoom="1.4" time="600"]
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO01_00" blink="true" x="0.24" y="0.6" size="1.3" fade="0.15"]
	//純一//
	「よう。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU19_00" brow="MMK_F01_BRO00_00" fade="0.15"]
	//桃子//
	「あ……純一。」
	//純一//
	「なんだか凄いことになってきちゃったな。」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU18_00" brow="MMK_F01_BRO00_00" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「ああ、ね、そうだね。」
	//純一//
	「受験したり、大会を控えてる人は大変だよな。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU18_00" brow="MMK_F01_BRO02_00" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「うん、そうだよね。」
	//純一//
	「杏ちゃんも、ようやく中学に馴染んできた頃だろうに。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU18_00" brow="MMK_F01_BRO00_00" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「あはは、そうかもね。」
	//純一//
	「…………」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_01" brow="MMK_F01_BRO00_00" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「そうだねー。」
	//純一//
	「…………」
	「……桃子、何かあったのか？」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO00_00" effect="MMK_E01_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「…………え？」
	//純一//
	「さっきから上の空だぜ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" effect="MMK_E00_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「…………ううん、なんでもないの。」
	//純一//
	「……本当か？」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO02_00" effect="MMK_E01_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「ちょっと、その……」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO02_00" effect="MMK_E01_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「あの…………」
	//純一//
	「…………？」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_02" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE00_00" effect="MMK_E01_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「…………」
	//純一//
	「……桃子？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" effect="MMK_E00_01" x="0.5" y="0.85" size="2.3" fade="0.15"]
	//桃子//
	「ごめん、お手洗い。」
	//純一//
	「？」
	「…………！あ、あぁ、悪い。」
[chara_hide name="桃子" fade="0.15"]
[se se="静かな一人の足音" volume="0.5" frequency="1" block="false"]
	//純一//
	「（今日の桃子、やっぱりいつもと少し違う……）」
	「（どうしちゃったんだろう、アイツ……）」

[chara_show name="増田" torso="MST_T01_ARM_0001" eye="MST_F01_EYE_0008" mouth="MST_F01_MOU_0015" brow="MST_F01_BRO_0005" blink="true" x="0.4" y="1.3" size="3.3" fade="0.15"]
[bgm bgm="MokMas42654" volume="0.5" loop="true"]
	//増田//
	「よッ！！」
	//純一//
	「うおっ！　脅かすなよ！」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「どうしたんだよ～、冴えない顔しちゃってよ～。」
	//純一//
	「（・・・）」
	「（そいつは僕じゃあないっての……）」
	「お前はいつだって元気だな……」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0008" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「そうそう聞いてくれよ！　事情通によるとあの空は——」
	//純一//
	「増田。今日桃子に会ったか？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0003" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「へ？」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0002" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「会いはしたけど……桃子がどうかしたのか？」
	//純一//
	「それが、今日の桃子、なんだか変なんだ。」
[chara_shift name="増田" torso="MST_T00_ARM_0002" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0004" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「桃子が？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0017" brow="MST_F00_BRO_0008" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「ウーン……」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「変ってどういうところが？」
	//純一//
	「うーん、何というか……」
	「元気がないというか……」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0012" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「そうか？俺はあんまりわからんな。気のせいじゃないのか？」
	//純一//
	「どうなんだろう……」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0011" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「まっ、そっとしておくのも良いんじゃないか？」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0011" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「色々あるんだろ、オンナのコなんだし！」
	//純一//
	「お前なぁ……」
[chara_shift name="増田" torso="MST_T00_ARM_0004" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0015" brow="MST_F00_BRO_0005" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「へへへ！」

[fadeout color="black" time="1.0"]
[bgm bgm="muon" volume="0.5" loop="true"]
	//純一//
	「（結局、彼女への違和感は拭えないまま、僕は日常を墨守することに務めた。）」
	「（増田に影響されたわけでは無いが、確かに、彼女も皆と同じく時間を必要としているのかもしれない。）」
	「（とりあえず様子をみよう。そう思う僕を、異常な空と、それに浮かぶ巨星が照らしていた。）」
[scroll-stop]