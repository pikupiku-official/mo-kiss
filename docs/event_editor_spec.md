# event_editor.py 仕様書

> 生成日: 2026-06-29  
> 対象ファイル: `event_editor.py`（2543行）  
> 目的: スマホ向けWEB UI版（ks-editor）への移植ガイドとして作成

---

## 目次

1. [全体アーキテクチャ](#1-全体アーキテクチャ)
2. [主要クラス一覧](#2-主要クラス一覧)
3. [機能詳細](#3-機能詳細)
4. [dialogue subsystem との接点](#4-dialogue-subsystem-との接点)
5. [KSフォーマット仕様](#5-ksフォーマット仕様)
6. [WEB版移植ギャップ分析](#6-web版移植ギャップ分析)
7. [推奨アーキテクチャ（Pythonサーバー案）](#7-推奨アーキテクチャpythonサーバー案)

---

## 1. 全体アーキテクチャ

```
EventEditorGUI (QMainWindow)
├── KSTextEditor              # テキスト編集ウィジェット（カスタムショートカット付き）
├── file_listbox              # KSファイル一覧（左パネル）
├── metadata fields           # events.csv連動メタデータフォーム
├── PreviewWindow (別スレッド) # Pygameプレビューウィンドウ
│   └── dialogue subsystem   # IR実行エンジン（下記参照）
├── StepEditorDialog          # Step右クリック編集ダイアログ
│   └── CharaCompositePreviewDialog  # 立ち絵合成プレビュー（別ウィンドウ）
└── CharaPreviewCanvas        # 立ち絵ズーム・パンキャンバス
```

### データフロー

```
KSファイル (.ks)
  ↓ load_file()
  → _load_step_memos()      # ;@memo: 行を抽出してstep_memosに格納
  → text_editor表示          # メモなし表示テキスト
  ↓ build_paragraph_line_map()
  → DialogueLoader.load_dialogue_from_ks()  # 段落↔行番号マッピング
  ↓ update_step_highlights()
  → _parse_steps_from_ks_text()  # step解析
  → ExtraSelections で背景色ハイライト
```

---

## 2. 主要クラス一覧

| クラス | 役割 | 移植先 |
|---|---|---|
| `PreviewWindow` | Pygameゲームプレビュー（別スレッド） | Python APIサーバー（PNG返却） |
| `CharaPreviewCanvas` | 立ち絵ズーム・パンキャンバス | Canvas2D（フロントエンド） |
| `CharaCompositePreviewDialog` | 立ち絵パーツ合成・選択UI | Python APIサーバー（Pillow合成）+ フロントエンドUI |
| `StepEditorDialog` | Step編集ダイアログ（アクション・セリフ） | 既存 step-panel を拡張 |
| `KSTextEditor` | カスタムショートカット付きテキストエディタ | contenteditable + KeyboardEvent |
| `EventEditorGUI` | メインウィンドウ | ks-editor index.html 全体 |

---

## 3. 機能詳細

### 3-1. ファイル管理

| 機能 | PC版実装 | WEB版現状 | ギャップ |
|---|---|---|---|
| KSファイル一覧 | `os.listdir(events/)` | ✅ GitHub API | ローカルFS → Python API |
| ファイル読み込み | `open(utf-8)` | ✅ raw.githubusercontent | ローカルFS → Python API |
| ファイル保存 | `open(w, utf-8)` + 自動保存1秒 | ✅ GitHub API PUT | ローカルFS → Python API |
| 新規作成 | ダイアログ + events.csv連動 | ✅ 基礎的 | events.csv未連動 |
| ファイル削除 | KSファイル + events.csv行削除 | ✅ | events.csv未連動 |
| 自動保存 | 1秒デバウンス | ❌ | 要実装 |
| 未保存変更検知 | `document().isModified()` | ❌ | 要実装 |

### 3-2. テキスト編集（KSTextEditor）

カスタムショートカット：

| キー | 動作 | 移植 |
|---|---|---|
| `Ctrl+/` | `\t////` 挿入、カーソルを `//` の間に | KeyboardEvent |
| `Ctrl+/`（`」`の後） | 次行に `\t////` 挿入 | 同上 |
| `Enter`（`//` or `」`の後） | 次行に `\t「」` 挿入、カーソルを中に | 同上 |
| `F2` | `//話者名//` テンプレート挿入 | toolbar button |
| `F3` | `「」` 挿入 | toolbar button |
| `Ctrl+S` | 保存 | ✅ 既存 |

### 3-3. Step解析・ハイライト

**stepの定義（KSフォーマット上の1つの会話単位）：**

```
[アクション行群]  ← bg_show, chara_show など
//話者名//        ← speaker行（省略可）
「セリフ」        ← 本文行（必須）
```

解析ロジック（`_parse_steps_from_ks_text`）：
- `「` で始まる行 → stepの本文行（1step確定）
- `//xxx//` → speaker行（直後のstepに紐付け）
- `[tag ...]` / `@tag ...` → actionとして収集
- `;@memo:xxx` → stepメモ（表示テキストからは除去）
- 奇数/偶数stepで背景色を交互に変える

### 3-4. Stepメモ機能

- KSファイル内に `;@memo:メモテキスト` 行として保存
- エディタ表示時は `_load_step_memos()` でメモ行を除去して表示
- 保存時は `_inject_memos_into_text()` でメモ行を再挿入
- メモありのstepは緑色背景ハイライト

### 3-5. イベントメタデータ（events.csv）

- `events/events.csv` にイベント情報を管理（CSVヘッダーは動的）
- 主要フィールド例: `イベントID`, `タイトル`, `日付`, `場所` 等
- KSファイル選択時に自動ロード、専用フォームで編集・保存

### 3-6. Step編集ダイアログ（StepEditorDialog）

右クリックメニューから開く。構成：

```
左カラム:
├── プレビュー（4:3, 400×300） ← "Preview Update"ボタンで要求
└── セリフ編集（speaker / body / scroll-stop / memo）

右カラム:
├── アクション一覧（リスト、追加/削除/上下移動）
└── アクション編集
    ├── タグ選択コンボ（18種類）
    ├── カスタムエディタ（タグ別専用フォーム）
    │   ├── bg / bg_show / bg_move: storage, 位置, ズーム
    │   ├── chara_show / chara_shift: 全パーツフィールド + 🎨立ち絵プレビューボタン
    │   ├── chara_move / chara_hide: name, 位置, fade
    │   └── se: se名, volume等
    └── 詳細パラメータ表示（key-valueテーブル、トグル）
```

**対応タグ一覧：**

```python
TAG_NAMES = [
    "bg", "bg_show", "bg_move",
    "chara_show", "chara_shift", "chara_move", "chara_hide",
    "bgm", "bgmstop", "bgmstart",
    "se", "fadeout", "fadein",
    "choice", "flag_set", "if", "endif", "event_control"
]
```

**Browseボタン（アセット選択）：**
- `storage` → `images/BG/` ダイアログ
- キャラパーツ → `images/{CHAR_CODE}/` ダイアログ（name フィールドから推定）

### 3-7. 立ち絵合成プレビュー（CharaCompositePreviewDialog）

`chara_show` / `chara_shift` 編集時に起動。

**レイヤー構成（描画順、下から上）：**

```
torso → brow → cheek → eye → mouth → effect → accessory
```

**トルソー番号連動フィルタ：**
- `_T{num}_` パターンでトルソーを判別（例: `MMK_T01_...` → num=01）
- 顔パーツ（brow/eye/mouth/cheek）は `_F{num}_` でフィルタ
- effect は `_E{num}_`、accessory は `_A{num}_`
- フィルタ不一致パーツは ⚠️ 黄色ハイライト

**chara_shift の差分モード：**
- 「変更パーツのみ適用」チェックボックス
- 前回の chara_show/chara_shift と比較して変更があったパーツのみ返す

**キャンバス操作：**
- マウスホイール：ズーム（0.02〜10.0）
- ドラッグ：パン（位置移動）

### 3-8. Pygameプレビュー（PreviewWindow）

別スレッド（または別プロセス/macOS）で動作。

**コマンドキュー（command_queue）：**

```python
{'type': 'load', 'file': path, 'jump_to_paragraph': N}  # KS読み込み
{'type': 'reload', 'keep_position': True}                 # リロード
{'type': 'jump', 'paragraph': N}                          # 段落ジャンプ
{'type': 'stop'}                                          # 停止
```

**ステータスキュー（status_queue）：**

```python
("initialized", True)
("loaded", True)
("paragraph_update", N)  # 現在段落がchangeした
("error", str)
("quit", True)
("stopped", True)
```

**描画パイプライン（30fps）：**

```
draw_background(game_state)
  ↓
draw_characters(game_state)
  ↓
draw_fade_overlay(game_state)
  ↓
image_manager.draw_ui_elements(...)   # UIフレーム（テキストウィンドウ背景等）
  ↓
text_renderer.render_text_window(...) # テキスト・名前表示
  ↓
choice_renderer.render()              # 選択肢（表示中のみ）
  ↓
backlog_manager.render()              # バックログ
  ↓
notification_manager.render()         # 通知
  ↓
smoothscale → window.blit            # スケーリング表示
```

**仮想解像度:** `VIRTUAL_WIDTH × VIRTUAL_HEIGHT`（`core/config.py` 定義）

---

## 4. dialogue subsystem との接点

### 使用モジュール

| モジュール | 役割 | プレビューへの必要性 |
|---|---|---|
| `dialogue/dialogue_loader.py` | KS → raw_dialogue_data | ✅ 必須 |
| `dialogue/data_normalizer.py` | raw → normalized | ✅ 必須 |
| `dialogue/ir_builder.py` | normalized → IR | ✅ 必須 |
| `dialogue/controller2.py` | IR実行（handle_events, update_game） | ✅ 必須 |
| `dialogue/text_renderer.py` | テキスト描画 | ✅ 必須 |
| `dialogue/character_manager.py` | 立ち絵描画 | ✅ 必須 |
| `dialogue/background_manager.py` | 背景描画 | ✅ 必須 |
| `dialogue/choice_renderer.py` | 選択肢描画 | ✅ 必須 |
| `dialogue/fade_manager.py` | フェード描画 | ✅ 必須 |
| `dialogue/backlog_manager.py` | バックログ | 🔶 オプション |
| `dialogue/notification_manager.py` | 通知 | 🔶 オプション |
| `dialogue/model.py` | `advance_dialogue()` | ✅ 段落ジャンプ時 |
| `core/image_manager.py` | 画像スキャン・UI描画 | ✅ 必須 |
| `core/bgm_manager.py` | BGM再生 | 🔶 スキップ可（無音） |
| `core/se_manager.py` | SE再生 | 🔶 スキップ可（無音） |

### IRデータ構造（概要）

```python
ir_data = build_ir_from_normalized(dialogue_data)
# → リスト of IRステップ
# game_state['ir_step_index'] でステップを管理
# update_game() がステップを進める
```

### game_state の主要キー

```python
{
    'screen': pygame.Surface,
    'ir_data': [...],
    'ir_step_index': int,
    'character_pos': {name: (x, y)},
    'character_expressions': {name: {part: stem}},
    'background_state': {'current_bg': Surface, 'pos': [...], 'zoom': float},
    'fade_state': {...},
    'dialogue_data': [...],
    'current_paragraph': int,
    ...
}
```

---

## 5. KSフォーマット仕様

### 基本構造

```ks
; コメント行
// コメント行（// で始まる）
*label名           ← ラベル（段落区切り）

//話者名//          ← speaker宣言（次の「」行に適用）
「セリフ本文」      ← 会話テキスト

[tag_name param1="value1" param2="value2"]  ← アクションタグ（[]形式）
@tag_name param1="value1"                   ← アクションタグ（@形式）

;@memo:ここにメモ   ← editorメモ（保存時埋め込み、表示時除去）
```

### 主要タグ・パラメータ

#### 背景系

```ks
[bg storage="BG_ROOM01"]
[bg_show storage="BG_ROOM01" bg_x="0.5" bg_y="0.5" bg_zoom="1.0"]
[bg_move storage="BG_ROOM01" bg_left="0.0" bg_top="0.0" bg_zoom="1.0" time="600"]
```

#### キャラクター系

```ks
[chara_show name="キャラ名" torso="MMK_T01_A" eye="MMK_F01_EYE01" mouth="MMK_F01_MOU01"
            brow="MMK_F01_BRO01" cheek="" effect="" accessory=""
            blink="true" x="0.5" y="0.5" size="1.0" fade="0.3"]

[chara_shift name="キャラ名" torso="" eye="MMK_F01_EYE02" fade="0.3"]
  # 変更パーツのみ指定可

[chara_move name="キャラ名" left="0.3" top="0.0" zoom="1.0" time="600"]
[chara_hide name="キャラ名" fade="0.3"]
```

#### 音声系

```ks
[bgm bgm="BGM_TITLE" volume="0.5" loop="true"]
[bgmstop time="1.0"]
[se se="SE_CLICK" volume="0.5" frequency="1" block="false"]
[fadeout color="black" time="1.0"]
[fadein time="1.0"]
```

#### 制御系

```ks
[choice option1="はい" option2="いいえ"]
[flag_set name="FLAG_001" value="true"]
[if condition="FLAG_001"]
[endif]
[event_control unlock="E002" lock="E001"]
```

---

## 6. WEB版移植ギャップ分析

### 移植済み（ks-editor 現状）

- ✅ ログイン（パスワード認証）
- ✅ ファイルブラウザ（GitHub API経由、ディレクトリ対応）
- ✅ KS表示・構文ハイライト
- ✅ テキスト編集（textarea）
- ✅ 保存（GitHub API PUT）
- ✅ 新規作成・削除
- ✅ 検索（Ctrl+F相当）
- ✅ アウトライン（*ラベル一覧）
- ✅ Step編集パネル（基礎的：speaker/body/scroll-stop/actions）

### 未実装

| 機能 | 工数感 | 移植方針 |
|---|---|---|
| Stepメモ（;@memo）保存・表示 | 小 | JS側で解析・保存 |
| Step色分けハイライト（交互） | 小 | JS正規表現 |
| events.csv メタデータ管理 | 中 | Python API `/api/metadata` |
| 自動保存（1秒デバウンス） | 小 | JS setTimeout |
| 未保存変更検知 | 小 | JS isDirty flag |
| カスタムショートカット（Ctrl+/, Enter補完） | 小 | KeyboardEvent |
| **Pygameプレビュー** | **大** | **Python API `/api/preview`（PNG）** |
| **立ち絵合成プレビュー** | **大** | **Python API `/api/chara` + Canvas表示** |
| 立ち絵パーツ選択UI（コンボ・フィルタ） | 中 | JS + Python API |
| chara_shift 差分モード | 小 | JS |
| 段落ジャンプ（プレビュー連動） | 中 | Python API 拡張 |
| Browse（アセット選択）ダイアログ | 中 | Python API `/api/assets` + モーダル |
| アクション追加/削除/並び替え（Step内） | 小 | ✅ 既存 step-panel を拡張 |

---

## 7. 推奨アーキテクチャ（Pythonサーバー案）

### なぜPythonサーバーか

- `dialogue/` 以下14モジュールをJSに再実装する必要がない
- Pygame/Pillow でレンダリングしてPNG返却 → ブラウザにそのまま表示
- `companion_server.py`（標準ライブラリのみ）が既存：ベースとして拡張可能
- ローカルFS直接読み書き → GitHub API不要（LAN/tunnel経由で十分）

### 推奨エンドポイント設計

```
GET  /                         → index.html (ks-editor)
GET  /api/files?dir=events     → ファイル一覧 JSON
GET  /api/file?path=events/E001.ks → ファイル内容 JSON
PUT  /api/file?path=...        → ファイル保存
DELETE /api/file?path=...      → ファイル削除

GET  /api/metadata?id=E001     → events.csv 行 JSON
PUT  /api/metadata             → events.csv 行保存

GET  /api/assets?type=bg       → 背景画像一覧 JSON
GET  /api/assets?type=chara&char=MMK → キャラパーツ一覧 JSON

POST /api/preview              → KS内容受取 → IR実行 → PNG base64
     body: {ks_content, paragraph}
     返却: {image_b64, current_paragraph, total_paragraphs}

POST /api/chara                → パーツ合成 → PNG base64
     body: {char_name, torso, eye, mouth, brow, cheek, effect, accessory}
     返却: {image_b64}
```

### 技術スタック

```
サーバー: Python 3.x
  ├── HTTP: http.server（標準ライブラリ、Flask追加も可）
  ├── 画像: Pillow（立ち絵合成）
  ├── ゲームエンジン: Pygame + dialogue subsystem（プレビュー）
  └── ファイルI/O: pathlib（標準）

フロントエンド: 既存 ks-editor index.html
  ├── API切替: GitHub API → localhost Python API
  └── プレビュー: <img src="data:image/png;base64,..."> で表示

外部公開: cloudflared tunnel（既存 companion_server の手順と同じ）
```

### 実装フェーズ

```
Phase 2: companion_server.py を拡張
  ├── /api/files, /api/file, /api/metadata を追加（ローカルFS）
  └── ks-editor の apiCall を localhost向けに切替可能に

Phase 3: プレビューAPI
  ├── Pygameをheadlessモードで起動（pygame.display不使用）
  ├── virtual_screen（Surface）に描画
  └── pygame.image.tostring → Pillow → PNG base64

Phase 4: 立ち絵合成API
  ├── Pillow で layers を alpha_composite
  └── PNG base64返却

Phase 5: フロントエンド統合
  ├── プレビューパネル追加（<img> + 段落ナビ）
  └── 立ち絵パーツ選択モーダル追加
```

---

## 補足：ファイルパス構成

```
c:\Users\kohet\モーキス作業ディレクトリ\
├── event_editor.py          # PC版エディタ（本仕様書の対象）
├── events/
│   ├── events.csv           # イベントメタデータ
│   └── E001.ks, E002.ks ... # KSファイル
├── images/
│   ├── BG/                  # 背景画像
│   └── {CHAR_CODE}/         # キャラクター画像（例: 01MMK/）
├── dialogue/                # dialogue subsystem（14モジュール）
├── core/
│   ├── config.py            # VIRTUAL_WIDTH/HEIGHT, CHAR_CODE等
│   └── image_manager.py     # 画像スキャン・描画
└── tools/
    ├── companion_server.py  # 既存Pythonサーバー（拡張ベース）
    └── dev/ks-editor/
        ├── index.html       # WEB版エディタ（1066行）
        └── api.php          # GitHub APIプロキシ（要置き換え）
```
