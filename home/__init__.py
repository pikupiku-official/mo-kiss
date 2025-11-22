"""
homeサブシステム - プレイヤーの家画面管理

家では以下の機能を提供：
- 寝る：次の日の朝に時間を進めてmapモジュールへ
- セーブ・ロード：ゲームデータの保存・読み込み
- メインメニューへ：main_menuモジュールへ
"""

from home.home import HomeModule

__all__ = ['HomeModule']
