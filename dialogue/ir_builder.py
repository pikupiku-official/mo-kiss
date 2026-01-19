import json
import os
from typing import Any, Dict, List, Optional

from .ir_model import (
    ON_ADVANCE_COMPLETE,
    ON_ADVANCE_BLOCK,
    make_action,
    make_animation,
    make_step,
    make_text,
)


def build_ir_from_normalized(dialogue_data: List[Any]) -> Dict[str, Any]:
    steps: List[Dict[str, Any]] = []
    source_to_step: Dict[int, int] = {}
    if not dialogue_data:
        return {"steps": steps, "source_to_step": source_to_step}

    pending_actions: List[Dict[str, Any]] = []
    pending_sources: List[int] = []
    last_expressions: Dict[str, Dict[str, str]] = {}
    step_counter = 1

    def emit_step(
        *,
        text: Optional[Dict[str, Any]] = None,
        actions: Optional[List[Dict[str, Any]]] = None,
        source_index: Optional[int] = None,
        source_indices: Optional[List[int]] = None,
    ) -> None:
        nonlocal step_counter
        step_id = f"step_{step_counter:04d}"
        steps.append(
            make_step(
                step_id=step_id,
                text=text,
                actions=actions,
                source_index=source_index,
            )
        )
        step_pos = len(steps) - 1
        indices = []
        if source_indices:
            indices.extend(source_indices)
        if source_index is not None:
            indices.append(source_index)
        for idx in indices:
            source_to_step[idx] = step_pos
        step_counter += 1

    for source_index, entry in enumerate(dialogue_data):
        if isinstance(entry, dict):
            action_type = entry.get("type", "unknown")
            target = entry.get("name") if action_type == "chara_shift" else None
            params = entry
            if action_type == "chara_shift":
                params = _normalize_chara_shift_params(entry)
            if action_type in ("if_start", "if_end", "flag_set", "event_unlock"):
                if pending_actions:
                    emit_step(
                        actions=pending_actions,
                        source_index=pending_sources[-1],
                        source_indices=pending_sources,
                    )
                    pending_actions = []
                    pending_sources = []
                animation = None
                if action_type == "chara_shift":
                    animation = make_animation(on_advance=ON_ADVANCE_BLOCK)
                emit_step(
                    actions=[make_action(action=action_type, target=target, params=params, animation=animation)],
                    source_index=source_index,
                    source_indices=[source_index],
                )
            else:
                animation = None
                if action_type == "chara_shift":
                    animation = make_animation(on_advance=ON_ADVANCE_BLOCK)
                pending_actions.append(
                    make_action(action=action_type, target=target, params=params, animation=animation)
                )
                pending_sources.append(source_index)
                if action_type == "chara_shift" and target:
                    _update_last_expressions(last_expressions, target, params)
            continue

        if not isinstance(entry, list) or len(entry) < 7:
            continue

        text_or_cmd = entry[6]
        if isinstance(text_or_cmd, str) and text_or_cmd.startswith("_"):
            action = _action_from_command(entry, text_or_cmd)
            if not action:
                continue
            action_type = action.get("action")
            if action_type in ("chara_show", "chara_shift"):
                target = action.get("target") or entry[1]
                params = action.get("params") or {}
                if target:
                    _update_last_expressions(last_expressions, target, params)
            if action_type in ("scroll_stop", "choice"):
                combined_actions = pending_actions + [action]
                combined_sources = pending_sources + [source_index]
                emit_step(
                    actions=combined_actions,
                    source_index=source_index,
                    source_indices=combined_sources,
                )
                pending_actions = []
                pending_sources = []
            else:
                pending_actions.append(action)
                pending_sources.append(source_index)
            continue

        speaker = entry[10] if len(entry) > 10 and entry[10] else entry[1]
        text = make_text(
            speaker=speaker or "",
            body=text_or_cmd or "",
            scroll=bool(entry[11]) if len(entry) > 11 else False,
        )
        shift_action = _action_for_expression(entry, last_expressions)
        combined_actions = list(pending_actions)
        if shift_action:
            shift_target = shift_action.get("target")
            has_pending_shift = any(
                act.get("action") == "chara_shift" and act.get("target") == shift_target
                for act in pending_actions
            )
            if not has_pending_shift:
                shift_action["animation"] = make_animation(on_advance=ON_ADVANCE_BLOCK)
                combined_actions.append(shift_action)
        combined_sources = pending_sources + [source_index]
        emit_step(
            text=text,
            actions=combined_actions if combined_actions else None,
            source_index=source_index,
            source_indices=combined_sources,
        )
        pending_actions = []
        pending_sources = []

    if pending_actions:
        emit_step(
            actions=pending_actions,
            source_index=pending_sources[-1],
            source_indices=pending_sources,
        )

    return {"steps": steps, "source_to_step": source_to_step}


