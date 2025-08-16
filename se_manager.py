import pygame
import os

class SEManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.SE_PATH = os.path.join("sounds", "ses")
        pygame.mixer.pre_init(buffer=512)

    def is_valid_se_filename(self, filename):
        """SEファイル名の有効性をチェック"""
        if not filename or not isinstance(filename, str):
            return False
        
        # 音楽ファイルの拡張子をチェック
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            return False
        
        return True

    def play_se(self, filename, volume=0.5, frequency=1):
        try:
            # ファイル名の有効性をチェック
            if not self.is_valid_se_filename(filename):
                if self.debug:
                    print(f"無効なSEファイル名: {filename}")
                return False
            
            se_path = os.path.join(self.SE_PATH, filename)
            
            # ファイルの存在チェック
            if not os.path.exists(se_path):
                if self.debug:
                    print(f"SEファイルが見つかりません: {se_path}")
                return False
            
            # 効果音を読み込み
            sound = pygame.mixer.Sound(se_path)
            sound.set_volume(volume)
            
            # frequency回数分再生（間隔を開けて）
            import time
            import threading
            
            def play_sequential():
                for i in range(int(frequency)):
                    sound.play()
                    if i < int(frequency) - 1:  # 最後以外は待機
                        time.sleep(sound.get_length())
            
            # バックグラウンドで連続再生
            if int(frequency) > 1:
                threading.Thread(target=play_sequential, daemon=True).start()
            else:
                sound.play()
            
            if self.debug:
                print(f"SEを再生: {filename} (volume={volume}, frequency={frequency})")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"SEの再生に失敗しました: {e}")
            return False

    def get_se_for_scene(self, scene_name):
        """シーン名からSEファイル名を取得（直接ファイル名を返す）"""
        if self.debug:
            print(f"[SE] SE取得要求: {scene_name}")
        
        # 直接ファイル名が指定された場合はそのまま返す
        if self.is_valid_se_filename(scene_name):
            if self.debug:
                print(f"[SE] 直接ファイル名指定: {scene_name}")
            return scene_name
        
        # 拡張子がない場合、.mp3を自動補完
        if scene_name and not any(scene_name.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
            candidate = f"{scene_name}.mp3"
            if self.debug:
                print(f"[SE] 拡張子自動補完: {scene_name} -> {candidate}")
            return candidate
        
        if self.debug:
            print(f"[SE] 無効なSE名: {scene_name}")
        return None
