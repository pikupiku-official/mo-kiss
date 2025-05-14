import re
from bgm_manager import BGMManager
from config import *

class DialogueLoader:
    def __init__(self, debug=False):
        self.debug = debug
        self.bgm_manager = BGMManager(debug)
        # キャラクター名と画像ファイル名の対応付け
        self.character_image_map = CHARACTER_IMAGE_MAP

    def load_dialogue_from_ks(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                content = file.read()

            dialogue_list = []
            current_background = DEFAULT_BACKGROUND  # デフォルトの背景
            current_character = "girl1"    # デフォルトのキャラクター
            current_eye = None            # デフォルトの目
            current_mouth = None          # デフォルトの口
            current_bgm = self.bgm_manager.DEFAULT_BGM  # デフォルトのBGM
            current_bgm_volume = DEFAULT_BGM_VOLUME  # デフォルトの音量
            current_bgm_loop = DEFAULT_BGM_LOOP   # デフォルトでループ再生

            # キャラクターごとの現在の表情設定を保持
            character_expressions = {}

            # シーンごとのBGM設定を検出
            scene_matches = re.finditer(r'\*scene\d+\|.*?\n(.*?)(?=\*scene\d+\||$)', content, re.DOTALL)
            for scene_match in scene_matches:
                scene_content = scene_match.group(1)
                
                # シーン内のBGM設定を検出
                bg_matches = re.finditer(r'\[BGM bgm="([^"]+)"(?:\s+volume="([^"]+)")?(?:\s+loop="([^"]+)")?\]', scene_content)
                for match in bg_matches:
                    bgm_name = match.group(1)
                    volume = float(match.group(2)) if match.group(2) else current_bgm_volume
                    loop = match.group(3).lower() == "true" if match.group(3) else current_bgm_loop
                    
                    current_bgm = self.bgm_manager.get_bgm_for_scene(bgm_name)
                    current_bgm_volume = volume
                    current_bgm_loop = loop
                    
                    if self.debug:
                        print(f"シーンのBGMを設定: {bgm_name} -> {current_bgm}")
                        print(f"音量: {volume}, ループ: {loop}")

                # シーン内のテキストを検出
                text_matches = re.finditer(r'\[([^[\]]+?)(?:\s+eye="([^"]+)"\s+mouth="([^"]+)"\s+brow="([^"]+)")?\]([^[]+)\[en\]', scene_content)
                for match in text_matches:
                    character_name = match.group(1)  # キャラクター名をそのまま使用
                    # キャラクター名から画像ファイル名を取得
                    character = self.character_image_map.get(character_name, "girl1")
                    
                    # 新しい表情設定があれば更新
                    new_eye = match.group(2)
                    new_mouth = match.group(3)
                    new_brow = match.group(4)
                    
                    # キャラクターの現在の表情設定を取得（なければ初期化）
                    if character_name not in character_expressions:
                        character_expressions[character_name] = {"eye": None, "mouth": None, "brow": None}
                    
                    # 新しい設定があれば更新
                    if new_eye:
                        character_expressions[character_name]["eye"] = new_eye
                    if new_mouth:
                        character_expressions[character_name]["mouth"] = new_mouth
                    if new_brow:
                        character_expressions[character_name]["brow"] = new_brow
                    
                    # 現在の表情設定を使用
                    eye = character_expressions[character_name]["eye"]
                    mouth = character_expressions[character_name]["mouth"]
                    brow = character_expressions[character_name]["brow"]
                    
                    text = match.group(5)
                    
                    # テキストに二つ連続したスペースがあれば分割する
                    text_parts = text.split("  ")
                    
                    for text_part in text_parts:
                        if text_part.strip():
                            dialogue_list.append([
                                current_background,
                                character,  # 画像ファイル名
                                eye,
                                mouth,
                                text_part.strip(),
                                current_bgm,
                                current_bgm_volume,
                                current_bgm_loop,
                                character_name,  # 表示用のキャラクター名を追加
                                brow  # 眉毛の設定を追加
                            ])

            return dialogue_list
        
        except FileNotFoundError:
            print(f"ファイルが見つかりません: {filename}")
            return []
        except Exception as e:
            print(f"エラー: {e}")
            return []

    def get_default_dialogue(self):
        return [
            ["classroom", "girl1", None, None, "TyranoScriptファイルが読み込めませんでした。", self.bgm_manager.DEFAULT_BGM, DEFAULT_BGM_VOLUME, DEFAULT_BGM_LOOP, "girl1"],
            ["classroom", "girl1", None, None, "デフォルトの会話を表示しています。", self.bgm_manager.DEFAULT_BGM, DEFAULT_BGM_VOLUME, DEFAULT_BGM_LOOP, "girl1"]
        ] 