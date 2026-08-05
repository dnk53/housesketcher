# ________________________________________________________________________________________________
# VÄGG - Väggens egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, BoolProperty

from .. import utils


class BT_VaggProperties(bpy.types.PropertyGroup):
    """Inställningar för väggar"""
    
    bredd: FloatProperty(
        name="Width",
        description="Wall width (0 = use Wall Thickness from Main Dimensions)",
        default=0.0,  # <-- DEFAULT 0
        min=0.0,
        soft_min=0.0,
        step=1,
        update=utils.bt_update_selected_vaggar
    )
    
    spegelvänd: BoolProperty(
        name="Mirror",
        description="Mirror the selected wall in X direction",
        default=False,
        update=utils.bt_update_single_vagg_spegelvänd
    )