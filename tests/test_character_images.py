import gc
import weakref

import pygame
import pytest

from dialogue.character_images import CharacterImages, image_pixels, prepare_character_images
from core.services.image_manager import ImageManager


class Images:
    def __init__(self):
        self.requests = []
        self.last_source = None

    def get_image(self, category, key):
        self.requests.append((category, key))
        image = pygame.Surface((8, 1080), pygame.SRCALPHA)
        image.fill((255, 0, 0, 255))
        self.last_source = weakref.ref(image)
        return image


def test_resized_cache_retains_pixels_without_pinning_native_images():
    source = Images()
    cache = CharacterImages(source)
    image = cache.get('eye', 'expression', 0.5)
    gc.collect()
    assert source.last_source() is None
    assert image.get_size() == (4, 540)
    requests = len(source.requests)
    assert cache.get('eye', 'expression', 0.5) is image
    assert len(source.requests) == requests


def test_resized_cache_is_lru_bounded_by_bytes():
    cache = CharacterImages(Images(), budget=4 * 540 * 4 * 2)
    first = cache.get('eye', 'first', 0.5)
    cache.get('eye', 'second', 0.5)
    assert cache.get('eye', 'first', 0.5) is first
    cache.get('eye', 'third', 0.5)
    assert len(cache.images) == 2
    assert ('eye', 'second', (4, 540)) not in cache.images
    assert cache.bytes <= cache.budget


def test_equivalent_scales_reuse_the_same_rendered_size():
    cache = CharacterImages(Images())
    first = cache.get('eye', 'expression', 0.5)
    assert cache.get('eye', 'expression', 0.50000000001) is first


def test_scene_preparation_inherits_torso_expression_and_size():
    source = Images()
    state = {'image_manager': source, 'ir_data': {'steps': [
        {'actions': [{'action': 'chara_show', 'target': 'actor',
                      'params': {'torso': 'body', 'eye': 'open', 'size': 0.5}}]},
        {'actions': [{'action': 'chara_shift', 'target': 'actor',
                      'params': {'eye': 'closed'}}]},
        {'actions': [{'action': 'chara_shift', 'target': 'actor',
                      'params': {'size': 1.0}}]},
    ]}}
    prepare_character_images(state)
    requests = len(source.requests)
    cache = state['_character_images']
    assert cache.get('torso', 'body', 0.5) is not None
    assert cache.get('eye', 'open', 0.5) is not None
    assert cache.get('eye', 'closed', 0.5) is not None
    assert cache.get('eye', 'closed', 1.0) is not None
    assert len(source.requests) == requests
    assert 'character_expressions' not in state


def test_native_image_cache_evicts_by_bytes():
    manager = ImageManager(cache_bytes=800)
    try:
        for name in ('first', 'second', 'third'):
            manager._manage_cache(name, pygame.Surface((10, 10), pygame.SRCALPHA))
        assert list(manager.image_cache) == ['second', 'third']
        assert manager._cache_bytes == 800
    finally:
        manager.cleanup()


@pytest.mark.parametrize('extension', ['png', 'webp', 'jpg'])
def test_geometry_reads_asset_dimensions_without_decoding_pixels(tmp_path, monkeypatch, extension):
    from PyQt5.QtGui import QImage

    path = tmp_path / f'body.{extension}'
    source = QImage(8, 1080, QImage.Format_ARGB32)
    source.fill(0xffffffff)
    assert source.save(str(path))
    manager = ImageManager(cache_bytes=1)
    manager.image_paths = {'torso': {'body': str(path)}}
    decodes = []
    monkeypatch.setattr(manager, 'get_image', lambda *args: decodes.append(args))
    try:
        geometry = CharacterImages(manager).geometry('torso', 'body')
        assert geometry is not None
        assert (geometry.width, geometry.height) == (8, 1080)
        assert decodes == []
    finally:
        manager.cleanup()


