import pygame
import random
from collections import OrderedDict
from core.config import *
from .render_monitor import (
    capture_surface_bytes,
    changed_pixel_count,
    surface_summary,
    trace_enabled,
    trace_light_enabled,
    trace_event,
)

# 画像スケーリングキャッシュ
_SCALED_IMAGE_CACHE_LIMIT = 100
_scaled_image_cache = OrderedDict()
_opaque_bounds_cache = OrderedDict()
_PREMULTIPLIED_CROP_CACHE_LIMIT = 12
_premultiplied_crop_cache = OrderedDict()


def _trace_surface_info(surface):
    if surface is None:
        return {"present": False}
    try:
        bounds = surface.get_bounding_rect(min_alpha=1)
        return {
            "present": True,
            "size": list(surface.get_size()),
            "opaque_rect": [bounds.x, bounds.y, bounds.width, bounds.height],
        }
    except (AttributeError, pygame.error):
        return {"present": False}


def _trace_transition_info(transition):
    if not transition:
        return None
    return {
        "mode": transition.get("mode"),
        "phase": transition.get("phase"),
        "pending_render": bool(transition.get("pending_render")),
        "start_time": transition.get("start_time"),
        "duration": transition.get("duration"),
        "from_surface": _trace_surface_info(transition.get("from_surface")),
        "to_surface": _trace_surface_info(transition.get("to_surface")),
        "from_pos": list(transition.get("from_surface_pos", (0, 0))),
        "to_pos": list(transition.get("to_surface_pos", (0, 0))),
    }


def _trace_transition_region(screen, transition):
    if not transition:
        return None
    region = None
    for surface_key, position_key in (
        ("from_surface", "from_surface_pos"),
        ("to_surface", "to_surface_pos"),
    ):
        surface = transition.get(surface_key)
        if surface is None:
            continue
        bounds = surface.get_bounding_rect(min_alpha=1)
        if bounds.width <= 0 or bounds.height <= 0:
            continue
        destination = bounds.move(transition.get(position_key, (0, 0)))
        region = destination if region is None else region.union(destination)
    if region is None:
        return None
    region = region.clip(screen.get_rect())
    if region.width <= 0 or region.height <= 0:
        return None
    return {
        "rect": [region.x, region.y, region.width, region.height],
        "surface": (
            None
            if trace_light_enabled()
            else surface_summary(screen.subsurface(region))
        ),
    }


def _trace_screen_region(screen, region):
    if region is None:
        return None
    try:
        clipped = region.clip(screen.get_rect())
    except (AttributeError, pygame.error):
        return None
    if clipped.width <= 0 or clipped.height <= 0:
        return None
    return {
        "rect": [clipped.x, clipped.y, clipped.width, clipped.height],
        "surface": (
            None
            if trace_light_enabled()
            else surface_summary(screen.subsurface(clipped))
        ),
    }


def _trace_frame_start(game_state):
    if not trace_enabled():
        return None
    transitions = game_state.get("character_transitions", {})
    fades = game_state.get("character_part_fades", {})
    fade_state = game_state.get("fade_state", {})
    frame_id = trace_event(
        "character_frame",
        ticks=pygame.time.get_ticks(),
        ir_step_index=game_state.get("ir_step_index"),
        current_paragraph=game_state.get("current_paragraph"),
        active_characters=list(game_state.get("active_characters", [])),
        ir_active_anims=[
            {
                "action": anim.get("action"),
                "target": anim.get("target"),
                "end_time": anim.get("end_time"),
            }
            for anim in game_state.get("ir_active_anims", [])
        ],
        transitions={
            name: _trace_transition_info(transition)
            for name, transition in transitions.items()
        },
        part_fades={
            name: sorted(part_map.keys())
            for name, part_map in fades.items()
        },
        fade_state={
            "active": bool(fade_state.get("active")),
            "type": fade_state.get("type"),
            "alpha": fade_state.get("alpha"),
            "start_time": fade_state.get("start_time"),
            "duration": fade_state.get("duration"),
        },
    )
    game_state["_render_trace_frame_seq"] = frame_id
    return frame_id


def _trace_character_result(
    game_state,
    frame_id,
    char_name,
    before,
    status,
    draw_called,
    current_time,
    transition=None,
    display_region=None,
):
    if frame_id is None:
        return
    trace_event(
        "character_display",
        ticks=current_time,
        frame_seq=frame_id,
        char_name=char_name,
        status=status,
        draw_called=bool(draw_called),
        changed_pixels=(
            None
            if trace_light_enabled()
            else changed_pixel_count(before, game_state.get("screen"))
        ),
        transition=_trace_transition_info(
            transition
            if transition is not None
            else game_state.get("character_transitions", {}).get(char_name)
        ),
        display_region=(
            _trace_screen_region(game_state.get("screen"), display_region)
            if display_region is not None
            else _trace_transition_region(
                game_state.get("screen"),
                transition
                if transition is not None
                else game_state.get("character_transitions", {}).get(char_name),
            )
        ),
        part_fades=sorted(
            game_state.get("character_part_fades", {})
            .get(char_name, {})
            .keys()
        ),
        fade_state={
            "active": bool(game_state.get("fade_state", {}).get("active")),
            "type": game_state.get("fade_state", {}).get("type"),
            "alpha": game_state.get("fade_state", {}).get("alpha"),
        },
    )

def get_scaled_image(image, zoom_scale):
    """画像をキャッシュ付きでスケーリング"""
    if zoom_scale == 1.0:
        return image

    # Surface自体をキーとして保持する。id(image)だけを使うと、元Surfaceが
    # 解放された後に同じidが別画像へ再利用され、誤った拡大画像を返し得る。
    cache_key = (image, zoom_scale)

    # キャッシュから取得を試行
    if cache_key in _scaled_image_cache:
        _scaled_image_cache.move_to_end(cache_key)
        return _scaled_image_cache[cache_key]
    
    # スケーリングして新しい画像を作成
    new_width = int(image.get_width() * zoom_scale)
    new_height = int(image.get_height() * zoom_scale)
    # Character art is commonly reduced to a small dialogue size.  Nearest
    # neighbour scaling leaves those silhouettes and expression parts looking
    # like pixel art, especially after the final 640x480 presentation scale.
    # Use the filtered scaler for every cached resize so torso, face parts,
    # and transition snapshots share the same anti-aliased result.
    scaled_image = pygame.transform.smoothscale(image, (new_width, new_height))
    
    # 元Surfaceへの参照もキー内に保持し、LRUで上限を管理する。
    _scaled_image_cache[cache_key] = scaled_image
    while len(_scaled_image_cache) > _SCALED_IMAGE_CACHE_LIMIT:
        _scaled_image_cache.popitem(last=False)
    return scaled_image

