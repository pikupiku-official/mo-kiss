import io
from collections import OrderedDict
from contextlib import redirect_stdout

from core.services.image_manager import ImageManager


def test_get_image_debug_logs_request_cache_hit_and_load(monkeypatch):
    manager = ImageManager(debug=True)
    manager.image_paths = {"eye": {"EYE01": "eye01.png"}}
    cache_key = "eye01.png_original"
    manager.image_cache = OrderedDict([(cache_key, object())])

    output = io.StringIO()
    with redirect_stdout(output):
        assert manager.get_image("eye", "EYE01") is not None

    cache_log = output.getvalue()
    assert "[IMG_REQUEST] 要求: eye/EYE01" in cache_log
    assert "[IMG_CACHE_HIT] ヒット: eye/EYE01" in cache_log
    assert "[IMG_LOAD]" not in cache_log

    manager.image_cache.clear()
    monkeypatch.setattr(
        manager,
        "_load_image_immediately",
        lambda filepath, size, key: object(),
    )

    output = io.StringIO()
    with redirect_stdout(output):
        assert manager.get_image("eye", "EYE01") is not None

    load_log = output.getvalue()
    assert "[IMG_REQUEST] 要求: eye/EYE01" in load_log
    assert "[IMG_LOAD] ロード: eye/EYE01" in load_log
    assert "[IMG_CACHE_HIT]" not in load_log


def test_get_image_does_not_trace_when_debug_is_disabled(monkeypatch):
    manager = ImageManager(debug=False)
    manager.image_paths = {"eye": {"EYE01": "eye01.png"}}
    monkeypatch.setattr(
        manager,
        "_load_image_immediately",
        lambda filepath, size, key: object(),
    )

    output = io.StringIO()
    with redirect_stdout(output):
        assert manager.get_image("eye", "EYE01") is not None

    assert output.getvalue() == ""
