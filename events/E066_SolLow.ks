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
[fadein time="1.0"]
//桃子//
[chara_show name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
「ねえ、{愛沼|あいぬま}は{boten:ミニスト}寄ってかない？」


[choice option1="いいよ、行こう！" option2="ミニストって？"]

	//{苗字}//
	「{選択肢1}」

 [if condition="choice_1==1"]
 	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
     	「え、本当！やったー！！」
      	//{苗字}//
     	「喜び方が大げさだよ・・・」
 [endif]

 [if condition="choice_1==2"]
      	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" effect="" fade="0.3"]
      	「ミニスト！通学路のミニストップだよ！」
      	//{苗字}//
      	「あ、南町の踏切のとこのミニストップね。」
      	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
      	「{苗字}ももう二年生なんだから、そんくらい知っててよー！」
 [endif]


//桃子//
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="" fade="0.3"]
「CM見た？ミニストの。」
	//{苗字}//
	「え、どんなやつだっけ？覚えてないや」


//桃子//
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
「強がり！ほんとだって！パイナップルソフトくださーい。」
	//{苗字}//
	「うわびっくりした！なんだよいきなり。」

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="" fade="0.3"]
	「CMのマネ。似てるでしょ。」
//{苗字}//
「似てるも何も、覚えてないよ・・・」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「いいから、早く行こ！ね！」
	//{苗字}//
	「焦らず行こうぜ・・・」

[fadeout color="black" time="1.5"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「うん！」
	[chara_hide name="桃子" fade="0.3"]
	[scroll-stop]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="test.bg.schoolroute01"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[fadein time="1.5"]

	//{苗字}//
	「ミニストのCM思い出したけど、別に特別な感じじゃなかったろ」

	//桃子//
	[chara_show name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「私が食べたいって思ったから特別なのー！」
	//{苗字}//
	「そうですか。」

[fadeout color="black" time="1.5"]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「うん。」
	[chara_hide name="桃子" fade="0.3"]
	[scroll-stop]

*scene3|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="test.bg.schoolroute02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[fadein time="1.5"]

	//{苗字}//
	「てか、あのCMいつ見たの？」
	//桃子//
	[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「なんかね、うたばん見てたら出てきた！」
	//{苗字}//
	「そうですか。あ、車来てるよ桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.3"]
	「え！」

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="" fade="0.3"]
	「あぶなーい、ありがとね{苗字}。」
	//{苗字}//
	「危ないの桃子だからな、ちゃんと気を付けてね」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「へへ、ごめんね。」
	[chara_hide name="桃子" fade="0.3"]
	[scroll-stop]

*scene4|&f.title+"教室のシーン"
[resetlaypos]
[bg_show storage="test.bg.ministop02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[fadein time="1.5"]

	//{苗字}//
	「あ、信号チカチカしてるよ。」
	//桃子//
	[chara_show name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「ね、ちょっと待とっか。」
	//{苗字}//
	「ちょっと待ったほうがソフトクリームも美味しいよ。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「へへ、楽しみだね。」
	[chara_hide name="桃子" fade="0.3"]

[fadeout time="1.5"]

	[scroll-stop]

*scene5|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="test.bg.ministop"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[fadein time="1.5"]

	//桃子//
	[chara_show name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「ついた！ついたついたついたよー！」
	//{苗字}//
	「楽しみだね桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" effect="" fade="0.3"]
	「うん！」
	「じゃあ私買ってくるから、{苗字}ここで待っててね」
	//{苗字}//
	「えっ、おいおいここで待ちぼうけかよ」
	「一緒に買わないの？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「うん、私が一人で買いたいから。」
	//{苗字}//
	「なんで？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「秘密。」
	//{苗字}//
	「まあいいや、僕の分も忘れるなよ桃子。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「分かってるって、お任せあれ～」
	[chara_hide name="桃子" fade="0.3"]
	
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
	[chara_show name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「パイナップルソフトくださーい！」
	[chara_hide name="桃子" fade="0.3"]
	[scroll-stop]

[fadein time="1.5"]

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]


	//桃子//
	[chara_show name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" blink="true" x="0.5" y="1.1" size="2.3" fade="0.3"]
	「・・・」

	「・・・」

	//{苗字}//
	「何だ」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「一個しか買えませんでした。」
	//{苗字}//
	「見れば分かる。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「で、でもスプーンは二つあるから！」
	//{苗字}//
	「・・・」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	「ご、ごめんってばー・・・」
	//{苗字}//
	「・・・」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	「・・・{苗字}？」
	//{苗字}//
	「冗談だよ、一緒に食べよう。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" effect="" fade="0.3"]
	「ふふっ、そうだね。」
	「でも一番ショックなの私なんだからね～！」
	//{苗字}//
	「桃子ちょっと多く食べていいぞ。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" effect="MMK_E00_01" fade="0.3"]
	「本当！じゃ、いただきま～す。」

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" effect="" fade="0.3"]
	「美味しかった～あんな人だかりができるのも当然だね。」
	//{苗字}//
	「人だかり？あったかそんなの。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「ううん、CMでレジで大勢の人が『パイナップルソフトくださーい』って言うの。」
	//{苗字}//
	「CMの話ね。
	「桃子にそんな話してもらって、電通の人も喜んでるよ多分。」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" fade="0.3"]
	「電通が作ってるの？」
	//{苗字}//
	「知らない。」
	「てか桃子、お茶買ってきてくれた？」
	//桃子//
	[chara_shift name="桃子" torso="MMK_T00_ARM01_CLO00" eye="MMK_F00_EYE01_02" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.3"]
	「え？買ってないけど・・・」
	「そんなこと言ってた？」
	[chara_hide name="桃子" fade="0.3"]
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

