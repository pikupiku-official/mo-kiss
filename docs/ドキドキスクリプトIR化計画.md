# IR仕様書 Ver0.3（ドラフト）

この仕様書は、現行のシナリオ処理（`dialogue_loader.py` + `scenario_manager.py`）から
**中間表現（IR）を導入して実装可能な形**で整理したものです。
テキスト進行・アニメ進行・Enter/Skip/Autoの挙動が矛盾しないことを目的にします。

---

## 1. 用語と前提

### 1.1 シナリオ進行度（step）
- 1つのシナリオ進行度（step）に **テキスト/演出** が紐づく。
- どちらか片方のみの場合もある。
- 現行では `dialogue_data` の「段落」単位（`current_paragraph`）が step に相当する。

### 1.2 idle状態
- **テキスト表示が完了していること**
- **block/complete/interrupt 対象のアニメが完了していること**
→ これらが揃った状態が idle。

### 1.3 進行イベント
IR上では **Enter / Skip / Auto を分けない**。
「進行が発生した」という事実のみを扱う。

---

## 2. IRの基本構造

IRは、step単位の配列として扱う。

```json
{
  "steps": [
    {
      "id": "step_0001",
      "text": {
        "speaker": "momoko",
        "body": "セリフ本文",
        "scroll": false
      },
      "actions": [
        { "action": "chara_pose", "target": "momoko", ... }
      ]
    }
  ]
}
```

### 2.1 stepの構成要素
- `text`（任意）: 表示するテキスト（`speaker` は **object_id** を指定）
- `actions`（任意）: アニメ/演出コマンドの配列、複数存在することもある。
  - 同一step内で複数アニメを並列に開始することは可能。
  - ただし **同一オブジェクトは1アニメまで** の制約があるため、
    並列は「別オブジェクト同士」で成立する。
  - `bg` / `audio` / `fx` など **objectに紐づかないアクション** も `actions` に含める（targetなし）。
    - これは 1オブジェクト1アニメ のスコープ外。
  - テキストの話者とアクション対象は一致しなくてよい（例: Aの台詞中にBが表情変化）。

---

## 3. アクション仕様

### 3.1 最小アニメ仕様
```json
{
  "action": "chara_move|chara_pose|bg_move|fade|...",
  "target": "object_id",
  "animation": {
    "type": "once|cycle",
    "on_advance": "block|complete|interrupt|continue"
  }
}
```

※ `target` はobjectに紐づくアクションで必須。bgm/se/fx等のグローバルアクションは省略可。


#### on_advance の定義
- `block`: 進行（advance）を止める
- `continue`: 進行を許可しつつアニメ継続
- `complete`: 飛ばし処理（超高速補間）
- `interrupt`: 飛ばし処理（クロスフェードで瞬間移動）

#### on_advance 運用方針
- 視覚変化（`chara_move` / `bg_move` / `fade` / `chara_shift` など）は **block/complete を基本**とする。
- `continue` は「明示的に跨がせたい」ケースでのみ使用する。

#### zoom の扱い
- `zoom` は **現在の表示サイズに対する相対倍率**。元画像基準の絶対倍率ではない。

#### chara_show / chara_shift / chara_move のパラメータ
- `chara_show` は `size` で表示サイズを指定する。
- `chara_shift` は `size` を持たない（表示サイズは維持）。
- `chara_move` は `zoom` を持つ（相対倍率として拡大縮小を行う）。

### 3.2 飛ばし処理
- **complete = 超高速補間**
- **interrupt = クロスフェードで瞬間移動**
両者を総称して **飛ばし処理** と呼ぶ。

---

## 4. Enter/Skip/Autoの挙動

### 4.1 Enter/Skip
- **idle でない場合**:
  - テキストは即時表示完了
  - アニメは300msの飛ばし処理で idle に移行
- **idle の場合**: advance

### 4.2 Auto
- auto は **idleになるまで待機**し、進行条件が整ったら advance を発生させる。
- **飛ばし処理は発生しない**（テキスト/アニメへの強制介入なし）。

---

## 5. 1オブジェクト1アニメ原則

- 同一オブジェクトには同時に1アニメのみ
- block, complete, interrupt の場合は自明
- continue の場合も、次のstepに新しいアニメが来たら `complete` または `interrupt` の飛ばし処理で終了する
- `bg` / `audio` / `fx` など target なしのアクションはこの制約の対象外

---

## 6. continueの解釈（シナリオ進行度をまたぐアニメ）

- `continue` は **次のstepにまたがって継続**できる（明示指定時のみ使用）
- `continue` は 継続ステップ数（Nステップ）を指定し、指定済みの終了ステップがadvanceしたタイミングで終了する。
- 終了時の状態は **開始時と同じ状態** がデフォルト。例外的に終了状態を変更できる（保持/終了ステップのステートに移行など）。
- 同一オブジェクトに新アニメが来たら上書きされる
  - 既存アニメは `complete` / `interrupt` により終了

#### 参考案（中立的検討）
- `continue` は **開始時点では idle 扱い**にする。
- 次のstepで同一オブジェクトにアニメがある場合のみ、
  - idle状態を解除する
  - continueのアニメは `complete` / `interrupt` で終了
- 利点: idle判定が単純化する可能性がある。
- 懸念: continueを「明示的に跨る」と解釈していた場合に仕様差が生まれる。

---

## 7. sequenceアニメ

