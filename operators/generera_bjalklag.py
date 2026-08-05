# ________________________________________________________________________________________________
# OPERATOR - GENERERA BJÄLKLAG
# ________________________________________________________________________________________________

import bpy
import bmesh
import math

from .. import utils


class MESH_OT_bt_skapa_bjalklag(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_bjalklag"
    bl_label = "Generate Slab"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Hämta bjälklagets inställningar
        p = context.scene.bt_bjalklag
        
        # Beräkna bjälklagets mått
        langd_x, bredd_y, H, start_x, start_y, pos_z = utils.compute_bjalklag_matt(context.scene)
        
        # Kontrollera att måtten är giltiga
        if langd_x <= 0 or bredd_y <= 0 or H <= 0:
            self.report({'WARNING'}, "Invalid floor slab dimensions!")
            return {'CANCELLED'}
        
        # Skapa bjälklaget
        coords = [
            (0, 0, 0), (langd_x, 0, 0), (langd_x, bredd_y, 0), (0, bredd_y, 0),
            (0, 0, H), (langd_x, 0, H), (langd_x, bredd_y, H), (0, bredd_y, H)
        ]
        
        faces = [
            (0, 3, 2, 1),  # botten
            (4, 5, 6, 7),  # topp
            (0, 1, 5, 4),  # fram
            (1, 2, 6, 5),  # höger
            (2, 3, 7, 6),  # bak
            (3, 0, 4, 7)   # vänster
        ]
        
        mesh = bpy.data.meshes.new("bjalklag_Mesh")
        obj = bpy.data.objects.new("bjalklag", mesh)
        
        # Lägg i "Hus"-collectionen
        hus_collection = bpy.data.collections.get("Hus")
        if hus_collection:
            hus_collection.objects.link(obj)
        else:
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
        mat = utils.get_material_bjalklag()
        obj.data.materials.append(mat)
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        # Spara custom properties
        obj["start_x"] = p.start_x
        obj["start_y"] = p.start_y
        obj["langd_x"] = p.langd_x
        obj["bredd_y"] = p.bredd_y
        obj["niva_z"] = p.niva_z
        obj["tjocklek"] = p.tjocklek
        obj["guide_type"] = p.guide_type
        
        # Placera bjälklaget
        obj.location = (start_x, start_y, pos_z)
        empty = bpy.data.objects.get("Referenspunkt")
        if empty:
            obj.parent = empty
        
        # Lägg till Boolean modifier (använder samma funktion som i utils)
        utils.bt_update_single_bjalklag(obj, context)

        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        self.report({'INFO'}, f"Created floor slab: {langd_x:.2f} x {bredd_y:.2f} x {H:.2f} m")
        return {'FINISHED'}