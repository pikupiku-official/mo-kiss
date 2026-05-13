# To‑Be 構造

本書は **理想状態の構造（概念レイヤ）** を示す。  
ファイルの一覧ではなく、責務の配置を定義する。

---

## レイヤ構成

1) **Entry**
- `main.py` が起点

2) **Base State（主画面）**
- TITLE / MAIN_MENU / HOME / DIALOGUE / MAP

3) **Overlay**
- OPTION（ポーズ型オーバーレイ、BGM継続）

4) **Backend State**
- セーブデータ
- シナリオフラグ
- 時間/日付
- プレイヤー名
- 設定

5) **Assets**
- images / sounds / fonts

6) **Tooling**
- Event Editor

7) **Docs**
- 概要（安定情報）
- As‑Is（変動情報）

---

## 原則

- 遷移は **非線形** を許容する  
- OPTION は **Base State ではなく Overlay**
- 状態の責務を明示する  
- 仕様未確定は `TBD` として残す

---

## 物理配置（現状に対応）

- Runtime: ルートPython + `dialogue/` `menu/` `map/` `home/`
- Data: `data/` `events/`
- Assets: `images/` `sounds/` `fonts/`
- Tooling: `event_editor.py` `EVENT_EDITOR_README.md`
