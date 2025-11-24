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
     	「喜び方が大げさだよ」
      	//増田//
      	「確かに…あの声で締まる感じはあるよな。」
	[scroll-stop]
 [endif]

 [if condition="choice_1==2"]
      	//桃子//
      	「ミニスト！通学路のミニストップだよ！」
      	//{苗字}//
      	「あ、殿ヶ谷戸立体のとこのミニストップね。」
      	//桃子//
      	「{苗字}もう二年生なんだからそんくらい知っててよね！」
	[scroll-stop]
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
	「パイナップルソフトが世界一美味しそうなのっ！！」
	//{苗字}//
	「うわびっくりした！なんだよいきなり」

[chara_show name="T00_02_01" eye="F00_Eh00_00" mouth="F00_Mh01_03" brow="F00_Bn00_00" cheek="" x="0.5" y="1.05" size="2.5"]

	//桃子//
	「いいから、早く行こ！ね！」
	//{苗字}//
	「焦らず行こうぜ…」
	[scroll-stop]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[chara_hide subh="T00_02_01"]
[bg_show storage="test.bg.schoolroute01"  bg_x="0.5" bg_y="0.5" bg_zoom="1"]
[BGM bgm="classroom" volume="0" loop="true"]
[chara_show name="T03_00_01" eye="F03_En00_00" mouth="F03_Mh00_00" brow="F03_Bn00_00" cheek="" x="0.6" y="0.95" size="2"]

	//桃子//
	「今日は学校どうだったの？」

	//桃子//
	「わかる人にしかわからない、快速みたいな言葉もあって、一番言葉の集まる駅にしか止まらない、新幹線みたいな言葉もあります。」
	「地下の暗闇を走る言葉もあります。」
	「地下から地下へ受け渡されるよこしまな想像力たち。」
	[scroll-stop]




