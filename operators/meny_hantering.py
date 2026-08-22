# ________________________________________________________________________________________________
# OPERATOR - MINIMERA ALLA MENYER
# ________________________________________________________________________________________________

import bpy


class MESH_OT_bt_dolj_alla_menyer(bpy.types.Operator):
    bl_idname = "mesh.bt_dolj_alla_menyer"
    bl_label = "Minimera alla"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Minimera alla sektioner"

    def execute(self, context):
        scene = context.scene
        # Minimera ALLA sektioner
        scene.bt_show_huvudmått = False
        scene.bt_show_symmetrisk = False
        scene.bt_show_osymmetrisk = False
        scene.bt_show_platta = False
        scene.bt_show_vagg = False
        scene.bt_show_bjalklag = False
        scene.bt_show_fonster = False
        scene.bt_show_dorr = False
        scene.bt_show_innervagg = False
        scene.bt_show_komponenter = False  # <-- LÄGG TILL
        return {'FINISHED'}


class MESH_OT_bt_uppdatera_mallar(bpy.types.Operator):
    bl_idname = "mesh.bt_uppdatera_mallar"
    bl_label = "Uppdatera mallar"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Uppdatera alla mallar för aktivt hus"
    
    def execute(self, context):
        utils.bt_update_all_guides(self, context)
        self.report({'INFO'}, "Mallarna har uppdaterats!")
        return {'FINISHED'}