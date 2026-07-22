import pygame
import os
import threading
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

class BGMManager:
    def __init__(self, debug=False):
        self.debug = debug
        self.BGM_PATH = os.path.join("sounds", "bgms")
        self.current_bgm = None
        self.current_volume = 0.5
        self.target_volume = 0.5
        self.fade_thread = None
        self.is_fading = False
        self.is_paused = False
        self.paused_bgm = None  # 一時停止したBGMの情報を保持
        self.paused_volume = 0.5
        self.paused_loop = True
        
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

    def play_bgm(self, filename, volume=0.5, loop=True):
        print(f"[BGM_DEBUG] play_bgm要求: filename='{filename}', volume={volume}, loop={loop}")
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
                print("[BGM_DEBUG] pygame.mixer was not initialized. Auto initialized mixer.")
            except Exception as e:
                print(f"[BGM_DEBUG] pygame.mixer init error: {e}")
                return False
        try:
            # 音量の正規化
            try:
                volume = float(volume)
            except (ValueError, TypeError):
                volume = 0.5

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
            
            pygame.mixer.music.load(bgm_path)
            pygame.mixer.music.set_volume(volume)
            # ループ設定に応じて再生
            if loop:
                pygame.mixer.music.play(-1)  # ループ再生
            else:
                pygame.mixer.music.play(0)   # 一回のみ再生
            self.current_bgm = filename
            self.current_volume = volume
            self.target_volume = volume
            print(f"[BGM_DEBUG] BGM再生成功! file='{filename}', full_path='{bgm_path}', volume={volume}, loop={loop}")
            return True
            
        except Exception as e:
            print(f"[BGM_DEBUG] BGMの再生失敗: {e}")
            return False

    def stop_bgm(self):
        print(f"🔇 [BGM_DEBUG] stop_bgm呼び出し (現在再生中='{self.current_bgm}')")
        self._stop_fade()
        pygame.mixer.music.stop()
        self.current_bgm = None
        self.current_volume = 0.5
        self.target_volume = 0.5
    
    def pause_bgm(self):
        """BGMを一時停止"""
        if self.current_bgm:
            self.paused_bgm = self.current_bgm
            self.paused_volume = self.target_volume
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
                
                pygame.mixer.music.set_volume(self.current_volume)
                
                if self.debug and i % 10 == 0:  # デバッグ出力を減らす
                    print(f"フェード中: {self.current_volume:.2f} ({progress:.1%})")
                
                # より正確なタイミング
                time.sleep(step_duration)
            
            # 最終音量に設定
            if self.is_fading:
                self.current_volume = target_volume
                pygame.mixer.music.set_volume(self.current_volume)
                
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
                pygame.mixer.music.set_volume(self.current_volume)
                
                if self.debug and i % 10 == 0:
                    print(f"一時停止フェード中: {self.current_volume:.2f}")
                
                time.sleep(step_duration)
            
            # 最終音量に設定
            if self.is_fading:
                self.current_volume = target_volume
                pygame.mixer.music.set_volume(self.current_volume)
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
        self._stop_fade()
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
        pygame.mixer.music.set_volume(0.0)
        
        self.fade_thread = threading.Thread(target=self._fade_volume, args=(target_volume, fade_time))
        self.fade_thread.start()
    
    def pause_bgm_with_fade(self, fade_time=1.0):
        """BGMをフェードアウトして一時停止"""
        if not self.current_bgm:
            return
            
        # 一時停止情報を保存
        self.paused_bgm = self.current_bgm
        self.paused_volume = self.target_volume
        self.paused_loop = True  # デフォルトでループ有効
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
            self.play_bgm(self.paused_bgm, 0.0, self.paused_loop)  # 音量0で開始
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
            "Mok1_Lap1": "Mok1_Lap1.mp3",
            "Mok1_Lap2": "Mok1_Lap2.mp3",
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
        pygame.mixer.music.set_volume(0.0)
        
        await asyncio.to_thread(self._fade_volume, target_volume, fade_time)
    
    async def pause_bgm_with_fade_async(self, fade_time=1.0):
        """BGMを非同期でフェードアウトして一時停止"""
        if not self.current_bgm:
            return
            
        # 一時停止情報を保存
        self.paused_bgm = self.current_bgm
        self.paused_volume = self.target_volume
        self.paused_loop = True
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
            self.play_bgm(self.paused_bgm, 0.0, self.paused_loop)
        else:
            pygame.mixer.music.unpause()
        
        # フェードイン
        await asyncio.to_thread(self._fade_volume, self.paused_volume, fade_time)
        self.is_paused = False
        
        if self.debug:
            print(f"BGM非同期フェードイン再開: {fade_time}秒, 目標音量: {self.paused_volume}")
    
    def cleanup(self):
        """リソースのクリーンアップ"""
        # フェード処理を停止
        self._stop_fade()
        
        # ExecutorPoolをシャットダウン
        self.executor.shutdown(wait=False)
        
        if self.debug:
            print("BGMManager: リソースクリーンアップ完了")