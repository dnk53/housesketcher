# ________________________________________________________________________________________________
# INNERVÄGG - Innerväggens egenskaper
# ________________________________________________________________________________________________

import bpy
from bpy.props import FloatProperty, EnumProperty

from .. import utils


class BT_InnervaggProperties(bpy.types.PropertyGroup):
    """Inställningar för innerväggar"""
    
    tjocklek: FloatProperty(
        name="Thickness",
        description="Innerväggens tjocklek",
        default=0.120,
        min=0.02,
        step=1,
    )
    
    hojd: FloatProperty(
        name="Height",
        description="Innerväggens höjd (0 = full höjd upp till tak)",
        default=0.0,
        min=0.0,
        soft_min=0.0,
        step=10,
    )
    
    start_x: FloatProperty(
        name="Start X",
        description="Startposition i X-led (0 = mitten av byggnaden)",
        default=0.15,
        step=10,
    )
    
    start_y: FloatProperty(
        name="Start Y",
        description="Startposition i Y-led (0 = mitten av byggnaden)",
        default=0.0,
        step=10,
    )
    
    langd: FloatProperty(
        name="Length",
        description="Innerväggens längd (0 = hela vägen till motsatt vägg)",
        default=0.0,
        step=10,
    )
    
    rotation: FloatProperty(
        name="Rotation",
        description="Innerväggens rotation i grader (0 = X-led)",
        default=0.0,
        soft_min=-360.0,
        soft_max=360.0,
        step=100,
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
    )