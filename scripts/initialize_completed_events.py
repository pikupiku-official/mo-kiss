#!/usr/bin/env python3
"""
completed_events.csvを初期化するスクリプト
data/templatesからdata/current_stateに単純コピー
"""

import shutil
import os
import sys

def initialize_completed_events():
    # プロジェクトルートを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    template_path = os.path.join(project_root, 'data', 'templates', 'completed_events_template.csv')
    target_path = os.path.join(project_root, 'data', 'current_state', 'completed_events.csv')
    
    print(f"テンプレート: {template_path}")
    print(f"対象ファイル: {target_path}")
    
    try:
        if not os.path.exists(template_path):
            print(f"❌ テンプレートファイルが見つかりません: {template_path}")
            return False
            
        # 単純なファイルコピー
        shutil.copy2(template_path, target_path)
        print("✅ completed_events.csv初期化完了（テンプレートからコピー）")
        return True
        
    except Exception as e:
        print(f"❌ completed_events.csv初期化エラー: {e}")
        return False

if __name__ == "__main__":
    success = initialize_completed_events()
    sys.exit(0 if success else 1)