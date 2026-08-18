# ________________________________________________________________________________________________
# OPERATOR - GENERERA TAK (med fyra separata delar)
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
from math import radians, sin, tan, cos
from mathutils import Euler
from .. import utils

DELTA = 0.00001

class MESH_OT_bt_skapa_tak(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_tak"
    bl_label = "Generera tak"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Beräkna takgeometri med central funktion
        geo = utils.calculate_tak_geometry(context.scene)
        
        # Material
        mat_ytter = utils.get_material_tak()
        mat_innertak = utils.get_material_innertak()
        
        # Skapa varje takdel
        for namn, info in utils.TAKDELAR_INFO.items():
            v_indices = info["v_indices"]
            h_indices = info["h_indices"]
            faces = info["faces"]
            
            # Hämta vertices för denna del
            del_verts = []
            for idx in v_indices:
                del_verts.append(geo['v_verts'][idx])
            for idx in h_indices:
                del_verts.append(geo['h_verts'][idx])
            
            # Skapa mesh
            mesh = bpy.data.meshes.new(f"{namn}_Mesh")
            obj = bpy.data.objects.new(namn, mesh)
            
            # Lägg i "Hus"-collectionen
            hus_collection = bpy.data.collections.get("Hus")
            if hus_collection:
                hus_collection.objects.link(obj)
            else:
                context.collection.objects.link(obj)
            
            # Skapa bmesh
            bm = bmesh.new()
            for v in del_verts:
                bm.verts.new(v)
            bm.verts.ensure_lookup_table()
            
            # Skapa faces
            for face_indices in faces:
                try:
                    bm.faces.new([bm.verts[i] for i in face_indices])
                except:
                    pass
            
            # Räkna om normalerna
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            
            # Lägg till material
            obj.data.materials.append(mat_ytter)
            obj.data.materials.append(mat_innertak)
            
            # Tilldela material baserat på normalernas riktning
            for face in bm.faces:
                if face.normal.z > 0:
                    face.material_index = 0  # Yttertak
                else:
                    face.material_index = 1  # Innertak
            
            bm.to_mesh(mesh)
            bm.free()
            mesh.update()
            
            obj.location = (0, 0, 0)
        # ----- SÄTT PARENT TILL EMPTY (från temp property) -----
        empty = None
        temp_empty_name = context.scene.get("temp_empty")
        if temp_empty_name:
            for obj in context.scene.objects:
                if obj.name == temp_empty_name:
                    empty = obj
                    break
        
        if empty:
            for obj in context.scene.objects:
                if obj.name.startswith("Tak_") and obj.parent is None:
                    global_matrix = obj.matrix_world.copy()
                    obj.parent = empty
                    obj.matrix_parent_inverse = empty.matrix_world.inverted()
                    obj.location = (0, 0, 0)
        
        # Välj alla takdelar
        bpy.ops.object.select_all(action='DESELECT')
        for obj in context.scene.objects:
            if obj.name.startswith("Tak_"):
                obj.select_set(True)
                context.view_layer.objects.active = obj

        self.report({'INFO'}, f"Skapade 4 takdelar")
        return {'FINISHED'}