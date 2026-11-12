from dataclasses import dataclass, field


@dataclass(slots=True)
class Health:
    maximum: float
    current: float = field(init=False)

    def __post_init__(self):
        self.current = self.maximum
