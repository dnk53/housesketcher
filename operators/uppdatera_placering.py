# ________________________________________________________________________________________________
# OPERATOR - UPPDATERA PLACERING AV MARKERAD KOMPONENT
# ________________________________________________________________________________________________

import bpy


class MESH_OT_bt_uppdatera_placering(bpy.types.Operator):
    bl_idname = "mesh.bt_uppdatera_placering"
    bl_label = "Update Placement"
    bl_description = "Update position of selected component"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        selected = context.selected_objects
        
        # Hitta markerad komponent (root_empty med komponent_namn)
        selected_component = None
        for obj in selected:
            if obj.get("komponent_namn"):
                selected_component = obj
                break
        
        if not selected_component:
            self.report({'WARNING'}, "Markera en komponent först!")
            return {'CANCELLED'}
        
        # Hämta väggen (parent)
        wall_obj = selected_component.parent
        if not wall_obj:
            self.report({'ERROR'}, "Komponenten har ingen vägg som parent!")
            return {'CANCELLED'}
        
        # Hämta nya placeringsparametrar
        placering = scene.bt_component_placering
        niva = scene.bt_component_niva
        indragning = scene.bt_component_indragning
        
        # Hämta väggens egenskaper
        if wall_obj.get("typ") == "innervagg":
            wall_length = wall_obj.get("langd", 5.0)
            if wall_length == 0:
                wall_length = utils.calculate_innervagg_length(wall_obj, context)
            wall_bredd = wall_obj.get("tjocklek", 0.120)
            is_interior = True
            half_thickness = wall_bredd / 2
        else:
            wall_length = wall_obj.get("vagg_langd", 5.0)
            wall_bredd = wall_obj.get("vagg_bredd", 0.15)
            is_interior = False
            half_thickness = 0
        
        # Beräkna position längs väggen
        if placering == 0:
            x_pos = wall_length / 2.0
        elif placering < 0:
            x_pos = wall_length + placering
        else:
            x_pos = placering
        
        # Uppdatera position
        if is_interior:
            selected_component.location = (x_pos, -half_thickness + indragning, niva)
        else:
            selected_component.location = (x_pos, indragning, niva)
        
        # Spara nya värden i root_empty
        selected_component["placering"] = x_pos
        selected_component["niva"] = niva
        selected_component["indragning"] = indragning
        
        self.report({'INFO'}, f"Uppdaterade placering av {selected_component.name}")
        return {'FINISHED'}