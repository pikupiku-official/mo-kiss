"""The demo owns its sequence independently of the regular game calendar."""

from dataclasses import dataclass


TITLE_IDLE_MS = 20_000


@dataclass(frozen=True)
class Stage:
    name: str
    kind: str
    source: str = ""
    date: str = "1999-05-31"
    period: str = "朝"
    answer_turning_point: str = ""
    answer_prompt: str = ""


STAGES = (
    Stage("op", "dialogue", "GD000.ks"),
    Stage("morning", "dialogue", "GD001.ks",
          answer_turning_point="MOMOKO_GD_MONEY", answer_prompt="桃子が誘いを渋る理由は？"),
    Stage("before_map", "choice"),
    Stage("map", "map", period="昼"),
    Stage("noon", "dialogue", "GD002.ks", period="昼"),
    Stage("evening", "dialogue", "GD003.ks", period="放課後"),
    Stage("home", "home", period="夜"),
    Stage("before_monologue", "choice", period="夜"),
    Stage("monologue", "dialogue", "GD004.ks", "1999-06-15", "朝"),
    Stage("free_text", "dialogue", "GD005.ks", "1999-06-15", "昼"),
    Stage("ending", "movie", "PV1min.mp4", "1999-06-15", "昼"),
)


class DemoFlow:
    def __init__(self):
        self.index = -1

    @property
    def stage(self):
        return STAGES[self.index] if 0 <= self.index < len(STAGES) else None

    def start(self):
        self.index = 0
        return self.stage

    def advance(self):
        self.index += 1
        return self.stage

    def reset(self):
        self.index = -1
