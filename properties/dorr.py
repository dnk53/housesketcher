# ________________________________________________________________________________________________
# DÖRR - Dörrens egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, StringProperty, EnumProperty, BoolProperty

from .. import utils

# Globala variabler
_updating_from_ui = False
_last_selected_dorr = None

def bt_update_dorr_placering(self, context):
    """Uppdaterar dörrens position när placering ändras"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_dorrar = [o for o in context.selected_objects if o.get("typ") == "dorr"]
    
    if not selected_dorrar:
        return
    
    for dorr in selected_dorrar:
        dorr["placering"] = self.placering
        
        parent_obj = dorr.parent
        if parent_obj and parent_obj.get("typ") == "vägg":
            wall_length = parent_obj.get("vagg_langd", 5.0)
            
            x_pos = self.placering
            if x_pos == 0:
                x_pos = wall_length / 2.0
            elif x_pos < 0:
                x_pos = wall_length + x_pos
            
            dorr.location.x = x_pos


# MODIFIERA DENNA FUNKTION - den ska uppdatera dörrens nivå
def bt_update_dorr_niva(self, context):
    """Uppdaterar dörrens nivå när niva ändras"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_dorrar = [o for o in context.selected_objects if o.get("typ") == "dorr"]
    
    if not selected_dorrar:
        return
    
    p = scene.bt_dorr
    for dorr in selected_dorrar:
        dorr["niva"] = p.niva
        dorr.location.z = p.niva  # Detta är nyckeln!


def bt_update_dorr(self, context):
    """Uppdaterar markerade dörrar när användaren ändrar parametrar"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected_dorrar = [o for o in context.selected_objects if o.get("typ") == "dorr"]
    
    if not selected_dorrar:
        return
    
    p = scene.bt_dorr
    
    values = {
        "bredd": p.bredd,
        "hojd": p.hojd,
        "karmtjocklek": p.karmtjocklek,
        "karmdjup": p.karmdjup,
        "indragning": p.indragning,
        "tröskelhöjd": p.tröskelhöjd
    }
    
    for dorr in selected_dorrar:
        # Spara alla parametrar
        dorr["dorr_bredd"] = p.bredd
        dorr["dorr_hojd"] = p.hojd
        dorr["karmtjocklek"] = p.karmtjocklek
        dorr["karmdjup"] = p.karmdjup
        dorr["indragning"] = p.indragning
        dorr["tröskelhöjd"] = p.tröskelhöjd
        dorr["hangning"] = p.hangning
        dorr["niva"] = p.niva  # Spara nivå också
        
        # Uppdatera geometri
        utils.bt_update_single_dorr(dorr, values)
        
        # Sätt nivå (höjd över golv)
        dorr.location.z = p.niva


# FUNKTION FÖR ATT SYNKRONISERA PANELEN FRÅN MARKERAD DÖRR
def sync_dorr_panel_from_selection(context):
    """Synkroniserar panelens properties från markerad dörr"""
    global _updating_from_ui, _last_selected_dorr
    
    scene = context.scene
    selected = [o for o in context.selected_objects if o.get("typ") == "dorr"]
    
    if not selected:
        return
    
    dorr = selected[0]
    
    # Kolla om det är samma dörr som tidigare
    if dorr == _last_selected_dorr:
        return
    
    _last_selected_dorr = dorr
    p = scene.bt_dorr
    
    _updating_from_ui = True
    
    try:
        if "dorr_bredd" in dorr:
            p.bredd = dorr["dorr_bredd"]
        if "dorr_hojd" in dorr:
            p.hojd = dorr["dorr_hojd"]
        if "karmtjocklek" in dorr:
            p.karmtjocklek = dorr["karmtjocklek"]
        if "karmdjup" in dorr:
            p.karmdjup = dorr["karmdjup"]
        if "indragning" in dorr:
            p.indragning = dorr["indragning"]
        if "tröskelhöjd" in dorr:
            p.tröskelhöjd = dorr["tröskelhöjd"]
        if "placering" in dorr:
            p.placering = dorr["placering"]
        if "niva" in dorr:
            p.niva = dorr["niva"]  # Läs nivå från dörren
        if "hangning" in dorr:
            p.hangning = dorr["hangning"]
    finally:
        _updating_from_ui = False


class BT_DorrProperties(bpy.types.PropertyGroup):
    """Inställningar för dörrar"""
    
    bredd: FloatProperty(
        name="Bredd",
        description="Dörrens bredd",
        default=1.0,
        min=0.3,
        step=10,
        update=bt_update_dorr
    )
    
    hojd: FloatProperty(
        name="Höjd",
        description="Dörrens höjd",
        default=2.1,
        min=0.5,
        step=10,
        update=bt_update_dorr
    )
    
    niva: FloatProperty(
        name="Nivå",
        description="Höjd över golv för dörrens underkant",
        default=0.0,
        min=0.0,
        step=10,
        update=bt_update_dorr_niva  # Använd den nya funktionen
    )
    
    karmtjocklek: FloatProperty(
        name="Karmtjocklek",
        description="Tjocklek på dörrkarmen",
        default=0.05,
        min=0.01,
        step=1,
        update=bt_update_dorr
    )
    
    karmdjup: FloatProperty(
        name="Karmdjup",
        description="Djup på dörrkarmen i väggens riktning",
        default=0.10,
        min=0.01,
        step=1,
        update=bt_update_dorr
    )
    
    tröskelhöjd: FloatProperty(
        name="Tröskelhöjd",
        description="Höjd på tröskel (0 = ingen tröskel)",
        default=0.05,
        min=0.0,
        step=1,
        update=bt_update_dorr
    )
    
    indragning: FloatProperty(
        name="Indragning från utsida",
        description="Hur långt in dörren sitter från väggens utsida",
        default=0.05,
        min=0.0,
        step=1,
        update=bt_update_dorr
    )
    
    hangning: EnumProperty(
        name="",
        description="Vilken sida dörren hänger på",
        items=[
            ('LEFT', "Vänsterhängd", "Gångjärn på vänster sida, handtag på höger"),
            ('RIGHT', "Högerhängd", "Gångjärn på höger sida, handtag på vänster")
        ],
        default='RIGHT',
        update=bt_update_dorr
    )
    
    placering: FloatProperty(
        name="Placering",
        description="Avstånd från vänster kant (positivt) eller höger kant (negativt). 0 = centrera",
        default=1.5,
        min=-100.0,
        step=10,
        update=bt_update_dorr_placering
    )