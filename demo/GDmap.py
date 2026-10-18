"""Temporary school destination selector; intentionally only one destination."""

from demo.screens import ChoiceScreen


class GDMap(ChoiceScreen):
    def __init__(self, screen):
        super().__init__(screen, ("教室",), ("demo_next",))
