# ks-editor Webプレビュー移植方針

## Phase 2 判断

`mokiss.jp/dev/ks-editor` は、現在のGitHub ActionsからLolipopへ静的ファイルとPHPを配置する構成である。常駐Pythonプロセス、Pygame、ローカルファイルシステムを前提にすると、共有サーバー上の起動・監視・依存更新が別途必要になる。

そのため、プレビュー用途では `dialogue/` をサーバーへそのまま配置せず、次の境界でブラウザへ移植する。

- KS解析: ブラウザ内JavaScript
- IR相当: `step + actions + text` の小さい中間表現
- 状態遷移: 選択Stepまで先頭から再生する決定的リプレイ
- 描画: Canvas 2D（1440×1080の仮想座標）
- アセット一覧・画像: GitHub Contents API / raw.githubusercontent.comから取得
- 保存: 既存 `api.php` 経由のGitHub Contents API

この方式では、Python側の変更を自動反映することはできない。一方、画像とKSはGitHubの最新 `main` を都度参照し、Webサーバー側にゲーム一式を複製しなくてよい。

## 移植した規則

- `bg`, `bg_show`, `bg_move`
- `chara_show`, `chara_shift`, `chara_move`, `chara_hide`
- `fadeout`, `fadein`
- `choice`, `bgm`, `bgmstart`, `bgmstop`, `se`
- ラベル、話者、本文、`scroll-stop`
- 立ち絵レイヤー順: torso → brow → cheek → eye → mouth → effect → accessory
- トルソー番号に応じた `_Fxx_`, `_Exx_`, `_Axx_` パーツ候補フィルタ
- `VIRTUAL_WIDTH=1440`, `VIRTUAL_HEIGHT=1080`
- 背景を1440×1080へ変形後、Python版と同じズーム・オフセット制限で描画
- `ui.text-box.png`, `ui.auto.png`, `ui.skip.png` の実画像とRGB乗算色 `(40, 83, 120)`
- M PLUS 1p Medium/Bold/Regularの動的ロード
- 本文20文字×最大3行、固定文字グリッド、69px行間、2px文字間、1.05倍横伸長、2分の1縮小再拡大、6px影
- 女性話者色 `(255, 200, 255)`、1・2文字名の均等配置
- `{本文|よみ}` ルビ、`{boten:本文}` 傍点
- 日付・時間帯表示と選択肢の最大3列レイアウト

## 意図的に簡略化した点

- プレビューは編集確認用の静止状態であり、文字送り、フェード、移動、瞬きの時間アニメーションは選択Step時点の最終状態を表示する。
- BGM/SEは再生せず、状態だけ解釈する。
- `if`、フラグ、イベント解放は描画状態へ影響させない。
- Python版のセーブ、バックログ、通知、日付、ゲーム進行管理はエディタプレビューの責務外とする。

## 配置

- `tools/dev/ks-editor/preview_engine.js`: パーサー、状態リプレイ、アセット解決、Canvas描画
- `tools/dev/ks-editor/index.html`: プレビューUI、Step連動、立ち絵パーツ選択
- `.github/workflows/deploy-ks-editor.yml`: `tools/dev/` を同期する既存処理により自動配置
