# ________________________________________________________________________________________________
# OPERATOR - GENERERA PLATTA
# ________________________________________________________________________________________________

import bpy
import bmesh
import math

from .. import utils

class MESH_OT_bt_skapa_platta(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_platta"
    bl_label = "Generera platta"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Hämta huvudmått
        h = context.scene.bt_huvudmått
        fasad_l = h.fasad_l
        fasad_b = h.fasad_b
        
        # Hämta plattans inställningar
        p = context.scene.bt_platta
        t = p.tjocklek
        ind = p.indrag
        H = p.total_hojd
        fb = p.forstyvning_bredd
        
        # Plattans mått = fasadmått minus indrag på båda sidor
        L = fasad_l - ind * 2
        B = fasad_b - ind * 2
        
        if H - t < 0:
            self.report({'ERROR'}, "Total höjd måste vara större än plattjocklek")
            return {'CANCELLED'}
        
        fi = (H - t) / math.tan(math.radians(p.lutning)) if p.lutning > 0 else 0
        
        x_min, y_min = 0, 0
        x_max, y_max = L, B
        x3, y3 = x_min + fb, y_min + fb
        x3b, y3b = x_max - fb, y_max - fb
        
        coords = [
            (x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0),
            (x_min, y_min, -H), (x_max, y_min, -H), (x_max, y_max, -H), (x_min, y_max, -H),
            (x3, y3, -H), (x3b, y3, -H), (x3b, y3b, -H), (x3, y3b, -H),
            (x3 + fi, y3 + fi, -t), (x3b - fi, y3 + fi, -t), (x3b - fi, y3b - fi, -t), (x3 + fi, y3b - fi, -t)
        ]
        
        faces = [
            (0, 3, 2, 1), (12, 13, 14, 15),
            (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
            (4, 5, 9, 8), (5, 6, 10, 9), (6, 7, 11, 10), (7, 4, 8, 11),
            (8, 9, 13, 12), (9, 10, 14, 13), (10, 11, 15, 14), (11, 8, 12, 15)
        ]
        
        mesh = bpy.data.meshes.new("P_mesh")
        obj = bpy.data.objects.new("Betongplatta", mesh)
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
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        # Material för betongplatta (grå)
        mat = utils.get_material_betong()
        obj.data.materials.append(mat)
        
        # Flytta plattan så att nedre vänstra hörnet hamnar vid (ind, ind)
        obj.location = (ind, ind, 0)
        
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        return {'FINISHED'}