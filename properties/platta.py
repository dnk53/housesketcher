# ________________________________________________________________________________________________
# PLATTA - Betongplattans egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty

from .. import utils

class BT_PlattaProperties(bpy.types.PropertyGroup):
    """Inställningar för betongplatta (grund)"""
    
    indrag: FloatProperty(
        name="Indragning från fasad",
        description="Avstånd från fasadens utsida till plattans kant",
        default=0.03,
        min=0.0,
        step=1,
        update=utils.bt_update_platta
    )
    
    tjocklek: FloatProperty(
        name="Plattjocklek",
        description="Tjocklek på själva plattan",
        default=0.12,
        min=0.02,
        step=1,
        update=utils.bt_update_platta
    )
    
    total_hojd: FloatProperty(
        name="Total höjd",
        description="Total höjd på grunden (platta + förstyvning)",
        default=0.40,
        min=0.05,
        step=1,
        update=utils.bt_update_platta
    )
    
    forstyvning_bredd: FloatProperty(
        name="Förstyvning bredd",
        description="Bredd på förstyvningskanter runt plattan",
        default=0.30,
        min=0.05,
        step=1,
        update=utils.bt_update_platta
    )
    
    lutning: FloatProperty(
        name="Lutning",
        description="Lutning på övergång mellan förstyvning och platta",
        default=60.0,
        min=10.0,
        max=90.0,
        step=100,
        update=utils.bt_update_platta
    )