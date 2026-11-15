import math

from game.components.hud import (
    WaveBannerLabel,
    WaveBannerSubLabel,
    WaveLabel,
    WaveRemainingLabel,
)
from game.components.ui import UILabel
from game.core_ecs.world import World
from game.resources.enemy_director import EnemyDirector, WavePhase
from game.systems.enemy_spawn import wave_remaining
from game.util.roman import to_roman

WAVE_COLOR = (235, 225, 200)
REMAINING_COLOR = (190, 190, 200)
LAST_ENEMY_COLOR = (255, 90, 90)
CLEARED_COLOR = (120, 230, 120)


def wave_hud_system(world: World):
    """Bottom right: the wave in roman numerals and enemies left. During a
    break, a banner announces the next wave; with one enemy left, it says so."""
    director = world.get_resource(EnemyDirector)

    if director.phase is WavePhase.ACTIVE:
        wave = director.wave
        remaining = wave_remaining(world)
        # Same test as the cue that points at it, so there's always one to see.
        last = not director.roster and remaining == 1
        corner = "1 ENEMY LEFT" if last else f"{remaining} left"
        corner_color = LAST_ENEMY_COLOR if last else REMAINING_COLOR
        banner = ""
        sub = "1 ENEMY LEFT" if last else ""
        sub_color = LAST_ENEMY_COLOR
    else:
        # The break shows the wave that's coming.
        wave = director.wave + 1
        # Clamped: a paused director (e.g. in tests) has an infinite timer.
        seconds = max(1, math.ceil(min(director.timer, 99.0)))
        corner = f"starts in {seconds}"
        corner_color = REMAINING_COLOR
        banner = f"WAVE {to_roman(wave)}"
        if director.held:
            corner = "pick a perk"
            sub = f"Wave {to_roman(director.wave)} cleared - choose a perk"
            sub_color = CLEARED_COLOR
        elif director.just_cleared:
            sub = f"Wave {to_roman(director.wave)} cleared - next in {seconds}"
            sub_color = CLEARED_COLOR
        else:
            sub = f"Get ready - {seconds}"
            sub_color = WAVE_COLOR

    for _, (label, _) in world.query(UILabel, WaveLabel):
        label.text = f"WAVE {to_roman(wave)}"
    for _, (label, _) in world.query(UILabel, WaveRemainingLabel):
        label.text, label.color = corner, corner_color
    for _, (label, _) in world.query(UILabel, WaveBannerLabel):
        label.text = banner
    for _, (label, _) in world.query(UILabel, WaveBannerSubLabel):
        label.text, label.color = sub, sub_color
