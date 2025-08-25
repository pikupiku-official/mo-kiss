import os
import json
import re

class NameManager:
    """名前データの管理とテキスト内の変数置換を行うクラス"""
    
    def __init__(self):
        self.surname = ""
        self.name = ""
        self.data_file = os.path.join("data", "current_state", "player_name.json")
        self.dialogue_loader = None  # あとで設定
        self.load_names()
    
    def set_names(self, surname, name):
        """苗字と名前を設定"""
        # 3文字までの制限
        self.surname = surname[:3] if surname else ""
        self.name = name[:3] if name else ""
        self.save_names()
        print(f"[NAME] 名前設定: 苗字='{self.surname}', 名前='{self.name}'")
    
    def get_surname(self):
        """苗字を取得"""
        return self.surname
    
    def get_name(self):
        """名前を取得"""
        return self.name
    
    def get_fullname(self):
        """フルネームを取得"""
        return f"{self.surname}{self.name}"
    
    def load_names(self):
        """名前データをファイルから読み込み"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.surname = data.get('surname', '')
                    self.name = data.get('name', '')
                print(f"[NAME] 名前読み込み完了: 苗字='{self.surname}', 名前='{self.name}'")
            else:
                print(f"[NAME] 名前ファイルが存在しないため、空の名前で初期化")
        except Exception as e:
            print(f"[NAME] 名前読み込みエラー: {e}")
            self.surname = ""
            self.name = ""
    
    def save_names(self):
        """名前データをファイルに保存"""
        try:
            data = {
                'surname': self.surname,
                'name': self.name
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"[NAME] 名前保存完了")
        except Exception as e:
            print(f"[NAME] 名前保存エラー: {e}")
    
    def substitute_variables(self, text):
        """テキスト内の変数を置換"""
        if not text:
            return text
        
        # 変数置換
        substitutions = {
            '{苗字}': self.surname,
            '{名前}': self.name,
            '{フルネーム}': self.get_fullname(),
            '{surname}': self.surname,
            '{name}': self.name,
            '{fullname}': self.get_fullname()
        }
        
        result = text
        for variable, value in substitutions.items():
            result = result.replace(variable, value)
        
        # 選択肢タグの置換 {選択肢1}, {選択肢2}, ...
        if self.dialogue_loader:
            result = re.sub(r'\{選択肢(\d+)\}', self._replace_choice_tag, result)
        
        return result
    
    def _replace_choice_tag(self, match):
        """選択肢タグを実際の選択肢テキストに置換"""
        choice_number = int(match.group(1))
        if self.dialogue_loader:
            result = self.dialogue_loader.get_choice_text(choice_number)
            print(f"[DEBUG] 選択肢タグ置換: {{選択肢{choice_number}}} → '{result}'")
            return result
        print(f"[DEBUG] 選択肢タグ置換失敗: dialogue_loader not found")
        return match.group(0)  # 置換できない場合はそのまま返す
    
    def set_dialogue_loader(self, dialogue_loader):
        """DialogueLoaderの参照を設定（選択肢タグ置換用）"""
        self.dialogue_loader = dialogue_loader
    
    def has_names(self):
        """名前が設定されているかどうかを確認"""
        return bool(self.surname or self.name)
    
    def clear_names(self):
        """名前データをクリア"""
        self.surname = ""
        self.name = ""
        self.save_names()
        print(f"[NAME] 名前データクリア完了")

# グローバルインスタンス
_name_manager = NameManager()

def get_name_manager():
    """NameManagerのグローバルインスタンスを取得"""
    return _name_manager

def set_player_names(surname, name):
    """プレイヤーの名前を設定（便利関数）"""
    _name_manager.set_names(surname, name)

def substitute_text_variables(text):
    """テキスト内の変数を置換（便利関数）"""
    return _name_manager.substitute_variables(text)

def get_player_surname():
    """プレイヤーの苗字を取得（便利関数）"""
    return _name_manager.get_surname()

def get_player_name():
    """プレイヤーの名前を取得（便利関数）"""
    return _name_manager.get_name()

def get_player_fullname():
    """プレイヤーのフルネームを取得（便利関数）"""
    return _name_manager.get_fullname()