# ________________________________________________________________________________________________
# FÖNSTER - Fönstrens egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty

from .. import utils

# Globala variabler
_updating_from_ui = False
_last_selected_fonster = None

def bt_update_fonster_placering(self, context):
    """Uppdaterar fönstrets position när placering ändras"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_fonster = [o for o in context.selected_objects if o.name.startswith("Fönster_")]
    
    if not selected_fonster:
        return
    
    # Uppdatera alla markerade fönster
    for fonster in selected_fonster:
        fonster["placering"] = self.placering
        
        parent_obj = fonster.parent
        if parent_obj and parent_obj.get("typ") == "vägg":
            wall_length = parent_obj.get("vagg_langd", 5.0)
            
            x_pos = self.placering
            if x_pos == 0:
                x_pos = wall_length / 2.0
            elif x_pos < 0:
                x_pos = wall_length + x_pos
            
            fonster.location.x = x_pos


def bt_update_fonster(self, context):
    """Uppdaterar markerade fönster när användaren ändrar parametrar"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_fonster = [o for o in context.selected_objects if o.name.startswith("Fönster_")]
    
    if not selected_fonster:
        return
    
    p = scene.bt_fonster
    
    values = {
        "bredd": p.bredd,
        "hojd": p.hojd,
        "karmtjocklek": p.karmtjocklek,
        "karmdjup": p.karmdjup,
        "indragning": p.indragning,
        "brostning": p.brostning
    }
    
    # Uppdatera alla markerade fönster
    for fonster in selected_fonster:
        fonster["fonster_bredd"] = p.bredd
        fonster["fonster_hojd"] = p.hojd
        fonster["karmtjocklek"] = p.karmtjocklek
        fonster["karmdjup"] = p.karmdjup
        fonster["indragning"] = p.indragning
        fonster["brostning"] = p.brostning
        
        utils.bt_update_single_fonster(fonster, values)


# FUNKTION FÖR ATT SYNKRONISERA PANELEN FRÅN MARKERAT FÖNSTER
def sync_fonster_panel_from_selection(context):
    """Synkroniserar panelens properties från markerat fönster"""
    global _updating_from_ui, _last_selected_fonster
    
    scene = context.scene
    selected = [o for o in context.selected_objects if o.name.startswith("Fönster_")]
    
    if not selected:
        return
    
    fonster = selected[0]
    
    # Kolla om det är samma fönster som tidigare
    if fonster == _last_selected_fonster:
        return
    
    _last_selected_fonster = fonster
    p = scene.bt_fonster
    
    # Sätt flaggan så att properties inte triggar uppdateringar
    _updating_from_ui = True
    
    try:
        # Uppdatera panelens värden från fönstrets custom properties
        if "fonster_bredd" in fonster:
            p.bredd = fonster["fonster_bredd"]
        if "fonster_hojd" in fonster:
            p.hojd = fonster["fonster_hojd"]
        if "karmtjocklek" in fonster:
            p.karmtjocklek = fonster["karmtjocklek"]
        if "karmdjup" in fonster:
            p.karmdjup = fonster["karmdjup"]
        if "indragning" in fonster:
            p.indragning = fonster["indragning"]
        if "brostning" in fonster:
            p.brostning = fonster["brostning"]
        if "placering" in fonster:
            p.placering = fonster["placering"]
    finally:
        _updating_from_ui = False


class BT_FonsterProperties(bpy.types.PropertyGroup):
    """Inställningar för fönster"""
    
    bredd: FloatProperty(
        name="Bredd",
        default=1.2,
        min=0.2,
        step=10,
        update=bt_update_fonster
    )
    
    hojd: FloatProperty(
        name="Höjd",
        default=1.4,
        min=0.2,
        step=10,
        update=bt_update_fonster
    )
    
    karmtjocklek: FloatProperty(
        name="Karmtjocklek",
        default=0.05,
        min=0.01,
        step=1,
        update=bt_update_fonster
    )
    
    karmdjup: FloatProperty(
        name="Karmdjup",
        default=0.10,
        min=0.01,
        step=1,
        update=bt_update_fonster
    )
    
    brostning: FloatProperty(
        name="Bröstningshöjd",
        default=0.9,
        min=0.0,
        step=10,
        update=bt_update_fonster
    )
    
    indragning: FloatProperty(
        name="Indragning från utsida",
        default=0.05,
        min=0.0,
        step=1,
        update=bt_update_fonster
    )
    
    placering: FloatProperty(
        name="Placering",
        description="Avstånd från vänster kant (positivt) eller höger kant (negativt). 0 = centrera",
        default=0.0,
        min=-100.0,
        step=10,
        update=bt_update_fonster_placering
    )