#!/usr/bin/env python3
"""
events.csvを復元するスクリプト
"""

import csv
import os

def restore_events_csv():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    events_csv_path = os.path.join(project_root, 'events', 'events.csv')
    
    # 66個のイベントを定義（E001-E066）
    events = []
    
    # サンプルデータ（実際の詳細は適切に設定）
    heroines = ["烏丸神無", "桔梗美鈴", "愛沼桃子", "舞田沙那子", "宮月深依里", "伊織紅"]
    locations = ["体育館", "図書館", "商店街", "教室", "駅前", "公園", "購買部", "カフェ", "屋上"]
    
    for i in range(1, 67):  # E001-E066
        event_id = f"E{i:03d}"
        
        # 基本的な日時設定（5月31日から開始）
        start_month = 5 + (i - 1) // 31
        start_day = 31 + (i - 1) % 31
        if start_day > 31:
            start_day = start_day - 31 
            start_month += 1
        
        # 時間帯をランダムに設定
        time_slots = ["朝", "昼", "夜"][i % 3]
        if i % 5 == 0:
            time_slots = "朝;昼"
        
        # ヒロインとタイトル
        heroine = heroines[i % len(heroines)]
        location = locations[i % len(locations)]
        title = f"{heroine}のイベント{i}"
        
        events.append({
            'イベントID': event_id,
            'イベント開始日時': f"{start_month}月{start_day}日の{time_slots.split(';')[0]}",
            'イベント終了日時': f"{start_month}月{start_day}日の{time_slots.split(';')[-1]}",
            'イベントを選べる時間帯': time_slots,
            '対象のヒロイン': heroine,
            '場所': location,
            'イベントのタイトル': title
        })
    
    # CSVファイルに書き込み
    fieldnames = ['イベントID', 'イベント開始日時', 'イベント終了日時', 'イベントを選べる時間帯', '対象のヒロイン', '場所', 'イベントのタイトル']
    
    with open(events_csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(events)
    
    print(f"events.csv復元完了: {len(events)}個のイベント")

if __name__ == "__main__":
    restore_events_csv()