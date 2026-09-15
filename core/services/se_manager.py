import pygame
import os
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from core.services.settings_manager import get_settings_manager
from core.services.audio_utils import peak_limited_gain_sound

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
        self.current_sound = None
        self.current_source_sound = None
        self.current_channel = None

    def is_valid_se_filename(self, filename):
        """SEファイル名の有効性をチェック"""
        if not filename or not isinstance(filename, str):
            return False
        
        # 音楽ファイルの拡張子をチェック
        valid_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        if not any(filename.lower().endswith(ext) for ext in valid_extensions):
            return False
        
        return True

    def _trim_sound(self, sound, start=0.0, end=None):
        """Create a mixer-compatible PCM slice of a decoded sound."""
        try:
            start = max(0.0, float(start or 0.0))
            end = None if end in (None, "") else max(0.0, float(end))
        except (TypeError, ValueError):
            return None
        if start <= 0 and end is None:
            return sound
        length = sound.get_length()
        end = length if end is None else min(end, length)
        if start >= end:
            return None
        init = pygame.mixer.get_init()
        if not init or not hasattr(sound, "get_raw"):
            return None
        sample_rate, sample_format, channels = init
        bytes_per_sample = max(1, abs(int(sample_format)) // 8)
        frame_bytes = bytes_per_sample * int(channels)
        raw = sound.get_raw()
        first = int(round(start * sample_rate)) * frame_bytes
        last = int(round(end * sample_rate)) * frame_bytes
        raw_slice = raw[first:last]
        return pygame.mixer.Sound(buffer=raw_slice) if raw_slice else None

    def play_se(self, filename, volume=0.5, frequency=1, start=0.0, end=None):
        try:
            if not pygame.mixer.get_init():
                try:
                    pygame.mixer.init()
                    if self.debug:
                        print("SEManager: pygame.mixerを初期化しました")
                except Exception as e:
                    if self.debug:
                        print(f"SEManager: pygame.mixer初期化エラー: {e}")
                    return False

            # 拡張子が含まれていない場合、実在する拡張子（.wav, .mp3, .ogg, .m4a）を自動補完
            if filename and not any(filename.lower().endswith(ext) for ext in ['.mp3', '.wav', '.ogg', '.m4a']):
                for ext in ['.wav', '.mp3', '.ogg', '.m4a']:
                    candidate = f"{filename}{ext}"
                    if os.path.exists(os.path.join(self.SE_PATH, candidate)):
                        filename = candidate
                        break
                else:
                    # 見つからない場合はデフォルトで.wavを付与
                    filename = f"{filename}.wav"

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
            source_sound = pygame.mixer.Sound(se_path)
            sound = self._trim_sound(source_sound, start, end)
            if sound is None:
                return False
            try:
                volume = float(volume)
                if volume > 2.0 and volume <= 10.0:
                    volume /= 10.0
                elif volume > 10.0:
                    volume /= 100.0
                volume = max(0.0, min(2.0, volume))
            except (TypeError, ValueError):
                volume = 0.5
            play_sound = peak_limited_gain_sound(sound, volume)
            play_sound.set_volume(min(1.0, volume))
            self.current_source_sound = sound
            self.current_sound = play_sound
            
            # frequency回数分再生（間隔を開けて）
            import time
            import threading
            
            def play_sequential():
                for i in range(int(frequency)):
                    channel = play_sound.play()
                    get_settings_manager().apply_se_channel_volume(channel)
                    if i < int(frequency) - 1:  # 最後以外は待機
                        time.sleep(play_sound.get_length())
            
            # バックグラウンドで連続再生（複数回はブロック追跡不可）
            if int(frequency) > 1:
                channel = play_sound.play(loops=int(frequency) - 1)
            else:
                channel = play_sound.play()
                get_settings_manager().apply_se_channel_volume(channel)
            self.current_channel = channel
            
            if self.debug:
                print(f"SEを再生: {filename} (volume={volume}, frequency={frequency})")
            return channel
            
        except Exception as e:
            if self.debug:
                print(f"SEの再生に失敗しました: {e}")
            return False

    def set_current_volume(self, volume):
        """直近に再生したSEの音量を即時変更する。"""
        try:
            volume = max(0.0, min(2.0, float(volume)))
        except (TypeError, ValueError):
            return False
        if self.current_sound is None:
            return False
        if volume <= 1.0:
            if (
                self.current_source_sound is not None
                and self.current_sound is not self.current_source_sound
            ):
                if self.current_channel is not None:
                    self.current_channel.stop()
                self.current_sound = self.current_source_sound
                self.current_channel = self.current_sound.play()
                get_settings_manager().apply_se_channel_volume(self.current_channel)
            self.current_sound.set_volume(volume)
        elif self.current_source_sound is not None:
            # Mixer channel volume cannot exceed 1. Rebuild the last trimmed
            # PCM slice with a peak-safe gain and restart it at the new level.
            amplified = peak_limited_gain_sound(self.current_source_sound, volume)
            if amplified is not self.current_sound:
                if self.current_channel is not None:
                    self.current_channel.stop()
                self.current_sound = amplified
                self.current_sound.set_volume(1.0)
                self.current_channel = self.current_sound.play()
                get_settings_manager().apply_se_channel_volume(self.current_channel)
        self.current_volume = volume
        return True

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
                channel = sound.play()
                get_settings_manager().apply_se_channel_volume(channel)
            
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
            channel = sound.play()
            get_settings_manager().apply_se_channel_volume(channel)
            if i < int(frequency) - 1:  # 最後以外は待機
                time.sleep(sound.get_length())

    def stop_all_se(self):
        """すべてのSEを停止"""
        try:
            # pygameのすべてのサウンドチャンネルを停止
            pygame.mixer.stop()
            self.current_sound = None
            self.current_source_sound = None
            self.current_channel = None
            self.current_volume = 0.5
            if self.debug:
                print("SEManager: すべてのSEを停止しました")
        except Exception as e:
            if self.debug:
                print(f"SE停止エラー: {e}")

    def cleanup(self):
        """リソースのクリーンアップ"""
        # すべてのSEを停止
        self.stop_all_se()

        # キャッシュをクリア
        with self.cache_lock:
            self.sound_cache.clear()

        # ExecutorPoolをシャットダウン
        self.executor.shutdown(wait=False)

        if self.debug:
            print("SEManager: リソースクリーンアップ完了")
