# ________________________________________________________________________________________________
# OPERATOR - GENERERA DÖRR (som komponent)
# ________________________________________________________________________________________________

import bpy
from ..komponenter import generera_dorr as komponent_dorr


class MESH_OT_bt_skapa_dorr(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_dorr"
    bl_label = "Create Door Component"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        p = context.scene.bt_dorr
        
        # Använd användarens namn eller default
        name = p.komponent_namn
        if not name.strip():
            name = "Dörr"
        
        # Skapa komponenten
        komponent_dorr.create_door_component(
            context,
            name=name,
            W=p.bredd,
            H=p.hojd,
            kt=p.karmtjocklek,
            kd=p.karmdjup,
            tröskel=p.tröskelhöjd,
            indragning=p.indragning,
            hangning=p.hangning
        )
        
        self.report({'INFO'}, f"Skapade dörrkomponent: {name}")
        return {'FINISHED'}