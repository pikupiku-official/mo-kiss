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
[BGM bgm="school" volume="0.5" loop="true"]
[SLP60]

[WINshow]
	[桃子　eye="eye1" mouth="mouth1" brow="brow1"]「こんにちは。これは最初のテキストです。」[en]
[WINhide]

[SLP30]
[WINshow]
	[桃子]「会話の2番目の部分です。」[en]
[WINhide]

[SLP30]
[WINshow]
	[桃子]「言葉は想像力を運ぶ電車です。 日本中どこまでも想像力を運ぶ 『私たち』という路線図 一個の私は想像力が乗り降りする 一つ一つの駅みたいなもので どんな小さな駅にも止まる 各停みたいな言葉もあれば 仕事をしやすくしてくれる 急行みたいな言葉もあるし」[en]
[WINhide]

*scene2|&f.title+"教室のシーン"
[resetlaypos]

[SLP30]
[BGM bgm="classroom" volume="0.4" loop="true"]
[SLP60]

[WINshow]
	[サナコ]「別の場面に移動しました。」[en]
[WINhide]

[SLP30]
[WINshow]
	[サナコ]「これは最後のテキストです。」[en]
[WINhide]

[return] 