def test_invalid_header_falls_back_to_existing_image_resolution(tmp_path, monkeypatch):
    path = tmp_path / 'body.png'
    path.write_bytes(b'unsupported header')
    manager = ImageManager()
    manager.image_paths = {'torso': {'body': str(path)}}
    monkeypatch.setattr(manager, 'get_image', lambda *args: pygame.Surface((8, 1080)))
    try:
        assert CharacterImages(manager).geometry('torso', 'body') == (8, 1080)
    finally:
        manager.cleanup()


def test_parallel_preparation_preserves_lru_order_and_stores_on_caller_thread(monkeypatch):
    from threading import Event, get_ident

    second_started = Event()
    source = Images()
    original = source.get_image
    worker_threads = set()

    def load(category, key):
        worker_threads.add(get_ident())
        if key == 'first':
            assert second_started.wait(5), 'second asset was not prepared concurrently'
        elif key == 'second':
            second_started.set()
        return original(category, key)

    source.get_image = load
    cache = CharacterImages(source, budget=4 * 540 * 4 * 2)
    # Metadata is already available, as with real assets' header dimensions.
    from dialogue.character_images import ImageGeometry
    for key in ('first', 'second', 'third'):
        cache.dimensions[('eye', key)] = ImageGeometry(8, 1080)
    caller = get_ident()
    store = cache._store

    def store_on_caller(identity, image):
        assert get_ident() == caller
        store(identity, image)

    monkeypatch.setattr(cache, '_store', store_on_caller)
    assert len(list(cache.prepare_many({('eye', key): {0.5}
                                      for key in ('first', 'second', 'third')}))) == 3
    assert len(worker_threads) == 2 and caller not in worker_threads
    assert list(cache.images) == [('eye', 'second', (4, 540)), ('eye', 'third', (4, 540))]
    assert cache.bytes <= cache.budget


def test_fixed_pose_sampling_is_independent_of_cached_larger_sizes():
    image = pygame.Surface((100, 100), pygame.SRCALPHA)
    image.fill((255, 255, 255, 255), (31, 27, 3, 5))
    source = Images()
    source.get_image = lambda category, key: image
    cache = CharacterImages(source)
    cache.get('eye', 'eye', 1.0)
    prepared = cache.get('eye', 'eye', 0.6)
    pixels, position = image_pixels(prepared, (0, 0))
    actual = pygame.Surface((60, 60), pygame.SRCALPHA)
    actual.blit(pixels, position)
    expected = pygame.transform.smoothscale(image, (60, 60))
    assert pygame.image.tobytes(actual, 'RGBA') == pygame.image.tobytes(expected, 'RGBA')


def test_intermediate_zoom_frames_do_not_decode_or_fill_the_pose_cache():
    source = Images()
    cache = CharacterImages(source)
    for part in ('torso', 'eye', 'mouth', 'brow'):
        cache.get(part, part, 1.0)
    requests = len(source.requests)
    stored = len(cache.images)
    for scale in (0.51, 0.52, 0.53, 0.54):
        for part in ('torso', 'eye', 'mouth', 'brow'):
            assert cache.get(part, part, scale, resample=True) is not None
    assert len(source.requests) == requests
    assert len(cache.images) == stored


def test_linear_zoom_and_crossfade_prepare_both_old_and_new_endpoints(monkeypatch):
    from dialogue.scenario_manager import _ir_handle_character_shift
    monkeypatch.setattr(pygame.time, 'get_ticks', lambda: 0)
    source = Images()
    state = {
        'image_manager': source, 'active_characters': ['actor'],
        'character_pos': {'actor': [0, 0]}, 'character_zoom': {'actor': 0.5},
        'character_torso': {'actor': 'old_body'},
        'character_expressions': {'actor': {'eye': 'old_eye'}},
    }
    _ir_handle_character_shift(state, 'actor', {
        'torso': 'new_body', 'eye': 'new_eye', 'size': 1.0,
        'move': 'linear', 'time': 300, 'fade': 0.3,
    })
    requests = len(source.requests)
    cache = state['_character_images']
    for scale in (0.6, 0.7, 0.8, 0.9):
        for part, key in [('torso', 'old_body'), ('torso', 'new_body'),
                          ('eye', 'old_eye'), ('eye', 'new_eye')]:
            assert cache.get(part, key, scale, resample=True) is not None
    assert len(source.requests) == requests
