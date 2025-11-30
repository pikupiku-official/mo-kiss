"""
パス管理ユーティリティ

全モジュールで統一されたパス取得を提供します。
クロスプラットフォーム対応（Windows、macOS、Linux）
"""

import os
import sys


def get_project_root():
    """
    プロジェクトルートディレクトリを取得

    Returns:
        str: プロジェクトルート（mo-kissディレクトリ）の絶対パス
    """
    # このファイル（path_utils.py）はmo-kissディレクトリ直下にある
    return os.path.dirname(os.path.abspath(__file__))


def get_font_path(font_filename):
    """
    フォントファイルの絶対パスを取得

    Args:
        font_filename (str): フォントファイル名（例: "MPLUS1p-Regular.ttf"）

    Returns:
        str: フォントファイルの絶対パス
    """
    project_root = get_project_root()
    font_path = os.path.join(project_root, "fonts", font_filename)
    return os.path.abspath(font_path)


def get_resource_path(resource_type, filename):
    """
    リソースファイルの絶対パスを取得

    Args:
        resource_type (str): リソースタイプ（"images", "sounds", "events"など）
        filename (str): ファイル名

    Returns:
        str: リソースファイルの絶対パス
    """
    project_root = get_project_root()
    resource_path = os.path.join(project_root, resource_type, filename)
    return os.path.abspath(resource_path)


def ensure_directory_exists(directory_path):
    """
    ディレクトリが存在しない場合は作成

    Args:
        directory_path (str): ディレクトリパス
    """
    os.makedirs(directory_path, exist_ok=True)


# クロスプラットフォーム対応のための定数
IS_WINDOWS = sys.platform.startswith('win')
IS_MACOS = sys.platform == 'darwin'
IS_LINUX = sys.platform.startswith('linux')


if __name__ == "__main__":
    # テスト実行
    print(f"プロジェクトルート: {get_project_root()}")
    print(f"フォントパス例: {get_font_path('MPLUS1p-Regular.ttf')}")
    print(f"画像パス例: {get_resource_path('images', 'title.png')}")
    print(f"OS: Windows={IS_WINDOWS}, macOS={IS_MACOS}, Linux={IS_LINUX}")
