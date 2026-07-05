*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene1|&f.title+"スクショ１"
[resetlaypos]
[bg_show storage="connectingCorridor" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃子" torso="MMK_T00_ARM10_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.07" size="2.2" fade="0.3"]
	//桃子//
	「スカートあが苦しくなってきた最近ちょっちスカートが苦しくなってきたかな〜…なんて」
	//久保田//
      	「それが桃子のチャームポイントだろ？」
      	//桃子//
      	「も～すぐいぢわる言うんだから…」
      
*scen2|&f.title+"スクショ２"
[resetlaypos]
[bg_show storage="covenienceStore" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_shift name="桃子" torso="MMK_T01_ARM10_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE00_00" effect="MMK_E01_01" accessory="MMK_A01_01" x="0.6" fade="0.3"]
	//桃子//
	「何買う何買う〜？」
	//久保田//
	「桃子はどうせ新発売のパインソフトだろ」
//桃子//
「えへへ〜、ばれた？」

*scen3|&f.title+"スクショ３"
[resetlaypos]
[chara_hide name="桃子" fade="0.3"]
[bg_show storage="libraryShelf" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃k" torso="MMK_T00_ARM10_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" blink="true" x="0.5" y="1.3" size="3" fade="0.3"]
//久保田//
「女の子っていい匂いがするよな。」
	//桃子//
「あー、貴方もエッチなんだ〜、ヤラシ〜」
	//久保田//
	「い、いや、違うってば！」

*scen4|&f.title+"スクショ４"
[resetlaypos]
[chara_hide name="桃k" fade="0.3"]
[bg_show storage="classroomBack" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃子" torso="MMK_T00_ARM10_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE00_00" blink="true" x="0.5" y="1.3" size="3" fade="0.3"]
	//桃子//
	「そりゃそうだよ〜、坂井泉水とか宇多田ヒカルとか！大好き！」
      	//久保田//
      	「最近でいうと僕はモー娘。かなあ。」
	//桃子//
	「そういえば明日香ちゃん抜けてから、アイドルっ気強いよね～。」

*scen5|&f.title+"スクショ５"
[resetlaypos]
[chara_hide name="桃子" fade="0.3"]
[bg_show storage="test.bg.schoolroute02" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="桃o" torso="MMK_T03_ARM03_CLO00" eye="MMK_F03_EYE00_00" mouth="MMK_F03_MOU01_00" brow="MMK_F03_BRO03_00" cheek="MMK_F03_CHE01_00" blink="true" x="0.35" y="0.7" size="0.5" fade="0.3"]
//桃子//
「ねー！駅まで競走しよー！」
	//桃子//
	「勝った方が何の映画観るか選ぶの！」
      	//久保田//
      	「おいおい…部活帰りじゃないのかよ…」

*scen5|&f.title+"スクショ５"
[resetlaypos]
[chara_hide name="桃o" fade="0.3"]
//桃子//
「あ、おはよ～航輝！」
[bg_show storage="7557" bg_x="0.5" bg_y="1" bg_zoom="1.0"]
	//久保田//
	「あれ先輩、ゲームボーイ持ってきてないんですか。牧場物語、ずっとやってるのに。」
//沙那子//
「大好きだけど、今日くらいはね。ふふ。」[female]

[bg_show storage="6870" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
//桃子//
「あ、おはよ～航輝！」
	


//久保田//
「至りってあるよな。例えばほら、中学生の時とか、なんで親に冷たくしちゃうんだろう。」

//桃子//
「へぇー、航輝にも反抗期があったんだー！なんかへんな感じ。」


[scroll-stop]