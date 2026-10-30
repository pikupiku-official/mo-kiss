"""Exercise actual FFmpeg decoding even on machines with OpenCV installed."""

import shutil
import subprocess
import sys
import time

import numpy as np
import pygame
import pytest

from dialogue.movie_manager import MovieManager


@pytest.fixture
def ffmpeg_movie(tmp_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg or not shutil.which("ffprobe"):
        pytest.skip("ffmpeg/ffprobe are not installed")
    movies = tmp_path / "movies"
    movies.mkdir()
    path = movies / "sample.mp4"
    subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
         "-f", "lavfi", "-i", "color=c=red:s=320x180:r=30:d=1",
         "-c:v", "mpeg4", str(path)],
        check=True, timeout=15,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    return tmp_path


def test_ffmpeg_fallback_displays_frames_before_natural_end(ffmpeg_movie, monkeypatch):
    monkeypatch.setitem(sys.modules, "cv2", None)
    movie = MovieManager(pygame.Surface((64, 48)), str(ffmpeg_movie))
    try:
        assert movie.show({"file": "sample.mp4", "loop": False, "mode": "opaque"})
        deadline = time.monotonic() + 10
        while movie.current_frame is None and not movie.state["ended"] and time.monotonic() < deadline:
            movie.update()
            time.sleep(0.01)
        assert movie.state["backend"] == "ffmpeg"
        assert movie.current_frame is not None, movie.state
        assert movie.current_frame.dtype == np.uint8
        assert not movie.state["ended"]
        movie.render()
        assert movie.screen.get_at((32, 24)).r > 200
        first_sequence = movie._ffmpeg_consumed_seq
        while not movie.state["ended"] and time.monotonic() < deadline:
            movie.update()
            time.sleep(0.01)
        assert movie.state["ended"]
        assert not movie.state["error"]
        assert movie._ffmpeg_consumed_seq > first_sequence
    finally:
        movie.stop()


@pytest.mark.parametrize("loop", [False, True])
@pytest.mark.parametrize("exit_code", [0, 7])
def test_ffmpeg_exit_without_frames_reports_failure(ffmpeg_movie, monkeypatch, loop, exit_code):
    movie = MovieManager(pygame.Surface((64, 48)), str(ffmpeg_movie))
    starts = []

    def fail_decoder(path, start_seconds):
        starts.append(path)
        movie._ffmpeg_process = subprocess.Popen(
            [sys.executable, "-c", f"raise SystemExit({exit_code})"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )

    monkeypatch.setitem(sys.modules, "cv2", None)
    monkeypatch.setattr(movie, "_start_ffmpeg_process", fail_decoder)
    try:
        assert movie.show({"file": "sample.mp4", "loop": loop})
        deadline = time.monotonic() + 10
        while not movie.state["ended"] and time.monotonic() < deadline:
            movie.update()
            time.sleep(0.01)
        assert movie.state["ended"]
        assert f"exit code {exit_code}" in movie.state["error"]
        assert movie.current_frame is None
        assert len(starts) == 1
    finally:
        movie.stop()
