# TestForGD 自由記述チュートリアル

`events/TestForGD.ks` は、桃子がディズニーランドへの誘いを渋る理由を答える会話。
問題IDは `MOMOKO_GD_MONEY`。既存の桃子・増田の問題とは別に追加している。
事前のタネ取得は不要。教室背景、桃子と増田の立ち絵、既存BGMを使用する。
提示された台詞を使い、💦は桃子の既存エフェクトで表現する。

## 判定と分岐

- 正解：「桃子は今月、お金がない」。主語・今月・断定口調の省略を許す。
- 「金欠」「旅行で使いすぎた」「妹のプレゼントでお金がない」「お金がないのかもしれない」も正解。
- 借金などの誤った理由、他人の金欠、ディズニー嫌いなどの余計な断定は不正解側へ戻す。
- 正解時は入力文を純一の発言として表示し、「――そうだろ？」以降に進む。
- 不正解・微妙の場合は「（入力文・・・？）」を表示し、状況整理後に何度でも再入力できる。
- 微妙の場合は既存仕様に従って前回の入力を残す。不正解の場合は空欄から再入力する。
- モデルの重みは変更していない。既存Ruri INT8の正負例・拒否パターン・しきい値を問題単位で設定した。

設定は `data/turning_points.json`、評価用回答例は `data/evaluation/momoko_gd_money.json`。
`answer_echo` 設定のない既存問題は従来どおり入力文を表示する。
プレビューには入力用マネージャー・描画を接続し、進行と回答結果はメモリ内に保持する。

## 試遊

既存エディタで `events/TestForGD.ks` を開いて試遊する。
既存のプレビューツールからも実行できる。この作業で用意したPython 3.12環境の場合：

```powershell
$env:QT_PLUGIN_PATH = (Resolve-Path '.venv-gd/Lib/site-packages/PyQt5/Qt5/plugins').Path
$env:QT_QPA_PLATFORM_PLUGIN_PATH = "$env:QT_PLUGIN_PATH/platforms"
.\.venv-gd\Scripts\python.exe tools/dialogue_preview_player.py events/TestForGD.ks
```

この作業環境の `python` 単体には依存パッケージが入っていないため、上記の仮想環境を使用する。
入力は日本語IMEに対応し、変換確定後のEnterで回答する。

## 検証結果（2026-10-15）

- 実モデルで86例を評価し、正解側／再入力側への振り分けは86/86一致。
- 内訳は調整用33例、補強に用いた検証用33例、最終設定に未使用の20例。
- 最終未使用20例は正解10、不正解側10。後者の1例は微妙判定で再入力に進む。
- 厳密な `correct` / `incorrect` の一致は85/86。結果の詳細は `outputs/gd-money-evaluation.json`。
- 新規86例、実際のプレビュー再生、既存の入力・保存・タネ管理を合わせて110テスト成功。
- 実プレビューではTEXTINPUTとEnterを送信し、不正解→再入力→微妙→再入力→正解の遷移を確認。
- プレビュー前後で既存のストーリーフラグとタネ状態ファイルのバイト列が不変であることを確認。
- 入力画面と正解会話のPNGを目視確認。長い入力プロンプトの画面外へのはみ出しを修正した。
- 描画とBGM再生処理はオフスクリーン・ダミー音声環境で確認。実スピーカーでの聴取、日本語IMEの手操作は未検証。

別途、既存の増田の実モデルテストに1件の失敗がある。
`増田は真性包茎なんだ` が不正解になる結果を、HEADの変更前設定でも再現した。
既存設定は変更していない。再現記録は `outputs/gd-existing-regression.json`。
全関連テストをまとめた結果は139成功・既存の1件失敗。今回対象の110テストは成功している。

回答例は有限のため、未知のすべての言い回しに対する正しさを保証する評価ではない。

再評価：

```powershell
.\.venv-gd\Scripts\python.exe tools/evaluate_momoko_gd.py --split all --out outputs/gd-money-evaluation.json
```

画面：`outputs/gd-money-input.png`、`outputs/gd-money-success.png`。
