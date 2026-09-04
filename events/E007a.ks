*start
;@expression-status: ai_draft

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene7|


[resetlaypos]
[bg storage="純一部屋"]
	//純一//
	「（久しぶりにデパートにでも行って、夏服でも見ようかな。）」
	//純一//
	「（・・・よし！早速、ルンルンを買ってお家に帰ってくるとしよう。）」
[bg storage="ーーデパート（エル想定。写真ないやん💛）"]
;@standalone-step
	//純一//
	「（やっぱり休日のエルは賑やかだな。）」
	//純一//
	「（段々蒸し蒸ししてきたし、梅雨にも負けない涼し気な服を調達しよう。）」
	//純一//
	「（えっと、紳士服屋はどこだっけか・・・）」
[bg storage="デパート内の画像②"]
	//純一//
	「（・・・）」
[bg storage="デパート内の画像③"]
	//純一//
	「（・・・）」
[bg storage="デパート内の画像④"]
	//純一//
	「（・・・）」
[bg storage="デパート内の画像⑤"]
[bg_move bg_left="0.0" bg_top="0.0" bg_zoom="1.2" time="600"]
	//純一//
	「（・・・）」[scroll-stop]
	「（不覚だった。まさかここまで土地勘をなくしているとは・・・）」
	「（それに加え、レディースエリアに迷い込んでしまったみたいだ。）」
	「（まったく、僕は上品で教養があって礼儀正しい紳士だというのに・・・）」
	//？？//
	「そうねぇ。これはチョット背伸びしすぎじゃないかしら？」
	//？？//
	「えー、そんなことない、年相応だよ～。」
	//純一//
	「（・・・おや？この聞き覚えのある声は――）」
[chara_show name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0007" mouth="SZK_F01_MOU_0010" brow="SZK_F01_BRO_0003" cheek="SZK_F01_CHE_0001" blink="true" x="0.1" y="0.7" size="1.5" fade="0.15"]
[chara_show name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0003" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" blink="true" x="0.3" y="0.7" size="1.5" fade="0.15"]
	//静//
	「私の頃は考えられなかったけどねぇ……そういうものかしら。」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0014" fade="0.15"]
	「ママ、今は平成だってば。」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0005" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" blink="true" x="0.1" y="0.7" size="1.5" fade="0.15"]
	//純一//
	「（桃子のお母さんと杏ちゃんの愛沼親子だ。やはり夏服を買いに来たのかな。）」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0005" brow="SZK_F01_BRO_0003" cheek="SZK_F01_CHE_0001" blink="true" x="0.1" y="0.7" size="1.5" fade="0.15"]
	//静//
	「まぁ確かに、そういうのが一着あってもいいかもしれないわね。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" blink="true" x="0.1" y="0.7" size="1.5" fade="0.15"]
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" x="0.3" y="0.7" size="1.5" fade="0.15"]
	//杏//
	「ね、そうでしょ！それに・・・」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0008" mouth="ANZ_F01_MOU_0012" brow="ANZ_F01_BRO_0002" cheek="ANZ_F01_CHE_0001" fade="0.5"]
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0010" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" fade="0.5"]
	//杏//
	「ほらみて！おねぇにすごく似合ってる！」
[chara_shift name="杏" mouth="ANZ_F01_MOU_0001" fade="0.15"]
	//純一//
	「（ん？おねぇ？）」
	「（ということは・・・）」
