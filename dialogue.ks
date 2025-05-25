*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

*scene1|&f.title+"最初のシーン"
[resetlaypos]

[bg_show storage="school"  bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[BGM bgm="school" volume="0.5" loop="true"]

[chara_show name="桃子"　eye="eye1" mouth="mouth1" brow="brow1" x="0.5" y="0.5"]

	//桃子//
	「こんにちは。」
	「これは最初のテキストです。」

[chara_move subm="桃子" time="400" left="0.1" top="0.02" zoom="3"]

	//桃子//
	「会話の2番目の部分です。」

[bg_move storage="school" bg_left="0.1" bg_top="0.1" time="1000" bg_zoom="1.5"]
[chara_move subm="桃子" time="1000" left="-0.2" top="0" zoom="0.3"]

	//桃子//
	「言葉は想像力を運ぶ電車です。日本中どこまでも想像力を運ぶ、『私たち』という路線図。」
	「一個の私は想像力が乗り降りする一つ一つの駅みたいなもので、どんな小さな駅にも止まる各停みたいな言葉もあれば、」
	「仕事をしやすくしてくれる 急行みたいな言葉もあるし。」

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[bg_show storage="classroom"]
[BGM bgm="classroom" volume="0.4" loop="true"]

	//桃子//
	「別の場面に移動しました。」

[chara_show name="サナコ"　eye="eye1" mouth="mouth1" brow="brow1" x="0.2" y="0.2"]

	//サナコ//
	「わかる人にしかわからない、快速みたいな言葉もあって、一番言葉の集まる駅にしか止まらない、新幹線みたいな言葉もあります。」
	「地下の暗闇を走る言葉もあります。地下から地下へ受け渡されるよこしまな想像力たち。」
	「でも時折、地下から地上に顔を出してビルの谷間をくぐるとき、不意の太陽が無理矢理たてじまに変えようとするから、想像力は眉をしかめたりします。」

[chara_hide subh="桃子"]

[chara_move subm="サナコ" time="600" left="0.1" top="0.1" zoom="1.7"]

	//サナコ//
	「これは最後のテキストです。」