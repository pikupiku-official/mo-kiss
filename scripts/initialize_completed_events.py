#!/usr/bin/env python3
"""
completed_events.csvを初期化するスクリプト
すべてのイベントを実行回数0、有効フラグTRUEで事前登録
"""

import csv
import os
import sys

def initialize_completed_events():
    # プロジェクトルートを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    events_csv_path = os.path.join(project_root, 'events', 'events.csv')
    completed_csv_path = os.path.join(project_root, 'data', 'current_state', 'completed_events.csv')
    
    print(f"Events.csv: {events_csv_path}")
    print(f"Completed events.csv: {completed_csv_path}")
    
    # events.csvから全イベント情報を読み込み
    events_data = []
    try:
        with open(events_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                events_data.append(row)
        print(f"読み込み完了: {len(events_data)}個のイベント")
    except Exception as e:
        print(f"events.csv読み込みエラー: {e}")
        return False
    
    # completed_events.csvを初期化（全イベント実行回数0で登録）
    fieldnames = ['イベントID', '実行日時', '実行回数', '有効フラグ']
    
    try:
        with open(completed_csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for event in events_data:
                # 有効フラグはデフォルトでTRUE（E012, E013のみFALSE）
                active_flag = 'FALSE' if event['イベントID'] in ['E012', 'E013'] else 'TRUE'
                
                writer.writerow({
                    'イベントID': event['イベントID'],
                    '実行日時': '',  # 初期状態では空
                    '実行回数': '0',
                    '有効フラグ': active_flag
                })
        
        print(f"completed_events.csv初期化完了: {len(events_data)}個のイベント")
        return True
        
    except Exception as e:
        print(f"completed_events.csv初期化エラー: {e}")
        return False

if __name__ == "__main__":
    success = initialize_completed_events()
    sys.exit(0 if success else 1)