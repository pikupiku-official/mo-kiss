import pygame
import os

class BGMManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.BGM_PATH = os.path.join("sounds", "bgms")
        self.DEFAULT_BGM = "maou_bgm_8bit29.mp3"
        self.SECOND_BGM = "maou_bgm_piano41.mp3"
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

    def play_bgm(self, filename, volume=0):
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
            pygame.mixer.music.play(-1)  # ループ再生
            self.current_bgm = filename
            if self.debug:
                print(f"BGMを再生開始: {filename}")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"BGMの再生に失敗しました: {e}")
            return False

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

    def get_bgm_for_scene(self, scene_name):
        if scene_name == "classroom":
            return self.SECOND_BGM
        return self.DEFAULT_BGM