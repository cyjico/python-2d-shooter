"""ASRP's startup intro: the lead developer's photo with a slow push-in and
the team name landing on the audio's big hit. Plays every time the game opens.

The timeline fits itself to the intro audio file, so swapping the audio
re-times everything. Without a file, a synthesized sound is used."""

import math
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pygame

INTRO_DIR = Path(__file__).parent.parent / "assets" / "intro"
IMAGE_PATH = INTRO_DIR / "asrp_lead_dev.png"
SOUND_PATHS = [INTRO_DIR / f"asrp_intro{ext}" for ext in (".ogg", ".wav", ".mp3")]
"""The first of these that exists is played. With none, the sound is synthesized."""

TEAM_NAME = "ASRP"

ZOOM = (1.0, 1.12)
"""Image scale at the start and end: a slow push-in over the whole intro."""
FOCUS = (0.33, 0.33)
"""Point of the photo the push-in moves toward (the valve and head), 0..1."""

TEXT_SIZE = 120
TEXT_COLOR = (235, 235, 235)
TEXT_SPACING = 18
"""Extra px between letters."""
TEXT_CENTER = (0.785, 0.25)
"""Where the name sits on screen, 0..1: the empty black space top right."""
TEXT_FADE = 0.6
"""Seconds for the name to fade in, starting on the hit."""
END_FADE = 1.2
"""Seconds to fade everything to black, ending just before the audio does."""

SKIP_FADE_MS = 300
SAMPLE_RATE = 44100

# Timing of the synthesized sound (used when there's no audio file).
DURATION = 7.5
IMPACT_TIME = 3.0
FADE_OUT = (6.2, 7.2)


def _ramp(t: float, start: float, end: float):
    """0 before `start`, 1 after `end`, smooth in between."""
    if t <= start:
        return 0.0
    if t >= end:
        return 1.0
    x = (t - start) / (end - start)
    return x * x * (3 - 2 * x)


@dataclass(frozen=True, slots=True)
class Timeline:
    """When each part of the intro happens, in seconds."""

    duration: float
    impact: float
    """The big hit in the audio: the team name appears here."""
    image_fade_in: tuple[float, float]
    text_fade_in: tuple[float, float]
    fade_out: tuple[float, float]

    @classmethod
    def fitted(cls, duration: float, impact: float):
        """Build-up: the photo fades in over the first ~60% of the wait for the
        hit. The name lands on the hit. Everything fades out as the audio ends."""
        image_end = max(0.8, impact * 0.6)
        fade_end = max(impact + TEXT_FADE, duration - 0.15)
        return cls(
            duration=duration,
            impact=impact,
            image_fade_in=(min(0.5, image_end / 2), image_end),
            text_fade_in=(impact, impact + TEXT_FADE),
            fade_out=(max(impact + TEXT_FADE, fade_end - END_FADE), fade_end),
        )


SYNTH_TIMELINE = Timeline.fitted(DURATION, IMPACT_TIME)


def find_impact(sound: pygame.mixer.Sound):
    """Time (s) of the biggest jump in loudness: the audio's main hit.

    Ignores the first half second (the sound starting from silence) and the
    last 15% (the tail).
    """
    samples = np.abs(pygame.sndarray.array(sound).astype(np.float32))
    if samples.ndim > 1:
        samples = samples.mean(axis=1)

    rate = pygame.mixer.get_init()[0]
    window = max(1, int(0.1 * rate))
    count = len(samples) // window
    if count < 8:
        return sound.get_length() / 2
    loudness = samples[: count * window].reshape(count, window).mean(axis=1)

    rises = np.diff(loudness)
    first = 5
    last = max(first + 1, int(len(rises) * 0.85))
    best = first + int(np.argmax(rises[first:last]))
    return (best + 1) * window / rate