[chara_show name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE01_00" blink="true" x="0.325" y="0.7" size="1.5" fade="0.5"]
[chara_shift name="杏" x="0.55" y="0.7" size="1.5" fade="0.5"]
	//桃子//
	「そ、そうかなぁ・・・？」
	//純一//
	「（・・・）」
	「（ですよねーーー。）」
	「（愛沼家御一行もデパートへショッピングか。）」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" fade="0.15"]
	//静//
	「これはどう？ホワイトで涼しげだから、これからの季節にいいんじゃないかしら。」
[chara_shift name="杏" torso="ANZ_T01_0006" eye="ANZ_F01_EYE_0008" mouth="ANZ_F01_MOU_0011" brow="ANZ_F01_BRO_0004" cheek="ANZ_F00_CHE_0001" fade="0.15"]
	//杏//
	「こっちのワインレッドはオトナの女性って感じー！」
[chara_shift name="桃子" torso="MMK_T00_ARM04_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU13_00" brow="MMK_F00_BRO03_00" fade="0.15"]
	//桃子//
	「えぇ～？恥ずかしいよ～。」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0003" mouth="ANZ_F01_MOU_0013" brow="ANZ_F01_BRO_0003" cheek="ANZ_F01_CHE_0001" fade="0.15"]
	//杏//
	「もー全然決まらないじゃん！おねぇはどっちが良いの？」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" fade="0.15"]
[chara_shift name="杏" mouth="ANZ_F01_MOU_0002" fade="0.15"]
	//静//
	「いい加減決めちゃいなさい。」
[chara_shift name="桃子" torso="MMK_T00_ARM11_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU03_00" brow="MMK_F00_BRO05_00" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「う～んと・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU13_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「えぇ～っとぉ・・・」
	//純一//
	「（休日に家族でお買い物ですか。）」
	「（・・・ふふふ、相変わらず家族で仲良しだなぁ。）」
	「（家族の時間に水は差すまい。よし、ここはそっと通り過ぎて――）」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" fade="0.15"]
	//静//
	「それにほら、こっちはフロントホックだから着たり脱いだり楽ちんよ。」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" fade="0.15"]
	//純一//
	「・・・」
	「・・・！？」
[chara_shift name="杏" torso="ANZ_T01_0006" eye="ANZ_F01_EYE_0004" mouth="ANZ_F01_MOU_0011" brow="ANZ_F01_BRO_0004" cheek="ANZ_F01_CHE_0001" fade="0.15"]
	//杏//
	「でもさでもさ、こっちはバストがもーっと強調されるんだよ！？」
	//純一//
	「（・・・）」
	「（ま、まさか・・・よりによって・・・）」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0008" mouth="ANZ_F01_MOU_0001" fade="0.15"]
	//杏//
	「しかもレースが花柄で色っぽい！」
[chara_shift name="杏" torso="ANZ_T01_0006" eye="ANZ_F01_EYE_0005" mouth="ANZ_F01_MOU_0012" fade="0.15"]
	//杏//
	「情熱の赤、寄せて上げて魅力的～！」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" fade="0.15"]
[chara_shift name="杏" torso="ANZ_T01_0006" eye="ANZ_F01_EYE_0005" mouth="ANZ_F01_MOU_0001" fade="0.15"]
	//静//
	「あら、純潔な白色はね、オンナを一番引き立てるのよ。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//桃子//
	「う～ん・・・」
	//純一//
	「（あの三人・・・ブラジャー選んでる！？）」
	「（マズイぞ、至急この場から離脱して――）」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0009" mouth="ANZ_F00_MOU_0007" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" fade="0.15"]
	//杏//
	「ん？」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" fade="0.15"]
	//杏//
	「・・・あ、純一おにぃだ！」
[chara_shift name="静" eye="SZK_F01_EYE_0008" mouth="SZK_F01_MOU_0003" fade="0.15"]
[chara_shift name="桃子" torso="MMK_T00_ARM19_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO00_00" fade="0.15"]
[chara_shift name="杏" mouth="ANZ_F00_MOU_0001" fade="0.15"]
	//純一//
	「（げッ――！？）」
	//桃子//
	「！？」
	「うそ！？」
[chara_shift name="桃子" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//純一//
	「（――しまった！！）」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" x="0.2" y="0.8" size="1.8" fade="0.15"]
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_01" brow="MMK_F00_BRO03_00" x="0.5" y="0.8" size="1.8" fade="0.15"]
[chara_shift name="杏" x="0.8" y="0.8" size="1.8" fade="0.15"]
	//静//
	「あら、純一ちゃんじゃない！こんにちは。」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" fade="0.15"]
	//杏//
	「こんにちはー！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE00_02" fade="0.15"]
	//桃子//
	「・・・」
	//純一//
	「・・・」
	「あ～～～！奇遇ですね～っ。」
	「いや、これはこれは皆さん勢揃いで、どうもどうも～。あははは。」
[chara_shift name="杏" torso="ANZ_T00_0003" mouth="ANZ_F00_MOU_0004" fade="0.15"]
	//杏//
	「おにぃもマルイでお買い物ですか？」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0010" mouth="ANZ_F00_MOU_0010" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" fade="0.15"]
	//杏//
	「・・・ってちょっと待って。そもそも何で女性用エリアにいるの？」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0007" fade="0.15"]
[chara_shift name="静" mouth="SZK_F01_MOU_0007" fade="0.15"]
	//純一//
	「・・・うん、そうだよね。」
	「久しぶりにエルへ夏服を買いに来たら、マルイの中で迷っちゃってさ。」
	「・・・ただそれだけ。本当に。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU05_00" fade="0.15"]
	//桃子//
	「・・・」
	//純一//
	「（だから桃子が着脱の利便性か寄せて上げてかで迷ってたのは聞いてませんよー。）」
	「本当、マイっちゃうよなぁ、あははは。」
	「・・・」
	「（すまない桃子、君を辱しめるつもりはないのだ・・・）」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0007" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" fade="0.15"]
	//静//
	「・・・」
