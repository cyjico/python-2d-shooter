from game.components.loadout import FireMode, GunSpec

PISTOL = GunSpec(
    id="pistol",
    name="Pistol",
    fire_mode=FireMode.SEMI,
    damage=20,
    fire_rate=4.0,
    magazine_size=12,
    max_reserve=60,
    reload_time=1.2,
    projectile_speed=800,
    max_range=500,
    spread=1.5,
    knockback=600,
)

SMG = GunSpec(
    id="smg",
    name="SMG",
    fire_mode=FireMode.AUTO,
    damage=12,
    fire_rate=14.0,
    magazine_size=32,
    max_reserve=160,
    reload_time=1.6,
    projectile_speed=850,
    max_range=450,
    spread=5.0,
    knockback=400,
    projectile_color=(255, 200, 90),
)

RIFLE = GunSpec(
    id="rifle",
    name="Assault Rifle",
    fire_mode=FireMode.AUTO,
    damage=28,
    fire_rate=8.0,
    magazine_size=30,
    max_reserve=150,
    reload_time=2.0,
    projectile_speed=1000,
    max_range=700,
    spread=2.5,
    knockback=900,
    projectile_size=(12.0, 4.0),
)

SHOTGUN = GunSpec(
    id="shotgun",
    name="Shotgun",
    fire_mode=FireMode.SEMI,
    damage=12,
    fire_rate=1.2,
    magazine_size=6,
    max_reserve=36,
    reload_time=2.4,
    projectile_speed=800,
    max_range=300,
    spread=9.0,
    pellets=8,
    knockback=700,
    projectile_size=(6.0, 3.0),
    projectile_color=(255, 160, 80),
)

SNIPER = GunSpec(
    id="sniper",
    name="Sniper",
    fire_mode=FireMode.SEMI,
    damage=120,
    fire_rate=0.8,
    magazine_size=5,
    max_reserve=30,
    reload_time=3.0,
    projectile_speed=1400,
    max_range=1500,
    spread=0.0,
    pierce=2,
    knockback=6000,
    projectile_size=(24.0, 3.0),
    projectile_color=(140, 220, 255),
)

ALL_GUNS: dict[str, GunSpec] = {g.id: g for g in (PISTOL, SMG, RIFLE, SHOTGUN, SNIPER)}
