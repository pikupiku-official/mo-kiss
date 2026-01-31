from typing import Any, Dict, List, Optional

# IR data is represented as plain dicts for easy JSON serialization.

ON_ADVANCE_BLOCK = "block"
ON_ADVANCE_COMPLETE = "complete"
ON_ADVANCE_INTERRUPT = "interrupt"
ON_ADVANCE_CONTINUE = "continue"


def make_text(speaker: str, body: str, scroll: bool = False) -> Dict[str, Any]:
    return {"speaker": speaker, "body": body, "scroll": scroll}


def make_animation(
    anim_type: str = "once",
    on_advance: str = ON_ADVANCE_BLOCK,
    **kwargs: Any,
) -> Dict[str, Any]:
    data = {"type": anim_type, "on_advance": on_advance}
    data.update(kwargs)
    return data


def make_continue_animation(
    continue_steps: int,
    end_state: str = "start",
    anim_type: str = "once",
) -> Dict[str, Any]:
    # end_state is a policy string (e.g., "start", "keep", "end_step").
    return make_animation(
        anim_type=anim_type,
        on_advance=ON_ADVANCE_CONTINUE,
        continue_steps=continue_steps,
        end_state=end_state,
    )


def make_action(
    action: str,
    target: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    animation: Optional[Dict[str, Any]] = None,
    sequence: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {"action": action}
    if target is not None:
        data["target"] = target
    if params:
        data["params"] = params
    if animation:
        data["animation"] = animation
    if sequence:
        data["sequence"] = sequence
    return data


def make_step(
    step_id: str,
    text: Optional[Dict[str, Any]] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    source_index: Optional[int] = None,
) -> Dict[str, Any]:
    data: Dict[str, Any] = {"id": step_id}
    if text is not None:
        data["text"] = text
    if actions:
        data["actions"] = actions
    if source_index is not None:
        data["source_index"] = source_index
    return data
