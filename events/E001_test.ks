//システム//
「テスト用の分岐シナリオです」

[chara_show name="girl1" eye="eye1" mouth="mouth1" x="0.5" y="0.5"]

//烏丸神無//
「こんにちは...」
「あなたは新しい人ね」

「どう話しかけますか？」

[choice option1="積極的に話しかける" option2="慎重に様子を見る" option3="そっと立ち去る"]

[if condition="choice==1"]
//烏丸神無//
「積極的なのね...」
「興味深いわ」
[flag_set name="aggressive_approach" value="true"]
[event_unlock target="E010,E011" lock="E012,E013"]
[endif]

[if condition="choice==2"]
//烏丸神無//
「慎重なタイプなのね」
「悪くないわ」
[flag_set name="careful_approach" value="true"]
[event_unlock target="E012" lock="E010,E011,E013"]
[endif]

[if condition="choice==3"]
//烏丸神無//
「...そう、立ち去るのね」
「またいつか...」
[flag_set name="passive_approach" value="true"]
[event_unlock target="E013" lock="E010,E011,E012"]
[endif]

//システム//
「あなたの選択により、新しいイベントが解放されました」