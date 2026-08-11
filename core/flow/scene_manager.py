"""Lifecycle management for the active full-screen subsystem."""

from __future__ import annotations


class SceneManager:
    """Own the current scene and enforce cleanup-before-enter ordering."""

    def __init__(self, initial_mode="menu"):
        self.current_mode = initial_mode
        self.current_subsystem = None

    def switch_to(self, subsystem, mode_name: str) -> None:
        if self.current_subsystem:
            self.current_subsystem.cleanup()
            print(f"🔇 {self.current_mode} cleanup完了")
        self.current_subsystem = subsystem
        self.current_mode = mode_name
        self.current_subsystem.on_enter()
        print(f"✅ {mode_name} に切り替え")
