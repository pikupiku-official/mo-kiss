"""Save-slot and resume-state flow for the application shell."""

from core.flow.game_flow import Navigate, Scene


class SessionFlow:
    """Coordinate persistence with scene restoration without owning UI state."""

    def __init__(
        self,
        application,
        *,
        save_manager_getter,
        dialogue_factory,
        dialogue_type,
    ):
        self.application = application
        self._save_manager_getter = save_manager_getter
        self._dialogue_factory = dialogue_factory
        self._dialogue_type = dialogue_type

    @staticmethod
    def serialize_completion(completion):
        if isinstance(completion, Navigate):
            return {"type": "navigate", "scene": completion.scene.value}
        if isinstance(completion, str):
            return {"type": "legacy", "value": completion}
        return None

    @staticmethod
    def deserialize_completion(data):
        if not isinstance(data, dict):
            return None
        if data.get("type") == "navigate":
            try:
                return Navigate(Scene(data.get("scene")))
            except ValueError:
                return None
        if data.get("type") == "legacy":
            return data.get("value")
        return None

    def build_resume_state(self, mode=None):
        app = self.application
        mode = mode or app.current_mode
        state = {"version": 1, "mode": mode}
        if mode == "dialogue" and isinstance(
            app.current_subsystem, self._dialogue_type
        ):
            state["dialogue"] = app.current_subsystem.export_save_state()
            state["completion"] = self.serialize_completion(
                app.dialogue_completion_result
            )
        return state

    def save_manual_slot(self, slot_name: str, thumbnail_surface=None) -> bool:
        manager = self._save_manager_getter()
        if not manager.write_resume_state(self.build_resume_state()):
            return False
        return manager.save_game(
            slot_name,
            thumbnail_surface=thumbnail_surface,
        )

    def autosave(self, mode: str, slot_name: str) -> bool:
        manager = self._save_manager_getter()
        manager.write_resume_state(self.build_resume_state(mode))
        return manager.save_game(slot_name)

    def resume_loaded_state(self) -> None:
        app = self.application
        state = self._save_manager_getter().get_resume_state()
        mode = state.get("mode")
        app.reload_game_systems()

        if mode == "dialogue" and isinstance(state.get("dialogue"), dict):
            if self._resume_dialogue(state):
                return

        app.dialogue_completion_result = None
        app.current_event_id = None
        if mode == "home":
            app.switch_to_home()
        else:
            app.switch_to_map()

    def _resume_dialogue(self, state) -> bool:
        app = self.application
        snapshot = state["dialogue"]
        event_file = snapshot.get("event_file")
        if not event_file and snapshot.get("event_id"):
            event_file = f"events/{snapshot['event_id']}.ks"
        if not event_file:
            return False

        dialogue = self._dialogue_factory(event_file)
        dialogue.restore_save_state(snapshot)
        app.current_event_id = dialogue.current_event_id
        app.dialogue_completion_result = self.deserialize_completion(
            state.get("completion")
        )
        app.switch_to(dialogue, "dialogue")
        return True
