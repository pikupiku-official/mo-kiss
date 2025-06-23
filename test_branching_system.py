#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dialogue_loader import DialogueLoader

def test_branching_system():
    """分岐システムのテスト"""
    print("🧪 分岐システムテスト開始")
    
    # DialogueLoaderを初期化
    loader = DialogueLoader(debug=True)
    
    # E001_test.ksファイルを読み込み
    ks_file_path = os.path.join("events", "E001_test.ks")
    dialogue_data = loader.load_dialogue_from_ks(ks_file_path)
    
    print(f"\n📝 読み込み結果: {len(dialogue_data)}個のエントリー")
    
    # 選択肢イベントをシミュレート
    print("\n🎯 選択肢1をシミュレート（積極的アプローチ）")
    loader.set_story_flag('choice', 1)
    
    # 条件分岐をテスト
    test_conditions = [
        'choice==1',
        'choice==2', 
        'choice==3'
    ]
    
    for condition in test_conditions:
        result = loader.check_condition(condition)
        print(f"条件 '{condition}': {result}")
    
    # イベント制御をテスト
    print("\n🎮 イベント制御テスト")
    control_command = {
        'type': 'event_control',
        'unlock': ['E010', 'E011'],
        'lock': ['E012', 'E013']
    }
    
    loader.execute_story_command(control_command)
    
    print("\n✅ テスト完了！")
    return True

if __name__ == "__main__":
    test_branching_system()