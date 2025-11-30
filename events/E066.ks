*start

;----------------------------------------------
;◆実験
;桃子に帰り道、ミニストップに誘われるが…！？
;----------------------------------------------

*scene1|&f.title+"校門前"

[bg_show storage="test.bg.TEUgate"  bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[BGM bgm="subete_no_hajimari" volume="0.2" loop="true"]

[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.6" y="0.95" size="2"]
	
	//桃子//
	「ねえ、今日はミニスト寄ってかない？」


[choice option1="いいよ、行こう！" option2="ミニストって？"]

	//{苗字}//
	「{選択肢1}」

 [if condition="choice_1==1"]
 	//桃子//
     	「え、本当！やったー！！」
      	//{苗字}//
     	「喜び方が大げさだよ・・・」
 [endif]

 [if condition="choice_1==2"]
      	//桃子//
      	「ミニスト！通学路のミニストップだよ！」
      	//{苗字}//
      	「あ、南町の踏切のとこのミニストップね。」
      	//桃子//
      	「{苗字}ももう二年生なんだから、そんくらい知っててよー！」
 [endif]

[chara_hide subh="T03_00_01"]
[chara_show name="T03_00_01" eye="F03_Ex00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.6" y="0.95" size="2"]

	//桃子//
	「CM見た？ミニストの。」
	//{苗字}//
	「え、どんなやつだっけ？覚えてないや」

[chara_hide subh="T03_00_01"]
[chara_show name="T00_02_01" eye="F00_Ew00_00" mouth="F00_Mh01_03" brow="F00_Bn00_00" cheek="" x="0.5" y="1.05" size="2.5"]

	//桃子//
	「強がり！ほんとだって！パイナップルソフトくださーい。」
	//{苗字}//
	「うわびっくりした！なんだよいきなり。」

[chara_show name="T00_02_01" eye="F00_Eh00_00" mouth="F00_Mh01_03" brow="F00_Bn00_00" cheek="" x="0.5" y="1.05" size="2.5"]

	//桃子//
	「CMのマネ。似てるでしょ。」
	//{苗字}//
	「似てるも何も、覚えてないよ・・・」
	//桃子//
	「いいから、早く行こ！ね！」
	//{苗字}//
	「焦らず行こうぜ・・・」

[fadeout color="black" time="1.5"]

	//桃子//
	「うん！」
	[scroll-stop]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide subh="T00_02_01"]
[bg_show storage="test.bg.schoolroute01"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.6" y="0.95" size="2"]
[fadein time="1.5"]

	//{苗字}//
	「ミニストのCM思い出したけど、別に特別な感じじゃなかったろ」

	//桃子//
	「私が食べたいって思ったから特別なのー！」
	//{苗字}//
	「そうですか。」

[fadeout color="black" time="1.5"]

	//桃子//
	「うん。」
	[scroll-stop]

*scene3|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide subh="T03_00_01"]
[bg_show storage="test.bg.schoolroute02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.8" y="0.95" size="2"]
[fadein time="1.5"]

	//{苗字}//
	「てか、あのCMいつ見たの？」
	//桃子//
	「なんかね、うたばん見てたら出てきた！」
	//{苗字}//
	「そうですか。あ、車来てるよ桃子。」
	//桃子//
	「え！」

[chara_move subm="T03_00_01" time="500" left="-0.4" top="0" zoom="2.0"]

	//桃子//
	「あぶなーい、ありがとね{苗字}。」
	//{苗字}//
	「危ないの桃子だからな、ちゃんと気を付けてね」
	//桃子//
	「へへ、ごめんね。」
	[scroll-stop]

*scene4|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide subh="T03_00_01"]
[bg_show storage="test.bg.ministop02"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.67" y="0.95" size="2"]
[fadein time="1.5"]

	//{苗字}//
	「あ、信号チカチカしてるよ。」
	//桃子//
	「ね、ちょっと待とっか。」
	//{苗字}//
	「ちょっと待ったほうがソフトクリームも美味しいよ。」
	//桃子//
	「へへ、楽しみだね。」

[fadeout time="1.5"]

	[scroll-stop]

*scene5|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide subh="T03_00_01"]
[bg_show storage="test.bg.ministop"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.67" y="0.95" size="2"]
[fadein time="1.5"]

	//桃子//
	「ついた！ついたついたついたよー！」
	//{苗字}//
	「楽しみだね桃子。」
	//桃子//
	「うん！」
	「じゃあ私買ってくるから、{苗字}ここで待っててね」
	//{苗字}//
	「えっ、おいおいここで待ちぼうけかよ」
	「一緒に買わないの？」
	//桃子//
	「うん、私が一人で買いたいから。」
	//{苗字}//
	「なんで？」
	//桃子//
	「秘密。」
	//{苗字}//
	「まあいいや、僕の分も忘れるなよ桃子。」
	//桃子//
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
	「パイナップルソフトくださーい！」
	[scroll-stop]

[chara_hide subh="T03_00_01"]
[fadein time="1.5"]

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

[chara_show name="T00_02_01" eye="F00_En00_00" mouth="F00_Mh01_01" brow="F00_Bn00_00" cheek="" x="0.78" y="0.6" size="0.4"]

	//桃子//
	「・・・」
[chara_hide subh="T00_02_01"]
[chara_show name="T00_02_01" eye="F00_En00_00" mouth="F00_Mh01_01" brow="F00_Bn00_00" cheek="" x="0.55" y="0.6" size="0.4"]

	「・・・」

[chara_move subm="T00_02_01" time="1500" left="-0.5" top="-0.6" zoom="3"]


	//{苗字}//
	「何だ」
	//桃子//
	「一個しか買えませんでした。」
	//{苗字}//
	「見れば分かる。」
	//桃子//
	「で、でもスプーンは二つあるから！」
	//{苗字}//
	「・・・」
	//桃子//
	「ご、ごめんってばー・・・」
	//{苗字}//
	「・・・」
	//桃子//
	「・・・{苗字}？」
	//{苗字}//
	「冗談だよ、一緒に食べよう。」
	//桃子//
	「ふふっ、そうだね。」
	「でも一番ショックなの私なんだからね～！」
	//{苗字}//
	「桃子ちょっと多く食べていいぞ。」
	//桃子//
	「本当！じゃ、いただきま～す。」

	//　　　//
	「　　　　　　　　・」
	「　　　　　　　　・」
	「　　　　　　　　・」
	[scroll-stop]

	//桃子//
	「美味しかった～あんな人だかりができるのも当然だね。」
	//{苗字}//
	「人だかり？あったかそんなの。」
	//桃子//
	「ううん、CMでレジで大勢の人が『パイナップルソフトくださーい』って言うの。」
	//{苗字}//
	「CMの話ね。
	「桃子にそんな話してもらって、電通の人も喜んでるよ多分。」
	//桃子//
	「電通が作ってるの？」
	//{苗字}//
	「知らない。」
	「てか桃子、お茶買ってきてくれた？」
	//桃子//
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







