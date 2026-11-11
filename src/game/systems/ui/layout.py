from game.components.ui import UIRect
from game.core_ecs.world import World
from game.resources.camera import Camera


def ui_layout_system(world: World):
    vw, vh = world.get_resource(Camera).viewport_size

    for _, (ui,) in world.query(UIRect):
        w, h = ui.size
        x = vw * ui.anchor[0] + ui.offset[0] - w * ui.pivot[0]
        y = vh * ui.anchor[1] + ui.offset[1] - h * ui.pivot[1]
        ui.rect.update(round(x), round(y), w, h)
