import pygame
import os
import threading
import time
import asyncio
import re
from concurrent.futures import ThreadPoolExecutor

from core.services.settings_manager import get_settings_manager

class BGMManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.BGM_PATH = os.path.join("sounds", "bgms")
        self.current_bgm = None
        self.current_loop = True
        self.current_volume = 0.5
        self.target_volume = 0.5
        self.fade_thread = None
        self.is_fading = False
        self.is_paused = False
        self.paused_bgm = None  # 一時停止したBGMの情報を保持
        self.paused_volume = 0.5
        self.paused_loop = True
        self.sequence_thread = None
        self.sequence_stop = threading.Event()
        
        # 非同期処理用
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.fade_event = threading.Event()  # フェード制御用

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

    def _sequence_candidates(self, filename):
        """Find exact-prefix numeric siblings such as MokLap1/MokLap2."""
        match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", filename or "")
        if not match or not os.path.isdir(self.BGM_PATH):
            return [filename]
        prefix, _number, extension = match.groups()
        candidates = []
        for candidate in os.listdir(self.BGM_PATH):
            candidate_match = re.match(r"^(.*?)(\d+)(\.[^.]+)$", candidate)
            if not candidate_match:
                continue
            candidate_prefix, candidate_number, candidate_extension = candidate_match.groups()
            if (
                candidate_prefix == prefix
                and candidate_extension.lower() == extension.lower()
            ):
                candidates.append((int(candidate_number), candidate))
        candidates.sort(key=lambda item: (item[0], item[1]))
        return [candidate for _number, candidate in candidates] or [filename]

    def _stop_sequence(self):
        self.sequence_stop.set()
        thread = self.sequence_thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=1.0)
        self.sequence_thread = None
        self.sequence_stop = threading.Event()

    def _play_loaded_bgm(self, filename, volume, loop, start=0.0):
        pygame.mixer.music.load(os.path.join(self.BGM_PATH, filename))
        get_settings_manager().apply_bgm_volume(volume)
        loops = -1 if loop else 0
        if start > 0:
            pygame.mixer.music.play(loops, start=start)
        else:
            pygame.mixer.music.play(loops)
        self.current_bgm = filename
        self.current_loop = loop
        self.current_volume = volume
        self.target_volume = volume
        self.is_paused = False

    def _monitor_sequence(self, sequence, volume):
        """Play numbered tracks in order, repeating the final track."""
        index = 0
        while not self.sequence_stop.wait(0.05):
            if pygame.mixer.music.get_busy():
                continue
            if index + 1 < len(sequence):
                index += 1
            try:
                self._play_loaded_bgm(sequence[index], volume, False)
                # Keep the logical BGM name stable while the physical track
                # advances through Lap2, Lap2, ... .
                self.current_bgm = sequence[0]
                self.current_loop = True
            except Exception as exc:
                if self.debug:
                    print(f"BGM sequence playback error: {exc}")
                return

    def play_bgm(self, filename, volume=0.5, loop=True, fade_time=0.0, start=0.0):
        print(f"[BGM_DEBUG] play_bgm要求: filename='{filename}', volume={volume}, loop={loop}, fade={fade_time}")
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                print("[BGM_DEBUG] pygame.mixer was not initialized. Auto initialized mixer.")
            except Exception as e:
                print(f"[BGM_DEBUG] pygame.mixer init error: {e}")
                return False
        try:
            self._stop_sequence()
            self._stop_fade()
            # 音量の正規化
            try:
                volume = float(volume)
            except (ValueError, TypeError):
                volume = 0.5

            try:
                fade_time = max(0.0, float(fade_time))
            except (ValueError, TypeError):
                fade_time = 0.0
            try:
                start = max(0.0, float(start))
            except (ValueError, TypeError):
                start = 0.0
            if isinstance(loop, str):
                loop = loop.strip().lower() in ("true", "1", "yes", "on")
            else:
                loop = bool(loop)

            if volume <= 0:
                print(f"[BGM_DEBUG] volume={volume} (0以下) 指定のため BGM 停止/消音処理: filename='{filename}'")
                self.stop_bgm()
                return True
            elif volume > 1.0:
                if volume <= 10.0:
                    volume = volume / 10.0
                else:
                    volume = min(volume / 100.0, 1.0)

            # ファイル名の有効性をチェック
            if not self.is_valid_bgm_filename(filename):
                # 拡張子がない場合は実在するファイル名を探す
                actual_filename = self.get_bgm_for_scene(filename)
                if actual_filename:
                    filename = actual_filename
                else:
                    print(f"[BGM_DEBUG] 無効なBGMファイル名 & 代替ファイルなし: '{filename}'")
                    return False
            
            bgm_path = os.path.join(self.BGM_PATH, filename)
            
            # ファイルの存在チェック
            if not os.path.exists(bgm_path):
                actual_filename = self.get_bgm_for_scene(filename)
                if actual_filename:
                    filename = actual_filename
                    bgm_path = os.path.join(self.BGM_PATH, filename)
                else:
                    print(f"[BGM_DEBUG] BGMファイルが存在しません: '{bgm_path}'")
                    return False
            
            sequence = self._sequence_candidates(filename)
            sequence_mode = loop and len(sequence) > 1 and sequence[0] == filename
            if sequence_mode:
                self._play_loaded_bgm(filename, 0.0 if fade_time > 0 else volume, False, start=start)
                self.sequence_thread = threading.Thread(
                    target=self._monitor_sequence,
                    args=(sequence, volume),
                    daemon=True,
                )
                self.sequence_thread.start()
            else:
                self._play_loaded_bgm(filename, 0.0 if fade_time > 0 else volume, loop, start=start)
            start_volume = 0.0 if fade_time > 0 else volume
            self.current_bgm = filename
            self.current_loop = loop
            self.current_volume = start_volume
            self.target_volume = volume
            self.is_paused = False
            self.paused_bgm = None
            if fade_time > 0:
                self.fade_in(volume, fade_time)
            print(f"[BGM_DEBUG] BGM蜀咲函謌仙粥! file='{filename}', full_path='{bgm_path}', volume={volume}, loop={loop}")
            return True
            self.current_bgm = filename
            self.current_loop = loop
            self.current_volume = start_volume
            self.target_volume = volume
            self.is_paused = False
            self.paused_bgm = None
            if fade_time > 0:
                self.fade_in(volume, fade_time)
            print(f"[BGM_DEBUG] BGM再生成功! file='{filename}', full_path='{bgm_path}', volume={volume}, loop={loop}")
            return True
            
        except Exception as e:
            print(f"[BGM_DEBUG] BGMの再生失敗: {e}")
            return False

    def stop_bgm(self):
        self._stop_sequence()
        print(f"[BGM_DEBUG] stop_bgm呼び出し (現在再生中='{self.current_bgm}')")
        self._stop_fade()
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        self.current_bgm = None
        self.current_loop = True
        self.current_volume = 0.5
        self.target_volume = 0.5
        self.is_paused = False
        self.paused_bgm = None

    def set_volume(self, volume):
        """再生中のBGM音量を即時変更する。"""
        try:
            volume = max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return False
        self._stop_fade()
        self.current_volume = volume
        self.target_volume = volume
        get_settings_manager().apply_bgm_volume(volume)
        return True
    
    def pause_bgm(self):
        """BGMを一時停止"""
        if self.current_bgm:
            self.paused_bgm = self.current_bgm
            self.paused_volume = self.target_volume
            self.paused_loop = self.current_loop
            self.is_paused = True
            pygame.mixer.music.pause()
            self.current_bgm = None
            if self.debug:
                print("BGMを一時停止しました")
    
    def unpause_bgm(self):
        """BGMの再生を再開"""
        if self.is_paused and self.paused_bgm:
            # 一時停止状態から再開
            if not self.current_bgm:
                # BGMが停止している場合は再度読み込んで再生
                self.play_bgm(self.paused_bgm, self.paused_volume, self.paused_loop)
            else:
                # 単純な一時停止の場合
                pygame.mixer.music.unpause()
            self.is_paused = False
            if self.debug:
                print("BGMの再生を再開しました")
        elif self.debug:
            print("再開するBGMがありません")
    
    def _stop_fade(self):
        """フェードスレッドを停止"""
        if self.fade_thread and self.fade_thread.is_alive():
            self.is_fading = False
            self.fade_thread.join(timeout=1.0)
    
    def _fade_volume(self, target_volume, fade_time):
        """音量をフェードするスレッド（最適化版）"""
        self.is_fading = True
        start_volume = self.current_volume
        
        # より細かいステップでスムーズなフェード
        fps = 30  # 30FPSでフェード更新
        total_steps = max(int(fade_time * fps), 1)
        step_duration = fade_time / total_steps
        volume_step = (target_volume - start_volume) / total_steps
        
        try:
            for i in range(total_steps):
                if not self.is_fading:
                    break
                
                # より正確な音量計算
                progress = (i + 1) / total_steps
                # イージング関数を適用（より自然なフェード）
                eased_progress = self._ease_in_out(progress)
                self.current_volume = start_volume + (target_volume - start_volume) * eased_progress
                self.current_volume = max(0.0, min(1.0, self.current_volume))
                
                get_settings_manager().apply_bgm_volume(self.current_volume)
                
                if self.debug and i % 10 == 0:  # デバッグ出力を減らす
                    print(f"フェード中: {self.current_volume:.2f} ({progress:.1%})")
                
                # より正確なタイミング
                time.sleep(step_duration)
            
            # 最終音量に設定
            if self.is_fading:
                self.current_volume = target_volume
                get_settings_manager().apply_bgm_volume(self.current_volume)
                
                # フェードアウト完了後に停止
                if target_volume <= 0.0:
                    pygame.mixer.music.stop()
                    self.current_bgm = None
                    
        except Exception as e:
            if self.debug:
                print(f"フェードエラー: {e}")
        finally:
            self.is_fading = False
    
    def _ease_in_out(self, t):
        """イージング関数（スムーズなフェード用）"""
        return 3 * t * t - 2 * t * t * t
    
    def _fade_volume_for_pause(self, target_volume, fade_time):
        """一時停止用の音量フェード（音量を下げる）"""
        self.is_fading = True
        start_volume = self.current_volume
        fps = 30
        total_steps = max(int(fade_time * fps), 1) if fade_time > 0 else 0
        step_duration = fade_time / total_steps if total_steps > 0 else 0
        
        try:
            for i in range(total_steps):
                if not self.is_fading:
                    break
                
                progress = (i + 1) / total_steps
                eased_progress = self._ease_in_out(progress)
                self.current_volume = start_volume + (target_volume - start_volume) * eased_progress
                self.current_volume = max(0.0, min(1.0, self.current_volume))
                get_settings_manager().apply_bgm_volume(self.current_volume)
                
                if self.debug and i % 10 == 0:
                    print(f"一時停止フェード中: {self.current_volume:.2f}")
                
                time.sleep(step_duration)
            
            # 最終音量に設定
            if self.is_fading:
                self.current_volume = target_volume
                get_settings_manager().apply_bgm_volume(self.current_volume)
                if target_volume <= 0.0:
                    pygame.mixer.music.pause()
                    self.current_bgm = None
                    
        except Exception as e:
            if self.debug:
                print(f"一時停止フェードエラー: {e}")
        finally:
            self.is_fading = False
    
    def fade_out(self, fade_time=1.0):
        """BGMをフェードアウト"""
        self._stop_sequence()
        self._stop_fade()
        self.is_paused = False
        self.paused_bgm = None
        if self.debug:
            print(f"BGMフェードアウト開始: {fade_time}秒")
        
        self.fade_thread = threading.Thread(target=self._fade_volume, args=(0.0, fade_time))
        self.fade_thread.start()
    
    def fade_in(self, target_volume=None, fade_time=1.0):
        """BGMをフェードイン"""
        if target_volume is None:
            target_volume = self.target_volume
        
        self._stop_fade()
        if self.debug:
            print(f"BGMフェードイン開始: {fade_time}秒, 目標音量: {target_volume}")
        
        # 現在の音量を0に設定してから開始
        self.current_volume = 0.0
        get_settings_manager().apply_bgm_volume(0.0)
        
        self.fade_thread = threading.Thread(target=self._fade_volume, args=(target_volume, fade_time))
        self.fade_thread.start()
    
    def pause_bgm_with_fade(self, fade_time=1.0):
        """BGMをフェードアウトして一時停止"""
        if not self.current_bgm:
            return
            
        # 一時停止情報を保存
        self.paused_bgm = self.current_bgm
        self.paused_volume = self.target_volume
        self.paused_loop = self.current_loop
        self.is_paused = True
        
        self._stop_fade()
        if self.debug:
            print(f"BGMフェードアウト一時停止: {fade_time}秒")
        
        def fade_and_pause():
            self._fade_volume_for_pause(0.0, fade_time)
        
        self.fade_thread = threading.Thread(target=fade_and_pause)
        self.fade_thread.start()
    
    def unpause_bgm_with_fade(self, fade_time=1.0):
        """BGMをフェードインして再開"""
        if not self.is_paused or not self.paused_bgm:
            if self.debug:
                print("再開するBGMがありません")
            return
        
        # BGMが停止している場合は再度読み込んで再生
        if not self.current_bgm:
            if self.debug:
                print(f"BGMを再読み込みして再生: {self.paused_bgm}")
            self.play_bgm(
                self.paused_bgm,
                self.paused_volume,
                self.paused_loop,
                fade_time=fade_time,
            )
            self.is_paused = False
            return
        else:
            # 単純な一時停止の場合
            pygame.mixer.music.unpause()
        
        # フェードイン
        self.fade_in(self.paused_volume, fade_time)
        self.is_paused = False
        
        if self.debug:
            print(f"BGMフェードイン再開: {fade_time}秒, 目標音量: {self.paused_volume}")

    def get_bgm_for_scene(self, scene_name):
        """シーン名から実在するBGMファイル名を取得"""
        if not scene_name or not isinstance(scene_name, str):
            return None

        bgm_dir = self.BGM_PATH
        if not os.path.exists(bgm_dir):
            return None

        # シナリオ論理名 -> 実ディスクファイル名のマッピングテーブル
        BGM_ALIAS_MAP = {
            "school_daily": "02_学校生活.ogg",
            "school": "02_学校生活.ogg",
            "classroom": "02_学校生活.ogg",
            "晴海の昼": "02_学校生活.ogg",
            "MokMas42654": "MokMas42654.mp3",
            "Mok1_Lap1": "MokLap1.mp3",
            "Mok1_Lap2": "MokLap2.mp3",
            "title": "maou_bgm_8bit29.mp3",
            "BGM_TITLE": "maou_bgm_8bit29.mp3",
        }

        if scene_name in BGM_ALIAS_MAP:
            alias_file = BGM_ALIAS_MAP[scene_name]
            if os.path.exists(os.path.join(bgm_dir, alias_file)):
                return alias_file

        # 1. 直接存在するファイルの場合
        if os.path.exists(os.path.join(bgm_dir, scene_name)):
            return scene_name

        # 2. 拡張子がない場合、主要拡張子（.mp3, .ogg, .wav, .m4a）で実在チェック
        for ext in ['.mp3', '.ogg', '.wav', '.m4a']:
            candidate = f"{scene_name}{ext}"
            if os.path.exists(os.path.join(bgm_dir, candidate)):
                return candidate

        # 3. ディレクトリ内の全ファイルから大文字小文字無視・部分一致で探索
        try:
            all_files = os.listdir(bgm_dir)
            scene_lower = scene_name.lower()

            for f in all_files:
                name_without_ext = os.path.splitext(f)[0].lower()
                if name_without_ext == scene_lower:
                    return f

            for f in all_files:
                f_lower = f.lower()
                if scene_lower in f_lower or f_lower in scene_lower:
                    return f
        except Exception:
            pass

        return None
    
    async def fade_out_async(self, fade_time=1.0):
        """BGMを非同期でフェードアウト"""
        self._stop_fade()
        if self.debug:
            print(f"BGM非同期フェードアウト開始: {fade_time}秒")
        
        await asyncio.to_thread(self._fade_volume, 0.0, fade_time)
    
    async def fade_in_async(self, target_volume=None, fade_time=1.0):
        """BGMを非同期でフェードイン"""
        if target_volume is None:
            target_volume = self.target_volume
        
        self._stop_fade()
        if self.debug:
            print(f"BGM非同期フェードイン開始: {fade_time}秒, 目標音量: {target_volume}")
        
        # 現在の音量を0に設定してから開始
        self.current_volume = 0.0
        get_settings_manager().apply_bgm_volume(0.0)
        
        await asyncio.to_thread(self._fade_volume, target_volume, fade_time)
    
    async def pause_bgm_with_fade_async(self, fade_time=1.0):
        """BGMを非同期でフェードアウトして一時停止"""
        if not self.current_bgm:
            return
            
        # 一時停止情報を保存
        self.paused_bgm = self.current_bgm
        self.paused_volume = self.target_volume
        self.paused_loop = self.current_loop
        self.is_paused = True
        
        if self.debug:
            print(f"BGM非同期フェードアウト一時停止: {fade_time}秒")
        
        await asyncio.to_thread(self._fade_volume_for_pause, 0.0, fade_time)
    
    async def unpause_bgm_with_fade_async(self, fade_time=1.0):
        """BGMを非同期でフェードインして再開"""
        if not self.is_paused or not self.paused_bgm:
            if self.debug:
                print("再開するBGMがありません")
            return
        
        # BGMが停止している場合は再度読み込んで再生
        if not self.current_bgm:
            if self.debug:
                print(f"BGMを再読み込みして再生: {self.paused_bgm}")
            self.play_bgm(
                self.paused_bgm,
                self.paused_volume,
                self.paused_loop,
                fade_time=fade_time,
            )
            self.is_paused = False
            return
        else:
            pygame.mixer.music.unpause()
        
        # フェードイン
        await asyncio.to_thread(self._fade_volume, self.paused_volume, fade_time)
        self.is_paused = False
        
        if self.debug:
            print(f"BGM非同期フェードイン再開: {fade_time}秒, 目標音量: {self.paused_volume}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        self._stop_sequence()
        # フェード処理を停止
        self._stop_fade()
        
        # ExecutorPoolをシャットダウン
        self.executor.shutdown(wait=False)
        
        if self.debug:
            print("BGMManager: リソースクリーンアップ完了")
