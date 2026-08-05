# ________________________________________________________________________________________________
# OPERATOR - GENERERA FÖNSTER (med vägg-parent)
# ________________________________________________________________________________________________

import bpy
import bmesh
from mathutils import Matrix

from .. import utils

class MESH_OT_bt_skapa_fonster(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_fonster"
    bl_label = "Generera fönster"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        p = context.scene.bt_fonster
        W, H, kt, kd = p.bredd, p.hojd, p.karmtjocklek, p.karmdjup
        indragning = p.indragning
        brostning = p.brostning
        w_halv, x_inner, z_inner, y_glas = W / 2.0, (W / 2.0) - kt, H - kt, kd / 2.0
        
        # Hitta ALLA markerade väggar
        selected_walls = [obj for obj in context.selected_objects if obj.get("typ") == "vägg"]
        
        # Om inga väggar är markerade, gör inget
        if not selected_walls:
            self.report({'WARNING'}, "Markera minst en vägg först!")
            return {'CANCELLED'}
        
        # Skapa collections om de inte finns
        hal_collection = bpy.data.collections.get("Hål")
        if not hal_collection:
            hal_collection = bpy.data.collections.new("Hål")
            context.scene.collection.children.link(hal_collection)
        
        fonster_collection = bpy.data.collections.get("Fönster")
        if not fonster_collection:
            fonster_collection = bpy.data.collections.new("Fönster")
            context.scene.collection.children.link(fonster_collection)
        
        # Loopa över alla markerade väggar
        total_fonster = 0
        last_fonster = None
        
        for parent_obj in selected_walls:
            wall_bredd = parent_obj.get("vagg_bredd", 0.15)
            wall_length = parent_obj.get("vagg_langd", 5.0)
            cutter_depth = wall_bredd + 0.2
            
            # Hämta position från FloatProperty
            x_pos = p.placering

            # Beräkna position baserat på värde
            if x_pos == 0:
                # Centrera på väggen
                x_pos = wall_length / 2.0
            elif x_pos < 0:
                # Negativt värde = avstånd från höger kant
                x_pos = wall_length + x_pos
            # Positivt värde = avstånd från vänster kant (används direkt)
            
            # Skapa ett fönster på denna vägg
            idx = total_fonster
            coords = [
                (-w_halv, indragning, 0), (w_halv, indragning, 0), (w_halv, indragning, H), (-w_halv, indragning, H),
                (-x_inner, indragning, kt), (x_inner, indragning, kt), (x_inner, indragning, z_inner), (-x_inner, indragning, z_inner),
                (-w_halv, indragning + kd, 0), (w_halv, indragning + kd, 0), (w_halv, indragning + kd, H), (-w_halv, indragning + kd, H),
                (-x_inner, indragning + kd, kt), (x_inner, indragning + kd, kt), (x_inner, indragning + kd, z_inner), (-x_inner, indragning + kd, z_inner),
                (-x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, z_inner), (-x_inner, indragning + y_glas, z_inner)
            ]
            
            faces = [
                (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
                (8, 9, 13, 12), (9, 10, 14, 13), (10, 11, 15, 14), (11, 8, 12, 15),
                (0, 1, 9, 8), (1, 2, 10, 9), (2, 3, 11, 10), (3, 0, 8, 11),
                (4, 5, 13, 12), (5, 6, 14, 13), (6, 7, 15, 14), (7, 4, 12, 15),
                (16, 17, 18, 19)
            ]
            
            mesh = bpy.data.meshes.new(f"F_mesh_{idx}")
            obj = bpy.data.objects.new(f"Fönster_{idx}", mesh)
            fonster_collection.objects.link(obj)
            
            obj["fonster_bredd"] = W
            obj["fonster_hojd"] = H
            obj["karmtjocklek"] = kt
            obj["karmdjup"] = kd
            obj["indragning"] = indragning
            obj["brostning"] = brostning
            obj["placering"] = p.placering
            
            bm = bmesh.new()
            for c in coords:
                bm.verts.new(c)
            bm.verts.ensure_lookup_table()
            for f in faces:
                bm.faces.new([bm.verts[i] for i in f])
            
            # Material
            mk = utils.get_material_fonsterkarm()
            mg = utils.get_material_glas()
            
            obj.data.materials.append(mk)
            obj.data.materials.append(mg)
            for face_idx, face in enumerate(bm.faces):
                face.material_index = 0 if face_idx < 16 else 1
            
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            
            # Cutter
            m_cut = bpy.data.meshes.new(f"C_mesh_{idx}")
            o_cut = bpy.data.objects.new(f"Hål_Fönster_{idx}", m_cut)
            hal_collection.objects.link(o_cut)
            
            cc = [
                (-w_halv, indragning - 0.1, -0.0001), (w_halv, indragning - 0.1, -0.0001), 
                (w_halv, indragning - 0.1, H), (-w_halv, indragning - 0.1, H),
                (-w_halv, cutter_depth, -0.0001), (w_halv, cutter_depth, -0.0001), 
                (w_halv, cutter_depth, H), (-w_halv, cutter_depth, H)
            ]
            cf = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
            
            bm_c = bmesh.new()
            for c in cc:
                bm_c.verts.new(c)
            bm_c.verts.ensure_lookup_table()
            for f in cf:
                bm_c.faces.new([bm_c.verts[i] for i in f])
            bm_c.to_mesh(m_cut)
            bm_c.free()
            m_cut.update()
            
            o_cut.display_type = 'WIRE'
            o_cut.visible_camera = False
            o_cut.visible_shadow = False
            
            # Placera fönstret
            mat_loc = Matrix.Translation((x_pos, 0.0, brostning))
            obj.parent = parent_obj
            obj.matrix_local = mat_loc
            o_cut.parent = obj
            
            # Lägg till Boolean-modifierare på väggen
            old_mod = parent_obj.modifiers.get("Hål_Collection")
            if old_mod:
                parent_obj.modifiers.remove(old_mod)
            
            bm_mod = parent_obj.modifiers.new(name="Hål_Collection", type='BOOLEAN')
            bm_mod.operation = 'DIFFERENCE'
            bm_mod.object = None
            bm_mod.collection = hal_collection
            bm_mod.operand_type = 'COLLECTION'
            bm_mod.solver = 'FLOAT'
            
            total_fonster += 1
            last_fonster = obj  # Spara det sista fönstret som skapades
        
        # ----- MARKERA DET SISTA FÖNSTRET (precis som dörr) -----
        bpy.ops.object.select_all(action='DESELECT')
        if last_fonster:
            last_fonster.select_set(True)
            context.view_layer.objects.active = last_fonster
        
        self.report({'INFO'}, f"Skapade {total_fonster} fönster på {len(selected_walls)} vägg(ar)")
        return {'FINISHED'}