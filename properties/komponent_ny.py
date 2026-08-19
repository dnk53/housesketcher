# ________________________________________________________________________________________________
# KOMPONENT NY - Egenskaper för att skapa nya komponenter
# ________________________________________________________________________________________________

import bpy
from bpy.props import StringProperty, FloatProperty, EnumProperty


class BT_KomponentNyProperties(bpy.types.PropertyGroup):
    """Inställningar för att skapa en ny komponent"""
    
    namn: StringProperty(
        name="Name",
        description="Name of the component",
        default=""
    )
    
    komponent_typ: EnumProperty(
        name="Type",
        description="Type of component",
        items=[
            ('WINDOW', "Window", "Create a window component"),
            ('DOOR', "Door", "Create a door component"),
        ],
        default='WINDOW'
    )
    
    bredd: FloatProperty(
        name="Width",
        description="Width of the component",
        default=1.20,
        min=0.1,
        step=10
    )
    
    hojd: FloatProperty(
        name="Height",
        description="Height of the component",
        default=1.50,
        min=0.1,
        step=10
    )
    
    karmtjocklek: FloatProperty(
        name="Frame Thickness",
        description="Thickness of the frame",
        default=0.05,
        min=0.01,
        step=1
    )
    
    karmdjup: FloatProperty(
        name="Frame Depth",
        description="Depth of the frame",
        default=0.10,
        min=0.01,
        step=1
    )
    
    indragning: FloatProperty(
        name="Inset",
        description="Inset from wall surface",
        default=0.01,
        min=0.0,
        step=1
    )
    
    tröskelhöjd: FloatProperty(
        name="Threshold Height",
        description="Height of the threshold (door only)",
        default=0.05,
        min=0.0,
        step=1
    )
    
    hangning: EnumProperty(
        name="Hanging",
        description="Door hanging direction",
        items=[
            ('LEFT', "Left", "Hinges on left side"),
            ('RIGHT', "Right", "Hinges on right side")
        ],
        default='RIGHT'
    )