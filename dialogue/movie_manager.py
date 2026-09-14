"""KS movie overlay playback for the pygame runtime.

Movie overlays are intentionally kept separate from the background and CG
managers: they are a continuously playing layer and do not replace the
current scene.  OpenCV is optional at import time so existing projects can
still start when the movie dependency is not installed.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
from typing import Any, Dict, Optional

import pygame


MOVIE_DEFAULT_OPACITY = 1.0
MOVIE_DEFAULT_FADE_SECONDS = 0.0
MOVIE_DEFAULT_SPEED = 1.0


def _number(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed == parsed else default


def _boolean(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def _fade_seconds(params: Dict[str, Any], key: str = "fade") -> float:
    value = params.get(key)
    if value is None and key == "fade":
        value = params.get("time")
    return max(0.0, _number(value, MOVIE_DEFAULT_FADE_SECONDS))


class MovieManager:
    """Decode and draw one transparent movie overlay at a time."""

    def __init__(self, screen: pygame.Surface, project_root: Optional[str] = None):
        self.screen = screen
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.capture = None
        self.cv2 = None
        self.decode_backend = None
        self.current_frame = None
        self.frame_duration_ms = 1000.0 / 30.0
        self.next_frame_at_ms = 0.0
        self.frame_index = 0
        self.started_at_ms = 0
        self._ffmpeg_process = None
        self._ffmpeg_thread = None
        self._ffmpeg_stop = threading.Event()
        self._ffmpeg_lock = threading.Lock()
        self._ffmpeg_latest_frame = None
        self._ffmpeg_latest_seq = 0
        self._ffmpeg_consumed_seq = 0
        self._ffmpeg_frame_shape = None
        self.state: Dict[str, Any] = {
            "file": None,
            "loop": True,
            "opacity": MOVIE_DEFAULT_OPACITY,
            "mode": "alpha",
            "x": 0.5,
            "y": 0.5,
            "zoom": 1.0,
            "fit": "stretch",
            "speed": MOVIE_DEFAULT_SPEED,
            "alpha": 0.0,
            "target_alpha": 0.0,
            "fade_started_at_ms": 0,
            "fade_from_alpha": 0.0,
            "fade_duration_ms": 0,
            "ended": False,
            "error": None,
            "backend": None,
        }

    @property
    def is_active(self) -> bool:
        return (
            self.capture is not None
            or self._ffmpeg_process is not None
            or self.state.get("fade_duration_ms", 0) > 0
        )

    def _resolve_path(self, requested: Any) -> Optional[str]:
        value = str(requested or "").strip().replace("\\", "/")
        if not value or value.startswith("/") or ".." in value.split("/"):
            return None
        movies_root = os.path.abspath(os.path.join(self.project_root, "movies"))
        candidates = [os.path.join(movies_root, value)]
        if not os.path.splitext(value)[1]:
            candidates.extend(os.path.join(movies_root, value + ext) for ext in (".mov", ".webm", ".mp4"))
        for candidate in candidates:
            absolute = os.path.abspath(candidate)
            if os.path.commonpath((movies_root, absolute)) == movies_root and os.path.isfile(absolute):
                return absolute
        return None

    def _set_fade(self, target: float, seconds: float) -> None:
        now = pygame.time.get_ticks()
        self.state["fade_from_alpha"] = float(self.state.get("alpha", 0.0))
        self.state["target_alpha"] = max(0.0, min(1.0, target))
        self.state["fade_started_at_ms"] = now
        self.state["fade_duration_ms"] = max(0, round(seconds * 1000))
        if not self.state["fade_duration_ms"]:
            self.state["alpha"] = self.state["target_alpha"]

    def _open_capture(self, path: str, start_seconds: float) -> bool:
        try:
            import cv2
        except ImportError:
            self.state["error"] = "OpenCV is unavailable; trying FFmpeg fallback."
            return self._open_ffmpeg(path, start_seconds)

        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            capture.release()
            self.state["error"] = f"OpenCV could not open movie: {path}; trying FFmpeg fallback."
            return self._open_ffmpeg(path, start_seconds)
        fps = capture.get(cv2.CAP_PROP_FPS)
        if fps and fps > 0:
            self.frame_duration_ms = 1000.0 / fps
        start_frame = max(0, round(start_seconds * fps)) if fps and fps > 0 else 0
        if start_frame:
            capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        success, frame = capture.read()
        if not success or frame is None:
            capture.release()
            self.state["error"] = f"Could not read first movie frame: {path}"
            return False
        self.cv2 = cv2
        self.capture = capture
        self.decode_backend = "opencv"
        self.current_frame = frame
        self.frame_index = start_frame
        now = pygame.time.get_ticks()
        self.started_at_ms = now
        self.next_frame_at_ms = now + self.frame_duration_ms
        self.state["backend"] = "opencv"
        print(f"[MOVIE] opened file={os.path.basename(path)} backend=opencv fps={fps:.3f}")
        return True

    @staticmethod
    def _parse_frame_rate(value: str) -> float:
        try:
            if "/" in value:
                numerator, denominator = value.split("/", 1)
                return float(numerator) / float(denominator)
            return float(value)
        except (TypeError, ValueError, ZeroDivisionError):
            return 30.0

    def _open_ffmpeg(self, path: str, start_seconds: float) -> bool:
        """Use the system FFmpeg when OpenCV cannot decode the movie.

        FFmpeg emits realtime RGB frames on a background reader thread. The
        main Pygame loop only consumes the newest complete frame, so a slow
        decoder cannot block input or dialogue progression.
        """
        ffmpeg = shutil.which("ffmpeg")
        ffprobe = shutil.which("ffprobe")
        if not ffmpeg or not ffprobe:
            self.state["error"] = (
                "Movie playback requires OpenCV or ffmpeg/ffprobe on PATH."
            )
            return False
        try:
            probe = subprocess.run(
                [
                    ffprobe,
                    "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate",
                    "-of", "csv=p=0:s=,",
                    path,
                ],
                capture_output=True,
                text=True,
                check=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            fields = probe.stdout.strip().split(",")
            if len(fields) != 3:
                raise RuntimeError(f"unexpected ffprobe output: {probe.stdout!r}")
            width, height = int(fields[0]), int(fields[1])
            fps = self._parse_frame_rate(fields[2])
            if width <= 0 or height <= 0 or fps <= 0:
                raise RuntimeError("invalid movie dimensions or frame rate")
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
            self.state["error"] = f"FFmpeg probe failed: {exc}"
            return False

        self._ffmpeg_stop.clear()
        self._ffmpeg_latest_frame = None
        self._ffmpeg_latest_seq = 0
        self._ffmpeg_consumed_seq = 0
        self._ffmpeg_frame_shape = (height, width, 3)
        self.frame_duration_ms = 1000.0 / fps
        self.decode_backend = "ffmpeg"
        self.state["backend"] = "ffmpeg"
        self.state["error"] = None
        try:
            self._start_ffmpeg_process(path, max(0.0, start_seconds))
        except (OSError, subprocess.SubprocessError) as exc:
            self.decode_backend = None
            self.state["backend"] = None
            self.state["error"] = f"FFmpeg process failed: {exc}"
            return False
        self._ffmpeg_thread = threading.Thread(
            target=self._read_ffmpeg_frames,
            args=(path,),
            name="ks-movie-reader",
            daemon=True,
        )
        self._ffmpeg_thread.start()
        print(
            f"[MOVIE] opened file={os.path.basename(path)} "
            f"backend=ffmpeg size={width}x{height} fps={fps:.3f}"
        )
        return True

    def _start_ffmpeg_process(self, path: str, start_seconds: float) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if not ffmpeg:
            raise OSError("ffmpeg is not on PATH")
        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin"]
        if start_seconds > 0:
            command.extend(["-ss", f"{start_seconds:.3f}"])
        command.extend(
            [
                "-re",
                "-i", path,
                "-an", "-sn", "-dn",
                "-f", "rawvideo",
                "-pix_fmt", "rgb24",
                "-vsync", "0",
                "pipe:1",
            ]
        )
        self._ffmpeg_process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

    def _read_ffmpeg_frames(self, path: str) -> None:
        frame_size = 0
        if self._ffmpeg_frame_shape:
            height, width, channels = self._ffmpeg_frame_shape
            frame_size = height * width * channels
        try:
            while not self._ffmpeg_stop.is_set() and frame_size:
                process = self._ffmpeg_process
                if process is None or process.stdout is None:
                    break
                data = process.stdout.read(frame_size)
                if len(data) == frame_size:
                    with self._ffmpeg_lock:
                        self._ffmpeg_latest_frame = data
                        self._ffmpeg_latest_seq += 1
                    continue
                if self._ffmpeg_stop.is_set():
                    break
                if self.state.get("loop"):
                    process.wait(timeout=1.0)
                    process.stdout.close()
                    process = None
                    self._ffmpeg_process = None
                    self._start_ffmpeg_process(path, 0.0)
                    continue
                self.state["ended"] = True
                break
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            if not self._ffmpeg_stop.is_set():
                self.state["error"] = f"FFmpeg frame read failed: {exc}"
                self.state["ended"] = True

    def _update_ffmpeg_frame(self) -> None:
        if self.decode_backend != "ffmpeg" or not self._ffmpeg_frame_shape:
            return
        with self._ffmpeg_lock:
            sequence = self._ffmpeg_latest_seq
            data = self._ffmpeg_latest_frame
        if data is None or sequence == self._ffmpeg_consumed_seq:
            return
        import numpy as np

        self.current_frame = np.frombuffer(data, dtype=np.uint8).reshape(
            self._ffmpeg_frame_shape
        )
        self._ffmpeg_consumed_seq = sequence

    def show(self, params: Dict[str, Any]) -> bool:
        """Start or replace the overlay without stopping dialogue progression."""
        params = params or {}
        path = self._resolve_path(params.get("file") or params.get("storage"))
        self.stop()
        self.state.update(
            {
                "file": path,
                "loop": _boolean(params.get("loop"), True),
                "opacity": max(0.0, min(1.0, _number(params.get("opacity"), MOVIE_DEFAULT_OPACITY))),
                "mode": str(params.get("mode") or "alpha").strip().lower(),
                "x": max(0.0, min(1.0, _number(params.get("x"), 0.5))),
                "y": max(0.0, min(1.0, _number(params.get("y"), 0.5))),
                "zoom": max(0.1, _number(params.get("zoom"), 1.0)),
                "fit": str(params.get("fit") or "stretch").strip().lower(),
                "speed": max(0.05, _number(params.get("speed"), MOVIE_DEFAULT_SPEED)),
                "alpha": 0.0,
                "target_alpha": 1.0,
                "ended": False,
                "error": None if path else "Movie file not found in movies/."
            }
        )
        print(
            f"[MOVIE] show requested file={params.get('file') or params.get('storage')} "
            f"resolved={path or '(missing)'}"
        )
        if not path or not self._open_capture(path, max(0.0, _number(params.get("start"), 0.0))):
            return False
        fade_in = _fade_seconds(params, "fade_in")
        if "fade_in" not in params:
            fade_in = _fade_seconds(params, "fade")
        self._set_fade(1.0, fade_in)
        return True

    def hide(self, params: Optional[Dict[str, Any]] = None) -> None:
        params = params or {}
        fade_out = _fade_seconds(params, "fade_out")
        if "fade_out" not in params:
            fade_out = _fade_seconds(params, "fade")
        self._set_fade(0.0, fade_out)
        if not self.state["fade_duration_ms"]:
            self.stop()

    def stop(self) -> None:
        if self.capture is not None:
            self.capture.release()
        self._ffmpeg_stop.set()
        process = self._ffmpeg_process
        self._ffmpeg_process = None
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=0.5)
            except (OSError, subprocess.SubprocessError):
                try:
                    process.kill()
                except OSError:
                    pass
        thread = self._ffmpeg_thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.5)
        self._ffmpeg_thread = None
        self.capture = None
        self.current_frame = None
        self.cv2 = None
        self.decode_backend = None
        self._ffmpeg_latest_frame = None
        self.state.update({"file": None, "alpha": 0.0, "target_alpha": 0.0, "fade_duration_ms": 0, "ended": False, "backend": None})

    def update(self) -> None:
        now = pygame.time.get_ticks()
        duration = int(self.state.get("fade_duration_ms", 0))
        if duration:
            progress = max(0.0, min(1.0, (now - self.state["fade_started_at_ms"]) / duration))
            start = self.state.get("fade_from_alpha", 0.0)
            target = self.state.get("target_alpha", 0.0)
            self.state["alpha"] = start + (target - start) * progress
            if progress >= 1.0:
                self.state["fade_duration_ms"] = 0
                if target <= 0.0:
                    self.stop()
                    return
        if self.capture is None or self.current_frame is None or self.state.get("ended"):
            self._update_ffmpeg_frame()
            if self.decode_backend == "ffmpeg":
                return
        if self.capture is None or self.current_frame is None or self.state.get("ended"):
            return

        speed = max(0.05, float(self.state.get("speed", 1.0)))
        frame_duration = self.frame_duration_ms / speed
        frames_read = 0
        while now >= self.next_frame_at_ms and frames_read < 5:
            success, frame = self.capture.read()
            if not success or frame is None:
                if not self.state.get("loop"):
                    self.state["ended"] = True
                    return
                self.capture.set(self.cv2.CAP_PROP_POS_FRAMES, 0)
                self.frame_index = 0
                success, frame = self.capture.read()
                if not success or frame is None:
                    self.state["ended"] = True
                    return
            self.current_frame = frame
            self.frame_index += 1
            self.next_frame_at_ms += frame_duration
            frames_read += 1

    def render(self) -> None:
        if self.current_frame is None:
            return
        effective_alpha = max(0.0, min(1.0, float(self.state.get("alpha", 0.0))))
        effective_alpha *= max(0.0, min(1.0, float(self.state.get("opacity", 1.0))))
        if effective_alpha <= 0.0:
            return
        if self.decode_backend == "opencv":
            rgb = self.cv2.cvtColor(self.current_frame, self.cv2.COLOR_BGR2RGB)
        elif self.decode_backend == "ffmpeg":
            rgb = self.current_frame
        else:
            return
        mode = self.state.get("mode", "alpha")
        if mode in {"alpha", "luma", "key", "chroma"}:
            # OpenCV's VideoCapture exposes ProRes 4444 as BGR on many builds.
            # Rain overlays are white-on-black, so use brightness as a portable
            # alpha fallback; black background pixels become fully transparent.
            import numpy as np

            alpha = rgb.max(axis=2).astype(np.float32)
            rgba = np.dstack((rgb, (alpha * effective_alpha).clip(0, 255).astype(np.uint8)))
        else:
            import numpy as np

            rgba = np.dstack(
                (rgb, np.full(rgb.shape[:2], round(255 * effective_alpha), dtype=np.uint8))
            )
        height, width = rgba.shape[:2]
        # ``frombuffer`` borrows the temporary bytes object.  The next
        # transform/blit can then observe a released or reused buffer on
        # some SDL builds, which presents as a partially updated movie
        # surface.  Copy the frame into an owned Pygame surface instead.
        image_from_bytes = getattr(pygame.image, "frombytes", None)
        if image_from_bytes is None:
            image_from_bytes = pygame.image.fromstring
        surface = image_from_bytes(rgba.tobytes(), (width, height), "RGBA")
        screen = self.screen
        screen_width, screen_height = screen.get_size()
        zoom = max(0.1, float(self.state.get("zoom", 1.0)))
        target_size = (max(1, round(screen_width * zoom)), max(1, round(screen_height * zoom)))
        if self.state.get("fit") == "cover":
            source_width, source_height = surface.get_size()
            scale = max(target_size[0] / source_width, target_size[1] / source_height)
            cover_size = (
                max(target_size[0], round(source_width * scale)),
                max(target_size[1], round(source_height * scale)),
            )
            if surface.get_size() != cover_size:
                surface = pygame.transform.smoothscale(surface, cover_size)
            crop_x = max(0, (surface.get_width() - target_size[0]) // 2)
            crop_y = max(0, (surface.get_height() - target_size[1]) // 2)
            surface = surface.subsurface(
                pygame.Rect(crop_x, crop_y, target_size[0], target_size[1])
            ).copy()
        elif surface.get_size() != target_size:
            surface = pygame.transform.smoothscale(surface, target_size)
        # A cover movie at the default zoom is a viewport layer, not a
        # positioned sprite.  Applying normalized x/y to a surface that is
        # already exactly the viewport size can move half of the layer off
        # screen (for example x=1 -> destination x=720).  Keep positioning
        # available for zoomed/non-fullscreen movies, but make rain overlays
        # deterministic and origin-anchored.
        if self.state.get("fit") == "cover" and abs(zoom - 1.0) < 1e-6:
            destination = (0, 0)
        else:
            center_x = screen_width * float(self.state.get("x", 0.5))
            center_y = screen_height * float(self.state.get("y", 0.5))
            destination = (
                round(center_x - target_size[0] / 2),
                round(center_y - target_size[1] / 2),
            )

        from dialogue.render_monitor import trace_event
        trace_event(
            "movie_render_geometry",
            ticks=pygame.time.get_ticks(),
            file=os.path.basename(str(self.state.get("file") or "")),
            source_surface=list(surface.get_size()),
            target_surface=[screen_width, screen_height],
            target_size=list(target_size),
            destination=list(destination),
            x=float(self.state.get("x", 0.5)),
            y=float(self.state.get("y", 0.5)),
            zoom=zoom,
            fit=self.state.get("fit"),
            clip=list(screen.get_clip()),
        )

        # A previous UI/overlay draw can leave a smaller SDL clip rectangle on
        # the shared virtual surface.  That makes a full-screen movie appear
        # to occupy only one band of the screen even though its frame and
        # destination rectangle are correct.  Movie overlays own the whole
        # viewport, so temporarily restore the caller's clip after the blit.
        old_clip = screen.get_clip()
        try:
            screen.set_clip(None)
            screen.blit(surface, destination)
        finally:
            screen.set_clip(old_clip)


def get_movie_manager(game_state: Dict[str, Any]) -> MovieManager:
    manager = game_state.get("movie_manager")
    if manager is None:
        manager = MovieManager(game_state["screen"])
        game_state["movie_manager"] = manager
    return manager


def update_movie(game_state: Dict[str, Any]) -> None:
    manager = game_state.get("movie_manager")
    if manager is not None:
        manager.update()


def draw_movie(game_state: Dict[str, Any]) -> None:
    manager = game_state.get("movie_manager")
    if manager is not None:
        # DialogueSubsystem swaps game_state['screen'] to the fixed virtual
        # surface.  Rebind on every draw so a manager created before that
        # swap, or reused by a preview runtime, cannot draw into a stale
        # window/subsurface with a different height.
        target = game_state.get("screen")
        if target is not None and manager.screen is not target:
            manager.screen = target
        manager.render()
