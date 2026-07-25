"""E002.ks and E006.ksを、タイトル画面を挟んで交互に再生する。

遷移:
    タイトル -> E002 -> タイトル -> E006 -> タイトル -> ...
    タイトルで20秒間無操作 -> demo.mp4 -> タイトル

この専用プレイヤーでは、セーブ、ゲーム内時間の進行、イベント完了記録を
行わない。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

import pygame

from core import config
from core.loading_screen import hide_loading, show_loading
from core.subsystem_base import SubsystemBase
from core.title_subsystem import TitleSubsystem
from dialogue.dialogue_subsystem import DialogueSubsystem
from main import GameApplication


PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
EVENT_FILES = ("events/E002.ks", "events/E006.ks")
DEMO_VIDEO_FILE = os.path.join(PROJECT_ROOT, "movies", "demo.mp4")
TITLE_IDLE_TIMEOUT_MS = 10_000
KS_AUDIO_VOLUME_SCALE = 0.5


def _normalize_ks_volume(volume, default=0.5):
    """KSの0～1／0～10／0～100表記を0～1へ揃えて減衰する。"""
    try:
        normalized = float(volume)
    except (TypeError, ValueError):
        normalized = default

    if normalized <= 0:
        return 0.0
    if normalized > 10:
        normalized /= 100.0
    elif normalized > 1:
        normalized /= 10.0

    normalized = max(0.0, min(1.0, normalized))
    return normalized * KS_AUDIO_VOLUME_SCALE


def _apply_ks_audio_volume(dialogue):
    """専用プレイヤー内のKS由来BGM・SEへマスター音量を適用する。"""
    game_state = dialogue.game_state
    bgm_manager = game_state.get("bgm_manager")
    se_manager = game_state.get("se_manager")

    if bgm_manager:
        original_play_bgm = bgm_manager.play_bgm

        def play_bgm(filename, volume=0.5, loop=True):
            return original_play_bgm(
                filename,
                _normalize_ks_volume(volume),
                loop,
            )

        bgm_manager.play_bgm = play_bgm

    if se_manager:
        original_play_se = se_manager.play_se

        def play_se(filename, volume=0.5, frequency=1):
            return original_play_se(
                filename,
                _normalize_ks_volume(volume),
                frequency,
            )

        se_manager.play_se = play_se


class TimedTitleSubsystem(TitleSubsystem):
    """20秒間入力がなければデモ動画への遷移を要求するタイトル画面。"""

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)
        self._idle_started_at = pygame.time.get_ticks()

    def on_enter(self):
        self.reset_idle_timer()
        super().on_enter()

    def reset_idle_timer(self):
        self._idle_started_at = pygame.time.get_ticks()

    def handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()

        # TitleSubsystemはKEYDOWNとMOUSEBUTTONDOWNだけを入力として扱う。
        # MOUSEMOTIONは無視されるため、マウス移動ではタイマーを解除しない。
        result = super().handle_events(events)
        if result:
            return result

        elapsed = pygame.time.get_ticks() - self._idle_started_at
        if elapsed >= TITLE_IDLE_TIMEOUT_MS:
            return "play_demo"
        return None


class DemoVideoSubsystem(SubsystemBase):
    """OpenCVで映像を描画し、ffplayで動画音声を再生する。"""

    def __init__(self, screen: pygame.Surface, video_file: str):
        super().__init__(screen)
        self.video_file = video_file
        self.capture = None
        self.audio_process = None
        self.current_frame = None
        self.frame_duration_ms = 1000.0 / 30.0
        self.next_frame_at_ms = 0.0
        self.started_at_ms = 0
        self.ended = False
        self.error_message = None
        self._cv2 = None
        self._prepare_video()

    @property
    def is_ready(self):
        return self.capture is not None and self.current_frame is not None

    def _prepare_video(self):
        if not os.path.isfile(self.video_file):
            self.error_message = f"動画ファイルがありません: {self.video_file}"
            return

        try:
            import cv2
        except ImportError:
            self.error_message = "動画再生に必要なOpenCVがインストールされていません"
            return

        capture = cv2.VideoCapture(self.video_file)
        if not capture.isOpened():
            capture.release()
            self.error_message = f"動画ファイルを開けません: {self.video_file}"
            return

        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps and fps > 0:
            self.frame_duration_ms = 1000.0 / fps

        success, frame = capture.read()
        if not success or frame is None:
            capture.release()
            self.error_message = f"動画の最初のフレームを読み込めません: {self.video_file}"
            return

        self._cv2 = cv2
        self.capture = capture
        self.current_frame = frame
        self.next_frame_at_ms = self.frame_duration_ms

    def on_enter(self):
        self.started_at_ms = pygame.time.get_ticks()
        self._start_audio()

    def _start_audio(self):
        ffplay_path = shutil.which("ffplay")
        if not ffplay_path:
            print("[DEMO] ffplayがないため、動画音声を再生できません")
            return

        creation_flags = 0
        if os.name == "nt":
            creation_flags = subprocess.CREATE_NO_WINDOW

        try:
            self.audio_process = subprocess.Popen(
                [
                    ffplay_path,
                    "-nodisp",
                    "-autoexit",
                    "-loglevel",
                    "quiet",
                    "-vn",
                    self.video_file,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creation_flags,
            )
        except OSError as exc:
            print(f"[DEMO] 動画音声を開始できません: {exc}")
            self.audio_process = None

    def handle_events(self, events=None):
        if events is None:
            events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                return "quit"
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return "video_ended"

        if self.ended:
            return "video_ended"
        return None

    def update(self):
        if self.ended or not self.capture:
            return

        elapsed_ms = pygame.time.get_ticks() - self.started_at_ms
        frames_read = 0

        # 再生時刻に追いつくまでフレームを進める。重いフレームで大幅に
        # 遅れた場合はシークし、音声とのずれが広がらないようにする。
        while elapsed_ms >= self.next_frame_at_ms and frames_read < 5:
            success, frame = self.capture.read()
            if not success or frame is None:
                self.ended = True
                return
            self.current_frame = frame
            self.next_frame_at_ms += self.frame_duration_ms
            frames_read += 1

        if elapsed_ms >= self.next_frame_at_ms:
            self.capture.set(self._cv2.CAP_PROP_POS_MSEC, elapsed_ms)
            success, frame = self.capture.read()
            if not success or frame is None:
                self.ended = True
                return
            self.current_frame = frame
            self.next_frame_at_ms = elapsed_ms + self.frame_duration_ms

    def render(self):
        self.screen.fill((0, 0, 0))
        if self.current_frame is None:
            return

        rgb_frame = self._cv2.cvtColor(
            self.current_frame,
            self._cv2.COLOR_BGR2RGB,
        )
        frame_height, frame_width = rgb_frame.shape[:2]
        frame_surface = pygame.image.frombuffer(
            rgb_frame.tobytes(),
            (frame_width, frame_height),
            "RGB",
        )

        screen_width, screen_height = self.screen.get_size()
        # 動画の縦幅を画面いっぱいに合わせる。横方向にはみ出した部分は、
        # 画面中央を基準にクリッピングされる。
        scale = screen_height / frame_height
        scaled_size = (
            max(1, round(frame_width * scale)),
            screen_height,
        )
        if scaled_size != (frame_width, frame_height):
            frame_surface = pygame.transform.smoothscale(
                frame_surface,
                scaled_size,
            )

        x = (screen_width - scaled_size[0]) // 2
        y = 0
        self.screen.blit(frame_surface, (x, y))

    def cleanup(self):
        if self.capture:
            self.capture.release()
            self.capture = None

        if self.audio_process and self.audio_process.poll() is None:
            self.audio_process.terminate()
            try:
                self.audio_process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.audio_process.kill()
                self.audio_process.wait(timeout=0.5)
        self.audio_process = None


class NoSaveDialogueSubsystem(DialogueSubsystem):
    """会話の進行位置をファイルへ保存しないDialogueSubsystem。"""

    def _save_dialogue_state(self, paragraph_index: int):
        # DialogueSubsystemは通常、段落が進むたびにdialogue_state.jsonを更新する。
        # このプレイヤーでは永続状態を変更しない。
        return None


class AlternatingScenarioApplication(GameApplication):
    """タイトルを挟みながらE002とE006を交互に再生するアプリ。"""

    def __init__(self):
        super().__init__()
        self._next_event_index = 0

    def initialize(self):
        """メニューやセーブ機構を起動せず、タイトル画面だけを初期化する。"""
        try:
            pygame.init()
            pygame.mixer.init()

            self.window_surface = config.init_game()
            self.virtual_screen = pygame.Surface(
                (config.VIRTUAL_WIDTH, config.VIRTUAL_HEIGHT)
            )
            self.screen = self.virtual_screen
            self.clock = pygame.time.Clock()

            self.current_subsystem = TimedTitleSubsystem(self.screen)
            self.current_mode = "title"
            self.current_subsystem.on_enter()

            print("タイトル画面を表示しました")
            return True
        except Exception as exc:
            print(f"初期化エラー: {exc}")
            return False

    def switch_to_dialogue(self, event_file=None):
        """保存処理を持たない会話サブシステムへ切り替える。"""
        if not event_file:
            return

        from dialogue import game_manager

        print(f"シナリオを開始します: {event_file}")
        self.current_event_id = os.path.splitext(os.path.basename(event_file))[0]
        previous_ir_dump_setting = game_manager.IR_DUMP_JSON

        try:
            # 通常は会話初期化時にデバッグ用IRファイルが生成されるが、
            # このプレイヤーでは永続ファイルを一切更新しない。
            game_manager.IR_DUMP_JSON = False
            show_loading("イベントを読み込み中...", self.window_surface)
            dialogue = NoSaveDialogueSubsystem(
                self.screen,
                self.virtual_screen,
                event_file,
            )
            _apply_ks_audio_volume(dialogue)
        except Exception as exc:
            print(f"シナリオ読み込みエラー: {exc}")
            self.running = False
            return
        finally:
            game_manager.IR_DUMP_JSON = previous_ir_dump_setting
            hide_loading()

        self.switch_to(dialogue, "dialogue")

    def _handle_transition(self, result: str):
        """このプレイヤーで必要な遷移だけを処理する。"""
        if not result:
            return

        if result == "quit":
            self.running = False
            return

        if result == "go_to_menu" and self.current_mode == "title":
            self.switch_to_dialogue(EVENT_FILES[self._next_event_index])
            return

        if result == "play_demo" and self.current_mode == "title":
            demo = DemoVideoSubsystem(self.screen, DEMO_VIDEO_FILE)
            if not demo.is_ready:
                print(f"[DEMO] {demo.error_message}")
                print("[DEMO] タイトル画面を維持し、20秒タイマーをリセットします")
                demo.cleanup()
                self.current_subsystem.reset_idle_timer()
                return
            self.switch_to(demo, "video")
            return

        if result == "video_ended" and self.current_mode == "video":
            self.switch_to(TimedTitleSubsystem(self.screen), "title")
            return

        if result == "dialogue_ended" and self.current_mode == "dialogue":
            completed_event = EVENT_FILES[self._next_event_index]
            self._next_event_index = (self._next_event_index + 1) % len(EVENT_FILES)
            self.current_event_id = None
            print(
                f"{completed_event}が終了しました。"
                f"次は{EVENT_FILES[self._next_event_index]}です"
            )
            self.switch_to(TimedTitleSubsystem(self.screen), "title")
            return

        if result == "show_option":
            # OPTIONからのセーブ等を発生させないため、このプレイヤーでは無効。
            print("このプレイヤーではOPTION画面を使用しません")

    def cleanup(self):
        """永続状態を初期化・保存せず、表示と音声だけを終了する。"""
        print("プレイヤーを終了します")
        if self.current_subsystem:
            self.current_subsystem.cleanup()
        pygame.quit()


def main():
    os.chdir(PROJECT_ROOT)
    app = AlternatingScenarioApplication()
    return 0 if app.run() else 1


if __name__ == "__main__":
    sys.exit(main())
