*start

;----------------------------------------------
;◆メインシナリオ
;----------------------------------------------

[iscript]
	f.title = "メインシナリオ";
[endscript]

[rclick call=true storage="rclick.ks" target="*rclick" enable=true]

*scene1|&f.title+"最初のシーン"
[resetlaypos]

[SLP30]
[bg storage="school"]
[BGM bgm="school" volume="0.5" loop="true"]
[SLP60]

[WINshow]
	[chara_new name="桃子"　eye="eye1" mouth="mouth1" brow="brow1"]
	「こんにちは。」[en]
	「これは最初のテキストです。」[en]
[WINhide]

[SLP30]
[chara_move sub="桃子" time=400 left="+=100" top="+=50"]
[WINshow]
	「会話の2番目の部分です。」[en]
[WINhide]

[SLP30]
[chara_move sub="桃子" time=1000 left="-=50" top=0]
[WINshow]
	「言葉は想像力を運ぶ電車です。日本中どこまでも想像力を運ぶ、『私たち』という路線図。[en]
	一個の私は想像力が乗り降りする一つ一つの駅みたいなもので、どんな小さな駅にも止まる各停みたいな言葉もあれば、[en]
	仕事をしやすくしてくれる 急行みたいな言葉もあるし。」[en]
[WINhide]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[SLP30]
[bg storage="classroom"]
[BGM bgm="classroom" volume="0.4" loop="true"]
[SLP60]

[WINshow]
	[chara_new sub="桃子"　eye="eye1" mouth="mouth1" brow="brow1"]
	「別の場面に移動しました。」[en]
[WINhide]


[chara_move sub="サナコ" time=700 left=200 top=20]
[WINshow]
	「わかる人にしかわからない、快速みたいな言葉もあって、一番言葉の集まる駅にしか止まらない、新幹線みたいな言葉もあります。[en]
	地下の暗闇を走る言葉もあります。地下から地下へ受け渡されるよこしまな想像力たち。[en]
	でも時折、地下から地上に顔を出してビルの谷間をくぐるとき、不意の太陽が無理矢理たてじまに変えようとするから、想像力は眉をしかめたりします。」[en]
[WINhide]

[SLP30]
[chara_move sub="サナコ" time=600 left="-=200" top="+=60"]
[WINshow]
	「これは最後のテキストです。」[en]
[WINhide]

[return] 