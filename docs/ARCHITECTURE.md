# mo-kiss アーキテクチャ

設計・システム・データ・用語をまとめた1枚リファレンス。

---

## 用語

| 用語 | 定義 |
|------|------|
| **Base State** | TITLE / MAIN_MENU / HOME / DIALOGUE / MAP の主画面 |
| **Overlay** | Base State の上に開く画面。本作では OPTION |
| **Event** | DIALOGUE を起動するストーリー単位（例: `events/E001.ks`）|
| **シナリオフラグ** | イベント完了・分岐選択を表す状態。開始/ロード時に初期化 |
| **セーブスロット** | セーブ単位。スロットごとに別世界線として扱う |
| **プレイヤー名** | 「はじめから」で決定し、スロット内で固定 |

---

## 実行モデル

```
main.py
└─ Base State: TITLE → MAIN_MENU → HOME / DIALOGUE / MAP
                                  └─ Overlay: OPTION
```

### 遷移

| 遷移 | 種別 |
|------|------|
| TITLE → MAIN_MENU | 固定 |
| MAIN_MENU → DIALOGUE（E001.ks） | 新規開始 |
| MAIN_MENU → 保存時の状態 | 続きから |
| HOME → DIALOGUE / MAP | 状況依存 |
| DIALOGUE ↔ MAP | 昼ループ |
| DIALOGUE → HOME | 帰宅 |

---

## 各 Base State

### TITLE
- 起動画面・初期化の入口
- デモ動画再生（スキップ可）→ PRESS ANY KEY → MAIN_MENU

### MAIN_MENU
- はじめから（名前入力 → E001.ks）/ つづきから（ロード）
- セーブ・OPTION なし

### HOME
- 自宅シーン・日の切り替え起点
- セーブ可・OPTION 可
- 出口: DIALOGUE（登校）or MAP

### DIALOGUE
- 物語進行・分岐
- セーブ **不可**・OPTION 可
- シナリオフラグはここで主に更新
- 出口: MAP（昼ループ）/ HOME（帰宅）

### MAP
- イベント選択・移動
- セーブ可・OPTION 可
- 時間スキップ用 UI/キー操作あり
- 出口: DIALOGUE / HOME

### OPTION（Overlay）
- ポーズ・BGM継続・設定即時反映
- HOME / DIALOGUE / MAP から開ける（TITLE / MAIN_MENU は不可）
- 想定項目: 音量 / キーコンフィグ / 表示 / テキスト速度 / スキップ / セーブ・ロード / メインメニューへ戻る

---

## データ設計

### データ区分

| 種別 | 場所 | 備考 |
|------|------|------|
| セーブ状態 | `data/save/saveslot_XX/` | Base State / 進行度 / 時間 |
| シナリオフラグ | `data/current_state/story_flags.json` | スロットに保持 |
| 時間/日付 | `data/current_state/time_state.json` | イベント終了で進む |
| プレイヤー名 | `data/current_state/player_name.json` | スロット固定 |
| 設定（共通） | `data/settings.json` | スロット横断 |

### フラグ運用
1. `events/story_flags.json` を初期値として読み込む
2. 開始/ロード時に `current_state/` へ展開
3. MAIN_MENU に戻ると初期化
4. セーブ時はスロットへ保存・ロード時はスロットから展開

### アセット構成

```
images/
├── backgrounds/
├── icons/
├── maps/
└── 桃子/（キャラパーツ）
sounds/
├── bgms/
└── ses/
fonts/       # M+ 系
```

---

## バックエンド責務（案）

| モジュール | 責務 |
|-----------|------|
| `save_manager.py` | セーブ/ロード |
| `time_manager.py` | 時間管理 |
| `story_flags.json` | フラグ管理 |

---

## 未決事項

- OPTION の追加項目の精査
- アセット命名規約（イベントID / キャラパーツ / UI画像）
- `map copy.py` の整理
- `events/` 内スクショの扱い
