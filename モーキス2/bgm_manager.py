import pygame
import os

class BGMManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.BGM_PATH = os.path.join("sounds", "bgms")
        self.DEFAULT_BGM = "maou_bgm_8bit29.mp3"
        self.SECOND_BGM = "maou_bgm_piano41.mp3"
        self.current_bgm = None

    def play_bgm(self, filename, volume=0.1):
        try:
            bgm_path = os.path.join(self.BGM_PATH, filename)
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)  # ループ再生
            self.current_bgm = filename
            if self.debug:
                print(f"BGMを再生開始: {filename}")
        except Exception as e:
            print(f"BGMの再生に失敗しました: {e}")

    def stop_bgm(self):
        pygame.mixer.music.stop()
        self.current_bgm = None

    def get_bgm_for_scene(self, scene_name):
        if scene_name == "classroom":
            return self.SECOND_BGM
        return self.DEFAULT_BGM 