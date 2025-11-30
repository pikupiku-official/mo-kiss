# mo-kiss プロジェクトガイド

このドキュメントは、mo-kissプロジェクトの構造と開発ガイドをまとめたものです。

## プロジェクト概要

mo-kissは、Pygameを使用したビジュアルノベル型ゲームです。1999年を舞台に、プレイヤーが様々なキャラクターと交流しながら物語を進めていきます。

## 技術スタック

- **Python**: 3.12
- **主要ライブラリ**:
  - pygame 2.6.1 - ゲームエンジン
  - PyQt5 - フォント管理・UI補助
  - その他: numpy, pandas（データ処理用）

## プロジェクト構造

```
mo-kiss/
├── main.py                 # エントリーポイント
├── config.py              # 設定ファイル
├── fonts/                 # フォントファイル（M PLUS Rounded 1c）
├── images/                # 画像リソース
├── sounds/                # 音声リソース
├── events/                # イベントデータ
├── dialogue/              # 会話システム
│   ├── controller2.py     # メインコントローラー
│   ├── text_renderer.py   # テキスト描画
│   ├── date_manager.py    # 日付管理
│   ├── notification_manager.py  # 通知システム
│   └── choice_renderer.py # 選択肢描画
├── map/                   # マップシステム
│   └── map.py
├── home/                  # ホーム画面
│   └── home.py
├── menu/                  # メニューシステム
│   └── main_menu.py
└── title_screen.py        # タイトル画面
```

## 環境構築

### 1. 仮想環境の作成（推奨）

```bash
cd mo-kiss
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate  # Windows
```

### 2. 依存パッケージのインストール

```bash
pip install pygame PyQt5
```

### 3. 実行

```bash
python3 main.py
```

## フォントシステム

### ⭐ 推奨：path_utils.pyを使用

**クロスプラットフォーム対応のため、必ず `path_utils.py` を使用してください:**

```python
from path_utils import get_font_path

# フォントパスを取得
font_path = get_font_path("MPLUS1p-Regular.ttf")

# 使用例
try:
    font = pygame.font.Font(font_path, font_size)
except Exception as e:
    print(f"フォント読み込みエラー: {e}")
    # フォールバック処理
    font = pygame.font.SysFont("msgothic", font_size)
```

### 従来のパス構築（非推奨）

```python
# ⚠️ 非推奨：モジュールによって階層が異なるため統一されていない
project_root = os.path.dirname(os.path.dirname(__file__))
font_dir = os.path.join(project_root, "fonts")
font_path = os.path.join(font_dir, "MPLUS1p-Regular.ttf")
```

**注意:**
- `"mo-kiss"` ディレクトリを重複して含めないこと
- 新規コードでは必ず `path_utils.py` を使用すること

### フォント使用箇所

1. **home/home.py** - ホーム画面
2. **dialogue/text_renderer.py** - 会話テキスト、日付表示
3. **dialogue/choice_renderer.py** - 選択肢
4. **dialogue/notification_manager.py** - 通知
5. **map/map.py** - マップUI
6. **menu/main_menu.py** - メインメニュー
7. **title_screen.py** - タイトル画面
8. **events/event_base.py** - イベント表示

## 画面解像度

- **仮想解像度**: 1440x1080 (4:3)
- **実画面**: 可変（ピラーボックス対応）
- **スケール係数**: SCALE = SCREEN_HEIGHT / 1080

## ゲームシステム

### 時間管理システム

`time_manager.py` で管理:
- 朝・昼・夕方・夜の4つの時間帯
- イベントは時間帯によって発生条件が変わる

### イベントシステム

`events/events.csv` で管理:
- 各イベントには発生条件（日付、時間帯、場所）がある
- `event_unlock` で新しいイベントを解放

### セーブシステム

`save_manager.py` で管理:
- 10個のセーブスロット
- JSON形式で保存
- 保存場所: `saves/` ディレクトリ

## デバッグ

### ログ出力

各モジュールで `debug=True` を設定することで詳細ログが出力されます:

```python
text_renderer = TextRenderer(screen, debug=True)
```

### よくある問題

#### 1. フォントが文字化けする（四角く表示される）

**原因**: フォントパスが正しくない

**解決方法**:
- `os.path.dirname()` の回数を確認
- `"mo-kiss"` ディレクトリを重複させていないか確認

#### 2. Python環境の混在

**原因**: Homebrew版とFramework版が混在

**解決方法**:
```bash
# .zshrcにFramework版を優先するパスを追加
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:$PATH"
source ~/.zshrc
```

#### 3. pygameがインストールされているのにインポートエラー

**原因**: 異なるPython環境で実行

**解決方法**:
```bash
# 実行中のPythonとインストール先を確認
which python3
python3 -m pip list | grep pygame
```

## 開発ガイドライン

### コーディング規約

1. **フォントロード**: 必ずプロジェクト専用フォントを優先、フォールバック処理を含める
2. **パス指定**: 絶対パスではなく相対パス（`os.path.join`）を使用
3. **スケール対応**: 全ての座標・サイズは `SCALE` を考慮

### 新規モジュール追加時のチェックリスト

- [ ] **`path_utils.py` を使用してフォントをロードしているか**
- [ ] フォント読み込みに適切なエラーハンドリングとフォールバックがあるか
- [ ] `config.py` から設定を読み込んでいるか
- [ ] スケール係数を適用しているか
- [ ] 4:3コンテンツ領域を考慮しているか
- [ ] Windows / macOS / Linux 全てで動作確認したか

## トラブルシューティング

### macOSでの実行

```bash
cd "/Users/kohetsuwatanabe/Library/CloudStorage/OneDrive-個人用/モーキスリポジトリ/mo-kiss"
python3 main.py
```

### Windowsでの実行

```bash
cd "C:\path\to\mo-kiss"
python main.py
```

### Linuxでの実行

```bash
cd /path/to/mo-kiss
python3 main.py
```

### path_utils.pyの動作確認

```bash
python3 path_utils.py
```

出力例:
```
プロジェクトルート: /path/to/mo-kiss
フォントパス例: /path/to/mo-kiss/fonts/MPLUS1p-Regular.ttf
画像パス例: /path/to/mo-kiss/images/title.png
OS: Windows=False, macOS=True, Linux=False
```

## 参考リソース

- [Pygame公式ドキュメント](https://www.pygame.org/docs/)
- [M PLUS Fonts](https://github.com/coz-m/MPLUS_FONTS)

## 更新履歴

- 2025-12-01: `path_utils.py` 追加（クロスプラットフォーム対応）
- 2025-12-01: フォントパス問題を修正（Mac環境対応）
- 2025-12-01: claude.md作成

## 重要な設計方針

### ⭐ クロスプラットフォーム最優先

このプロジェクトは **Windows / macOS / Linux 全環境での動作を最優先** します。

**必須事項:**
1. パス操作は `os.path.join()` を使用（`/` や `\` の直接使用禁止）
2. フォント・リソースのロードは `path_utils.py` を使用
3. 全ての外部ファイルアクセスにエラーハンドリングを実装
4. プラットフォーム依存の機能は `path_utils.IS_WINDOWS / IS_MACOS / IS_LINUX` で分岐

**テスト要件:**
- 新機能追加時は、可能な限り複数のOSで動作確認すること
- CI/CDでの自動テスト実装を検討すること