def _blit_with_alpha(screen, image, pos, alpha):
    if image is None or alpha <= 0:
        return
    if alpha >= 255:
        screen.blit(image, pos)
        return
    temp = image.copy()
    temp.set_alpha(alpha)
    screen.blit(temp, pos)

def _blit_crossfade(screen, from_image, from_pos, to_image, to_pos, progress):
    """Blend two alpha surfaces linearly without dimming the overlap."""
    progress = max(0.0, min(float(progress), 1.0))
    if from_image is None:
        if to_image is not None:
            _blit_with_alpha(screen, to_image, to_pos, round(255 * progress))
        return
    if to_image is None:
        _blit_with_alpha(screen, from_image, from_pos, round(255 * (1.0 - progress)))
        return
    if progress <= 0.0:
        screen.blit(from_image, from_pos)
        return
    if progress >= 1.0:
        screen.blit(to_image, to_pos)
        return

    def get_opaque_bounds(image):
        bounds = _opaque_bounds_cache.get(image)
        if bounds is not None:
            _opaque_bounds_cache.move_to_end(image)
            return bounds
        bounds = image.get_bounding_rect(min_alpha=1)
        _opaque_bounds_cache[image] = bounds
        while len(_opaque_bounds_cache) > _SCALED_IMAGE_CACHE_LIMIT:
            _opaque_bounds_cache.popitem(last=False)
        return bounds

    def get_premultiplied_crop(image, bounds):
        premultiplied = _premultiplied_crop_cache.get(image)
        if premultiplied is not None:
            _premultiplied_crop_cache.move_to_end(image)
            return premultiplied
        # premul_alpha() requires a contiguous surface here. Calling it
        # directly on a pitched subsurface can produce horizontal corruption.
        premultiplied = image.subsurface(bounds).copy().premul_alpha()
        _premultiplied_crop_cache[image] = premultiplied
        while len(_premultiplied_crop_cache) > _PREMULTIPLIED_CROP_CACHE_LIMIT:
            _premultiplied_crop_cache.popitem(last=False)
        return premultiplied

    from_bounds = get_opaque_bounds(from_image)
    to_bounds = get_opaque_bounds(to_image)
    weighted_sources = []
    if from_bounds.width > 0 and from_bounds.height > 0:
        weighted_sources.append(
            (from_image, from_bounds, from_bounds.move(from_pos), 1.0 - progress)
        )
    if to_bounds.width > 0 and to_bounds.height > 0:
        weighted_sources.append(
            (to_image, to_bounds, to_bounds.move(to_pos), progress)
        )
    if not weighted_sources:
        return

    blend_rect = weighted_sources[0][2].copy()
    for _, _, destination_rect, _ in weighted_sources[1:]:
        blend_rect.union_ip(destination_rect)
    blend_rect = blend_rect.clip(screen.get_clip())
    if blend_rect.width <= 0 or blend_rect.height <= 0:
        return

    # Normal source-over blending makes the background contribute up to 25%
    # halfway through a crossfade. Build the weighted, premultiplied result on
    # a transparent surface first so old/new weights remain (1-p)/p.
    blended = pygame.Surface(blend_rect.size, pygame.SRCALPHA)

    def add_weighted(image, source_bounds, destination_rect, weight):
        visible_rect = destination_rect.clip(blend_rect)
        if visible_rect.width <= 0 or visible_rect.height <= 0:
            return
        source_rect = pygame.Rect(
            source_bounds.x + visible_rect.x - destination_rect.x,
            source_bounds.y + visible_rect.y - destination_rect.y,
            visible_rect.width,
            visible_rect.height,
        )
        premultiplied = get_premultiplied_crop(image, source_bounds)
        crop_rect = source_rect.move(-source_bounds.x, -source_bounds.y)
        weighted = premultiplied.subsurface(crop_rect).copy()
        channel_weight = round(255 * weight)
        weighted.fill(
            (channel_weight, channel_weight, channel_weight, channel_weight),
            special_flags=pygame.BLEND_RGBA_MULT,
        )
        blended.blit(
            weighted,
            (visible_rect.x - blend_rect.x, visible_rect.y - blend_rect.y),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

    for weighted_source in weighted_sources:
        add_weighted(*weighted_source)
    screen.blit(blended, blend_rect.topleft, special_flags=pygame.BLEND_PREMULTIPLIED)

def start_character_part_fade(game_state, character_name, part_type, from_id, to_id, duration_ms):
    if duration_ms <= 0:
        return
    if from_id == to_id:
        if DEBUG:
            print(f"[FADE] skip (same) char={character_name} part={part_type} id={from_id}")
        return
    if DEBUG:
        print(f"[FADE] start char={character_name} part={part_type} from={from_id} to={to_id} duration_ms={duration_ms}")
    fades = game_state.setdefault('character_part_fades', {})
    char_fades = fades.setdefault(character_name, {})
    char_fades[part_type] = {
        'from': from_id,
        'to': to_id,
        'start_time': pygame.time.get_ticks(),
        'duration': duration_ms
    }
    pending = game_state.setdefault('character_fade_pending_render', {})
    pending.setdefault(character_name, set()).add(part_type)


def prewarm_character_fade_images(game_state, character_name, changed_parts):
    """Populate scaled-image caches before a character fade starts.

    Character assets are large enough that the first scale operation can take
    longer than a short (150ms) transition.  If that work happens during the
    first rendered frame, the wall-clock fade can finish before the user sees
    an intermediate frame.  Keep the loading cost outside the transition.
    """
    image_manager = game_state.get('image_manager')
    if not image_manager or not changed_parts:
        return

    torso_id = game_state.get('character_torso', {}).get(character_name, character_name)
    torso_img = image_manager.get_image('torso', torso_id)
    if not torso_img:
        return

    zoom_scale = game_state.get('character_zoom', {}).get(character_name, 1.0)
    try:
        zoom_scale = float(zoom_scale)
    except (TypeError, ValueError):
        zoom_scale = 1.0

    # The normal (non-fading) torso is also drawn on every frame.  Warm it as
    # well; otherwise an expression-only shift can still spend the whole
    # transition scaling the unchanged body for the first time.
    torso_ids = {torso_id}
    part_ids = {}
    for part_type, (from_id, to_id) in changed_parts.items():
        if part_type == 'torso':
            torso_ids.update((from_id, to_id))
        else:
            part_ids[part_type] = (from_id, to_id)

    # These layers are drawn alongside the changed layers in the same frame.
    # Warm their current images too, using the exact scale used by
    # render_face_parts.
    expressions = game_state.get('character_expressions', {}).get(character_name, {})
    for part_type in ('brow', 'eye', 'mouth', 'cheek', 'effect', 'accessory'):
        current_id = expressions.get(part_type)
        if part_type not in part_ids:
            part_ids[part_type] = (current_id, current_id)

    for image_id in torso_ids:
        image = image_manager.get_image('torso', image_id) if image_id else None
        if image:
            scale = zoom_scale * VIRTUAL_HEIGHT / image.get_height() * SCALE
            get_scaled_image(image, scale)

    face_scale = zoom_scale * (VIRTUAL_HEIGHT / torso_img.get_height()) * SCALE
    for part_type, ids in part_ids.items():
        for image_id in ids:
            image = image_manager.get_image(part_type, image_id) if image_id else None
            if image:
                get_scaled_image(image, face_scale)


_CHARACTER_EXPRESSION_PARTS = (
    'brow', 'eye', 'mouth', 'cheek', 'effect', 'accessory'
)


def _build_character_snapshot(
    game_state,
    character_name,
    torso_id,
    expressions,
    character_pos,
    character_zoom,
):
    """Compose one character pose into a reusable transparent surface.

    A transition must not re-render every character part on every frame.  The
    two endpoint poses are composed once, then only their alpha is animated.
    The returned position is the global top-left of the compact surface.
    """
    image_manager = game_state.get('image_manager')
    if not image_manager or not torso_id or character_pos is None:
        return None, (0, 0)
    torso_img = image_manager.get_image('torso', torso_id)
    if not torso_img or torso_img.get_height() <= 0:
        return None, (0, 0)

    try:
        zoom = float(character_zoom)
    except (TypeError, ValueError):
        zoom = 1.0
    base_scale = VIRTUAL_HEIGHT / torso_img.get_height()
    final_zoom = zoom * base_scale * SCALE
    torso_surface = get_scaled_image(torso_img, final_zoom)
    x, y = character_pos
    layers = [(torso_surface, (round(x), round(y)))]

    if game_state.get('show_face_parts', True):
        center_x = round(x + torso_surface.get_width() / 2)
        center_y = round(y + torso_surface.get_height() / 2)
        expressions = expressions or {}
        for part_type in _CHARACTER_EXPRESSION_PARTS:
            part_id = expressions.get(part_type)
            if not part_id:
                continue
            part_img = image_manager.get_image(part_type, part_id)
            if not part_img:
                continue
            scaled_img = get_scaled_image(part_img, final_zoom)
            layers.append(
                (
                    scaled_img,
                    (
                        center_x - scaled_img.get_width() // 2,
                        center_y - scaled_img.get_height() // 2,
                    ),
                )
            )

    bounds = pygame.Rect(layers[0][1], layers[0][0].get_size())
    for image, pos in layers[1:]:
        bounds.union_ip(pygame.Rect(pos, image.get_size()))
    if bounds.width <= 0 or bounds.height <= 0:
        return None, (0, 0)

    snapshot = pygame.Surface(bounds.size, pygame.SRCALPHA, 32)
    for image, pos in layers:
        snapshot.blit(image, (pos[0] - bounds.x, pos[1] - bounds.y))
    return snapshot, (bounds.x, bounds.y)


def _commit_character_transition_target(game_state, character_name, transition):
    """Publish the target pose after a relocation or crossfade completes."""
    game_state.setdefault('character_torso', {})[character_name] = transition[
        'to_torso'
    ]
    game_state.setdefault('character_expressions', {})[character_name] = dict(
        transition.get('to_expressions') or {}
    )
    game_state.setdefault('character_pos', {})[character_name] = list(
        transition['to_pos']
    )
    game_state.setdefault('character_zoom', {})[character_name] = transition[
        'to_zoom'
    ]
    game_state.get('character_part_fades', {}).pop(character_name, None)
    game_state.get('character_fade_pending_render', {}).pop(character_name, None)


def start_character_transition(
    game_state,
    character_name,
    *,
    from_torso,
    from_expressions,
    from_pos,
    from_zoom,
    to_torso,
    to_expressions,
    to_pos,
    to_zoom,
    duration_ms,
    relocation=False,
):
    """Start a composited character transition.

    ``duration_ms`` is one fade leg.  Relocation uses two legs: FO at the old
    pose, then state commit and FI at the new pose.
    """
    duration_ms = max(int(duration_ms), 0)
    if duration_ms <= 0:
        game_state.setdefault('character_torso', {})[character_name] = to_torso
        game_state.setdefault('character_expressions', {})[character_name] = dict(
            to_expressions or {}
        )
        game_state.setdefault('character_pos', {})[character_name] = list(to_pos)
        game_state.setdefault('character_zoom', {})[character_name] = to_zoom
        return 0

    from_surface, from_surface_pos = _build_character_snapshot(
        game_state,
        character_name,
        from_torso,
        from_expressions,
        from_pos,
        from_zoom,
    )
    to_surface, to_surface_pos = _build_character_snapshot(
        game_state,
        character_name,
        to_torso,
        to_expressions,
        to_pos,
        to_zoom,
    )
    transition = {
        'mode': 'relocate' if relocation else 'crossfade',
        'phase': 'out' if relocation else 'blend',
        'from_surface': from_surface,
        'from_surface_pos': from_surface_pos,
        'to_surface': to_surface,
        'to_surface_pos': to_surface_pos,
        'from_torso': from_torso,
        'from_expressions': dict(from_expressions or {}),
        'from_pos': list(from_pos),
        'from_zoom': from_zoom,
        'to_torso': to_torso,
        'to_expressions': dict(to_expressions or {}),
        'to_pos': list(to_pos),
        'to_zoom': to_zoom,
        'start_time': pygame.time.get_ticks(),
        'duration': duration_ms,
        'pending_render': True,
    }
    game_state.setdefault('character_transitions', {})[character_name] = transition
    return duration_ms * (2 if relocation else 1)


def _begin_character_transition_on_first_render(game_state, char_name, current_time):
    transitions = game_state.get('character_transitions', {})
    transition = transitions.get(char_name)
    if not transition or not transition.get('pending_render'):
        return
    transition['pending_render'] = False
    transition['start_time'] = current_time
    total_duration = transition['duration'] * (
        2 if transition.get('mode') == 'relocate' else 1
    )
    end_time = current_time + total_duration
    for anim in game_state.get('ir_active_anims', []):
        if (
            anim.get('target') == char_name
            and anim.get('action') == 'chara_shift'
        ):
            anim['end_time'] = end_time
    matched_animation = any(
        anim.get('target') == char_name and anim.get('action') == 'chara_shift'
        for anim in game_state.get('ir_active_anims', [])
    )
    if matched_animation:
        game_state['ir_anim_pending'] = True
        # Multiple chara_shift actions can belong to the same IR step.  Keep
        # the longest deadline; the last character rendered must not shorten
        # the step while the other character is still transitioning.
        active_anims = game_state.get('ir_active_anims', [])
        game_state['ir_anim_end_time'] = max(
            (anim.get('end_time', 0) for anim in active_anims),
            default=end_time,
        )


def draw_character_transition(game_state, char_name, screen, current_time=None):
    transition = game_state.get('character_transitions', {}).get(char_name)
    if not transition:
        return False
    now = pygame.time.get_ticks() if current_time is None else current_time
    elapsed = max(0, now - transition.get('start_time', now))
    duration = max(int(transition.get('duration', 0)), 0)
    progress = 1.0 if duration <= 0 else min(elapsed / duration, 1.0)
    if trace_enabled():
        trace_event(
            "character_transition_draw",
            ticks=now,
            frame_seq=game_state.get("_render_trace_frame_seq"),
            char_name=char_name,
            mode=transition.get("mode"),
            phase=transition.get("phase"),
            progress=round(progress, 6),
            from_alpha=round(255 * (1.0 - progress)),
            to_alpha=round(255 * progress),
            from_surface=_trace_surface_info(transition.get("from_surface")),
            to_surface=_trace_surface_info(transition.get("to_surface")),
        )
    if transition.get('mode') == 'relocate':
        if transition.get('phase') == 'out':
            _blit_with_alpha(
                screen,
                transition.get('from_surface'),
                transition.get('from_surface_pos', (0, 0)),
                round(255 * (1.0 - progress)),
            )
        else:
            _blit_with_alpha(
                screen,
                transition.get('to_surface'),
                transition.get('to_surface_pos', (0, 0)),
                round(255 * progress),
            )
    else:
        _blit_crossfade(
            screen,
            transition.get('from_surface'),
            transition.get('from_surface_pos', (0, 0)),
            transition.get('to_surface'),
            transition.get('to_surface_pos', (0, 0)),
            progress,
        )
    return True


def update_character_transitions(game_state):
    now = pygame.time.get_ticks()
    transitions = game_state.get('character_transitions', {})
    for char_name, transition in list(transitions.items()):
        if transition.get('pending_render'):
            continue
        duration = max(int(transition.get('duration', 0)), 0)
        if now - transition.get('start_time', now) < duration:
            continue
        if (
            transition.get('mode') == 'relocate'
            and transition.get('phase') == 'out'
        ):
            _commit_character_transition_target(game_state, char_name, transition)
            transition['phase'] = 'in'
            transition['start_time'] = now
            continue
        _commit_character_transition_target(game_state, char_name, transition)
        transitions.pop(char_name, None)


def settle_character_transitions(game_state):
    """Seek live preview transitions to their final committed state."""
    now = pygame.time.get_ticks()
    for transition in game_state.get('character_transitions', {}).values():
        transition['pending_render'] = False
        transition['phase'] = 'in' if transition.get('mode') == 'relocate' else 'blend'
        transition['start_time'] = now - max(int(transition.get('duration', 0)), 0)

def start_character_hide_fade(game_state, character_name, duration_ms):
    if duration_ms <= 0:
        hide_character(game_state, character_name)
        return
    if DEBUG:
        print(f"[FADE] hide start char={character_name} duration_ms={duration_ms}")
    expressions = game_state.get('character_expressions', {}).get(character_name, {})
    torso_id = game_state.get('character_torso', {}).get(character_name, character_name)
    start_character_part_fade(game_state, character_name, 'torso', torso_id, None, duration_ms)
    start_character_part_fade(game_state, character_name, 'brow', expressions.get('brow'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'eye', expressions.get('eye'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'mouth', expressions.get('mouth'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'cheek', expressions.get('cheek'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'effect', expressions.get('effect'), None, duration_ms)
    start_character_part_fade(game_state, character_name, 'accessory', expressions.get('accessory'), None, duration_ms)
    hide_pending = game_state.setdefault('character_hide_pending', {})
    hide_pending[character_name] = pygame.time.get_ticks() + duration_ms

def move_character(game_state, character_name, target_x, target_y, duration=600, zoom=1.0):
    """キャラクターを指定位置に移動するアニメーションを設定する"""
    if character_name not in game_state['character_pos']:
        if DEBUG:
            print(f"警告: キャラクター '{character_name}' は登録されていません")

        # 遅延ロードでキャラクター画像を取得
        # 胴体IDを取得（新形式）後方互換性のためchar_nameをフォールバック
        torso_id = game_state.get('character_torso', {}).get(character_name, character_name)
        image_manager = game_state['image_manager']
        char_img = image_manager.get_image("torso", torso_id)
        
        if char_img:
            char_width = char_img.get_width()
            char_height = char_img.get_height()
        else:
            # キャラクター画像がない場合はデフォルトサイズを使用（元サイズ相当）
            char_width = 2894  # 元画像サイズ
            char_height = 4093
        
        game_state['character_pos'][character_name] = [
            (SCREEN_WIDTH - char_width) // 2,
            (SCREEN_HEIGHT - char_height) // 2
        ]
    
    # 現在の位置を取得
    current_x, current_y = game_state['character_pos'][character_name]
    current_zoom = game_state['character_zoom'].get(character_name, 1.0)

    # 目標位置を計算
    target_x_val = float(target_x)
    target_y_val = float(target_y)

    # 仮想解像度基準で位置を計算してスケーリング
    # X方向とY方向の移動を仮想解像度基準で計算
    virtual_offset_x = target_x_val * VIRTUAL_WIDTH
    virtual_offset_y = target_y_val * VIRTUAL_HEIGHT
    
    # スケーリングした実際の位置を計算
    offset_x, offset_y = scale_pos(virtual_offset_x, virtual_offset_y)
    
    # 最終的な目標位置を計算
    final_target_x = current_x + int(offset_x)
    final_target_y = current_y + int(offset_y)
    
    # アニメーション情報を設定
    start_time = pygame.time.get_ticks()
    game_state['character_anim'][character_name] = {
        'start_x': current_x,
        'start_y': current_y,
        'target_x': final_target_x,
        'target_y': final_target_y,
        'start_zoom': current_zoom,
        'target_zoom': zoom,
        'start_time': start_time,
        'duration': duration
    }
    
    # キャラクターをアクティブリストに追加
    if character_name not in game_state['active_characters']:
        game_state['active_characters'].append(character_name)

    if DEBUG:
        print(f"移動アニメーション開始: {character_name} 比率({target_x}, {target_y}) -> 座標({final_target_x}, {final_target_y}), zoom: {current_zoom} -> {zoom}, 時間: {duration}ms")

def move_character_to(game_state, character_name, target_pos, duration=0, zoom=1.0):
    """Animate to an absolute screen position for linear chara shifts."""
    character_pos = game_state.setdefault('character_pos', {})
    character_zoom = game_state.setdefault('character_zoom', {})
    character_anim = game_state.setdefault('character_anim', {})
    active_characters = game_state.setdefault('active_characters', [])
    current_pos = list(character_pos.get(character_name, target_pos))
    current_zoom = float(character_zoom.get(character_name, 1.0))
    target = [int(target_pos[0]), int(target_pos[1])]
    duration = max(0, int(duration))
    zoom = float(zoom)
    if duration <= 0:
        character_anim.pop(character_name, None)
        character_pos[character_name] = target
        character_zoom[character_name] = zoom
    else:
        character_anim[character_name] = {
            'start_x': current_pos[0],
            'start_y': current_pos[1],
            'target_x': target[0],
            'target_y': target[1],
            'start_zoom': current_zoom,
            'target_zoom': zoom,
            'start_time': pygame.time.get_ticks(),
            'duration': duration,
        }
    if character_name not in active_characters:
        active_characters.append(character_name)


def hide_character(game_state, character_name):
    """キャラクターを退場させる"""
    print(f"[HIDE] hide_character呼び出し: char_name='{character_name}'")
    print(f"[HIDE] 現在のactive_characters: {game_state['active_characters']}")

    if character_name in game_state['active_characters']:
        game_state['active_characters'].remove(character_name)
        print(f"[HIDE] ✓ キャラクター '{character_name}' を退場させました")
        print(f"[HIDE] 更新後のactive_characters: {game_state['active_characters']}")
    else:
        print(f"[HIDE] ⚠ キャラクター '{character_name}' はアクティブではありません")
        print(f"[HIDE] 現在のactive_characters: {game_state['active_characters']}")

    # アニメーション中の場合は停止
    game_state.get('character_transitions', {}).pop(character_name, None)
    game_state.get('character_fade_pending_render', {}).pop(character_name, None)
    if character_name in game_state['character_anim']:
        del game_state['character_anim'][character_name]
        print(f"[HIDE] キャラクター '{character_name}' の移動アニメーションを停止しました")

def set_blink_enabled(game_state, character_name, enabled):
    """キャラクターのまばたき機能の有効/無効を設定"""
    game_state['character_blink_enabled'][character_name] = enabled
    if not enabled:
        # まばたきを無効にする場合、状態をリセット
        if character_name in game_state['character_blink_state']:
            del game_state['character_blink_state'][character_name]
        if character_name in game_state['character_blink_timers']:
            del game_state['character_blink_timers'][character_name]

def init_blink_system(game_state, character_name):
    """キャラクターのまばたきシステムを初期化"""
    if character_name not in game_state['character_blink_enabled']:
        game_state['character_blink_enabled'][character_name] = True
    
    if game_state['character_blink_enabled'].get(character_name, True):
        current_time = pygame.time.get_ticks()
        # 2-5秒のランダムな間隔
        next_blink_time = current_time + random.randint(2000, 5000)
        
        game_state['character_blink_timers'][character_name] = next_blink_time
        game_state['character_blink_state'][character_name] = {
            'current_state': 'normal',
            'animation_start': 0,
            'base_eye_type': '',
            'blink_sequence': [],
            'sequence_index': 0
        }
        
        print(f"[BLINK] {character_name}: まばたきシステム初期化完了 - 次回まばたき予定: {next_blink_time - current_time}ms後")

def update_blink_system(game_state):
    """まばたきシステムを更新"""
    if not game_state.get('active_characters'):
        return
    
    current_time = pygame.time.get_ticks()
    
    # デバッグ: まばたきシステムが動作していることを定期的に表示
    if not hasattr(game_state, 'last_blink_debug_time'):
        game_state['last_blink_debug_time'] = 0
    
    if current_time - game_state['last_blink_debug_time'] > 10000:  # 10秒おき
        # print(f"[BLINK] システム動作中 - アクティブキャラクター: {game_state['active_characters']}")
        for char_name in game_state['active_characters']:
            if char_name in game_state['character_blink_timers']:
                remaining = (game_state['character_blink_timers'][char_name] - current_time) / 1000
                state = game_state['character_blink_state'].get(char_name, {}).get('current_state', 'normal')
                # print(f"[BLINK] {char_name}: 状態={state}, 次回まで={remaining:.1f}秒")
        game_state['last_blink_debug_time'] = current_time
    
    for char_name in game_state['active_characters'].copy():
        # まばたきが無効な場合はスキップ
        if not game_state['character_blink_enabled'].get(char_name, True):
            continue
        
        # まばたきタイマーがない場合は初期化
        if char_name not in game_state['character_blink_timers']:
            init_blink_system(game_state, char_name)
            continue
        
        # まばたきタイマーチェック（アニメーション中でない場合のみ）
        blink_state = game_state['character_blink_state'].get(char_name, {})
        if (current_time >= game_state['character_blink_timers'][char_name] and 
            blink_state.get('current_state', 'normal') == 'normal'):
            start_blink_animation(game_state, char_name)
        
        # まばたきアニメーション更新
        update_blink_animation(game_state, char_name, current_time)

def start_blink_animation(game_state, character_name):
    """まばたきアニメーションを開始"""
    current_time = pygame.time.get_ticks()
    expressions = game_state['character_expressions'].get(character_name, {})
    base_eye_type = expressions.get('eye', '')
    
    print(f"[BLINK] {character_name}: まばたき開始試行 - 目の種類: '{base_eye_type}', 表情データ: {expressions}")
    
    if not base_eye_type:
        # 次のまばたき時間を設定して終了
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
        print(f"[BLINK] {character_name}: 目の種類が設定されていません - スキップ")
        return
    
    # 目の種類を解析
    # 新命名形式: MMK_F00_EYE00_00 → eye_base='MMK_F00_EYE00', eye_number='00'
    if '_' in base_eye_type:
        parts = base_eye_type.split('_')
        print(f"[BLINK] {character_name}: 目の種類解析 - 分割結果: {parts}")
        if len(parts) >= 2:
            eye_number = parts[-1]   # 末尾のフレーム番号 (00/01/02)
            eye_base = '_'.join(parts[:-1])  # 末尾以外すべて

            print(f"[BLINK] {character_name}: eye_base='{eye_base}', eye_number='{eye_number}'")

            # まばたきシーケンスを決定
            if eye_number == '00':
                # 00 -> 01 -> 02 -> 01 -> 00
                sequence = ['00', '01', '02', '02', '02', '01', '00']
            elif eye_number == '01':
                # 01 -> 02 -> 01
                sequence = ['01', '02', '02', '02', '01']
            else:
                # その他の場合はまばたき無し
                print(f"[BLINK] {character_name}: サポートされていない目の種類 '{eye_number}' - スキップ")
                game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
                return

            # まばたきシーケンスの全画像が存在するか確認
            image_manager = game_state.get('image_manager')
            if image_manager:
                all_images_exist = True
                for suffix in sequence:
                    test_eye_type = f"{eye_base}_{suffix}"
                    # image_pathsに存在するか確認（'eyes'タイポ修正済み）
                    if 'eye' not in image_manager.image_paths or test_eye_type not in image_manager.image_paths['eye']:
                        print(f"[BLINK] {character_name}: まばたき画像が存在しません: {test_eye_type} - まばたき無効化")
                        all_images_exist = False
                        break

                if not all_images_exist:
                    # まばたきを無効化
                    game_state['character_blink_enabled'][character_name] = False
                    print(f"[BLINK] {character_name}: まばたき機能を無効化しました")
                    return

            # まばたき状態を設定
            blink_state = game_state['character_blink_state'].get(character_name, {})
            blink_state.update({
                'current_state': 'blinking',
                'animation_start': current_time,
                'base_eye_type': base_eye_type,
                'eye_base': eye_base,
                'blink_sequence': sequence,
                'sequence_index': 0
            })
            game_state['character_blink_state'][character_name] = blink_state

            print(f"[BLINK] {character_name}: まばたき開始 {base_eye_type} -> {sequence}")
        else:
            print(f"[BLINK] {character_name}: 目の種類の形式が不正 - スキップ")
            game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
    else:
        print(f"[BLINK] {character_name}: アンダースコアが含まれていない目の種類 - スキップ") 
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)

def update_blink_animation(game_state, character_name, current_time):
    """まばたきアニメーションを更新"""
    if character_name not in game_state['character_blink_state']:
        return
    
    blink_state = game_state['character_blink_state'][character_name]
    
    if blink_state['current_state'] != 'blinking':
        return
    
    elapsed = current_time - blink_state['animation_start']
    frame_duration = 40  # 各フレーム40ms

    # シーケンスの現在のフレームを計算
    frame_index = elapsed // frame_duration
    
    if frame_index >= len(blink_state['blink_sequence']):
        # アニメーション完了
        blink_state['current_state'] = 'normal'
        # まばたき用の一時的な目の情報を削除
        if 'eye_blink' in game_state['character_expressions'][character_name]:
            del game_state['character_expressions'][character_name]['eye_blink']
        # 次のまばたき時間を設定（3-6秒後）
        game_state['character_blink_timers'][character_name] = current_time + random.randint(3000, 6000)
        print(f"[BLINK] {character_name}: まばたき完了 - 次回予定: {(game_state['character_blink_timers'][character_name] - current_time) / 1000:.1f}秒後")
        return
    
    # 現在の目の状態を設定
    current_eye_suffix = blink_state['blink_sequence'][int(frame_index)]
    current_eye_type = f"{blink_state['eye_base']}_{current_eye_suffix}"
    
    # キャラクターの表情を一時的に更新（まばたき用）
    if character_name not in game_state['character_expressions']:
        game_state['character_expressions'][character_name] = {}
    
    # まばたき中の目の表情を設定
    game_state['character_expressions'][character_name]['eye_blink'] = current_eye_type

def update_character_animations(game_state):
    """キャラクターアニメーションを更新する"""
    current_time = pygame.time.get_ticks()

    # 各キャラクターのアニメーション状態を更新
    for char_name, anim_data in list(game_state['character_anim'].items()):
        # 経過時間の計算
        elapsed = current_time - anim_data['start_time']

        if elapsed >= anim_data['duration']:
            # アニメーション完了
            game_state['character_pos'][char_name] = [
                anim_data['target_x'],
                anim_data['target_y']
            ]
            game_state['character_zoom'][char_name] = anim_data['target_zoom']
            # アニメーション情報を削除
            del game_state['character_anim'][char_name]
        else:
            # アニメーション進行中
            progress = elapsed / anim_data['duration']  # 0.0～1.0

            # 現在位置を線形補間で計算
            current_x = anim_data['start_x'] + (anim_data['target_x'] - anim_data['start_x']) * progress
            current_y = anim_data['start_y'] + (anim_data['target_y'] - anim_data['start_y']) * progress
            current_zoom = anim_data['start_zoom'] + (anim_data['target_zoom'] - anim_data['start_zoom']) * progress

            # 位置を更新
            game_state['character_pos'][char_name] = [int(current_x), int(current_y)]
            game_state['character_zoom'][char_name] = current_zoom

    # まばたきシステムの更新
    update_character_transitions(game_state)
    update_blink_system(game_state)
    update_character_fades(game_state)

def update_character_fades(game_state):
    current_time = pygame.time.get_ticks()
    fades = game_state.get('character_part_fades', {})
    pending = game_state.get('character_fade_pending_render', {})
    for char_name, part_map in list(fades.items()):
        for part_type, fade in list(part_map.items()):
            # The clock is restarted when the first frame is actually drawn.
            # Do not let the update loop remove a fade before that happens.
            if part_type in pending.get(char_name, set()):
                continue
            duration = fade.get('duration', 0)
            if duration <= 0 or current_time - fade.get('start_time', 0) >= duration:
                if DEBUG:
                    print(f"[FADE] end char={char_name} part={part_type}")
                part_map.pop(part_type, None)
        if not part_map:
            fades.pop(char_name, None)
            pending.pop(char_name, None)

    hide_pending = game_state.get('character_hide_pending', {})
    for char_name, end_time in list(hide_pending.items()):
        if current_time >= end_time:
            hide_pending.pop(char_name, None)
            hide_character(game_state, char_name)
            fades.pop(char_name, None)


def _begin_character_fade_on_first_render(game_state, char_name, current_time):
    """Start a newly-created fade when its first frame is actually rendered."""
    pending = game_state.get('character_fade_pending_render', {})
    part_types = pending.pop(char_name, None)
    if not part_types:
        return
    part_map = game_state.get('character_part_fades', {}).get(char_name, {})
    max_duration = 0
    for part_type in part_types:
        fade = part_map.get(part_type)
        if fade:
            fade['start_time'] = current_time
            max_duration = max(max_duration, max(0, fade.get('duration', 0)))

    # The IR animation guard is registered just after the character action.
    # Extend its deadline to the same first-visible-frame origin, otherwise
    # an expensive preview frame could make the step look idle too early.
    if max_duration:
        end_time = current_time + max_duration
        matched_animation = False
        for anim in game_state.get('ir_active_anims', []):
            if (
                anim.get('target') == char_name
                and anim.get('action') in ('chara_show', 'chara_shift', 'chara_hide')
            ):
                anim['end_time'] = end_time
                matched_animation = True
        if matched_animation:
            game_state['ir_anim_pending'] = True
            game_state['ir_anim_end_time'] = end_time


def _hold_character_fade_for_first_render(game_state, char_name, current_time):
    """Render pending fades at their initial state before starting their clock."""
    pending = game_state.get('character_fade_pending_render', {})
    part_types = pending.get(char_name, set())
    part_map = game_state.get('character_part_fades', {}).get(char_name, {})
    for part_type in part_types:
        fade = part_map.get(part_type)
        if fade:
            fade['start_time'] = current_time

def render_face_parts(game_state, char_name, brow_type, eye_type, mouth_type, cheek_type, zoom_scale, fade_map=None, current_time=None, effect_type="", accessory_type=""):
    """Face parts rendering with strictly unified single-layer drawing."""
    screen = game_state['screen']
    if char_name not in game_state['character_pos']:
        return

    character_pos = game_state['character_pos'][char_name]
    image_manager = game_state['image_manager']

    torso_id = game_state.get('character_torso', {}).get(char_name, char_name)
    char_img = image_manager.get_image("torso", torso_id)
    if not char_img:
        return

    actual_char_width = char_img.get_width() * zoom_scale
    actual_char_height = char_img.get_height() * zoom_scale
    char_center_x = character_pos[0] + actual_char_width // 2
    char_center_y = character_pos[1] + actual_char_height // 2

    def draw_part_image(part_img, alpha=255):
        part_pos = (
            char_center_x - part_img.get_width() // 2,
            char_center_y - part_img.get_height() // 2
        )
        _blit_with_alpha(screen, part_img, part_pos, alpha)

    def draw_part(part_type, part_id, alpha=255, fade_info=None):
        if not part_id:
            if trace_enabled():
                trace_event(
                    "character_part_draw",
                    ticks=current_time,
                    frame_seq=game_state.get("_render_trace_frame_seq"),
                    char_name=char_name,
                    part_type=part_type,
                    requested_id=part_id,
                    drawn=False,
                    alpha=alpha,
                    fade=fade_info,
                    status="empty_id",
                )
            return False
        part_img = image_manager.get_image(part_type, part_id)
        if part_img:
            scaled_img = get_scaled_image(part_img, zoom_scale)
            draw_part_image(scaled_img, alpha)
            drawn = True
        else:
            drawn = False
        if trace_enabled():
            trace_event(
                "character_part_draw",
                ticks=current_time,
                frame_seq=game_state.get("_render_trace_frame_seq"),
                char_name=char_name,
                part_type=part_type,
                requested_id=part_id,
                drawn=drawn,
                alpha=alpha,
                fade=fade_info,
                status="drawn" if drawn else "missing_image",
            )
        return drawn

    def draw_part_with_fade(part_type, current_id):
        fade = (fade_map or {}).get(part_type)
        if not fade:
            draw_part(part_type, current_id)
            return

        duration = max(fade.get('duration', 0), 0)
        now = current_time if current_time is not None else pygame.time.get_ticks()
        elapsed = max(0, now - fade.get('start_time', 0))
        progress = 1.0 if duration <= 0 else min(elapsed / duration, 1.0)
        fade_info = {
            "from_id": fade.get("from"),
            "to_id": fade.get("to"),
            "progress": round(progress, 6),
            "from_alpha": round(255 * (1.0 - progress)),
            "to_alpha": round(255 * progress),
            "duration": duration,
            "start_time": fade.get("start_time"),
        }
        draw_part(
            part_type,
            fade.get('from'),
            fade_info["from_alpha"],
            fade_info=fade_info,
        )
        draw_part(
            part_type,
            fade.get('to'),
            fade_info["to_alpha"],
            fade_info=fade_info,
        )

    final_eye_type = eye_type
    if char_name in game_state.get('character_blink_state', {}) and \
       game_state['character_blink_state'][char_name].get('current_state') == 'blinking':
        blink_eye = game_state['character_expressions'].get(char_name, {}).get('eye_blink', '')
        if blink_eye:
            final_eye_type = blink_eye

    # 統一レイヤー順描画 (各スロット1枚のみ)
    draw_part_with_fade('brow', brow_type)
    # A blink must not replace either endpoint in the middle of an eye cross-fade.
    draw_part_with_fade('eye', eye_type if (fade_map or {}).get('eye') else final_eye_type)
    draw_part_with_fade('mouth', mouth_type)
    draw_part_with_fade('cheek', cheek_type)
    draw_part_with_fade('effect', effect_type)
    draw_part_with_fade('accessory', accessory_type)

def draw_characters(game_state):
    """Draw characters with optional part fades."""
    frame_id = _trace_frame_start(game_state)
    # A CG replaces the normal character layer while it is visible or
    # transitioning.  Character state remains in the game state so cg_hide
    # can reveal the latest expressions/positions again.
    cg_state = game_state.get("cg_state") or {}
    if cg_state.get("storage") or cg_state.get("transition"):
        # The character layer is intentionally hidden under a CG. Still let
        # its transition clock begin, otherwise a hidden shift could deadlock
        # the step until cg_hide reveals it.
        now = pygame.time.get_ticks()
        for char_name in list(game_state.get('character_transitions', {})):
            _begin_character_transition_on_first_render(
                game_state, char_name, now
            )
        return

    current_dialogue = game_state['dialogue_data'][game_state['current_paragraph']] if game_state['dialogue_data'] else None
    if isinstance(current_dialogue, dict):
        current_speaker = (
            current_dialogue.get('character')
            or current_dialogue.get('speaker')
        )
    else:
        current_speaker = current_dialogue[1] if current_dialogue and len(current_dialogue) > 1 else None
    image_manager = game_state['image_manager']
    screen = game_state['screen']

    for char_name in game_state['active_characters']:
        if char_name not in game_state['character_pos']:
            _trace_character_result(
                game_state,
                frame_id,
                char_name,
                None,
                "missing_position",
                False,
                pygame.time.get_ticks(),
            )
            continue

        trace_before = capture_surface_bytes(screen) if frame_id is not None else None
        fade_map = game_state.get('character_part_fades', {}).get(char_name, {})
        current_time = pygame.time.get_ticks()
        has_pending_fade = bool(
            game_state.get('character_fade_pending_render', {}).get(char_name)
        )
        if has_pending_fade:
            _hold_character_fade_for_first_render(game_state, char_name, current_time)

        transition = game_state.get('character_transitions', {}).get(char_name)
        if transition:
            if transition.get('pending_render'):
                # The transition clock starts at the first actual draw.  This
                # must happen before calculating progress; otherwise a preview
                # that spent time loading assets can render the new endpoint
                # at progress=1 on its first frame, then jump back to 0.
                _begin_character_transition_on_first_render(
                    game_state, char_name, current_time
                )
            draw_called = draw_character_transition(
                game_state, char_name, screen, current_time
            )
            _trace_character_result(
                game_state,
                frame_id,
                char_name,
                trace_before,
                "transition",
                draw_called,
                current_time,
                transition=transition,
            )
            continue

        torso_id = game_state.get('character_torso', {}).get(char_name, char_name)

        char_img = image_manager.get_image("torso", torso_id)
        if not char_img:
            if DEBUG:
                print(f"??: ????????'{char_name}' ????????")
            _trace_character_result(
                game_state,
                frame_id,
                char_name,
                trace_before,
                "missing_torso",
                False,
                current_time,
            )
            continue

        x, y = game_state['character_pos'][char_name]
        zoom_scale = game_state['character_zoom'].get(char_name, 1.0)

        def get_torso_image(torso_key):
            torso_img = image_manager.get_image("torso", torso_key)
            if not torso_img:
                return None
            base_scale = VIRTUAL_HEIGHT / torso_img.get_height()
            final_zoom = zoom_scale * base_scale * SCALE
            return get_scaled_image(torso_img, final_zoom)

        torso_fade = fade_map.get('torso')
        trace_region = None
        if torso_fade:
            duration = max(torso_fade.get('duration', 0), 0)
            elapsed = max(0, current_time - torso_fade.get('start_time', 0))
            progress = 1.0 if duration <= 0 else min(elapsed / duration, 1.0)
            _blit_crossfade(
                screen,
                get_torso_image(torso_fade.get('from')),
                (x, y),
                get_torso_image(torso_fade.get('to')),
                (x, y),
                progress,
            )
            trace_surfaces = [
                get_torso_image(torso_fade.get('from')),
                get_torso_image(torso_fade.get('to')),
            ]
            trace_width = max(
                (image.get_width() for image in trace_surfaces if image),
                default=0,
            )
            trace_height = max(
                (image.get_height() for image in trace_surfaces if image),
                default=0,
            )
            trace_region = pygame.Rect(x, y, trace_width, trace_height)
        else:
            torso_surface = get_torso_image(torso_id)
            if torso_surface:
                screen.blit(torso_surface, (x, y))
                trace_region = pygame.Rect(
                    x,
                    y,
                    torso_surface.get_width(),
                    torso_surface.get_height(),
                )

        char_base_scale = VIRTUAL_HEIGHT / char_img.get_height()

        if game_state['show_face_parts']:
            expressions = game_state['character_expressions'].get(char_name, {})
            eye_type = expressions.get('eye', '')
            mouth_type = expressions.get('mouth', '')
            brow_type = expressions.get('brow', '')
            cheek_type = expressions.get('cheek', '')
            effect_type = expressions.get('effect', '')
            accessory_type = expressions.get('accessory', '')

            face_final_zoom = zoom_scale * char_base_scale * SCALE
            render_face_parts(
                game_state,
                char_name,
                brow_type,
                eye_type,
                mouth_type,
                cheek_type,
                face_final_zoom,
                fade_map=fade_map,
                current_time=current_time,
                effect_type=effect_type,
                accessory_type=accessory_type,
            )

        if has_pending_fade:
            # Start the real-time clock after this frame has been fully
            # rendered, so a slow first frame cannot consume the transition.
            _begin_character_fade_on_first_render(
                game_state, char_name, pygame.time.get_ticks()
            )
        _trace_character_result(
            game_state,
            frame_id,
            char_name,
            trace_before,
            "regular",
            True,
            current_time,
            display_region=trace_region,
        )