[chara_shift name="静" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0005" fade="0.15"]
	//静//
	「そうだ、丁度いいわ。」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0010" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" fade="0.15"]
	//静//
	「桃子あんた、彼に決めてもらいなさいよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM19_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU13_00" fade="0.15"]
	//純一//
	「！？」
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0009" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="ANZ_E00_0001" fade="0.15"]
	//杏//
	「え、ブラを？」
[chara_shift name="桃子" torso="MMK_T00_ARM17_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU15_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.15"]
	//桃子//
	「え！？ちょっ、やめてよお母さん！！」
[chara_shift name="桃子" torso="MMK_T00_ARM17_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU18_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.15"]
	//純一//
	「（なッ・・・！下着だぞ！？）」
	「（いくら幼馴染とはいえ――）」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0010" mouth="SZK_F01_MOU_0005" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="" fade="0.15"]
	//静//
	「やぁねぇ、あんた。いくら私でもそれはしないわよ！」
[chara_shift name="静" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0003" fade="0.15"]
	//静//
	「そっちじゃなくて、服のほう。」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0004" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" fade="0.15"]
[chara_shift name="桃子" template="照れ笑い" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU04_01" brow="MMK_F00_BRO05_00" effect="MMK_E00_01" fade="0.15"]
	//杏//
	「あっ、そっちね！」
	//純一//
	「（・・・）」
	「（・・・ん？）」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" fade="0.15"]
[chara_shift name="杏" mouth="ANZ_F00_MOU_0001" fade="0.15"]
	//静//
	「さっきまでね、桃子も夏服を選んでたのよ。」
[chara_shift name="静" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0003" fade="0.15"]
[chara_shift name="桃子" eye="MMK_F00_EYE01_01" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO00_00" fade="0.15"]
	//静//
	「でも全然決まらなくって、ちょっと他の所に目が行っちゃってたんだけど・・・」
[chara_shift name="静" torso="SZK_T00_0002" eye="SZK_F00_EYE_0001" mouth="SZK_F00_MOU_0001" brow="SZK_F00_BRO_0001" cheek="SZK_F00_CHE_0001" fade="0.15"]
	//静//
	「そうだわ。折角だし桃子の服、選んであげてくれない？」
[chara_shift name="桃子" torso="MMK_T00_ARM17_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU13_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE02_00" fade="0.15"]
	//純一//
	「・・・はぁ。」
[chara_shift name="桃子" mouth="MMK_F00_MOU01_02" fade="0.15"]
	//桃子//
	「えっー！いいよっお母さん、自分で選ぶから！」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0002" mouth="ANZ_F01_MOU_0004" brow="ANZ_F01_BRO_0001" cheek="ANZ_F01_CHE_0001" effect="" fade="0.15"]
	//杏//
	「こうは言ってますが、おねぇ、全然決めないので困ってたんです。ね？おねぇ。」
[chara_shift name="桃子" torso="MMK_T00_ARM18_CLO00" eye="MMK_F00_EYE02_01" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE01_00" effect="MMK_E00_01" fade="0.15"]
	//桃子//
	「あ、あんずっ。」
[chara_shift name="桃子" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU04_02" fade="0.15"]
	//桃子//
	「仕方ないでしょー！どれも同じ位素敵だから迷っちゃうんだもん。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0010" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" fade="0.15"]
	//静//
	「あんた待ってたら日が暮れるっちゅーの・・・」
[chara_shift name="静" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0002" fade="0.15"]
	//静//
	「こういう訳だから、何か、見繕ってあげて頂戴な。」
	//純一//
	「・・・」
	「まぁ、それ位なら喜んで！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU13_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE01_00" fade="0.15"]
	//桃子//
	「ちょっ、純一まで！」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0008" mouth="ANZ_F01_MOU_0004" brow="ANZ_F01_BRO_0001" cheek="ANZ_F00_CHE_0001" fade="0.15"]
	//杏//
	「おねぇ、ちょっとそこに立ってみて！」
[chara_shift name="桃子" torso="MMK_T00_ARM03_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE02_00" fade="0.15"]
	//桃子//
	「えぇー！？」
[chara_shift name="杏" torso="ANZ_T01_0005" eye="ANZ_F01_EYE_0004" mouth="ANZ_F01_MOU_0011" brow="ANZ_F01_BRO_0001" cheek="ANZ_F01_CHE_0001" x="0.75" fade="0.15"]
	//杏//
	「いーからいーから。ホラ早く！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU04_02" fade="0.15"]
	//杏//
	「も、もぉ・・・わかったよお。」

＜コスト度外視なら3パターンの全く違う服がいいが、現実的なのは形は同じだけど色や模様が違う2パターンかな？＞
＜というのも、ここでPlayerが選んだ服を遊園地で実際に着てくる想定なので、立ち絵やスチルのパターンが増えてしまう＞
＜とりあえず全く違う3パターン（doc下に写真添付）で以下は書きました。＞


	//杏//
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「じゃあ早速、まずはこれ！」Aアイコンin
	//純一//
	「タイトな半袖シャツに、デニム生地のショートパンツか。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「露出が多いけど、活発で健康的な印象を与えるわね。」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" fade="0.15"]
	「若々くて瑞々しい、今が旬のおねぇにぴったりですよねー。」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0014" fade="0.15"]
	「家でのおねぇは大体こんな格好してますよ！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU15_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「こらー！」

	//杏//
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「お次はこちら！」Bアイコンin
	//純一//
	「ふむ、白と淡いピンクのボレロカーディガンとスカートだ。」
	//静//
[chara_shift name="静" mouth="SZK_F01_MOU_0001" fade="0.15"]
	「ルックも素材も柔らかくて、ふんわりしたイメージね。」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0012" fade="0.15"]
	「緻密な装飾も相まって、繊細な感じがしますよね～。」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「こういう服を着こなしてる人は、決まって良い匂いがするんだよなー。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU15_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" blink="true" fade="0.15"]
	//桃子//
	「こぼしたら目立っちゃうな・・・」
[chara_shift name="桃子" mouth="MMK_F00_MOU04_02" fade="0.15"]
	「――べっ、べつにこぼさないけど！」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「最後です、じゃじゃ～ん！」Cアイコンin
	//純一//
	「なるほど、ワインレッドが目を惹くオフショルダーワンピース。」
	//静//
[chara_shift name="静" mouth="SZK_F01_MOU_0003" fade="0.15"]
	「かなりお洒落な色だけど、一枚で着れるからさっぱりしてるわね。」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0012" fade="0.15"]
	「大人な雰囲気が良い意味でおねぇらしくない！」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「肩から手の先まで、腕は丸出しですよ～っ。」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE02_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE02_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「・・・」カァー///

	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" fade="0.15"]
	「こんな感じで、なんとか三つまでには絞ったんです！」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「どれも似合うとは思うのだけど、なにせ当の本人が優柔不断だからねえ。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「だってぇ～。」
	//純一//
	「でも確かに、これは迷いますね・・・」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「おにぃはどれがお好みですか？」
	//純一//
	「え〜・・・」
	「・・・う～ん。」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_01" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE01_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「ねー、恥ずかしいよーっ。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「意見を聞かせて頂戴？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「もー、おかーさーん！」
	//純一//
	「・・・」
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_01" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE01_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" mouth="MMK_F01_MOU03_00" fade="0.15"]
	「・・・うぅ。」
	//純一//
	「（・・・）」
	「（・・・ゴクリ。）」
	//純一//
	「・・・僕は――」

ーー分岐

Aそのままの、飾らない等身大のシャツスタイルが好きかな
Bピンク色のスカートがいいな〜桃子だし
C上品ながらも扇情的なレッドのワンピースが似合うと思う

A
	//純一//
	「僕は、そのままの・・・」
	「飾らない等身大のシャツスタイルが好きかな。」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE00_00" mouth="MMK_F01_MOU00_00" brow="MMK_F01_BRO02_00" cheek="MMK_F01_CHE02_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「・・・」
[chara_shift name="桃子" mouth="MMK_F01_MOU04_01" fade="0.15"]
	「そのままの・・・わたし・・・」
	//純一//
	「ん？あれ？」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「あー、おにぃ、そういうシュミ～？」
	//純一//
	「趣味って、あいや、僕は別に――」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" fade="0.15"]
	//静//
	「『飾らない等身大の』って！どこで覚えたのよそんな言葉！」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「なんかさー、おにぃってさー、えっちっぽいよね～。」
	//純一//
	「そういう意味じゃなくて、なんての、その・・・」
	「着回し！着回しやすいかなって！合わせやすいし！」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0003" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「まあそうね、飾りっ気ないのが飽きがこなくていいわよね～。」
	//純一//
	「そうそう、やっぱりシンプルなのがグッとくるというか・・・」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「Peach Johnよりグンゼだよねー。」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「なんであんたはすぐ下着の話に持ってくのよ・・・」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「おにぃのエロガッパ！むっつり助平！」
	//純一//
	「えっ？・・・ちゅおっ、チョトっ。」
	「やめてよお、あんず嬢・・・ムホホ。」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「キャーーー！」

B
	//純一//
	「僕は、ピンク色のスカートがいいな〜。」
	「・・・桃子だし！？」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「・・・」ぽかーん
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0006" mouth="SZK_F01_MOU_0005" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「・・・」ぽかーん
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「・・・」ぽかーん
	//純一//
	「（あ・・・まずいかも・・・）」
	「（この空気・・・ちょっと、しんどいかも・・・）」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" fade="0.15"]
	//静//
	「・・・」
[chara_shift name="静" mouth="SZK_F01_MOU_0003" fade="0.15"]
	「・・・ふっ。」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「・・・ひひ。」
	//純一//
	「（・・・ん？）」
	//静//
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0005" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" blink="true" fade="0.15"]
	「んふふふ。」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「うひひひっ。」
	//静・杏//
[chara_shift name="静" mouth="SZK_F01_MOU_0010" fade="0.15"]
[chara_shift name="杏" mouth="ANZ_F00_MOU_0014" fade="0.15"]
	「あははははは！！」
	//静//
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0005" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" blink="true" fade="0.15"]
	「ちょっと・・・！！」
[chara_shift name="静" mouth="SZK_F01_MOU_0004" fade="0.15"]
	「なによそれ！」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「おにぃ、テキトーすぎ！！」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「・・・あははははは！！」
	//純一//
	「・・・え。」
	//静//
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0004" mouth="SZK_F01_MOU_0002" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	「あほや・・・あほや・・・！」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" fade="0.15"]
	「っはぁ、はあ・・・あはははっ！」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0014" fade="0.15"]
	「おにぃってホント面白いよねー！」
	//純一//
	「・・・」
	「はは、はははははっ！」
	「それほども・・・」
	「――あるんですけどねッ！」

C
	//純一//
	「僕は、上品ながらも扇情的なワインレッドのワンピースが似合うと思う。」
[chara_shift name="桃子" torso="MMK_T01_ARM01_CLO00" eye="MMK_F01_EYE02_00" mouth="MMK_F01_MOU03_00" brow="MMK_F01_BRO00_00" cheek="MMK_F01_CHE02_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「・・・」！！
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_01" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE01_00" effect="" blink="true" fade="0.15"]
	「・・・」顔赤らめる
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「・・・」
[chara_shift name="杏" eye="ANZ_F00_EYE_0003" mouth="ANZ_F00_MOU_0015" brow="ANZ_F00_BRO_0003" fade="0.15"]
	「・・・純一おにぃ。」
	//純一//
	「・・・」
	「・・・はい。」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「・・・」
[chara_shift name="杏" mouth="ANZ_F00_MOU_0012" fade="0.15"]
	「わかってますね～！！」
	//純一//
	「・・・」
	「・・・そお？」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0003" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0004" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「や～ねえ、扇情的ってアンタ・・・」
[chara_shift name="静" mouth="SZK_F01_MOU_0003" fade="0.15"]
	「最近のコはおませだわぁ～。」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0001" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「ワインレッド・・・」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	「『今以上　それ以上　愛されるのに』ですね！」

＜解＞83年発売、オリコン一位獲得の安全地帯より「ワインレッドの心」のサビ

	//純一//
	「杏ちゃん、随分渋い曲知ってるね・・・」
	//杏//
[chara_shift name="杏" torso="ANZ_T00_0001" eye="ANZ_F00_EYE_0008" mouth="ANZ_F00_MOU_0012" brow="ANZ_F00_BRO_0001" cheek="ANZ_F00_CHE_0001" blink="true" fade="0.15"]
	「杏はなんでも知っているのです。」
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0004" brow="SZK_F01_BRO_0002" cheek="SZK_F01_CHE_0001" effect="SZK_E01_0001" blink="true" fade="0.15"]
	//静//
	「背伸びしたい年頃なのかしら？いいわねぇ、若いって。」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「もお、ママそればっかり！やめてよね〜。」


ーー収束
	//静//
[chara_shift name="静" torso="SZK_T01_0005" eye="SZK_F01_EYE_0005" mouth="SZK_F01_MOU_0014" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	「あはははは！」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「ふふふふふっ。」
	//純一//
	「ははははは。」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	//桃子//
	「あはははは。」
	//桃子//
[chara_shift name="桃子" torso="MMK_T01_ARM00_CLO00" eye="MMK_F01_EYE00_01" mouth="MMK_F01_MOU04_01" brow="MMK_F01_BRO01_00" cheek="MMK_F01_CHE01_00" effect="" blink="true" fade="0.15"]
	「・・・」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU15_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="" blink="true" fade="0.15"]
	「――じゃ・な・く・て！」
[chara_shift name="桃子" mouth="MMK_F00_MOU04_02" fade="0.15"]
	「もー！ほらっ、行くよっ杏！」
[chara_shift name="杏" torso="ANZ_T00_0002" eye="ANZ_F00_EYE_0002" mouth="ANZ_F00_MOU_0005" brow="ANZ_F00_BRO_0003" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「あっ、ちょっと、おねぇ！」
[chara_shift name="静" torso="SZK_T01_0004" eye="SZK_F01_EYE_0001" mouth="SZK_F01_MOU_0001" brow="SZK_F01_BRO_0001" cheek="SZK_F01_CHE_0001" effect="" blink="true" fade="0.15"]
	//静//
	「じゃあまたね、純一ちゃん！」
[chara_shift name="静" mouth="SZK_F01_MOU_0003" fade="0.15"]
	「また遊びにおいでなさいな！」
	//純一//
	「えっ、はい、是非！」
[chara_shift name="杏" torso="ANZ_T00_0003" eye="ANZ_F00_EYE_0001" mouth="ANZ_F00_MOU_0014" brow="ANZ_F00_BRO_0002" cheek="ANZ_F00_CHE_0001" effect="" blink="true" fade="0.15"]
	//杏//
	「あー！ワンピース欲しい、ワンピース！」
[chara_shift name="桃子" torso="MMK_T00_ARM00_CLO00" eye="MMK_F00_EYE01_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" blink="true" fade="0.15"]
	//桃子//
	「そ、それじゃガッコーで！！」
	//純一//
	「お、おう・・・」
	//杏//
[chara_shift name="杏" mouth="ANZ_F00_MOU_0015" fade="0.15"]
	「おにぃまたね～！」
[chara_hide name="桃子" fade="0.15"]
[chara_hide name="杏" fade="0.15"]
[chara_hide name="静" fade="0.15"]
	//純一//
	「うん。」
	「・・・」
	//純一//
	「（・・・）」
	「（・・・行ってしまった。）」
	//純一//
	「（昔から変わらず、活気のある家族だなぁ。）」
	「（・・・梅雨らしく、台風のように過ぎ去ってしまった。）」
	//純一//
	「（・・・）」
	「（さて・・・）」
	//純一//
	「・・・」
	「・・・」
	//純一//
	「（何しに来たんだっけ。）」

ーーエピローグ

	//純一//
	「（こうして今日はデパートで過ごした。）」
	//純一//
	「（まさか桃子達に会うとは思わなかった。）」
	「（・・・もうちょっとちゃんとした格好をして行けばよかったな。）」
	//純一//
	「（まっ、当初の目的だった僕の夏服もあの後買ったし、よしとしよう！）」