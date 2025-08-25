#!/usr/bin/env python3
"""セーブシステムのテストスクリプト"""

from save_manager import get_save_manager
from time_manager import get_time_manager
import json

def test_save_system():
    print("🧪 セーブシステムのテスト開始")
    
    save_manager = get_save_manager()
    time_manager = get_time_manager()
    
    # 現在の状態を表示
    print("\n📊 現在の状態:")
    time_state = time_manager.get_time_state()
    print(f"  時間: {time_state['full_string']}")
    
    # セーブスロット情報を表示
    print("\n💾 セーブスロット情報:")
    slots = save_manager.get_save_slots()
    for slot in slots[:5]:  # 最初の5スロットのみ表示
        status = "使用済み" if slot["exists"] else "空き"
        description = slot["description"] or "なし"
        print(f"  スロット{slot['slot_number']}: {status} - {description}")
    
    # テスト用に時間を進める
    print("\n⏰ 時間を進めてテスト...")
    time_manager.advance_period()
    time_state = time_manager.get_time_state()
    print(f"  変更後の時間: {time_state['full_string']}")
    
    # スロット1にセーブ
    print("\n💾 スロット1にセーブ...")
    if save_manager.save_game(1):
        print("  ✅ セーブ成功")
    else:
        print("  ❌ セーブ失敗")
    
    # さらに時間を進める
    time_manager.advance_period()
    time_state = time_manager.get_time_state()
    print(f"\n⏰ さらに時間を進める: {time_state['full_string']}")
    
    # スロット1からロード
    print("\n📂 スロット1からロード...")
    if save_manager.load_game(1):
        print("  ✅ ロード成功")
        time_state = time_manager.get_time_state()
        print(f"  ロード後の時間: {time_state['full_string']}")
    else:
        print("  ❌ ロード失敗")
    
    # 初期状態にリセット
    print("\n🔄 初期状態にリセット...")
    if save_manager.reset_current_state():
        print("  ✅ リセット成功")
        time_state = time_manager.get_time_state()
        print(f"  リセット後の時間: {time_state['full_string']}")
    else:
        print("  ❌ リセット失敗")
    
    print("\n🎉 テスト完了")

if __name__ == "__main__":
    test_save_system()