def _update_last_expressions(
    last_expressions: Dict[str, Dict[str, str]],
    target: str,
    params: Dict[str, Any],
) -> None:
    if not target:
        return
    record = last_expressions.setdefault(target, {})
    for key in ("eye", "mouth", "brow", "cheek"):
        if key in params and params.get(key):
            record[key] = params.get(key) or ""

def _action_for_expression(
    entry: List[Any],
    last_expressions: Dict[str, Dict[str, str]],
) -> Optional[Dict[str, Any]]:
    if len(entry) < 6:
        return None
    target = entry[10] if len(entry) > 10 and entry[10] else entry[1]
    if not target:
        return None
    incoming: Dict[str, str] = {}
    for key, value in (
        ("eye", entry[2]),
        ("mouth", entry[3]),
        ("brow", entry[4]),
        ("cheek", entry[5] if len(entry) > 5 else ""),
    ):
        if value:
            incoming[key] = value
    if not incoming:
        return None
    previous = last_expressions.get(target, {})
    params: Dict[str, Any] = {}
    for key, value in incoming.items():
        if previous.get(key) != value:
            params[key] = value
    if not params:
        return None
    _update_last_expressions(last_expressions, target, params)
    return make_action(action="chara_shift", target=target, params=params)

def _normalize_chara_shift_params(entry: Dict[str, Any]) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    for key in ("torso", "eye", "mouth", "brow", "cheek", "x", "y", "size", "fade"):
        if key in entry:
            params[key] = entry.get(key)
    for key in ("x", "y", "size", "fade"):
        if key in params and params[key] is not None:
            params[key] = _to_float(params[key], params[key])
    return params