sequenceは **step内で順序保証したいアクション群** をまとめるための仕組み。
- 同一オブジェクトの `hide` → `show` 連続は `chara_shift` に畳み込み、**sequenceで包む**。
- 別オブジェクト同士でも順序保証が必要なら sequence に入れる（例: Aが笑う → Bが笑う）。
- ドキドキスクリプト側に **sequenceを囲うタグ**（仮称 `[seq_begin] ... [seq_end]`）を導入する。

1つのアニメで複数動作をまとめる。

```json
{
  "action": "chara_sequence",
  "target": "momoko",
  "animation": {
    "type": "once",
    "on_advance": "block"
  },
  "sequence": [
    {"action": "move", "to": [0.2, 0.5], "duration_ms": 300},
    {"action": "move", "to": [0.8, 0.5], "duration_ms": 300},
    {"action": "move", "to": [0.2, 0.5], "duration_ms": 300}
  ]
}
```

### 飛ばし処理（sequence）
- **complete**: 最終状態まで300msで超高速補間
- **interrupt**: 最終状態へ300msクロスフェード
- 個々の action を飛ばす必要はない

---

## 8. キャラクターオブジェクト構造

### 8.0 object_id と素材IDの関係
- **object_id は演出対象の識別子**であり、素材ファイル名（Torso/Face）とは別物。
- `speaker` / `target` に指定するのは object_id を使用する。
- 素材の切り替えは object_id に紐づく「Torso/Face パーツ指定」で行う。

### 8.1 オブジェクト構造
```
CharacterObject
- torso (T0x_0x_0x)
- eye (F0x_Ez0x_0x)
- mouth (F0x_Mz0x_0x)
- brow (F0x_Bz0x_0x)
- cheek (F0x_Cz0x_0x)
```

### 8.2 表示画像切替
- chara_show, chara_hideの際の画像表示/消去は
- 今までchara_show,chara_hideを併用して実現していた画像切替をchara_shiftを新設し、変更前と変更後の各画像を **デフォルトでクロスフェード**
- 同一オブジェクトの `hide` → `show` 連続は `chara_shift` へ集約し、**sequenceで順序を固定**する。
- 表情変化等をしても、同一object_idのもとで一つのオブジェクトとして一貫して管理できるメリットがある。
- 表情変化の場合、対象オブジェクトとその変化するパーツだけをchara_shiftで指定し、クロスフェード。
- デフォルト時間は **300ms**
- show/shift/hide ?? `fade` ??? `time` ???????????
  - ?: `[chara_show name="??" ... fade="0.5"]`
  - ?: `[chara_shift name="??" eye="F03_Ex00_00" fade="0.3"]`
  - ?: `[chara_hide name="??" fade="0.2"]`
- 例:
```json
"transition": {
  "type": "crossfade|none",
  "duration_ms": 100
}
```

---

## 9. E066.ks のIR化例（アニメーションstep）

`events/E066.ks` の `chara_move` を含むstepをIR化した例。

元のKS:
```
	//桃子//
	「え！」

[chara_move subm="T03_00_01" time="500" left="-0.4" top="0" zoom="2.0"]
```

IR（例）:
```json
{
  "id": "step_0001",
  "text": {
    "speaker": "momoko",
    "body": "え！",
    "scroll": false
  },
  "actions": [
    {
      "action": "chara_move",
      "target": "momoko",
      "params": {
        "time": 500,
        "to": [-0.4, 0.0],
        "zoom": 2.0 // zoomは現在の表示サイズに対する相対倍率。1.0で維持、指定時のみ拡大縮小アニメとして扱う。
      },
      "animation": {
        "type": "once",
        "on_advance": "complete"
      }
    }
  ]
}
```

補足:
- `target` / `speaker` は **object_id**（例: momoko）を使用。ここの二つは別のオブジェクトでもいい。
- `subm="T03_00_01"` は **Torso素材ID**であり、object_idとは分離する。

---

## 10. 既存実装との対応関係

### 10.1 現行の進行処理
- `controller2.handle_enter_key` は
  - テキスト表示中 → `skip_text()`
  - 表示完了 → `advance_dialogue()` を呼ぶ
- `text_renderer` は auto/skip モードを管理し、条件が整うと `advance` に進む

この仕様は、**Enter時にテキストとアニメの双方を idle に揃える**ことで、
現在の進行ロジックと整合するよう設計されている。

---

## 11. 実装の導入ステップ案

1. `dialogue_loader.py` → IR形式に変換（dict統一）
2. `scenario_manager.py` → IRからアクションを生成
3. `controller2.py` → idle判定に「アニメ完了状態」を追加
4. `text_renderer.py` → auto/skip による advance を維持

---

## 12. IR生成の扱い（JSONファイルの扱い）
- **IRは基本的にランタイムで生成し、メモリ上で保持する。**
- JSONへの書き出しは **デバッグ/検証用途のオプション**として扱う。
  - 例: イベント開始時にIRを生成し、必要なら `debug/ir/E066.json` へ保存。
  - イベント終了/ゲーム終了時は **保持データを破棄**する。

---

## 13. 未確定項目（今後詰める）
- action種別一覧（bg / chara / audio / fx / ...）
- パーツ命名規則の部位リスト（B/E/M/C/O）
  - Oは Others（汗などのエフェクト）用の枠
- 具体的なクロスフェードの実装位置（実装者判断）
