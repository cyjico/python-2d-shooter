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

    # The pressed button may have been destroyed since last frame.
    if ui_state.pressed is not None and not world.has_component(
        ui_state.pressed, UIButton
    ):
        ui_state.pressed = None

    # Topmost UI element under the cursor.
    top, top_key = None, None
    for entity, (ui,) in world.query(UIRect):
        is_button = world.has_component(entity, UIButton)
        if not (is_button or world.has_component(entity, UIPanel)):
            continue
        if not ui.rect.collidepoint(mouse):
            continue

        key = (ui.layer, is_button)
        if top_key is None or key >= top_key:
            top, top_key = entity, key

    ui_state.is_pointer_over_ui = top is not None

    hovered = None
    if top is not None:
        top_button = world.try_get_component(top, UIButton)
        if top_button is not None and top_button.enabled:
            hovered = top
    ui_state.hovered = hovered

    if inputs.primary_pressed:
        ui_state.pressed = hovered

    if inputs.primary_released:
        pressed = ui_state.pressed
        if pressed is not None and pressed == hovered:
            button = world.try_get_component(pressed, UIButton)
            if button is not None:
                events.emit(ButtonClicked(pressed, button.action))

        ui_state.pressed = None

    for entity, (button,) in world.query(UIButton):
        if entity == ui_state.pressed and entity == hovered:
            button.state = ButtonState.PRESSED
        elif entity == hovered:
            button.state = ButtonState.HOVERED
        else:
            button.state = ButtonState.NORMAL
