"""Run an actual Pygame temporal probe for a multi-character chara_shift step.

This is intentionally separate from the normal game loop.  It uses the same
IR dispatcher and ``draw_characters`` path, renders every 16 ms, and records
image requests plus the final 640x480 presentation surface.
"""

import argparse
import json
import os
from datetime import datetime


def _settle_state(game_state):
    from dialogue.character_manager import (
        settle_character_transitions,
        update_character_animations,
    )

    now = __import__("pygame").time.get_ticks()
    settle_character_transitions(game_state)
    game_state.get("character_fade_pending_render", {}).clear()
    for part_map in game_state.get("character_part_fades", {}).values():
        for fade in part_map.values():
            fade["start_time"] = now - max(int(fade.get("duration", 0)), 0)
    update_character_animations(game_state)
    game_state["ir_active_anims"] = []
    game_state["ir_anim_pending"] = False
    game_state["ir_anim_end_time"] = None


def _find_multi_shift_step(steps, requested_index=None):
    candidates = []
    for index, step in enumerate(steps):
        actions = step.get("actions") or []
        shifts = [action for action in actions if action.get("action") == "chara_shift"]
        if len(shifts) >= 2:
            candidates.append((index, shifts))
    if requested_index is not None:
        for index, shifts in candidates:
            if index == requested_index or index + 1 == requested_index:
                return index, shifts
        raise SystemExit(f"multi-shift step not found: {requested_index}")
    if not candidates:
        raise SystemExit("no IR step contains two chara_shift actions")
    return candidates[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--event", default="events/E006.ks")
    parser.add_argument("--step", type=int, default=None)
    parser.add_argument("--duration-ms", type=int, default=700)
    parser.add_argument(
        "--advance-target",
        action="store_true",
        help="Enter the selected step through advance_dialogue_ir so its wait/next-step boundary is exercised.",
    )
    parser.add_argument(
        "--render-path",
        choices=("production", "direct"),
        default="production",
        help="Use DialogueSubsystem.render and WindowController for production-path evidence.",
    )
    args = parser.parse_args()

    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    trace_path = os.path.join("debug", f"chara_shift_trace_{stamp}.jsonl")
    # Keep initialization quiet.  The production initializer starts several
    # image operations before the interactive frame loop; tracing begins at
    # the selected target step below.
    os.environ["DIALOGUE_RENDER_TRACE"] = "0"
    os.environ["DIALOGUE_RENDER_TRACE_FILE"] = trace_path
    os.environ["DIALOGUE_RENDER_TRACE_MAX"] = "20000"

    import pygame

    pygame.init()
    pygame.display.set_mode((1, 1), pygame.HIDDEN)
    import core.config as config
    config.DEBUG = False
    import dialogue.game_manager as game_manager
    # The production preload uses a worker thread that decodes Pygame Surfaces.
    # Disable only that preload in this probe; target-frame image requests stay
    # synchronous and use the exact production ImageManager/get_image path.
    from core.services.image_manager import ImageManager
    ImageManager.preload_characters_from_dialogue = lambda self, data: None
    from dialogue.character_manager import draw_characters, update_character_animations
    from dialogue.render_monitor import (
        capture_surface_bytes,
        changed_pixel_count,
        surface_summary,
        trace_event,
    )
    from dialogue.scenario_manager import _ir_dispatch_action, advance_dialogue_ir

    game_manager.DEBUG = False
    game_state = game_manager.initialize_game(args.event)
    if not game_state:
        raise SystemExit("game initialization failed")

    os.environ["DIALOGUE_RENDER_TRACE"] = "1"

    steps = (game_state.get("ir_data") or {}).get("steps") or []
    target_index, shifts = _find_multi_shift_step(steps, args.step)

    # Freeze the clock after initialization so each simulated frame is exactly
    # reproducible while still exercising the real image and draw functions.
    real_ticks = pygame.time.get_ticks
    base_ticks = real_ticks()
    simulated_ticks = {"value": base_ticks}
    pygame.time.get_ticks = lambda: simulated_ticks["value"]

    trace_start = trace_event(
        "diagnostic_target",
        ticks=base_ticks,
        event_file=args.event,
        ir_step_index=target_index,
        targets=[action.get("target") for action in shifts],
        action_count=len(shifts),
        virtual_size=list(game_state["screen"].get_size()),
        final_size=[640, 480],
    )

    for index in range(target_index):
        step = steps[index]
        game_state["current_paragraph"] = step.get("source_index", index)
        for action in step.get("actions") or []:
            if action.get("action") in {
                "chara_show",
                "chara_shift",
                "chara_hide",
            }:
                _ir_dispatch_action(game_state, action)
        _settle_state(game_state)

    if args.advance_target:
        # Preserve the already-settled character scene, then enter the target
        # through the real IR step boundary. This retains ir_waiting_for_anim
        # and allows update_game to perform the same next-step handoff as the
        # interactive loop.
        game_state["ir_step_index"] = target_index - 1
        game_state["current_paragraph"] = (
            steps[target_index - 1].get("source_index", target_index - 1)
            if target_index > 0
            else -1
        )
        game_state["ir_active_anims"] = []
        game_state["ir_anim_pending"] = False
        game_state["ir_anim_end_time"] = None
        advance_dialogue_ir(game_state)
    else:
        game_state["ir_step_index"] = target_index
        game_state["current_paragraph"] = steps[target_index].get(
            "source_index", target_index
        )
        for action in shifts:
            _ir_dispatch_action(game_state, action)

    virtual_screen = game_state["screen"]
    renderer = None
    window_controller = None
    if args.render_path == "production":
        from dialogue.dialogue_subsystem import DialogueSubsystem
        from core.runtime.window_controller import WindowController

        # Keep update_game from advancing the dialogue while this probe holds
        # the selected IR step in place. Rendering itself remains the exact
        # DialogueSubsystem.render -> WindowController presentation path.
        text_renderer = game_state.get("text_renderer")
        if text_renderer is not None:
            text_renderer.auto_mode = False
            text_renderer.skip_mode = False
            text_renderer.is_ready_for_next = False

        renderer = object.__new__(DialogueSubsystem)
        renderer.game_state = game_state
        renderer.virtual_screen = virtual_screen
        renderer.screen = pygame.Surface(virtual_screen.get_size())
        renderer._saved_offset_x = 0
        renderer._saved_offset_y = 0
        renderer._saved_scale = 1.0

        import core.config as config
        config.WINDOW_CONTENT_WIDTH = 640
        config.WINDOW_CONTENT_HEIGHT = 480
        config.WINDOW_OFFSET_X = 0
        config.WINDOW_OFFSET_Y = 0
        final_screen = pygame.Surface((640, 480))
        window_controller = WindowController(final_screen, virtual_screen)
    else:
        final_screen = pygame.Surface((640, 480))
    previous_final_bytes = None
    for elapsed in range(0, max(args.duration_ms, 0) + 1, 16):
        simulated_ticks["value"] = base_ticks + elapsed
        if args.render_path == "production":
            renderer.update()
            renderer.render()
            window_controller.present_virtual_screen()
        else:
            update_character_animations(game_state)
            virtual_screen.fill((0, 0, 0))
            draw_characters(game_state)
            scaled = pygame.transform.smoothscale(virtual_screen, final_screen.get_size())
            final_screen.fill((0, 0, 0))
            final_screen.blit(scaled, (0, 0))
        frame_changed_pixels = changed_pixel_count(previous_final_bytes, final_screen)
        previous_final_bytes = capture_surface_bytes(final_screen)
        trace_event(
            "diagnostic_present",
            ticks=simulated_ticks["value"],
            frame_elapsed_ms=elapsed,
            virtual_surface=surface_summary(virtual_screen),
            final_640x480_surface=surface_summary(final_screen),
            final_frame_changed_pixels=frame_changed_pixels,
            remaining_transitions=list(
                game_state.get("character_transitions", {}).keys()
            ),
            ir_active_anims=[
                {
                    "target": anim.get("target"),
                    "end_time": anim.get("end_time"),
                }
                for anim in game_state.get("ir_active_anims", [])
            ],
            ir_step_index=game_state.get("ir_step_index"),
            current_paragraph=game_state.get("current_paragraph"),
        )

    pygame.time.get_ticks = real_ticks
    image_manager = game_state.get("image_manager")
    if image_manager is not None and hasattr(image_manager, "cleanup"):
        image_manager.cleanup()
    pygame.quit()

    with open(trace_path, "r", encoding="utf-8") as trace_file:
        events = [json.loads(line) for line in trace_file if line.strip()]
    events = [event for event in events if event.get("seq", 0) >= (trace_start or 0)]
    displays = [event for event in events if event.get("event") == "character_display"]
    image_results = [event for event in events if event.get("event") == "image_result"]
    target_keys = {
        str(value)
        for action in shifts
        for value in (action.get("params") or {}).values()
        if isinstance(value, str) and value
    }
    target_image_results = [
        event
        for event in image_results
        if event.get("requested_key") in target_keys
    ]
    zero_frames = [
        event
        for event in displays
        if event.get("status") == "transition"
        and event.get("changed_pixels") == 0
    ]
    transition_displays = [
        event for event in displays if event.get("status") == "transition"
    ]
    display_status_counts = {}
    for event in displays:
        key = f"{event.get('char_name')}:{event.get('status')}"
        display_status_counts[key] = display_status_counts.get(key, 0) + 1
    target_display_status_counts = {}
    for event in displays:
        if event.get("char_name") not in {
            action.get("target") for action in shifts
        }:
            continue
        key = f"{event.get('char_name')}:{event.get('status')}"
        target_display_status_counts[key] = (
            target_display_status_counts.get(key, 0) + 1
        )
    grouped_image_failures = {}
    for event in target_image_results:
        if event.get("ok"):
            continue
        key = (
            event.get("image_type"),
            event.get("requested_key"),
            event.get("status"),
        )
        grouped_image_failures[key] = grouped_image_failures.get(key, 0) + 1
    per_character = {}
    for target in [action.get("target") for action in shifts]:
        records = [
            event for event in transition_displays if event.get("char_name") == target
        ]
        if not records:
            continue
        region_pixels = [
            event.get("display_region", {}).get("surface", {}).get("non_black_pixels")
            for event in records
            if event.get("display_region")
            and event.get("display_region", {}).get("surface")
        ]
        per_character[target] = {
            "records": len(records),
            "min_changed_pixels": min(event.get("changed_pixels", 0) for event in records),
            "min_display_region_non_black_pixels": min(region_pixels) if region_pixels else None,
            "first": {
                "ticks": records[0].get("ticks"),
                "changed_pixels": records[0].get("changed_pixels"),
                "display_region_non_black_pixels": (
                    records[0].get("display_region", {})
                    .get("surface", {})
                    .get("non_black_pixels")
                ),
            },
            "last": {
                "ticks": records[-1].get("ticks"),
                "changed_pixels": records[-1].get("changed_pixels"),
                "display_region_non_black_pixels": (
                    records[-1].get("display_region", {})
                    .get("surface", {})
                    .get("non_black_pixels")
                ),
            },
        }
    presentations = [
        event
        for event in events
        if event.get("event") == "diagnostic_present"
    ]
    print(json.dumps({
        "trace_file": trace_path,
        "event": args.event,
        "ir_step_index": target_index,
        "targets": [action.get("target") for action in shifts],
        "display_records": len(displays),
        "zero_changed_transition_records": len(zero_frames),
        "target_image_status_counts": {
            status: sum(
                1 for event in target_image_results if event.get("status") == status
            )
            for status in sorted({event.get("status") for event in target_image_results})
        },
        "target_image_failures": [
            {
                "image_type": image_type,
                "requested_key": requested_key,
                "status": status,
                "count": count,
            }
            for (image_type, requested_key, status), count in sorted(
                grouped_image_failures.items()
            )
        ],
        "display_status_counts": display_status_counts,
        "target_display_status_counts": target_display_status_counts,
        "missing_display_records": sum(
            count
            for key, count in target_display_status_counts.items()
            if key.rsplit(":", 1)[-1]
            in {"missing_position", "missing_torso"}
        ),
        "per_character_display": per_character,
        "presentation_first": (
            presentations[0].get("final_640x480_surface") if presentations else None
        ),
        "presentation_last": (
            presentations[-1].get("final_640x480_surface") if presentations else None
        ),
        "fade_states_seen": sorted({
            json.dumps(event.get("fade_state"), sort_keys=True)
            for event in displays
        }),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
