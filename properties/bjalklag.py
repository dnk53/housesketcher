# ________________________________________________________________________________________________
# BJÄLKLAG - Bjälklagets egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, BoolProperty, EnumProperty

from .. import utils

# Globala variabler för att förhindra cirkulära uppdateringar
_updating_from_ui = False
_last_selected_bjalklag = None


def bt_update_bjalklag(self, context):
    """Uppdaterar markerade bjälklag när användaren ändrar parametrar i panelen"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_bjalklag = [obj for obj in context.selected_objects if obj.name.startswith("bjalklag")]
    
    if not selected_bjalklag:
        return
    
    p = scene.bt_bjalklag
    
    for bjalklag in selected_bjalklag:
        # Spara parametrar i custom properties
        bjalklag["start_x"] = p.start_x
        bjalklag["start_y"] = p.start_y
        bjalklag["langd_x"] = p.langd_x
        bjalklag["bredd_y"] = p.bredd_y
        bjalklag["niva_z"] = p.niva_z
        bjalklag["tjocklek"] = p.tjocklek
        bjalklag["guide_type"] = p.guide_type
        
        # Uppdatera geometrin (inklusive Boolean)
        utils.bt_update_single_bjalklag(bjalklag, context)


def sync_bjalklag_panel_from_selection(context):
    """Synkroniserar panelens properties från markerat bjälklag"""
    global _updating_from_ui, _last_selected_bjalklag
    
    scene = context.scene
    selected = [obj for obj in context.selected_objects if obj.name.startswith("bjalklag")]
    
    if not selected:
        return
    
    bjalklag = selected[0]
    
    # Kolla om det är samma bjälklag som tidigare
    if bjalklag == _last_selected_bjalklag:
        return
    
    _last_selected_bjalklag = bjalklag
    p = scene.bt_bjalklag
    
    _updating_from_ui = True
    
    try:
        # Läs alla parametrar från bjälklagets custom properties
        if "start_x" in bjalklag:
            p.start_x = bjalklag["start_x"]
        if "start_y" in bjalklag:
            p.start_y = bjalklag["start_y"]
        if "langd_x" in bjalklag:
            p.langd_x = bjalklag["langd_x"]
        if "bredd_y" in bjalklag:
            p.bredd_y = bjalklag["bredd_y"]
        if "niva_z" in bjalklag:
            p.niva_z = bjalklag["niva_z"]
        if "tjocklek" in bjalklag:
            p.tjocklek = bjalklag["tjocklek"]
        if "guide_type" in bjalklag:
            p.guide_type = bjalklag["guide_type"]
    finally:
        _updating_from_ui = False


class BT_BjälklagProperties(bpy.types.PropertyGroup):
    """Inställningar för bjälklag"""
    
    start_x: FloatProperty(
        name="Start X",
        description="Startposition i X-led (0 = utsida vänster vägg, negativt = utanför)",
        default=0.0,
        step=10,
        update=bt_update_bjalklag
    )
    
    start_y: FloatProperty(
        name="Start Y",
        description="Startposition i Y-led (0 = utsida framvägg, negativt = utanför)",
        default=0.0,
        step=10,
        update=bt_update_bjalklag
    )
    
    langd_x: FloatProperty(
        name="Length X",
        description="Längd i X-led (0 = hela vägen, negativt = till insida höger vägg)",
        default=0.0,
        step=10,
        update=bt_update_bjalklag
    )
    
    bredd_y: FloatProperty(
        name="Width Y",
        description="Bredd i Y-led (0 = hela vägen, negativt = till insida bakvägg)",
        default=0.0,
        step=10,
        update=bt_update_bjalklag
    )
    
    niva_z: FloatProperty(
        name="Level Z",
        description="Höjd för bjälklagets ovansida",
        default=3.0,
        min=0.0,
        step=10,
        update=bt_update_bjalklag
    )
    
    tjocklek: FloatProperty(
        name="Thickness",
        description="Bjälklagets tjocklek",
        default=0.30,
        min=0.02,
        step=1,
        update=bt_update_bjalklag
    )
    
    # ----- Välj guide för bjälklaget -----
    guide_type: EnumProperty(
        name="Guide",
        description="Which guide to use as Boolean INTERSECT for the floor slab",
        items=[
            ('NONE', "None", "No Boolean modifier"),
            ('INTERIOR', "Interior Guide", "Cut to interior walls"),
            ('EXTERIOR', "Exterior Guide", "Cut to exterior walls"),
            ('WALL', "Wall Guide", "Cut to wall guide (under roof)")
        ],
        default='INTERIOR',
        update=bt_update_bjalklag
    )