def _action_from_command(entry: List[Any], text: str) -> Optional[Dict[str, Any]]:
    if text.startswith("_SCROLL_STOP"):
        return make_action(action="scroll_stop")

    if text.startswith("_CHOICE_"):
        options = entry[12] if len(entry) > 12 else []
        return make_action(action="choice", params={"options": options})

    if text.startswith("_BGM_PAUSE"):
        fade_time = 0.0
        if len(entry) > 12 and isinstance(entry[12], dict):
            fade_time = float(entry[12].get("fade_time", 0.0))
        return make_action(action="bgm_pause", params={"fade_time": fade_time})

    if text.startswith("_BGM_UNPAUSE"):
        fade_time = 0.0
        if len(entry) > 12 and isinstance(entry[12], dict):
            fade_time = float(entry[12].get("fade_time", 0.0))
        return make_action(action="bgm_unpause", params={"fade_time": fade_time})

    if text.startswith("_CHARA_NEW_"):
        params = _parse_chara_new(text)
        if params is None:
            return None
        params.update(
            {
                "eye": entry[2],
                "mouth": entry[3],
                "brow": entry[4],
                "cheek": entry[5] if len(entry) > 5 else "",
            }
        )
        target = params.get("name") or entry[1] or params.get("torso")
        return make_action(
            action="chara_show",
            target=target,
            params=params,
            animation=make_animation(on_advance=ON_ADVANCE_BLOCK),
        )

    if text.startswith("_CHARA_HIDE_"):
        parts = text.split("_")
        target = parts[3] if len(parts) > 3 else entry[1]
        fade = _to_float(parts[4], 0.1) if len(parts) > 4 else 0.1
        return make_action(
            action="chara_hide",
            target=target,
            params={"fade": fade},
            animation=make_animation(on_advance=ON_ADVANCE_BLOCK),
        )

    if text.startswith("_MOVE_"):
        parts = text.split("_")
        left = _to_float(parts[2], 0.0) if len(parts) > 2 else 0.0
        top = _to_float(parts[3], 0.0) if len(parts) > 3 else 0.0
        duration = _to_int(parts[4], 600) if len(parts) > 4 else 600
        zoom = _to_float(parts[5], 1.0) if len(parts) > 5 else 1.0
        target = entry[1] if len(entry) > 1 else None
        return make_action(
            action="chara_move",
            target=target,
            params={"left": left, "top": top, "time": duration, "zoom": zoom},
            animation=make_animation(on_advance=ON_ADVANCE_COMPLETE),
        )

    if text.startswith("_BG_SHOW_"):
        parts = text.split("_")
        storage = parts[3] if len(parts) > 3 else None
        x = _to_float(parts[4], 0.5) if len(parts) > 4 else 0.5
        y = _to_float(parts[5], 0.5) if len(parts) > 5 else 0.5
        zoom = _to_float(parts[6], 1.0) if len(parts) > 6 else 1.0
        return make_action(
            action="bg_show",
            params={"storage": storage, "x": x, "y": y, "zoom": zoom},
            animation=make_animation(on_advance=ON_ADVANCE_BLOCK),
        )

    if text.startswith("_BG_MOVE_"):
        parts = text.split("_")
        left = _to_float(parts[3], 0.0) if len(parts) > 3 else 0.0
        top = _to_float(parts[4], 0.0) if len(parts) > 4 else 0.0
        duration = _to_int(parts[5], 600) if len(parts) > 5 else 600
        zoom = _to_float(parts[6], 1.0) if len(parts) > 6 else 1.0
        return make_action(
            action="bg_move",
            params={"left": left, "top": top, "time": duration, "zoom": zoom},
            animation=make_animation(on_advance=ON_ADVANCE_COMPLETE),
        )

    if text.startswith("_FADEOUT_"):
        parts = text.split("_")
        color = parts[2] if len(parts) > 2 else "black"
        time = _to_float(parts[3], 1.0) if len(parts) > 3 else 1.0
        return make_action(
            action="fadeout",
            params={"color": color, "time": time},
            animation=make_animation(on_advance=ON_ADVANCE_COMPLETE),
        )

    if text.startswith("_FADEIN_"):
        parts = text.split("_")
        time = _to_float(parts[2], 1.0) if len(parts) > 2 else 1.0
        return make_action(
            action="fadein",
            params={"time": time},
            animation=make_animation(on_advance=ON_ADVANCE_COMPLETE),
        )

    if text.startswith("_SE_PLAY_"):
        parts = text.split("_")
        filename = parts[3] if len(parts) > 3 else ""
        volume = _to_float(parts[4], 0.5) if len(parts) > 4 else 0.5
        frequency = _to_int(parts[5], 1) if len(parts) > 5 else 1
        return make_action(
            action="se_play",
            params={"file": filename, "volume": volume, "frequency": frequency},
        )

    return None


def _parse_chara_new(text: str) -> Optional[Dict[str, Any]]:
    parts = text.split("_")
    if len(parts) < 4:
        return None

    torso_id = None
    char_name = None
    try:
        if len(parts) >= 12:
            torso_id = f"{parts[3]}_{parts[4]}_{parts[5]}"
            char_name = parts[11]
            x = _to_float(parts[6], 0.5)
            y = _to_float(parts[7], 0.5)
            size = _to_float(parts[8], 1.0)
            blink = parts[9].lower() != "false"
            fade = _to_float(parts[10], 0.1)
        elif len(parts) >= 10:
            torso_id = f"{parts[3]}_{parts[4]}_{parts[5]}"
            char_name = torso_id
            x = _to_float(parts[6], 0.5)
            y = _to_float(parts[7], 0.5)
            size = _to_float(parts[8], 1.0)
            blink = parts[9].lower() != "false"
            fade = 0.1
        else:
            torso_id = parts[3]
            char_name = torso_id
            x = _to_float(parts[4], 0.5)
            y = _to_float(parts[5], 0.5)
            size = _to_float(parts[6], 1.0)
            blink = parts[7].lower() != "false" if len(parts) > 7 else True
            fade = 0.1
    except (ValueError, IndexError):
        return None

    return {
        "torso": torso_id,
        "name": char_name,
        "x": x,
        "y": y,
        "size": size,
        "blink": blink,
        "fade": fade,
    }


def _to_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_ir_dump_path(source_path: str, output_dir: str) -> str:
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    return os.path.join(output_dir, f"{base_name}.json")


def dump_ir_json(ir_data: Dict[str, Any], output_path: str) -> None:
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as handle:
        json.dump(ir_data, handle, ensure_ascii=False, indent=2)
