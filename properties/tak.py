# ________________________________________________________________________________________________
# TAK - Takets egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty

from .. import utils


def bt_uppdatera_tak(self, context):
    """Wrapper för att uppdatera taket"""
    utils.bt_update_tak(self, context)


class BT_TakProperties(bpy.types.PropertyGroup):
    """Inställningar för tak"""
    
    brytvinkel: FloatProperty(
        name="Brytvinkel",
        description="0 = sadeltak. Positiv = brantare upptill. Negativ = flackare upptill.",
        default=0.0,
        min=-45.0,
        max=45.0,
        step=1,
        update=utils.bt_update_tak
    )
    
    brytavstand: FloatProperty(
        name="Brytavstånd",
        description="Avstånd från insida vägg till brytpunkt (mätt horisontellt)",
        default=1.5,
        min=0.0,
        max=10.0,
        step=10,
        update=utils.bt_update_tak
    )