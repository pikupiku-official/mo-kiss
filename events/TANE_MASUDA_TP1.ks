*start

[scroll-stop]
	//純一//
	「温泉を断ったこと、局部を見られるのを極端に嫌がること、包茎という言葉だけ避けること……。」
	「この三つをつなげれば、増田が隠していることが分かるはずだ。」

[seed_answer turning_point="MASUDA_TP1"]

[if condition="MASUDA_TP1_RESULT==correct"]
	//純一//
	「そうか。全部つながった。増田は真性包茎なんだ。」
	//増田//
	「……そこまで分かったなら、もう何も言うな。」
[event_control lock="TANE_MASUDA_TP1"]
[endif]

[if condition="MASUDA_TP1_RESULT==incorrect"]
	//増田//
	「全然違う。勝手なことを言うなよ。」
	//純一//
	「推理を組み直したほうがよさそうだ。」
[event_control lock="TANE_MASUDA_TP1"]
[endif]
