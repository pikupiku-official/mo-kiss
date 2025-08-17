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
            self.current_volume = volume
            self.target_volume = volume
            if self.debug:
                print(f"BGMを再生開始: {filename} (loop={loop})")
            return True
            
        except Exception as e:
            if self.debug:
                print(f"BGMの再生に失敗しました: {e}")
            return False

    def stop_bgm(self):
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
        """一時停止用の音量フェード（BGMを停止せずに音量だけ下げる）"""
        self.is_fading = True
        start_volume = self.current_volume
        steps = int(fade_time * 10)  # 0.1秒間隔で更新
        volume_step = (target_volume - start_volume) / steps if steps > 0 else 0
        
        try:
            for i in range(steps):
                if not self.is_fading:
                    break
                
                self.current_volume = start_volume + (volume_step * (i + 1))
                self.current_volume = max(0.0, min(1.0, self.current_volume))
                pygame.mixer.music.set_volume(self.current_volume)
                
                if self.debug:
                    print(f"一時停止フェード中: {self.current_volume:.2f}")
                
                time.sleep(0.1)
            
            # 最終音量に設定（BGMは停止しない）
            if self.is_fading:
                self.current_volume = target_volume
                pygame.mixer.music.set_volume(self.current_volume)
                    
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