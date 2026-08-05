# ________________________________________________________________________________________________
# HOUSESKETCHER - Interactive house design for Blender
# ________________________________________________________________________________________________

bl_info = {
    "name": "HouseSketcher",
    "author": "Dan-Åke Engqvist",
    "version": (1, 0, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Sidebar > HouseSketcher",
    "description": "Sketch and build houses interactively in Blender",
    "category": "Mesh",
    "license": ["GPL-2.0-or-later"]
}

import bpy

# ---------------------------------------------------------------------------
# 1. IMPORTERA MODULER
# ---------------------------------------------------------------------------
from .properties import (
    huvudmatt, platta, vagg, vagg_settings, tak, bjalklag, fonster, dorr, innervagg
)
from .operators import (
    generera_hus, generera_platta, generera_vagg, 
    generera_tak, generera_bjalklag, generera_fonster, generera_dorr,
    generera_innervagg,
    meny_hantering
)
from . import ui
from . import utils


# ---------------------------------------------------------------------------
# 2. REGISTRERINGSKLASSER
# ---------------------------------------------------------------------------
classes = (
    # Properties
    huvudmatt.BT_HuvudmåttProperties,
    platta.BT_PlattaProperties,
    vagg_settings.BT_VaggSettingsProperties,
    vagg.BT_VaggProperties,
    tak.BT_TakProperties,
    bjalklag.BT_BjälklagProperties,
    fonster.BT_FonsterProperties,
    dorr.BT_DorrProperties,
    innervagg.BT_InnervaggProperties,  # <-- LÄGG TILL
    
    # Operators
    generera_hus.MESH_OT_bt_skapa_hus,
    generera_platta.MESH_OT_bt_skapa_platta,
    generera_vagg.MESH_OT_bt_skapa_vagg,
    generera_tak.MESH_OT_bt_skapa_tak,
    generera_bjalklag.MESH_OT_bt_skapa_bjalklag,
    generera_fonster.MESH_OT_bt_skapa_fonster,
    generera_dorr.MESH_OT_bt_skapa_dorr,
    generera_innervagg.MESH_OT_bt_skapa_innervagg,  # <-- LÄGG TILL
    meny_hantering.MESH_OT_bt_dolj_alla_menyer,
    meny_hantering.MESH_OT_bt_uppdatera_mallar,
    
    # UI
    ui.VIEW3D_PT_huvudpanel,
)


# ---------------------------------------------------------------------------
# 3. REGISTRERING
# ---------------------------------------------------------------------------
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Scene properties
    bpy.types.Scene.bt_huvudmått = bpy.props.PointerProperty(type=huvudmatt.BT_HuvudmåttProperties)
    bpy.types.Scene.bt_platta = bpy.props.PointerProperty(type=platta.BT_PlattaProperties)
    bpy.types.Scene.bt_vagg = bpy.props.PointerProperty(type=vagg.BT_VaggProperties)
    bpy.types.Scene.bt_vagg_settings = bpy.props.PointerProperty(type=vagg_settings.BT_VaggSettingsProperties)
    bpy.types.Scene.bt_tak = bpy.props.PointerProperty(type=tak.BT_TakProperties)
    bpy.types.Scene.bt_bjalklag = bpy.props.PointerProperty(type=bjalklag.BT_BjälklagProperties)
    bpy.types.Scene.bt_fonster = bpy.props.PointerProperty(type=fonster.BT_FonsterProperties)
    bpy.types.Scene.bt_dorr = bpy.props.PointerProperty(type=dorr.BT_DorrProperties)
    bpy.types.Scene.bt_innervagg = bpy.props.PointerProperty(type=innervagg.BT_InnervaggProperties)  # <-- LÄGG TILL
    
    # UI-kollaps properties
    bpy.types.Scene.bt_show_huvudmått = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_symmetrisk = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_osymmetrisk = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_asymmetric = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_mansard = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_platta = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_vagg = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_tak = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_bjalklag = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_fonster = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_dorr = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.bt_show_innervagg = bpy.props.BoolProperty(default=False)  # <-- LÄGG TILL
    
    # Synkroniseringshandlare
    bpy.app.handlers.depsgraph_update_post.append(utils.bt_master_synk_handler)
    bpy.app.handlers.depsgraph_update_post.append(utils.bt_selection_handler)
    
    # START: msgbus
    utils.bt_setup_msgbus()
    
    # Sätt update-funktioner
    utils.set_update_functions()


def unregister():
    # STOPP: msgbus
    utils.bt_clear_msgbus()
    
    # Ta bort handlare
    if utils.bt_master_synk_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(utils.bt_master_synk_handler)
    if utils.bt_selection_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(utils.bt_selection_handler)
    
    # Ta bort scene properties
    props = [
        'bt_huvudmått', 'bt_platta', 'bt_vagg', 'bt_vagg_settings', 
        'bt_tak', 'bt_bjalklag', 'bt_fonster', 'bt_dorr', 'bt_innervagg',
        'bt_show_huvudmått', 'bt_show_symmetrisk', 'bt_show_osymmetrisk',
        'bt_show_asymmetric', 'bt_show_mansard',
        'bt_show_platta', 'bt_show_vagg', 'bt_show_tak', 
        'bt_show_bjalklag', 'bt_show_fonster', 'bt_show_dorr', 'bt_show_innervagg'
    ]
    for prop in props:
        try:
            delattr(bpy.types.Scene, prop)
        except:
            pass
    
    # Avregistrera klasser
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except:
            pass


if __name__ == "__main__":
    register()