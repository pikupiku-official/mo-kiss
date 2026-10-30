"""Responsive PV playback: existing video decoder plus cached PCM audio."""

from pathlib import Path
import shutil
import subprocess

import pygame

from core.path_utils import get_font_path, get_project_root
from core.runtime.subsystem_base import SubsystemBase
from core.services.settings_manager import get_settings_manager
from dialogue.movie_manager import MovieManager
from demo.screens import is_activity


class PVScreen(SubsystemBase):
    def __init__(self, screen, filename, cache_dir, *, attract=False):
        super().__init__(screen)
        self.path = Path(get_project_root(), "movies", filename)
        self.audio_path = Path(cache_dir, filename + ".wav")
        self.attract = attract
        self.movie = MovieManager(screen)
        self.process = None
        self.channel = None
        self.sound = None
        self.canvas = None
        self.started = False
        self.finished = False
        self.error = ""
        self.font = pygame.font.Font(get_font_path("MPLUS1p-Medium.ttf"), 28)

    def on_enter(self):
        pygame.mixer.music.stop()
        pygame.mixer.stop()
        self.prepared_at = pygame.time.get_ticks()
        if not self.path.is_file():
            self.error = f"映像が見つかりません: movies/{self.path.name}"
            return
        if self.audio_path.is_file():
            self._start()
            return
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            self.error = "PV音声の再生にはffmpegが必要です"
            return
        try:
            self.process = subprocess.Popen(
                [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                 "-i", str(self.path), "-vn", "-ac", "2", "-ar", "44100",
                 "-c:a", "pcm_s16le", str(self.audio_path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except OSError as exc:
            self.error = f"PV音声を準備できません: {exc}"

    def _start(self):
        try:
            self.sound = pygame.mixer.Sound(str(self.audio_path))
            if not self.movie.show({"file": self.path.name, "loop": False, "mode": "opaque"}):
                raise RuntimeError(self.movie.state.get("error") or "動画を開けません")
            settings = get_settings_manager()
            self.sound.set_volume(settings.get("master_volume") * settings.get("music_volume"))
            self.channel = self.sound.play()
            if self.channel is None:
                raise RuntimeError("音声チャンネルを確保できません")
            self.started = True
        except (OSError, RuntimeError, pygame.error) as exc:
            self.movie.stop()
            self.error = f"PV再生エラー: {exc}"

    def handle_events(self, events=None):
        events = events or []
        if any(e.type == pygame.QUIT for e in events):
            return "quit"
        if self.attract and any(is_activity(e) for e in events):
            return "demo_title"
        if any(e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE for e in events):
            return "demo_title"
        if self.error and any(
            e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_SPACE)
            for e in events
        ):
            return "demo_title"
        return "demo_title" if self.finished else None

    def update(self):
        if self.process is not None and not self.started and not self.error:
            result = self.process.poll()
            if result is not None:
                _, errors = self.process.communicate()
                self.process = None
                if result:
                    self.audio_path.unlink(missing_ok=True)
                    print(f"[PV] {errors.decode('utf-8', errors='replace')}")
                    self.error = "PV音声を準備できません（映像ファイルを確認してください）"
                else:
                    self._start()
            elif pygame.time.get_ticks() - self.prepared_at > 60_000:
                self.error = "PV音声の準備がタイムアウトしました"
        if self.started:
            self.movie.update()
            error = self.movie.state.get("error")
            if error:
                self.error = f"PV再生エラー: {error}"
                if self.channel is not None:
                    self.channel.stop()
                self.movie.stop()
                self.started = False
            else:
                self.finished = bool(self.movie.state.get("ended"))

    def render(self):
        self.screen.fill((0, 0, 0))
        frame = self.movie.current_frame
        if self.started and frame is not None:
            height, width = frame.shape[:2]
            scale = min(self.screen.get_width() / width, self.screen.get_height() / height)
            size = (max(1, round(width * scale)), max(1, round(height * scale)))
            if self.canvas is None or self.canvas.get_size() != size:
                self.canvas = pygame.Surface(size)
            self.canvas.fill((0, 0, 0))
            self.movie.screen = self.canvas
            self.movie.render()
            self.screen.blit(self.canvas, self.canvas.get_rect(center=self.screen.get_rect().center))
        elif not self.started:
            label = self.font.render(self.error or "映像を準備しています…", True, (255, 255, 255))
            self.screen.blit(label, label.get_rect(center=self.screen.get_rect().center))
        hint = "操作するとタイトルに戻ります" if self.attract else "スキップ：ESCキー"
        label = self.font.render(hint, True, (255, 255, 255))
        box = label.get_rect(bottomright=(self.screen.get_width() - 28, self.screen.get_height() - 24))
        pygame.draw.rect(self.screen, (0, 0, 0), box.inflate(16, 10))
        self.screen.blit(label, box)

    def cleanup(self):
        if self.process is not None:
            if self.process.poll() is None:
                self.process.kill()
            self.process.communicate()
            self.process = None
            self.audio_path.unlink(missing_ok=True)
        if self.channel is not None:
            self.channel.stop()
        self.movie.stop()
