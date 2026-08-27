*start
;@expression-status: ai_draft

;----------------------------------------------
;◆実験
;桃子に帰り道、ミニストップに誘われるが…！？
;----------------------------------------------

*scene1|&f.title+"校門前"


	
; --- new step ---
[bg_show storage="test.bg.TEUgate"  bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[BGM bgm="subete_no_hajimari.mp3" volume="0.2" loop="true"]
[chara_show name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.6" y="1" size="2" fade="0"]
[fadein time="1.0"]
//桃子//
「ねえ、{愛沼|あいぬま}は{boten:ミニスト}寄ってかない？」


[choice option1="いいよ、行こう！" option2="ミニストって？"]

	//{苗字}//
	「{選択肢1}」

 [if condition="choice_1==1"]
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
 	//桃子//
     	「え、本当！やったー！！」
      	//{苗字}//
     	「喜び方が大げさだよ・・・」
 [endif]

 [if condition="choice_1==2"]
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true"]
      	//桃子//
      	「ミニスト！通学路のミニストップだよ！」
      	//{苗字}//
      	「あ、南町の踏切のとこのミニストップね。」
      	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" blink="true"]
      	「{苗字}ももう二年生なんだから、そんくらい知っててよー！」
 [endif]


[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true"]
//桃子//
「CM見た？ミニストの。」
	//{苗字}//
	「え、どんなやつだっけ？覚えてないや」


[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.05" size="2.5"]
//桃子//
「強がり！ほんとだって！パイナップルソフトくださーい。」
	//{苗字}//
	「うわびっくりした！なんだよいきなり。」

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「CMのマネ。似てるでしょ。」
//{苗字}//
「似てるも何も、覚えてないよ・・・」

[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	//桃子//
	「いいから、早く行こ！ね！」
	//{苗字}//
	「焦らず行こうぜ・・・」

[fadeout color="black" time="1.5"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「うん！」
	[scroll-stop]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="test.bg.schoolroute01"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[fadein time="1.5"]

	//{苗字}//
	「ミニストのCM思い出したけど、別に特別な感じじゃなかったろ」

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true"]
	「私が食べたいって思ったから特別なのー！」
	//{苗字}//
	「そうですか。」

[fadeout color="black" time="1.5"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「うん。」
	[scroll-stop]

*scene3|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide name="桃子"]
[bg_show storage="test.bg.schoolroute02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.8" y="0.95" size="2"]
[fadein time="1.5"]

	//{苗字}//
	「てか、あのCMいつ見たの？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「なんかね、うたばん見てたら出てきた！」
	//{苗字}//
	「そうですか。あ、車来てるよ桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" blink="true"]
	「え！」

[chara_move name="桃子" time="500" left="-0.4" top="0" zoom="2.0"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" blink="true"]
	「あぶなーい、ありがとね{苗字}。」
	//{苗字}//
	「危ないの桃子だからな、ちゃんと気を付けてね」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「へへ、ごめんね。」
	[scroll-stop]

*scene4|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide name="桃子"]
[bg_show storage="test.bg.ministop02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.67" y="0.95" size="2"]
[fadein time="1.5"]

	//{苗字}//
	「あ、信号チカチカしてるよ。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「ね、ちょっと待とっか。」
	//{苗字}//
	「ちょっと待ったほうがソフトクリームも美味しいよ。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「へへ、楽しみだね。」

[fadeout time="1.5"]

	[scroll-stop]

*scene5|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide name="桃子"]
[bg_show storage="test.bg.ministop"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.67" y="0.95" size="2"]
[fadein time="1.5"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「ついた！ついたついたついたよー！」
	//{苗字}//
	「楽しみだね桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「うん！」
	「じゃあ私買ってくるから、{苗字}ここで待っててね」
	//{苗字}//
	「えっ、おいおいここで待ちぼうけかよ」
	「一緒に買わないの？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「うん、私が一人で買いたいから。」
	//{苗字}//
	「なんで？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「秘密。」
	//{苗字}//
	「まあいいや、僕の分も忘れるなよ桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「分かってるって、お任せあれ～」
	
[fadeout color="black" time="1.5"]

	//{苗字}//
	「あ、ついでにお茶ー！」
	[scroll-stop]

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「パイナップルソフトくださーい！」
	[scroll-stop]

[chara_hide name="桃子"]
[fadein time="1.5"]

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

[chara_show name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true" x="0.78" y="0.6" size="0.4"]

	//桃子//
	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" blink="true" x="0.55" y="0.6" size="0.4"]

	「・・・」

[chara_move name="桃子" time="1500" left="-0.5" top="-0.6" zoom="3"]


	//{苗字}//
	「何だ」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU05_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「一個しか買えませんでした。」
	//{苗字}//
	「見れば分かる。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「で、でもスプーンは二つあるから！」
	//{苗字}//
	「・・・」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「ご、ごめんってばー・・・」
	//{苗字}//
	「・・・」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「・・・{苗字}？」
	//{苗字}//
	「冗談だよ、一緒に食べよう。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE04_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「ふふっ、そうだね。」
	「でも一番ショックなの私なんだからね～！」
	//{苗字}//
	「桃子ちょっと多く食べていいぞ。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「本当！じゃ、いただきま～す。」

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" blink="true"]
	「美味しかった～あんな人だかりができるのも当然だね。」
	//{苗字}//
	「人だかり？あったかそんなの。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true"]
	「ううん、CMでレジで大勢の人が『パイナップルソフトくださーい』って言うの。」
	//{苗字}//
	「CMの話ね。
	「桃子にそんな話してもらって、電通の人も喜んでるよ多分。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true"]
	「電通が作ってるの？」
	//{苗字}//
	「知らない。」
	「てか桃子、お茶買ってきてくれた？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU05_00" brow="MMK_F01_BRO03_00" cheek="MMK_F01_CHE02_00" blink="true"]
	「え？買ってないけど・・・」
	「そんなこと言ってた？」
	//{苗字}//
	「（僕が悪いか・・・）」
	[scroll-stop]

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

	//　　　//
	「そのまま桃子と国立まで帰った。」
	「今度は、僕がコンビニに入ろう。」

