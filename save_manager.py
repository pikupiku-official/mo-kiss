import os
import shutil
import json
from datetime import datetime
from typing import List, Dict, Optional

class SaveManager:
    """セーブ・ロード管理システム"""
    
    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.path.dirname(os.path.abspath(__file__))
        self.current_state_dir = os.path.join(self.project_root, "data", "current_state")
        self.save_dir = os.path.join(self.project_root, "data", "save")
        self.templates_dir = os.path.join(self.project_root, "data", "templates")
        
        # 状態ファイルの定義
        self.state_files = [
            "completed_events.csv",
            "time_state.json", 
            "player_name.json"
        ]
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(self.current_state_dir, exist_ok=True)
        os.makedirs(self.save_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
    
    def get_save_slots(self) -> List[Dict]:
        """利用可能なセーブスロット情報を取得"""
        save_slots = []
        
        for i in range(1, 11):  # セーブスロット1-10
            slot_name = f"saveslot_{i:02d}"
            slot_path = os.path.join(self.save_dir, slot_name)
            
            slot_info = {
                "slot_number": i,
                "slot_name": slot_name,
                "path": slot_path,
                "exists": os.path.exists(slot_path),
                "save_time": None,
                "description": None
            }
            
            # セーブファイルが存在する場合は詳細情報を取得
            if slot_info["exists"]:
                try:
                    # time_state.jsonから時間情報を取得
                    time_state_path = os.path.join(slot_path, "time_state.json")
                    if os.path.exists(time_state_path):
                        with open(time_state_path, 'r', encoding='utf-8') as f:
                            time_state = json.load(f)
                            slot_info["description"] = f"{time_state['year']}年{time_state['month']}月{time_state['day']}日 {time_state['period']}"
                    
                    # フォルダの更新時刻を取得
                    slot_info["save_time"] = datetime.fromtimestamp(os.path.getmtime(slot_path))
                    
                except Exception as e:
                    print(f"セーブスロット{i}の情報取得エラー: {e}")
            
            save_slots.append(slot_info)
        
        return save_slots
    
    def has_save(self, slot_name: str) -> bool:
        """指定されたスロットにセーブデータが存在するかチェック"""
        if slot_name.startswith('saveslot_'):
            slot_number = int(slot_name.split('_')[1])
            slot_path = os.path.join(self.save_dir, slot_name)
            return os.path.exists(slot_path)
        return False
    
    def get_save_metadata(self, slot_name: str) -> Dict:
        """指定されたスロットのメタデータを取得"""
        metadata = {}
        if slot_name.startswith('saveslot_'):
            slot_path = os.path.join(self.save_dir, slot_name)
            if os.path.exists(slot_path):
                try:
                    # player_name.jsonからプレイヤー名を取得
                    player_name_path = os.path.join(slot_path, "player_name.json")
                    if os.path.exists(player_name_path):
                        with open(player_name_path, 'r', encoding='utf-8') as f:
                            player_data = json.load(f)
                            surname = player_data.get('surname', '')
                            name = player_data.get('name', '')
                            metadata['player_name'] = f"{surname} {name}".strip()
                    
                    # time_state.jsonから時間情報を取得
                    time_state_path = os.path.join(slot_path, "time_state.json")
                    if os.path.exists(time_state_path):
                        with open(time_state_path, 'r', encoding='utf-8') as f:
                            time_state = json.load(f)
                            metadata['game_time'] = f"{time_state['month']}月{time_state['day']}日 {time_state['period']}"
                    
                    # セーブ日時
                    save_time = datetime.fromtimestamp(os.path.getmtime(slot_path))
                    metadata['save_date'] = save_time.strftime('%Y年%m月%d日 %H:%M')
                    
                except Exception as e:
                    print(f"メタデータ取得エラー ({slot_name}): {e}")
        
        return metadata
    
    def save_game(self, slot_name: str) -> bool:
        """現在のゲーム状態を指定スロット名に保存"""
        try:
            slot_path = os.path.join(self.save_dir, slot_name)
            
            # セーブスロットディレクトリを作成（存在する場合は削除して再作成）
            if os.path.exists(slot_path):
                shutil.rmtree(slot_path)
            os.makedirs(slot_path)
            
            # current_stateの各ファイルをセーブスロットにコピー
            for filename in self.state_files:
                src_path = os.path.join(self.current_state_dir, filename)
                dst_path = os.path.join(slot_path, filename)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    print(f"[SAVE] {filename} -> {slot_name}")
                else:
                    print(f"[SAVE] 警告: {filename}が見つかりません")
            
            print(f"✅ ゲームを{slot_name}に保存しました")
            return True
            
        except Exception as e:
            print(f"❌ セーブエラー ({slot_name}): {e}")
            return False
    
    def load_game(self, slot_name: str) -> bool:
        """指定スロット名からゲーム状態を読み込み"""
        try:
            slot_path = os.path.join(self.save_dir, slot_name)
            
            if not os.path.exists(slot_path):
                print(f"❌ {slot_name}にセーブデータがありません")
                return False
            
            # セーブスロットの各ファイルをcurrent_stateにコピー
            for filename in self.state_files:
                src_path = os.path.join(slot_path, filename)
                dst_path = os.path.join(self.current_state_dir, filename)
                
                if os.path.exists(src_path):
                    shutil.copy2(src_path, dst_path)
                    print(f"[LOAD] {slot_name} -> {filename}")
                else:
                    print(f"[LOAD] 警告: {filename}が{slot_name}にありません")
            
            # マネージャーを再読み込み
            self._reload_managers()
            
            print(f"✅ {slot_name}からゲームを読み込みました")
            return True
            
        except Exception as e:
            print(f"❌ ロードエラー ({slot_name}): {e}")
            return False
    
    
    
    def delete_save(self, slot_name: str) -> bool:
        """指定スロットのセーブデータを削除"""
        try:
            slot_path = os.path.join(self.save_dir, slot_name)
            
            if os.path.exists(slot_path):
                shutil.rmtree(slot_path)
                print(f"✅ {slot_name}のセーブデータを削除しました")
                return True
            else:
                print(f"❌ {slot_name}にセーブデータがありません")
                return False
                
        except Exception as e:
            print(f"❌ 削除エラー ({slot_name}): {e}")
            return False
    
    def reset_current_state(self) -> bool:
        """current_stateを初期状態にリセット"""
        try:
            # current_stateの各ファイルをテンプレートから復元
            template_mapping = {
                "completed_events.csv": "completed_events_template.csv",
                "time_state.json": "time_state_template.json",
                "player_name.json": "player_name_template.json"
            }
            
            for current_name, template_name in template_mapping.items():
                template_path = os.path.join(self.templates_dir, template_name)
                current_path = os.path.join(self.current_state_dir, current_name)
                
                if os.path.exists(template_path):
                    shutil.copy2(template_path, current_path)
                    print(f"[RESET] {current_name}を初期化")
                else:
                    print(f"[RESET] 警告: テンプレート{template_name}が見つかりません")
            
            # マネージャーを再読み込み
            self._reload_managers()
            
            print("✅ ゲーム状態を初期化しました")
            return True
            
        except Exception as e:
            print(f"❌ 初期化エラー: {e}")
            return False
    
    def backup_current_state(self, backup_name: str = None) -> bool:
        """current_stateをバックアップ"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.save_dir, backup_name)
            shutil.copytree(self.current_state_dir, backup_path)
            print(f"✅ バックアップを作成しました: {backup_name}")
            return True
            
        except Exception as e:
            print(f"❌ バックアップエラー: {e}")
            return False
    
    def _reload_managers(self):
        """全マネージャーを再読み込み（セーブ/ロード後に使用）"""
        try:
            # TimeManagerを再読み込み
            from time_manager import reload_time_manager
            reload_time_manager()
            print("[RELOAD] TimeManager再読み込み完了")
            
            # NameManagerを再読み込み（グローバルインスタンスを再初期化）
            from dialogue.name_manager import NameManager
            import dialogue.name_manager as nm
            nm._name_manager = NameManager()
            print("[RELOAD] NameManager再読み込み完了")
            
        except Exception as e:
            print(f"[RELOAD] マネージャー再読み込みエラー: {e}")

# グローバルインスタンス
_save_manager = None

def get_save_manager():
    """SaveManagerのグローバルインスタンスを取得"""
    global _save_manager
    if _save_manager is None:
        _save_manager = SaveManager()
    return _save_manager