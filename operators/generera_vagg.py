# ________________________________________________________________________________________________
# OPERATOR - GENERERA VÄGG (ENSKILD VÄGG)
# ________________________________________________________________________________________________

import bpy
import bmesh
import math

from .. import utils

class MESH_OT_bt_skapa_vagg(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_vagg"
    bl_label = "Generera vägg"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Hämta huvudmått
        h = context.scene.bt_huvudmått
        vagg_hojd = h.vagg_hojd
        
        # Hämta väggens inställningar
        p = context.scene.bt_vagg
        vagg_bredd = p.bredd
        
        # Standardmått för enskild vägg (längd = 5 m)
        L = 5.0
        B = vagg_bredd
        H = vagg_hojd
        
        coords = [
            (0, 0, 0), (L, 0, 0), (L, B, 0), (0, B, 0),
            (0, 0, H), (L, 0, H), (L, B, H), (0, B, H)
        ]
        
        faces = [
            (0, 3, 2, 1), (4, 5, 6, 7),
            (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)
        ]
        
        mesh = bpy.data.meshes.new("V_mesh")
        obj = bpy.data.objects.new("Väggblock", mesh)
        context.collection.objects.link(obj)
        
        bm = bmesh.new()
        for c in coords:
            bm.verts.new(c)
        bm.verts.ensure_lookup_table()
        for f in faces:
            try:
                bm.faces.new([bm.verts[i] for i in f])
            except:
                pass
        
        # Material
        mat_red = utils.get_material_tegel()
        mat_white = utils.get_material_vit()
        obj.data.materials.append(mat_red)    # index 0
        obj.data.materials.append(mat_white)  # index 1
        
        # Insidan är face 4 (bak)
        for i, face in enumerate(bm.faces):
            if i == 4:  # insida
                face.material_index = 1
            else:
                face.material_index = 0
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        # Spara väggens mått som custom properties
        obj["typ"] = "vägg"
        obj["vagg_bredd"] = B
        obj["vagg_langd"] = L
        obj["vagg_hojd"] = H
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        return {'FINISHED'}