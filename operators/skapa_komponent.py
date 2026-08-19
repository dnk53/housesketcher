# ________________________________________________________________________________________________
# OPERATOR - SKAPA NY KOMPONENT
# ________________________________________________________________________________________________

import bpy
from bpy.props import StringProperty, FloatProperty, EnumProperty


class MESH_OT_bt_skapa_komponent(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_komponent"
    bl_label = "New Component"
    bl_description = "Create a new component in the library"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        p = scene.bt_komponent_ny
        
        # Validera att vi har ett namn
        if not p.namn.strip():
            self.report({'WARNING'}, "Ange ett namn för komponenten!")
            return {'CANCELLED'}
        
        # Skapa komponent baserat på typ
        if p.komponent_typ == 'WINDOW':
            from ..komponenter import generera_fonster
            generera_fonster.create_window_component(
                context,
                p.namn,
                W=p.bredd,
                H=p.hojd,
                kt=p.karmtjocklek,
                kd=p.karmdjup,
                indragning=p.indragning
            )
            self.report({'INFO'}, f"Skapade fönsterkomponent: {p.namn}")
            
        elif p.komponent_typ == 'DOOR':
            from ..komponenter import generera_dorr
            generera_dorr.create_door_component(
                context,
                p.namn,
                W=p.bredd,
                H=p.hojd,
                kt=p.karmtjocklek,
                kd=p.karmdjup,
                tröskel=p.tröskelhöjd,
                indragning=p.indragning,
                hangning=p.hangning
            )
            self.report({'INFO'}, f"Skapade dörrkomponent: {p.namn}")
        
        else:
            self.report({'ERROR'}, f"Okänd komponenttyp: {p.komponent_typ}")
            return {'CANCELLED'}
        
        return {'FINISHED'}