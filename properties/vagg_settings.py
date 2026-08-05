# ________________________________________________________________________________________________
# VÄGG INSTÄLLNINGAR - PropertyGroup för väggar
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty

from .. import utils

# Global flagga för att förhindra cirkulära uppdateringar
_updating_from_selection = False


def update_vagg_from_panel(self, context):
    """Uppdaterar den aktiva väggen när en property ändras"""
    global _updating_from_selection
    
    # Hoppa över om vi är mitt i en selection-synkronisering
    if _updating_from_selection:
        return
    
    vagg = context.active_object
    if vagg and vagg.get("typ") == "vägg":
        # Spara panelens värden till custom properties
        vagg["start_x"] = self.start_x
        vagg["start_y"] = self.start_y
        vagg["langd_x"] = self.langd_x
        vagg["langd_y"] = self.langd_y
        vagg["vagg_hojd"] = self.vagg_hojd
        
        # Uppdatera väggens geometri
        utils.bt_update_single_vagg_from_props(vagg, context)


def sync_vagg_panel_from_selection(context):
    """Synkroniserar panelen med markerad vägg"""
    global _updating_from_selection
    
    scene = context.scene
    vagg = context.active_object
    
    if not vagg or vagg.get("typ") != "vägg":
        return
    
    if not hasattr(scene, "bt_vagg_settings"):
        return
    
    # Sätt flagga för att förhindra cirkulära uppdateringar
    _updating_from_selection = True
    
    try:
        # Uppdatera vägg-inställningarna (start, längd, höjd)
        p = scene.bt_vagg_settings
        
        p.start_x = vagg.get("start_x", 0.15)
        p.start_y = vagg.get("start_y", 0.0)
        p.langd_x = vagg.get("langd_x", -0.15)
        p.langd_y = vagg.get("langd_y", 0.0)
        p.vagg_hojd = vagg.get("vagg_hojd", 0.0)
        
        # Uppdatera bredden i huvudpanelen
        vagg_bredd = vagg.get("vagg_bredd", 0.0)
        scene.bt_vagg.bredd = vagg_bredd
        
    finally:
        _updating_from_selection = False


class BT_VaggSettingsProperties(bpy.types.PropertyGroup):
    """Inställningar för den markerade väggen"""
    
    start_x: FloatProperty(
        name="Start X",
        description="Start position in X direction",
        default=0.15,
        step=10,
        update=update_vagg_from_panel
    )
    
    start_y: FloatProperty(
        name="Start Y",
        description="Start position in Y direction",
        default=0.0,
        step=10,
        update=update_vagg_from_panel
    )
    
    langd_x: FloatProperty(
        name="Length X",
        description="Length in X direction (0 = full, negative = to inside)",
        default=-0.15,
        step=10,
        update=update_vagg_from_panel
    )
    
    langd_y: FloatProperty(
        name="Length Y",
        description="Length in Y direction (0 = full, negative = to inside)",
        default=0.0,
        step=10,
        update=update_vagg_from_panel
    )
    
    vagg_hojd: FloatProperty(
        name="Height",
        description="Wall height (0 = full height up to roof)",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        step=10,
        update=update_vagg_from_panel
    )