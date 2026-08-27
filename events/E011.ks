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
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_01" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" size="2.1" fade="0.15"]
	//桃子//
	「あ・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.15"]
	//桃子//
	「・・・」
	//純一//
	「・・・」
	「え～と、何を頼むんだっけ。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" fade="0.15"]
	//桃子//
	「あっ、えっとねっ！このお店の看板商品のスープスパゲッティ！」
[chara_shift name="桃子" eye="MMK_F00_EYE04_00" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「ちょっぴり辛いトマトソースに、パンチの効いたニンニクが特徴だって～。」
	//純一//
	「お～、聞いてるだけでも美味しそうだな！お腹減ってきた。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" brow="MMK_F00_BRO03_00" effect=""　fade="0.15"]
	//桃子//
	「ね～！！丁度お腹が空く頃合いだし、なんだかいい匂いもするし、楽しみだー！」
	//純一//
	「そういえば、普段ならこの時間も桃子は部活だろ。」
	「テニス部の方は平気なのか？」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_02" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「あー、うん、気にしないで！」
	//純一//
	「気にしないでっておまえ・・・」
	「え、まさかサボり？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO00_00" fade="0.15"]
	//桃子//
	「ううん、コーチにはちゃんと伝えたよ。」
[chara_shift name="桃子" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO03_00" fade="0.15"]
	//桃子//
	「・・・私ね、今週から休部してるの。」
	//純一//
	「休部？何でまた。」
	「中学の時から殆ど休まず行ってたのに。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE03_00" fade="0.15"]
	//桃子//
	「だってさ、部活があるせいで他の事出来ないし。」
[chara_shift name="桃子" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU02_01" brow="MMK_F01_BRO01_00" fade="0.15"]
	//桃子//
	「私だって他にやりたい事だってあるし。」
[chara_shift name="桃子" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" fade="0.15"]
	//純一//
	「そりゃ確かに、時間は有限だけれども。」
	「じゃあ、そのやりたい事っていうのは何だい？」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「それは・・・その・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU04_02" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE03_00" effect="MMK_E01_01" fade="0.15"]
	//桃子//
	「ぱっとは出てこないけど。」
	//純一//
	「なんだそれ。」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「でも！」
[chara_shift name="桃子" torso="MMK_T00_ARM11_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU04_02" fade="0.15"]
	//桃子//
	「大体、テニス部に入ったのもお父さんに薦められたからで、」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_01" fade="0.15"]
	//桃子//
	「・・・別に、そこまで・・・好きじゃないし。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//純一//
	「・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_01" fade="0.15"]
	//桃子//
	「だからいーのっ！」
[chara_shift name="桃子" torso="MMK_T00_ARM11_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU09_00" fade="0.15"]
	//桃子//
	「純一は心配しないでよし！」
[chara_shift name="桃子" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//純一//
	「・・・」
	「（嘘が下手だなぁ〜。滅茶苦茶好きなくせに、テニス。本当は。）」
	「（増田は『世の女は息をするように嘘を吐く』って言ってたが・・・）」
	「（・・・まぁそれはそれとして、ここまでわかりやすいとこの先心配だぞ、僕は。）」
	「・・・まっ、いいけどさ。」
	「じゃあその分、今日は楽しもうぜ！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO01_00" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" eye="MMK_F00_EYE03_00" brow="MMK_F00_BRO03_00" effect="" fade="0.15"]
	//桃子//
	「・・・う、うんっ！」
	//店員//
	「おまたせしました、こちらお水になります。」
	「ご注文はお決まりですか？」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO00_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「あ、はい！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO03_00" effect="" fade="0.15"]
	//桃子//
	「え～と、この『ミッドナイト・スパゲティ』をふたつ！」
	//店員//
	「スパゲティがおふたつですね。」
	「以上でよろしいですか？」
[chara_shift name="桃子" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" fade="0.15"]
	//純一//
	「はい、よろしくおねがいします。」
	//店員//
	「かしこまりました。」
	「ふふっ、おふたりは学生さん？」
[chara_shift name="桃子" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU01_01" brow="MMK_F00_BRO00_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「あっ、そうです！」
[chara_shift name="桃子" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO03_00" effect="" fade="0.15"]
	//桃子//
	「実はずっと来たかったので、お店がやっていてほっとしました！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" fade="0.15"]
	//純一//
	「こんなご時世でお店を開けない所も多いじゃないですか。」
	「こちらも臨時休業しているんじゃないかと不安だったんです。」
	//店員//
	「ははは、そりゃよかった。」
	「ウチは『皆様の日常に寄り添う』ってのがモットーでね。」
	「安寧を求める人のため、材料が揃ううちは暖簾を掲げるつもりだよ。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO00_00" fade="0.15"]
	//桃子//
	「・・・」
	//純一//
	「はあ～、感服です。」
	「この照明がいいですよね！絶妙な明るさが。」
	//店員//
	「アルバイトの方にはお休みしてもらって、家内と二人、」
	「のんびりやっても尚暇なくらいの客足だけどもね？」
	「おふたりが来てくれて、この時期に営業する甲斐があったってもんだ。」
[chara_shift name="桃子" torso="MMK_T01_ARM03_CLO00" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE03_00" fade="0.15"]
	//純一//
	「でも、普段は事前予約が必要ですから、そういう意味で僕達はラッキーでした。」
	//店員//
	「はっはっは、違いない。」
	「まま、せめてこの店にいる間だけは、日常と安息の時をお過ごしください。」
	「・・・おっと、若いお二人にとっては『非日常』かも知れないね！」
	//純一//
	「ははは、ありがとうございます。」
	//店員//
	「それではごゆっくり。」
[se 去る足音]
	//純一//
	「・・・気さくな方で、なんだか嬉しいな。」
	「あんなに構えていたのが馬鹿らしくなる。」
[chara_shift name="桃子"　torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO02_00" fade="0.15"]
	//桃子//
	「・・・うん。そうだね。」
	//純一//
	「ん？どうかしたか？」
[chara_shift name="桃子" mouth="MMK_F01_MOU00_01" fade="0.15"]
	//桃子//
	「ううん。なんだかね、あの店員さん、お父さんみたいだなーって！」
[chara_shift name="桃子" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU00_01" fade="0.15"]
	//桃子//
	「『日常に寄り添う』って、お父さんの信念も近しいと思うの。」
[chara_shift name="桃子" eye="MMK_F01_EYE01_00" mouth="MMK_F01_MOU00_00" fade="0.15"]
	//純一//
	「なるほど。確かに直樹おじさんも、自分じゃなくて他者の幸福を望んでいる。」
	「ひいてはそれが自分の幸福に繋がっていって、まさに循環構造だ。」
	「彼らは職業倫理が高いというか、もはや生きがいなのかもしれないね。」
[chara_shift name="桃子" template="取り繕った笑み斜め" eye="MMK_F01_EYE00_00" fade="0.15"]
	//桃子//
	「うん。そういう人なんだと思う。」
	//純一//
	「・・・」
	「・・・お父さん、格好いいな。」
[chara_shift name="桃子" template="驚き弱" fade="0.15"]
	//桃子//
	「――！」
[chara_shift name="桃子" template="取り繕った笑み" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU04_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="取り繕った笑み" fade="0.15"]
	「・・・」
	//純一//
	「・・・」
	「しかしさ、こんな洒落た店、よく見つけたよな。」
[chara_shift name="桃子" template="元気" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO03_00" fade="0.15"]
	//桃子//
	「あ、実はね、お友達の中村さんが教えてくれたんだ～。」
[chara_shift name="桃子" template="通常・口空き" fade="0.15"]
	//桃子//
	「多分OliveとかHanakoとか読んだんじゃないかな？」
[chara_shift name="桃子" template="通常・口閉じ" mouth="MMK_F00_MOU00_00" fade="0.15"]
	//純一//
	「ハイ・センスな友達だ。」
[chara_shift name="桃子" template="わくわく" fade="0.15"]
	//桃子//
	「なんかさ、私達まだ高校生なのに、相当背伸びしてこういうお店入ったりして・・・」
[chara_shift name="桃子" template="自慢げ" torso="MMK_T00_ARM02_CLO00" eye="MMK_F00_EYE04_00" fade="0.15"]
	//桃子//
	「――なんだかワクワクしない？？」
	//純一//
	「・・・それ、」
	「僕も丁度そう言おうと思ってた。」
[chara_shift name="桃子" template="大はしゃぎ" fade="0.15"]
	//桃子//
	「ほんと！？」
[chara_shift name="桃子" template="満面の笑み" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE04_00" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「えへへ、純一と来てよかった～。」
	//純一//
	「ははは、僕もだよ。」
[chara_shift name="桃子" template="拗ねる・ぷくー"　cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「あ～、なんか乗っかられた～。」
[chara_shift name="桃子" eye="MMK_F00_EYE03_01" mouth="MMK_F00_MOU04_02" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「そういうのはちゃんと言葉にしないと信じてもらえませんよー。」
	//純一//
	「え？心外だな。」
	「僕はそういう事ははっきり言葉にして伝えるように心掛けてるぞ。」
[chara_shift name="桃子" template="疑い照れ斜め" fade="0.15"]
	//桃子//
	「そーかなー？」
[chara_shift name="桃子" template="小悪魔斜め" mouth="MMK_F01_MOU07_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE01_00" fade="0.15"]
	//桃子//
	「じゃあね～・・・」
[chara_shift name="桃子" template="自慢げ" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「・・・私の良いところ！教えて？」
	//純一//
	「えっ〜！？いきなりだなぁ・・・」
	「じゃあ・・・」
	
	ーー選択肢（テキストは同じで立ち絵表示が分岐する（という案。だめか？））
	
	冗談っぽく伝える（桃子が怒る）
	本気っぽく伝える（桃子が照れる）
	
	「う～ん、まずは・・・優しいところ？」
	「後はそうだなぁ・・・テニスが上手いところ？」
[chara_shift name="桃子" template="小悪魔" fade="0.15"]
	//桃子//
	「・・・他は？」
	//純一//
	「他・・・？」
	「・・・いっぱい食べれるところ！」
	
	ーー収束
	
[chara_shift name="桃子" template="怒りツッコミ" fade="0.15"]
	//桃子//
	「も～！ぜぇったい言うと思った！」
[chara_shift name="桃子" template="拗ねる・ぷくー" fade="0.15"]
	「いいもん、別に。いっつもふざけてばっかし！」
	//純一//
	「いやいや、ぼくちん大マジですよ、お嬢さん。」
[chara_shift name="桃子" template="拗ねる・ぷくー" fade="0.15"]
	//桃子//
	「ふんっ、じゃあこのお店の良いところは？」
	//純一//
	「僕はまずこの店内の照度が気に入ったかな。明るすぎず暗すぎず、」
	「お互いの顔はちゃんと見えるけど、細かい所までは見えない位の明るさだから、」
	「脇目も振らず話に集中できる。人がリラックス出来る明るさであるのもポイントが」
	「高く、これがあんまり眩しいと脳は活発になるものの、やはり前傾姿勢になりがちで、」「肩の力が入ってしまう。精神的にもね。学校やオフィスのそれが好例だ。次に空調。」
	「季節は梅雨だし、食事して体温が上がるという人の生理機能を加味し、温度を下げる」
	「ために冷房をつけたくなるところだが、否。技術は日進進歩しているとは言え、細かな」
	「調節までオートマティックに出来る段階には達していない。では何が適するのか。」
	「除湿だよ。先に触れた照度によるトーン・アンド・マナーを維持するためかどうかは」
	「判然としないが、窓が極端に少ないのはお気づきの通り。この事実はそれすなわち」
	「換気能力に劣る事を意味する。確かに、冬場なんかは効率的な断熱効果ないし保温効果」
	「が期待できるが、それは今回脇に置いておこう。ともかく、風通しが悪いのでそもそも」
	「湿度が高くなりがちなのさ。第二に、人の体感温度を左右する重要なファクターとして」
	「湿度は温度の次点に位置する、という事実。要は温度は同じでも湿度を下げるだけで」
	「少し涼しく感じるということ。この二点を抑えてうまく除湿機能を駆使すればこそ、」
	「あまりに肌寒く会話どころか食事に集中出来ないという不安要素を潰すことが出来――」
	
	//店員//
	「お待たせしました。」
	「『ミッドナイト・スパゲティ』、おふたつですね。」
[chara_shift name="桃子" template="おいしそう！" fade="0.15"]
	//桃子//
	「わあ～～！美味しそーー！！」
	//純一//
	「おぉ～っ、待ってましたっ。」
	//店員//
	「それでは、ごゆっくり。」
	
[chara_shift name="桃子" template="おいしそう！" fade="0.15"]
	//桃子//
	「いいにお～い！」
	//純一//
	「服に飛ばさないように気をつけろよ？」
[chara_shift name="桃子" template="明るいツッコミ" fade="0.15"]
	//桃子//
	「もー、子供じゃないんだから、大丈夫だよ！」
[chara_shift name="桃子" template="わくわく" fade="0.15"]
	「それよりほら、はやくはやくっ。」
	//純一//
	「そうだな、それじゃ・・・」
	//純一 桃子//
	「「いただきます！！」」
	//純一//
	「こりゃ美味そうだなぁ・・・！」
	「（普通のスパゲッティボウルより幾分か深めの皿の乳白色が、）」
	「（トマトスープの朱色とスパゲッティの淡い橙色を良く映えさせる。）」
	「（これは魚介類の香りだろうか、ニンニクの陰で、僕の鼻腔から食欲を刺激しつつ、）」
	「（その名の通り真夜中に食べたくなるような佇まいを、緑のハーブが締めている。）」
	//純一//
	「よし、ではでは早速――」
[chara_shift name="桃子" template="真剣" fade="0.15"]
	//桃子//
	「ちょっと待って、純一。」
	//純一//
	「え、なんだ？」
	「やっぱり紙ナプキン貰うか？」
[chara_shift name="桃子" template="焦り" fade="0.15"]
	//桃子//
	「ううん、違うの。」
[chara_shift name="桃子" template="緊張" fade="0.15"]
	「・・・」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	「・・・あのね。」
	//純一//
	「・・・うん。」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	//桃子//
	「・・・折角こんな素敵なところに来たんだし、」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	「何か特別なこと、してみる・・・？」
	//純一//
	「・・・」
	「特別な、こと・・・？」
[chara_shift name="桃子" template="緊張" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	「・・・あ～ん、とか。」
	//純一//
	「・・・」
	「・・・」
	
	
	ーー選択肢
	
	
	あ～んする →A
	口を開ける →B
	
	A
	//純一//
	「・・・では。」
	「はい、あ～ん。」
[chara_shift name="桃子" template="緊張" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	「・・・あ～ん。」
	//純一//
	「・・・」
[chara_shift name="桃子" template="おいしそう！" fade="0.15"]
	//桃子//
	「・・・（もぐもぐ）」
	//純一//
	「どう、美味しい？」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	//桃子//
	「・・・ウン、」
[chara_shift name="桃子" template="おいしそう！" fade="0.15"]
	「おいひい。・・・ちょっと熱いケド。」
	//純一//
	「はは、それはよかった。」
[chara_shift name="桃子" template="照れ笑い" fade="0.15"]
	//桃子//
	「・・・えへへ。」
	
	B
[chara_shift name="桃子" template="緊張" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="照れ" fade="0.15"]
	「はい、あ～ん。」
	//純一//
	「・・・あ～ん。」
	「・・・」
[chara_shift name="桃子" template="緊張" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" template="緊張" fade="0.15"]
	「どうですか・・・？」
	//純一//
	「・・・（もぐもぐ）」
	「・・・うん、美味しいよ。」
[chara_shift name="桃子" template="照れ笑い" fade="0.15"]
	//桃子//
	「・・・えへへ、よかったねぇ。」
	
	
	ーー収束
	
	
[chara_shift name="桃子" template="驚き" fade="0.15"]
	//桃子//
	「――あっ、フォーク！」
	//純一//
	「え？」
	「・・・あ。」
[chara_shift name="桃子" template="気まずい" fade="0.15"]
	//桃子//
	「・・・どうしましょうか？」
	//純一//
	「・・・」
	「・・・まあ、僕は全然気にならないけど。」
[chara_shift name="桃子" template="ニヤニヤ" fade="0.15"]
	//桃子//
	「・・・んふっ！」
[chara_shift name="桃子" template="にっこり" fade="0.15"]
	「じゃあ～、いっか！」
	//純一//
	「いや、君が気にするなら換えてくれて構わな――」
[chara_shift name="桃子" template="照れ笑い" fade="0.15"]
	//桃子//
	「純一だし、別にいいよ！」
[chara_shift name="桃子" template="元気" fade="0.15"]
	「それよりほら、スパゲティ伸びちゃうよ～！」
	//純一//
	「・・・そうだな。」
	「食べよう食べよう。あれだな、イカが入ってるな。」
[chara_shift name="桃子" template="わくわく" fade="0.15"]
	//桃子//
	「だね、後はマッシュルームもあるみたい！」
[chara_shift name="桃子" template="おいしそう！" fade="0.15"]
	「んー、具沢山で嬉しー！」
	//純一//
	「うん、うまい。やはり具材は多いに限る。」
	「タバスコをちょっと足したらもっと美味しくなりそうだ。」
[chara_shift name="桃子" template="期待キラキラ" fade="0.15"]
	//桃子//
	「あっ、それも食べてみたいかもー！」
	
[chara_shift name="桃子" template="通常・口閉じ" fade="0.15"]
	「・・・」
	
	//純一//
	「（こうして桃子とイタリアンへ赴いた。）」
	「（家の事情や部活の事で、依然として不安はあるけれど、）」
	「（少しずつ元気を取り戻している様子だったから、少しホッとした。）」
	「（なんだか今日はデートみたいだったな。）」
	「（・・・ていうかデートそのものだったんじゃ・・・！？）」

	//あ//
	「あ」
	[scroll-stop]