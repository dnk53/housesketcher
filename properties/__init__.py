# ________________________________________________________________________________________________
# PROPERTIES PAKET
# ________________________________________________________________________________________________

from . import huvudmatt
from . import platta
from . import vagg
from . import vagg_settings
from . import tak
from . import bjalklag
from . import fonster
from . import dorr
from . import innervagg

classes = (
    huvudmatt.BT_HuvudmåttProperties,
    platta.BT_PlattaProperties,
    vagg_settings.BT_VaggSettingsProperties,
    vagg.BT_VaggProperties,
    tak.BT_TakProperties,
    bjalklag.BT_BjälklagProperties,
    fonster.BT_FonsterProperties,
    dorr.BT_DorrProperties,
    innervagg.BT_InnervaggProperties,
)


def register_properties():
    """Registrera alla scene-properties"""
    import bpy
    
    # Komponent-properties
    bpy.types.Scene.bt_selected_component = bpy.props.EnumProperty(
        name="Component",
        description="Select a component to place",
        items=ui.get_component_items  # <-- ANVÄND UI-CALLBACK
    )
    
    bpy.types.Scene.bt_component_placering = bpy.props.FloatProperty(
        name="Placement",
        description="Position along wall (0=center, negative=from right)",
        default=0.0,
        step=10
    )
    
    bpy.types.Scene.bt_show_komponenter = bpy.props.BoolProperty(
        name="Show Components",
        default=False
    )


def unregister_properties():
    """Avregistrera alla scene-properties"""
    import bpy
    
    props = [
        'bt_selected_component',
        'bt_component_placering',
        'bt_show_komponenter'
    ]
    for prop in props:
        try:
            delattr(bpy.types.Scene, prop)
        except:
            pass