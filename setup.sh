#!/bin/bash

# mo-kiss セットアップスクリプト
# 仮想環境の作成とパッケージインストールを自動化

echo "🎮 mo-kiss セットアップを開始します..."

# 仮想環境が存在するか確認
if [ -d "venv" ]; then
    echo "⚠️  既存の仮想環境が見つかりました。削除して再作成しますか？ (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "🗑️  既存の仮想環境を削除中..."
        rm -rf venv
    else
        echo "✅ 既存の仮想環境を使用します"
    fi
fi

# 仮想環境を作成
if [ ! -d "venv" ]; then
    echo "📦 仮想環境を作成中..."
    python3 -m venv venv
fi

# 仮想環境を有効化
echo "🔧 仮想環境を有効化中..."
source venv/bin/activate

# パッケージをインストール
echo "📥 必要なパッケージをインストール中..."
pip install --upgrade pip
pip install pygame PyQt5 numpy pandas

echo ""
echo "✅ セットアップ完了！"
echo ""
echo "📝 次回以降の実行方法:"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "🎮 今すぐゲームを起動しますか？ (y/N)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    python main.py
fi
