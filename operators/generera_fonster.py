# ________________________________________________________________________________________________
# OPERATOR - GENERERA FÖNSTER (som komponent)
# ________________________________________________________________________________________________

import bpy
from ..komponenter import generera_fonster as komponent_fonster


class MESH_OT_bt_skapa_fonster(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_fonster"
    bl_label = "Create Window Component"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        p = context.scene.bt_fonster
        
        # Använd användarens namn eller default
        name = p.komponent_namn
        if not name.strip():
            name = "Fönster"
        
        # Skapa komponenten
        komponent_fonster.create_window_component(
            context,
            name=name,
            W=p.bredd,
            H=p.hojd,
            kt=p.karmtjocklek,
            kd=p.karmdjup,
            indragning=p.indragning
        )
        
        self.report({'INFO'}, f"Skapade fönsterkomponent: {name}")
        return {'FINISHED'}