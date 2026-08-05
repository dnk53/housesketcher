# ________________________________________________________________________________________________
# OPERATOR - GENERERA DÖRR (med dörrblad som förälder)
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
import mathutils
from mathutils import Matrix, Vector

from .. import utils

class MESH_OT_bt_skapa_dorr(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_dorr"
    bl_label = "Generera dörr"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        p = context.scene.bt_dorr
        W, H, kt, kd = p.bredd, p.hojd, p.karmtjocklek, p.karmdjup
        tröskel = p.tröskelhöjd
        indragning = p.indragning
        
        # Hitta ALLA markerade väggar
        selected_walls = [obj for obj in context.selected_objects if obj.get("typ") == "vägg"]
        
        # Om inga väggar är markerade, gör inget
        if not selected_walls:
            return {'FINISHED'}
        
        # Skapa collections om de inte finns
        hal_collection = bpy.data.collections.get("Hål")
        if not hal_collection:
            hal_collection = bpy.data.collections.new("Hål")
            context.scene.collection.children.link(hal_collection)
        
        dorr_collection = bpy.data.collections.get("Dörrar")
        if not dorr_collection:
            dorr_collection = bpy.data.collections.new("Dörrar")
            context.scene.collection.children.link(dorr_collection)
        
        # Loopa över alla markerade väggar
        total_dorrar = 0
        for parent_obj in selected_walls:
            wall_bredd = parent_obj.get("vagg_bredd", 0.15)
            wall_length = parent_obj.get("vagg_langd", 5.0)
            cutter_depth = wall_bredd + 0.2
            # Hämta position från property
            x_pos = p.placering
            # Beräkna position baserat på värde
            if x_pos == 0:
                x_pos = wall_length / 2.0
            elif x_pos < 0:
                x_pos = wall_length + x_pos
            # Positivt värde = avstånd från vänster kant (används direkt)
            
            idx = total_dorrar
            w_halv = W / 2.0
            x_inner = w_halv - kt
            z_inner = H - kt
            mellanrum = 0.003
            
            # Dörrbladets mått
            blad_w = x_inner - mellanrum
            blad_h = z_inner - tröskel - mellanrum
            
            # ---------- SKAPA KARM ----------
            karm_coords = [
                (-w_halv, indragning, 0), (w_halv, indragning, 0), 
                (w_halv, indragning, H), (-w_halv, indragning, H),
                (-w_halv, indragning + kd, 0), (w_halv, indragning + kd, 0), 
                (w_halv, indragning + kd, H), (-w_halv, indragning + kd, H),
                (-x_inner, indragning, tröskel), (x_inner, indragning, tröskel), 
                (x_inner, indragning, z_inner), (-x_inner, indragning, z_inner),
                (-x_inner, indragning + kd, tröskel), (x_inner, indragning + kd, tröskel), 
                (x_inner, indragning + kd, z_inner), (-x_inner, indragning + kd, z_inner),
            ]
            
            karm_faces = [
                (0, 1, 9, 8), (1, 2, 10, 9), (2, 3, 11, 10), (3, 0, 8, 11),
                (4, 5, 13, 12), (5, 6, 14, 13), (6, 7, 15, 14), (7, 4, 12, 15),
                (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0),
                (8, 12, 13, 9), (9, 13, 14, 10), (10, 14, 15, 11), (11, 15, 12, 8),
            ]
            
            karm_mesh = bpy.data.meshes.new(f"Karm_mesh_{idx}")
            karm_obj = bpy.data.objects.new(f"Karm_{idx}", karm_mesh)
            dorr_collection.objects.link(karm_obj)
            
            bm = bmesh.new()
            for c in karm_coords:
                bm.verts.new(c)
            bm.verts.ensure_lookup_table()
            for f in karm_faces:
                try:
                    bm.faces.new([bm.verts[i] for i in f])
                except:
                    pass
            bm.to_mesh(karm_mesh)
            bm.free()
            karm_mesh.update()
            
            mk = utils.get_material_dorrkarm()
            karm_obj.data.materials.append(mk)
            
            # ---------- SKAPA DÖRRBLAD ----------
            blad_coords = [
                (-blad_w, indragning + 0.01, tröskel + 0.01),
                (blad_w, indragning + 0.01, tröskel + 0.01),
                (blad_w, indragning + 0.01, tröskel + blad_h - 0.01),
                (-blad_w, indragning + 0.01, tröskel + blad_h - 0.01),
                (-blad_w, indragning + kd - 0.01, tröskel + 0.01),
                (blad_w, indragning + kd - 0.01, tröskel + 0.01),
                (blad_w, indragning + kd - 0.01, tröskel + blad_h - 0.01),
                (-blad_w, indragning + kd - 0.01, tröskel + blad_h - 0.01),
            ]
            
            blad_faces = [
                (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6),
                (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1),
            ]
            
            blad_mesh = bpy.data.meshes.new(f"Dörrblad_mesh_{idx}")
            blad_obj = bpy.data.objects.new(f"Dörrblad_{idx}", blad_mesh)
            dorr_collection.objects.link(blad_obj)
            
            # Spara custom properties på dörrbladet
            blad_obj["typ"] = "dorr"
            blad_obj["dorr_bredd"] = W
            blad_obj["dorr_hojd"] = H
            blad_obj["karmtjocklek"] = kt
            blad_obj["karmdjup"] = kd
            blad_obj["tröskelhöjd"] = tröskel
            blad_obj["indragning"] = indragning
            blad_obj["hangning"] = p.hangning
            blad_obj["placering"] = p.placering
            blad_obj["niva"] = p.niva  # <-- LÄGG TILL DENNA RAD
            
            bm = bmesh.new()
            for c in blad_coords:
                bm.verts.new(c)
            bm.verts.ensure_lookup_table()
            for f in blad_faces:
                try:
                    bm.faces.new([bm.verts[i] for i in f])
                except:
                    pass
            bm.to_mesh(blad_mesh)
            bm.free()
            blad_mesh.update()
            
            md = utils.get_material_dorrblad()
            blad_obj.data.materials.append(md)
            
            # KARM BLIR BARN TILL DÖRRBLAD
            karm_obj.parent = blad_obj
            karm_obj.location = (0, 0, 0)
            
            # ---------- SKAPA DÖRRHANDTAG ----------
            w_halv = W / 2.0
            x_inner = w_halv - kt
            mellanrum = 0.003
            blad_w = x_inner - mellanrum
            
            # Ta bort eventuella gamla handtag
            for child in blad_obj.children:
                if child.name.startswith("Handtag_") or child.name.startswith("Dörrhandtag") or child.name.startswith("Rosett"):
                    bpy.data.objects.remove(child, do_unlink=True)
            
            # Skapa nya handtaget
            handtag_x = -blad_w + 0.03 if p.hangning == 'RIGHT' else blad_w - 0.03
            handtag_pos = (handtag_x, indragning + kd / 2, 0)
            
            handtag_obj = utils.skapa_dorrhandtag(
                context,
                hangning=p.hangning,
                position=handtag_pos,
                parent=blad_obj
            )
            
            # ---------- SKAPA CUTTER ----------
            m_cut = bpy.data.meshes.new(f"D_cutter_{idx}")
            o_cut = bpy.data.objects.new(f"Hål_Dörr_{idx}", m_cut)
            hal_collection.objects.link(o_cut)
            
            cutter_start = indragning - 0.1
            cutter_depth = wall_bredd + 0.2
            
            cc = [
                (-w_halv, cutter_start, -0.0001), (w_halv, cutter_start, -0.0001), 
                (w_halv, cutter_start, H), (-w_halv, cutter_start, H),
                (-w_halv, cutter_start + cutter_depth, -0.0001), 
                (w_halv, cutter_start + cutter_depth, -0.0001),
                (w_halv, cutter_start + cutter_depth, H), 
                (-w_halv, cutter_start + cutter_depth, H)
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
            
            # CUTTER BLIR BARN TILL DÖRRBLAD
            o_cut.parent = blad_obj
            o_cut.location = (0, 0, 0)
            
            # ---------- PLACERA DÖRREN ----------
            blad_obj.parent = parent_obj
            blad_obj.location = (x_pos, 0.0, p.niva)
            
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
            
            total_dorrar += 1
        
        self.report({'INFO'}, f"Skapade {total_dorrar} dörrar på {len(selected_walls)} vägg(ar)")
        return {'FINISHED'}