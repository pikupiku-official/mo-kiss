import pygame
import os

class BGMManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.BGM_PATH = os.path.join("sounds", "bgms")
        self.current_bgm = None

    def is_valid_bgm_filename(self, filename):
        """BGMファイル名の有効性をチェック"""
        if not filename or not isinstance(filename, str):
            return False
        
        # 音楽ファイルの拡張子をチェック
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            return False
        
        # 日本語文字や特殊文字が含まれていないかチェック
        invalid_chars = ['「', '」', '。', '、', '？', '！', '（', '）']
        if any(char in filename for char in invalid_chars):
            return False
        
        return True

    def play_bgm(self, filename, volume=0.5, loop=True):
        try:
            # ファイル名の有効性をチェック
            if not self.is_valid_bgm_filename(filename):
                if self.debug:
                    print(f"無効なBGMファイル名: {filename}")
                return False
            
            bgm_path = os.path.join(self.BGM_PATH, filename)
            
            # ファイルの存在チェック
            if not os.path.exists(bgm_path):
                return False
            
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(volume)
            # ループ設定に応じて再生
            if loop:
                pygame.mixer.music.play(-1)  # ループ再生
            else:
                pygame.mixer.music.play(0)   # 一回のみ再生
            self.current_bgm = filename
            if self.debug:
                print(f"BGMを再生開始: {filename} (loop={loop})")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"BGMの再生に失敗しました: {e}")
            return False

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

    def get_bgm_for_scene(self, scene_name):
        """シーン名からBGMファイル名を取得（直接ファイル名を返す）"""
        if self.debug:
            print(f"[BGM] BGM取得要求: {scene_name}")
        
        # 直接ファイル名が指定された場合はそのまま返す
        if self.is_valid_bgm_filename(scene_name):
            if self.debug:
                print(f"[BGM] 直接ファイル名指定: {scene_name}")
            return scene_name
        
        # 拡張子がない場合、.mp3を自動補完
        if scene_name and not any(scene_name.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            candidate = f"{scene_name}.mp3"
            if self.debug:
                print(f"[BGM] 拡張子自動補完: {scene_name} -> {candidate}")
            return candidate
        
        if self.debug:
            print(f"[BGM] 無効なBGM名: {scene_name}")
        return None