class Intro:
    def __init__(self, screen_size: tuple[int, int], image_path: Path = IMAGE_PATH):
        self.screen_size = screen_size
        self.time = 0.0
        self.done = False

        image = pygame.image.load(image_path).convert()
        # Cover the screen at the largest zoom, so per-frame scaling only shrinks.
        w, h = screen_size
        cover = max(w / image.get_width(), h / image.get_height()) * ZOOM[1]
        self.image = pygame.transform.smoothscale(
            image,
            (round(image.get_width() * cover), round(image.get_height() * cover)),
        )

        self.title = self._render_title()

        self.sound, from_file = load_sound()
        if self.sound is not None and from_file:
            self.timeline = Timeline.fitted(
                self.sound.get_length(), find_impact(self.sound)
            )
        else:
            self.timeline = SYNTH_TIMELINE
        if self.sound is not None:
            self.sound.play()

    @property
    def duration(self):
        return self.timeline.duration

    def _render_title(self):
        font = pygame.font.Font(None, TEXT_SIZE)
        letters = [font.render(c, True, TEXT_COLOR) for c in TEAM_NAME]
        width = sum(l.get_width() for l in letters) + TEXT_SPACING * (len(letters) - 1)
        height = max(l.get_height() for l in letters)
        title = pygame.Surface((width, height), pygame.SRCALPHA)
        x = 0
        for letter in letters:
            title.blit(letter, (x, 0))
            x += letter.get_width() + TEXT_SPACING
        return title

    def update(self, dt: float, events: Iterable[pygame.event.Event]):
        """Advances the intro. Returns True once it's over (finished or skipped)."""
        if any(e.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN) for e in events):
            self.skip()

        self.time += dt
        if self.time >= self.timeline.duration and not self.done:
            self.skip()
        return self.done

    def skip(self):
        if self.sound is not None:
            self.sound.fadeout(SKIP_FADE_MS)
        self.done = True

    def render(self, surface: pygame.Surface):
        surface.fill((0, 0, 0))
        t, tl = self.time, self.timeline
        fade_out = 1.0 - _ramp(t, *tl.fade_out)

        image_alpha = _ramp(t, *tl.image_fade_in) * fade_out
        if image_alpha > 0:
            self._draw_image(surface, t, image_alpha)

        text_alpha = _ramp(t, *tl.text_fade_in) * fade_out
        if text_alpha > 0:
            title = self.title.copy()
            title.set_alpha(round(255 * text_alpha))
            w, h = self.screen_size
            center = (round(w * TEXT_CENTER[0]), round(h * TEXT_CENTER[1]))
            surface.blit(title, title.get_rect(center=center))

    def _draw_image(self, surface: pygame.Surface, t: float, alpha: float):
        w, h = self.screen_size
        # Linear over the whole intro reads as a steady, slow camera move.
        progress = min(1.0, t / self.timeline.duration)
        zoom = ZOOM[0] + (ZOOM[1] - ZOOM[0]) * progress
        # The source is pre-scaled so 1 source px = 1 screen px at full zoom.
        # At a smaller zoom the screen shows a bigger window of it; that
        # window shrinks toward FOCUS as the zoom grows.
        iw, ih = self.image.get_size()
        crop_w = w * ZOOM[1] / zoom
        crop_h = h * ZOOM[1] / zoom
        fx, fy = FOCUS[0] * iw, FOCUS[1] * ih
        # Keep the focus point at the same relative spot of the crop.
        left = fx - FOCUS[0] * crop_w
        top = fy - FOCUS[1] * crop_h
        left = min(max(0.0, left), iw - crop_w)
        top = min(max(0.0, top), ih - crop_h)

        crop = self.image.subsurface(
            pygame.Rect(round(left), round(top), round(crop_w), round(crop_h)).clip(
                self.image.get_rect()
            )
        )
        frame = pygame.transform.smoothscale(crop, (w, h))
        if alpha < 1.0:
            frame.set_alpha(round(255 * alpha))
        surface.blit(frame, (0, 0))


# --- Sound ---


def load_sound():
    """(sound, came from a file). The intro audio file if there is one, else
    the synthesized sound. The sound is None if there's no audio device."""
    if pygame.mixer.get_init() is None:
        return None, False
    for path in SOUND_PATHS:
        if path.exists():
            try:
                return pygame.mixer.Sound(path), True
            except pygame.error:
                continue  # Unreadable; try the next one or fall back.
    return synthesize_sound(), False


def _envelope(t: np.ndarray, attack: float, decay: float, start: float = 0.0):
    """Instant-ish rise at `start`, exponential decay with time constant `decay`."""
    local = t - start
    rise = np.clip(local / attack, 0.0, 1.0)
    return np.where(local < 0, 0.0, rise * np.exp(-np.maximum(local, 0) / decay))


def synthesize_samples(rng: np.random.Generator | None = None):
    """The fallback intro audio as mono floats in -1..1."""
    rng = rng or np.random.default_rng(7)
    t = np.arange(int(DURATION * SAMPLE_RATE)) / SAMPLE_RATE

    # Drone: a low root and fifth, slightly detuned so they beat slowly.
    swell = np.clip(t / IMPACT_TIME, 0, 1) ** 2
    release = 1.0 - np.clip((t - FADE_OUT[0]) / (FADE_OUT[1] - FADE_OUT[0]), 0, 1)
    drone = (
        np.sin(2 * math.pi * 55.0 * t)
        + 0.8 * np.sin(2 * math.pi * 55.35 * t)
        + 0.45 * np.sin(2 * math.pi * 82.4 * t)
        + 0.15 * np.sin(2 * math.pi * 110.0 * t)
    )
    drone *= 0.22 * swell * release

    noise = rng.standard_normal(t.size)

    # Pipe hiss: bright noise (first difference ~ high-pass) bursting at impact.
    hiss = np.diff(noise, prepend=0.0) * 0.5
    hiss *= 0.18 * _envelope(t, 0.02, 0.9, IMPACT_TIME)

    # Clank: inharmonic partials, like struck metal pipe, plus a thump.
    clank = sum(
        amp * np.sin(2 * math.pi * freq * t) * _envelope(t, 0.002, decay, IMPACT_TIME)
        for freq, amp, decay in (
            (311.0, 0.50, 0.70),
            (743.0, 0.35, 0.45),
            (1187.0, 0.25, 0.30),
            (1873.0, 0.18, 0.20),
            (2715.0, 0.10, 0.12),
        )
    )
    thump = 0.6 * np.sin(2 * math.pi * 48.0 * t) * _envelope(t, 0.004, 0.25, IMPACT_TIME)
    click = 0.3 * noise * _envelope(t, 0.001, 0.015, IMPACT_TIME)

    mix = drone + hiss + 0.35 * clank + thump + click
    # Soft clip, then normalize with headroom.
    mix = np.tanh(mix * 1.4)
    return mix / max(1e-9, np.max(np.abs(mix))) * 0.8


def synthesize_sound():
    """The fallback intro sound in the mixer's format, or None if there's no audio."""
    init = pygame.mixer.get_init()
    if init is None:
        return None
    _, fmt, channels = init

    samples = synthesize_samples()
    if fmt == -16:
        data = (samples * 32767).astype(np.int16)
    elif fmt == 16:
        data = ((samples + 1) * 32767.5).astype(np.uint16)
    elif fmt == 32:
        data = (samples * 2_147_483_647).astype(np.int32)
    else:
        data = samples.astype(np.float32)

    if channels > 1:
        data = np.repeat(data[:, None], channels, axis=1)
    try:
        return pygame.sndarray.make_sound(np.ascontiguousarray(data))
    except (pygame.error, ValueError):
        return None
