# ________________________________________________________________________________________________
# OPERATOR - PLACERA KOMPONENT I VÄGG
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
from mathutils import Matrix, Vector

from .. import utils


class MESH_OT_bt_placera_komponent(bpy.types.Operator):
    bl_idname = "mesh.bt_placera_komponent"
    bl_label = "Place Component in Wall"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        scene = context.scene
        
        # Hämta vald komponent
        comp_name = scene.bt_selected_component
        if not comp_name:
            self.report({'WARNING'}, "Ingen komponent vald!")
            return {'CANCELLED'}
        
        # Hitta komponenten i biblioteket
        comp_collection = utils.get_component_by_name(comp_name)
        if not comp_collection:
            self.report({'ERROR'}, f"Komponenten '{comp_name}' hittades inte!")
            return {'CANCELLED'}
        
        # Hitta markerade väggar (inklusive innerväggar)
        selected_walls = [obj for obj in context.selected_objects 
                          if obj.get("typ") in ["vägg", "innervagg"]]
        
        if not selected_walls:
            self.report({'WARNING'}, "Markera minst en vägg eller innervägg!")
            return {'CANCELLED'}
        
        # Hämta komponent-parametrar
        comp_type = comp_collection.get("type")
        if comp_type == "WINDOW":
            width = comp_collection.get("width", 1.2)
            height = comp_collection.get("height", 1.5)
            indragning = comp_collection.get("indragning", 0.01)
        elif comp_type == "DOOR":
            width = comp_collection.get("width", 0.9)
            height = comp_collection.get("height", 2.1)
            indragning = comp_collection.get("indragning", 0.01)
        else:
            self.report({'ERROR'}, f"Okänd komponenttyp: {comp_type}")
            return {'CANCELLED'}
        
        # Skapa collections för hål om de inte finns
        hal_collection = bpy.data.collections.get("Hål")
        if not hal_collection:
            hal_collection = bpy.data.collections.new("Hål")
            context.scene.collection.children.link(hal_collection)
        
        # Loopa över alla markerade väggar
        total_placerade = 0
        
        for wall_obj in selected_walls:
            # Hämta väggens egenskaper
            if wall_obj.get("typ") == "innervagg":
                wall_length = wall_obj.get("langd", 5.0)
                if wall_length == 0:
                    wall_length = utils.calculate_innervagg_length(wall_obj, context)
                wall_bredd = wall_obj.get("tjocklek", 0.120)
                is_interior = True
            else:
                wall_length = wall_obj.get("vagg_langd", 5.0)
                wall_bredd = wall_obj.get("vagg_bredd", 0.15)
                is_interior = False
            
            # Hämta placering (från scene property)
            placering = scene.bt_component_placering
            if placering == 0:
                placering = wall_length / 2.0
            elif placering < 0:
                placering = wall_length + placering
            
            # ----- SKAPA EN ROOT EMPTY FÖR KOMPONENTEN -----
            root_empty = bpy.data.objects.new(f"{comp_name}_{total_placerade}", None)
            context.collection.objects.link(root_empty)
            root_empty.empty_display_type = 'PLAIN_AXES'
            root_empty.empty_display_size = 0.1
            
            # Duplicera komponentens objekt och parenta till root_empty
            for obj in comp_collection.objects:
                new_obj = obj.copy()
                new_obj.data = obj.data.copy()
                new_obj.parent = root_empty
                new_obj.location = (0, 0, 0)
                context.collection.objects.link(new_obj)
            
            # Sätt root_empty's position och parent
            if is_interior:
                half_thickness = wall_bredd / 2
                root_empty.parent = wall_obj
                root_empty.location = (placering, -half_thickness, 0)
            else:
                root_empty.parent = wall_obj
                root_empty.location = (placering, 0.0, 0)
            
            # Spara info om komponenten
            root_empty["komponent_namn"] = comp_name
            root_empty["komponent_typ"] = comp_type
            root_empty["placering"] = placering
            
            # ----- SKAPA CUTTER -----
            w_halv = width / 2.0
            H = height
            cutter_depth = wall_bredd + 0.5
            cutter_start = -0.1
            
            m_cut = bpy.data.meshes.new(f"Hål_{comp_name}_{total_placerade}")
            o_cut = bpy.data.objects.new(f"Hål_{comp_name}_{total_placerade}", m_cut)
            hal_collection.objects.link(o_cut)
            
            cc = [
                (-w_halv, cutter_start, -0.0001), (w_halv, cutter_start, -0.0001), 
                (w_halv, cutter_start, H), (-w_halv, cutter_start, H),
                (-w_halv, cutter_depth, -0.0001), (w_halv, cutter_depth, -0.0001), 
                (w_halv, cutter_depth, H), (-w_halv, cutter_depth, H)
            ]
            cf = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            
            bm_c = bmesh.new()
            for c in cc:
                bm_c.verts.new(c)
            bm_c.verts.ensure_lookup_table()
            for f in cf:
                try:
                    bm_c.faces.new([bm_c.verts[i] for i in f])
                except:
                    pass
            bm_c.to_mesh(m_cut)
            bm_c.free()
            m_cut.update()
            
            o_cut.display_type = 'WIRE'
            o_cut.visible_camera = False
            o_cut.visible_shadow = False
            o_cut.parent = root_empty
            o_cut.location = (0, 0, 0)
            
            # Lägg till Boolean-modifierare på väggen
            old_mod = wall_obj.modifiers.get("Hål_Collection")
            if old_mod:
                wall_obj.modifiers.remove(old_mod)
            
            bm_mod = wall_obj.modifiers.new(name="Hål_Collection", type='BOOLEAN')
            bm_mod.operation = 'DIFFERENCE'
            bm_mod.object = None
            bm_mod.collection = hal_collection
            bm_mod.operand_type = 'COLLECTION'
            bm_mod.solver = 'FLOAT'
            
            total_placerade += 1
        
        self.report({'INFO'}, f"Placerade {total_placerade} komponent(er)")
        return {'FINISHED'}