from game.components.ui import ButtonState, UIButton, UIPanel, UIRect
from game.core_ecs.world import World
from game.events.ui import ButtonClicked
from game.resources.event_bus import EventBus
from game.resources.input_state import InputState
from game.resources.ui_state import UIState


def ui_interaction_system(world: World):
    inputs = world.get_resource(InputState)
    ui_state = world.get_resource(UIState)
    events = world.get_resource(EventBus)
    mouse = (int(inputs.mouse_pos.x), int(inputs.mouse_pos.y))

    # Topmost enabled button under the cursor.
    hovered, best_layer = None, None
    for entity, (ui, button) in world.query(UIRect, UIButton):
        if button.enabled and ui.rect.collidepoint(mouse):
            if best_layer is None or ui.layer >= best_layer:
                hovered, best_layer = entity, ui.layer

    ui_state.hovered = hovered

    # Panels and buttons swallow pointer input so clicks don't leak to gameplay.
    ui_state.is_pointer_over_ui = hovered is not None or any(
        ui.rect.collidepoint(mouse) for _, (ui, _) in world.query(UIRect, UIPanel)
    )

    if inputs.primary_pressed:
        ui_state.pressed = hovered

    if inputs.primary_released:
        pressed = ui_state.pressed
        if pressed is not None and pressed == hovered:
            button = world.get_component(pressed, UIButton)
            events.emit(ButtonClicked(pressed, button.action))
        ui_state.pressed = None

    for entity, (button,) in world.query(UIButton):
        if entity == ui_state.pressed and entity == hovered:
            button.state = ButtonState.PRESSED
        elif entity == hovered:
            button.state = ButtonState.HOVERED
        else:
            button.state = ButtonState.NORMAL
