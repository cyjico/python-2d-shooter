import os

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from game.game import Game

game = Game()
for _ in range(120):  # about 2 seconds of game time
    game.handle_events()
    game.update(1 / 60)
    game.render()

print("Smoke test passed")
