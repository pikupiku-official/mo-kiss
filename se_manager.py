import pygame
import os
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

class SEManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.SE_PATH = os.path.join("sounds", "ses")
        pygame.mixer.pre_init(buffer=512)
        
        # 非同期処理用
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.sound_cache = {}  # SEキャッシュ
        self.cache_lock = threading.Lock()
        self.max_cache_size = 20

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
    
    def _get_cached_sound(self, se_path):
        """キャッシュからSEを取得またはロード"""
        with self.cache_lock:
            if se_path in self.sound_cache:
                return self.sound_cache[se_path]
            
            # キャッシュにない場合はロード
            if os.path.exists(se_path):
                sound = pygame.mixer.Sound(se_path)
                
                # キャッシュサイズ管理
                if len(self.sound_cache) >= self.max_cache_size:
                    # 最初のエントリを削除（簡単なLRU）
                    oldest_key = next(iter(self.sound_cache))
                    del self.sound_cache[oldest_key]
                    if self.debug:
                        print(f"SEキャッシュから削除: {oldest_key}")
                
                self.sound_cache[se_path] = sound
                if self.debug:
                    print(f"SEをキャッシュに追加: {se_path}")
                
                return sound
            return None
    
    async def play_se_async(self, filename, volume=0.5, frequency=1):
        """SEを非同期で再生"""
        try:
            # ファイル名の有効性をチェック
            if not self.is_valid_se_filename(filename):
                if self.debug:
                    print(f"無効なSEファイル名: {filename}")
                return False
            
            se_path = os.path.join(self.SE_PATH, filename)
            
            # ファイルの存在チェックを非同期で実行
            exists = await asyncio.to_thread(os.path.exists, se_path)
            if not exists:
                if self.debug:
                    print(f"SEファイルが見つかりません: {se_path}")
                return False
            
            # SEロードを非同期で実行
            sound = await asyncio.to_thread(self._get_cached_sound, se_path)
            if not sound:
                return False
            
            sound.set_volume(volume)
            
            # frequency回数分再生
            if int(frequency) > 1:
                await asyncio.to_thread(self._play_sequential_async, sound, frequency)
            else:
                sound.play()
            
            if self.debug:
                print(f"SE非同期再生: {filename} (volume={volume}, frequency={frequency})")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"SE非同期再生エラー: {e}")
            return False
    
    def _play_sequential_async(self, sound, frequency):
        """連続再生（非同期版）"""
        for i in range(int(frequency)):
            sound.play()
            if i < int(frequency) - 1:  # 最後以外は待機
                time.sleep(sound.get_length())
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        # キャッシュをクリア
        with self.cache_lock:
            self.sound_cache.clear()
        
        # ExecutorPoolをシャットダウン
        self.executor.shutdown(wait=False)
        
        if self.debug:
            print("SEManager: リソースクリーンアップ完了")