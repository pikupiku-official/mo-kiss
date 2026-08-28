*start
;@expression-status: human_confirmed

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene1|&f.title+"最初のシーン"
[resetlaypos]

[SE se="電車走行中1.mp3" volume="0.5" frequency="5"]
[bg_show storage="車窓①" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
	//ナレ//
	「＿＿＿」
	「＿＿＿」
	「見慣れた中央線の車窓から流れる風景。」
[bg_show storage="車窓②" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
	「いつだってこんな景色ばかり。」
	「やっぱりなんか物足りないな。西新宿みたいな高層ビルもないし。」
[bg_show storage="車窓テニス" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
	「そんなことを考えていると、停車のアナウンスが響く。」
[bg_show storage="車窓線路" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
	「僕を車内の隅に押し込んでいる周りの人たちも降りる支度をし始める。」
	「向かいの大学生らしき男がカバンに突っ込んだのはカーグラフィック。表紙はジャガー。」
	「僕もいつか、日曜洋画劇場で見たジェームズボンドみたいに、流麗なセダンを乗り回してみたい、と思った。」
[bg_show storage="車窓③" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
;@standalone-step
[bg_show storage="車窓④" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
;@standalone-step
[bg_show storage="車窓⑤" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
;@standalone-step
[sestop]
[bg_show storage="車窓⑥" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[SE se="電車停車.mp3" volume="0.5" frequency="1"]
;@standalone-step
[bg_show storage="車窓⑦" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[sestop]
[SE se="電車蒸気噴出.mp3" volume="0.5" frequency="1"]
;@standalone-step
[sestop]
[SE se="電車の発車ベル.mp3" volume="0.5" frequency="1"]
[SE se="電車のドアが開く1.mp3" volume="0.5" frequency="1"]
;@standalone-step
[fadeout color="black" time="0"]
[SE se="衣擦れ3" volume="0.5" frequency="1"]
	//ナレ//
	「ドアが開くといつものようにあっという間に車内から押し出される。」
[sestop]
[fadein time="0"]
[bg_show storage="国分寺駅構内" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[SE se="休日でごった返す駅構内.mp3" volume="0.5" frequency="5"]
	//ナレ//
	「＿＿＿」
	「やはり外の空気は最⾼だ。」
	「緑⾵が僕の周りにまとわりついていたすべての湿気を流し去ってくれる。」
	「僕は、朝の電⾞にはあるものが充満していると思う。」
	「それは通勤、通学を“しなければいけない⼈々”のネガティブな感情だ。」
	「そんな⼈々に流されながら階段を登る。」

[fadeout color="black" time="1.0"]
[SE se="階段を登る" volume="0.5" frequency="5"]
;@standalone-step

[sestop]
[bg_show storage="混んでいる国分寺駅改札内" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[SE se="station_ticket_gate1" volume="0.5" frequency="5"]
[fadein time="1.0"]
	//ナレ//
	「＿＿＿」
	「階段を上り切ると、⼈混みの３割ほどは⻄武線の⽅へ吸い込まれていった。」
	「＿＿＿」
	「僕は改札を抜け、いつもの通学路へ踏み出した。」
	
[event_control unlock="E002,E003,E004,E005"]


[fadeout color="black"]
;@standalone-step
[bg_show storage="通学路①" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[fadein time="1.5"]
;@standalone-step
	//？？//
	「君に触れたい〜♪君に触れたい〜♪」
	//純一//
	「（うげっ、朝からこの声はきっと・・・）」
[bg_show storage="通学路②" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="増田" torso="MST_T00_ARM_0007" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0009" brow="MST_F00_BRO_0007" blink="true" x="0.77006507" y="0.66919739" size="0.7" fade="0.15"]
	//？？//
	「⽇向の窓でぇ〜へ〜♪」
	//純一//
	「（やっぱりこいつだ・・・）」
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0006" blink="true" x="0.77006507" y="0.66919739" size="0.7" fade="0.15"]
[bgm bgm="MokMas42654.mp3" volume="0.5" loop="true" fade="0.0"]
	//増田//
	「おっ！純⼀じゃんかあ！」
	//純一//
	「（こ、ここはあえて放っておこう・・・）」
[bg_show storage="通学路①" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_hide name="増田" fade="0"]
	//純一//
	「（さ、僕は一人で学校へ・・・）」
[chara_show name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0014" brow="MST_F01_BRO_0008" blink="true" x="0.30639913" y="1.28958785" size="3.1" fade="0.15"]
[se se="Motion-Swish03-7.mp3" volume="0.5" frequency="1" block="false"]
	//？？//
	「おーい！無視すんなって！」
	//純一//
	「うわあ！びっくりした！」
[chara_shift name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0002" mouth="MST_F01_MOU_0017" brow="MST_F01_BRO_0007" effect="MST_E01_01" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//増田//
	「純一よ、いつからお前はそんな冷たい奴になったんだ？」
	//純一//
	「むしろ増⽥が暑いんだよ。」
[chara_shift name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0008" mouth="MST_F01_MOU_0003" brow="MST_F01_BRO_0007" effect="MST_E01_01" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//増田//
	「え～？俺が悪いのかよ～。」
	//純一//
	「（僕は軽⼝を叩く。そうそう、こんな感じ。これがいつものムード。）」
	「（彼は増⽥⼀樹。）」
	「（かれこれ中学から５年間の付き合いになる。）」
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0011" mouth="MST_F01_MOU_0003" brow="MST_F01_BRO_0006" effect="" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//増田//
	「まったく、つれないなあ。」
	//純一//
	「僕は昔から朝が弱いんだ。」
[chara_shift name="増田" torso="MST_T01_ARM_0007" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0004" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//増田//
	「そういやそうだったな。」
[se se="走る足音近づき止まる.mp3" volume="1.0" frequency="1" block="false"]
[chara_shift name="増田" torso="MST_T01_ARM_0007" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0005" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//増田//
	「修学旅行のときなんかお前…」
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0006" mouth="MST_F01_MOU_0013" brow="MST_F01_BRO_0006" x="0.25759219" y="1.0791757" size="2.4" fade="0.15"]
	//純一//
	「・・・ん？」
	//？？//
	「はぁ……はぁ……」[female]
[fadeout color="black" time="1.0"]
[bg_show storage="通学路②" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_hide name="増田" fade="0"]
[chara_show name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_01" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE00_00" effect="MMK_E00_01" blink="true" x="0.42841648" y="0.63882864" size="0.75" fade="0"]
[bgmend time="1.0"]
[fadein time="1.0"]
	//？？//
	「つ、疲れたあ・・・いったん休憩・・・」[female]
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE00_00" effect="" blink="true" x="0.42841648" y="0.63882864" size="0.75" fade="0.15"]
	//？？//
	「あれっ、じゅんいちだ。」[female]
[chara_shift name="桃子" torso="MMK_T00_ARM07_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.42841648" y="0.63882864" size="0.75" fade="0.15"]
	//？？//
	「じゅんいち～～～～！」[female]
[fadeout color="black" time="2.0"]
[bg storage="通学路①"]
[chara_show name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0001" brow="MST_F00_BRO_0004" blink="true" x="0.25" y="1.0" size="2.3" fade="0.15"]
[chara_show name="桃子" torso="MMK_T00_ARM07_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" blink="true" x="0.75" y="1.0" size="2.3" fade="0.15"]
[bgm bgm="MokLap1.mp3" volume="0.5" loop="true" fade="0.0"]
[fadein time="2.0"]
	//？？//
	「おはよう！」[female]
	//純一//
	「やあ桃⼦。」
	「（まるでお⽇様みたいな彼⼥は幼馴染の愛沼桃⼦。）」
	「（僕とは⼩学⽣以来の幼馴染で、増⽥と共に⼀緒のクラスでもある。）」
	「今⽇は珍しく遅いんだな。」
[chara_shift name="桃子" torso="MMK_T00_ARM09_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「うん。家族で古畑任三郎観ててね、夜更かししちゃったの。」
[chara_shift name="桃子" torso="MMK_T00_ARM08_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU09_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" effect="" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「ふわぁ～。」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0008" mouth="MST_F00_MOU_0010" brow="MST_F00_BRO_0005" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「でもさ、古畑は⽕曜だよな？」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO01_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「そうだよー。」
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0012" brow="MST_F00_BRO_0005" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「ってことは、わざわざ録画して⾒てるのか？」
[chara_shift name="桃子" torso="MMK_T00_ARM06_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU00_00" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「うん！」
[chara_shift name="桃子" torso="MMK_T00_ARM09_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU02_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0001" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0004" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「うちはみんな三谷幸喜ファンだからね～。」
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0011" mouth="MST_F00_MOU_0011" brow="MST_F00_BRO_0004" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「桃子ん家は相変わらず仲良しだよな。」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE04_00" mouth="MMK_F00_MOU11_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE01_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「えへへ…」
[se se="二人の歩く足音補装.mp3" volume="0.5" frequency="1" block="false"]
	//純一//
	「（ニコニコ笑う彼⼥の横を、リーボックのスニーカーを履いた⽣徒が通り過ぎていくのが⾒えた。）」
	「（それを⾒て、桃⼦の部活を思い出す。）」
	「……そういえばさ桃⼦、テニス部は今⽇朝練じゃなかった？」
[chara_shift name="桃子" torso="MMK_T00_ARM07_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU03_02" brow="MMK_F00_BRO00_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0005" eye="MST_F00_EYE_0006" mouth="MST_F00_MOU_0012" brow="MST_F00_BRO_0005" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「あっ…忘れてたぁ！」
[chara_shift name="増田" torso="MST_T00_ARM_0005" eye="MST_F00_EYE_0006" mouth="MST_F00_MOU_0016" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「やっぱりそうだと思った。」
[chara_shift name="桃子" torso="MMK_T00_ARM06_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU04_02" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「桃子は天然だし。」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE02_00" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0005" eye="MST_F00_EYE_0002" mouth="MST_F00_MOU_0007" brow="MST_F00_BRO_0005" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「天然ですって？」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE02_01" mouth="MMK_F00_MOU01_02" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「失礼ね〜〜！」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE02_01" mouth="MMK_F00_MOU06_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0010" mouth="MST_F00_MOU_0004" brow="MST_F00_BRO_0006" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「ま、まあでも純⼀に救われたな！」
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0007" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0006" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「桃⼦さんよ、早く⾏かないと遅刻するぞ？」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「うん…遅刻したら〇〇先⽣に怒られちゃう。」
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0003" mouth="MST_F00_MOU_0006" brow="MST_F00_BRO_0006" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「(まるで久しぶりに運動させられている飼い⽝みたいだ。)」
	「（けど、僕は桃⼦が他の⼈たちに笑われてる姿はあまり⾒たくないな。）」
	「今⾛っていけば間に合うと思うよ。」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE03_00" mouth="MMK_F00_MOU05_01" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
[chara_shift name="増田" torso="MST_T00_ARM_0006" eye="MST_F00_EYE_0006" mouth="MST_F00_MOU_0011" brow="MST_F00_BRO_0006" effect="MST_E00_02" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「そうかな？」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_02" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO03_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「……」
[chara_shift name="桃子" torso="MMK_T00_ARM05_CLO00" eye="MMK_F00_EYE00_00" mouth="MMK_F00_MOU05_00" brow="MMK_F00_BRO02_00" cheek="MMK_F00_CHE04_00" effect="MMK_E00_01" x="0.75" y="1.0" size="2.3" fade="0.15"]
	//桃子//
	「やっぱりせっかく純⼀が教えてくれたことだし、頑張ってみる！」
[chara_hide name="桃子" fade="1.0"]
[se se="走る足音遠ざかる.mp3" volume="0.5" frequency="1" block="false"]
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0006" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0004" effect="" x="0.25" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「おう。」
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
[bgmend time="1.0"]
	//増田//
	「・・・。」
	「結局、俺ら⼆⼈ってことだ。なあ純⼀。」
	//純一//
	「そうだね…」
[chara_shift name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0010" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
[bgm bgm="MokMas42654.mp3" volume="0.5" loop="true" fade="0.0"]
	//増田//
	「よし、そうと決まればスピッツでも歌うか？」
	//純一//
	「（いつもの増⽥リサイタルが始まりそうだ。今回はどの曲だろうか。）」
	「リクエストは受け付けてますか？」
[chara_shift name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0008" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「おう。何がいいんだ。」
	//純一//
	「なんだっけ、さっき増⽥が⼝ずさんでたやつ。あれ。」
[chara_shift name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0011" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0008" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「⽇なたの窓に憧れてか？」
[chara_shift name="増田" torso="MST_T01_ARM_0007" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0015" brow="MST_F01_BRO_0008" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「純⼀もセンスがいいねぇ！」
	//桃子//
	「純⼀〜〜〜〜〜！ありがとね〜〜〜！！」
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0008" mouth="MST_F01_MOU_0013" brow="MST_F01_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「え？」
[chara_shift name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0006" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「あ？」
	//純一//
	「（僕らの声は同時だった。突然の⼤声に驚いて、⾜を⽌める。そして辺りを⾒回す。）」
[chara_shift name="増田" torso="MST_T00_ARM_0005" eye="MST_F00_EYE_0004" mouth="MST_F00_MOU_0013" brow="MST_F00_BRO_0006" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「純⼀、あそこだ。⾒ろよほら、あっちの前を！」
	//純一//
	「（急いで視線を増⽥が指差す⽅に向ける。）」

[chara_show name="桃子" torso="MMK_T03_ARM03_CLO00" eye="MMK_F03_EYE04_00" mouth="MMK_F03_MOU07_00" brow="MMK_F03_BRO00_00" cheek="MMK_F03_CHE03_00" blink="true" x="0.23" y="0.54" size="0.6" fade="0.15"]
[chara_hide name="増田" fade="0.15"]
[bg_show storage="通学路③" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
	//純一//
	「(視線の先にはとびきりの笑顔の桃⼦がいる。)」
	「(僕は正直⼾惑いつつも、急いで彼⼥に⼿を振る。)」
	//増田//
	「頑張れよ～！」

[chara_hide name="桃子"　eye="eye1" mouth="mouth1" x="0.5" y="0.5"]
[bg_show storage="通学路①" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[chara_show name="増田" torso="MST_T01_ARM_0008" eye="MST_F01_EYE_0010" mouth="MST_F01_MOU_0015" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「（増⽥の声の後、桃⼦が校⾨の中に駆け込んでいく姿が⼩さく⾒えた。）」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「あいつたまにああいうことするよな。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「素直というか大胆というかさあ。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「・・・」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0009" brow="MST_F01_BRO_0004" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「人を惹きつけるものがあるよな、あの性格。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0006" brow="MST_F01_BRO_0004" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「・・・」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0001" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「なあ、純⼀。」
	//純一//
	「・・・」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0002" mouth="MST_F01_MOU_0013" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「純⼀？おい、どうしたんだよ。」
	//純一//
	「あ、ああ……えーと……なんだっけ。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「なんだよ全く。」
	「俺の話も聞かず、⽴ち⽌まってボーッとしやがって。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0002" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「ホントにお前は朝が弱いんだからさ、呆れるよ。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0002" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//純一//
	「（増⽥の⾔う通り、全く彼の話が頭に⼊ってこなかった。）」
	「（正直に⾔うと、坂上に⽴ち笑顔で⼿を振る彼⼥の姿、彼⼥を照らす朝の光。）」
	「（その景⾊に⽬が離せなかったからだ。）」
	「（それは映画の導⼊シーンみたいだった。）」
	「増田。」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0003" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「はあ。」
	//純一//
	「僕が今考えていたことを知りたい？」
[chara_show name="増田" torso="MST_T01_ARM_0006" eye="MST_F01_EYE_0002" mouth="MST_F01_MOU_0010" brow="MST_F01_BRO_0006" blink="true" x="0.5" y="1.0" size="2.3" fade="0.15"]
	//増田//
	「早く教えろよ。」
	//純一//
	「（僕は⽌めていた⾜を踏み出しながら、整理した答えを増⽥に返す。）」
	「朝も捨てたもんじゃないってこと。」

[SE se="風が流れる音。.mp3" volume="0.5" frequency="5"]

[scroll-stop]