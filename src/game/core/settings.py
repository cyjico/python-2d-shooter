from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    window_size: tuple[int, int] = (800, 600)
    window_title: str = "2D Shooter"

    target_fps: int = 60
    max_frame_time: float = 0.05

    background_color: tuple[int, int, int] = (30, 30, 30)


DEFAULT_SETTINGS = Settings()
