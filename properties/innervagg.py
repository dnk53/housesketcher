# ________________________________________________________________________________________________
# INNERVÄGG - Innerväggens egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, EnumProperty

from .. import utils

# ----- GLOBALA VARIABLER -----
_updating_from_ui = False
_last_selected_innervagg = None


# ----- UPDATE-FUNKTIONER -----
def bt_update_innervagg(self, context):
    """Uppdaterar markerade innerväggar när parametrar ändras"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected = [obj for obj in context.selected_objects if obj.get("typ") == "innervagg"]
    
    if not selected:
        return
    
    p = scene.bt_innervagg
    
    for innervagg in selected:
        # Spara parametrar
        innervagg["tjocklek"] = p.tjocklek
        innervagg["hojd"] = p.hojd
        innervagg["start_x"] = p.start_x
        innervagg["start_y"] = p.start_y
        innervagg["langd"] = p.langd
        innervagg["rotation"] = p.rotation
        innervagg["guide_type"] = p.guide_type
        
        # Uppdatera geometri
        utils.bt_update_single_innervagg(innervagg, context)


# ----- SYNKRONISERING FRÅN SELECTION -----
def sync_innervagg_panel_from_selection(context):
    """Synkroniserar panelens properties från markerad innervägg"""
    global _updating_from_ui, _last_selected_innervagg
    
    scene = context.scene
    selected = [obj for obj in context.selected_objects if obj.get("typ") == "innervagg"]
    
    if not selected:
        return
    
    innervagg = selected[0]
    
    # Kolla om det är samma innervägg som tidigare
    if innervagg == _last_selected_innervagg:
        return
    
    _last_selected_innervagg = innervagg
    p = scene.bt_innervagg
    
    _updating_from_ui = True
    
    try:
        # Läs alla parametrar från innerväggens custom properties
        if "tjocklek" in innervagg:
            p.tjocklek = innervagg["tjocklek"]
        if "hojd" in innervagg:
            p.hojd = innervagg["hojd"]
        if "start_x" in innervagg:
            p.start_x = innervagg["start_x"]
        if "start_y" in innervagg:
            p.start_y = innervagg["start_y"]
        if "langd" in innervagg:
            p.langd = innervagg["langd"]
        if "rotation" in innervagg:
            p.rotation = innervagg["rotation"]
        if "guide_type" in innervagg:
            p.guide_type = innervagg["guide_type"]
    finally:
        _updating_from_ui = False


# ----- PROPERTY GROUP -----
class BT_InnervaggProperties(bpy.types.PropertyGroup):
    """Inställningar för innerväggar"""
    
    tjocklek: FloatProperty(
        name="Thickness",
        description="Innerväggens tjocklek",
        default=0.120,
        min=0.02,
        step=1,
        update=bt_update_innervagg
    )
    
    hojd: FloatProperty(
        name="Height",
        description="Innerväggens höjd (0 = full höjd upp till tak)",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        step=10,
        update=bt_update_innervagg
    )
    
    start_x: FloatProperty(
        name="Start X",
        description="Startposition i X-led (0 = mitten av byggnaden)",
        default=0.15,
        step=10,
        update=bt_update_innervagg
    )
    
    start_y: FloatProperty(
        name="Start Y",
        description="Startposition i Y-led (0 = mitten av byggnaden)",
        default=0.0,
        step=10,
        update=bt_update_innervagg
    )
    
    langd: FloatProperty(
        name="Length",
        description="Innerväggens längd (0 = hela vägen till motsatt vägg)",
        default=0.0,
        step=10,
        update=bt_update_innervagg
    )
    
    rotation: FloatProperty(
        name="Rotation",
        description="Innerväggens rotation i grader (0 = X-led)",
        default=0.0,
        soft_min=0.0,
        soft_max=270.0,
        step=9000,          # <-- Steg om 90 grader
        # subtype='ANGLE',  # <-- Visas som grader i UI:t
        update=bt_update_innervagg
    )    
    
    guide_type: EnumProperty(
        name="Guide",
        description="Which guide to use for the top of the interior wall",
        items=[
            ('NONE', "None", "No guide - full height only"),
            ('INTERIOR', "Interior Guide", "Cut to interior walls"),
            ('EXTERIOR', "Exterior Guide", "Cut to exterior walls"),
            ('WALL', "Wall Guide", "Cut to wall guide (under roof)")
        ],
        default='INTERIOR',
        update=bt_update_innervagg
    )