# ________________________________________________________________________________________________
# OPERATOR - GENERERA INNERVÄGG
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

from .. import utils


class MESH_OT_bt_skapa_innervagg(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_innervagg"
    bl_label = "Add Interior Wall"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        p = scene.bt_innervagg
        h = scene.bt_huvudmått
        
        # Hämta byggnadens mått
        fasad_l = h.fasad_l
        fasad_b = h.fasad_b
        teoretisk_bredd = h.teoretisk_vagg_bredd
        
        # ----- HITTA MARKERAT BJÄLKLAG -----
        selected_slab = None
        for obj in context.selected_objects:
            if obj.name.startswith("bjalklag"):
                selected_slab = obj
                break
        
        # ----- BERÄKNA BASNIVÅ (Z) -----
        if selected_slab:
            slab_thickness = selected_slab.get("tjocklek", 0.30)
            base_z = selected_slab.location.z + slab_thickness
        else:
            base_z = 0.0
        
        # Beräkna innermått (insida av väggar) - används för "hela vägen"
        inner_l = fasad_l - teoretisk_bredd * 2
        inner_b = fasad_b - teoretisk_bredd * 2

        # Beräkna startpunkt
        if p.start_x == 0:
            start_x = fasad_l / 2
        else:
            start_x = p.start_x

        if p.start_y == 0:
            start_y = fasad_b / 2
        else:
            start_y = p.start_y

        # Beräkna längd
        langd = p.langd
        rotation_rad = math.radians(p.rotation)
        
        if langd == 0:
            if abs(p.rotation) < 1 or abs(p.rotation - 180) < 1 or abs(p.rotation + 180) < 1:
                langd = inner_l
            elif abs(p.rotation - 90) < 1 or abs(p.rotation + 90) < 1:
                langd = inner_b
            else:
                langd = 5.0
        
        # Beräkna höjd
        if p.hojd == 0:
            total_hojd = utils._calculate_total_wall_height(scene)
        else:
            total_hojd = p.hojd
        
        # ----- BYGG VÄGGEN LOKALT VID ORIGO -----
        half_width = p.tjocklek / 2
        
        coords = [
            # Botten (4 hörn)
            (0, -half_width, 0),
            (langd, -half_width, 0),
            (langd, half_width, 0),
            (0, half_width, 0),
            # Topp (4 hörn)
            (0, -half_width, total_hojd),
            (langd, -half_width, total_hojd),
            (langd, half_width, total_hojd),
            (0, half_width, total_hojd),
        ]
        
        faces = [
            (0, 3, 2, 1),  # botten
            (4, 5, 6, 7),  # topp
            (0, 1, 5, 4),  # fram
            (1, 2, 6, 5),  # höger
            (2, 3, 7, 6),  # bak
            (3, 0, 4, 7)   # vänster
        ]
        
        # Skapa mesh och objekt
        mesh = bpy.data.meshes.new("Innervagg_Mesh")
        obj = bpy.data.objects.new("Innervagg", mesh)
        
        # Lägg i "Hus"-collectionen
        hus_collection = bpy.data.collections.get("Hus")
        if hus_collection:
            hus_collection.objects.link(obj)
        else:
            context.collection.objects.link(obj)
        
        # Skapa bmesh
        bm = bmesh.new()
        vert_indices = []
        
        for c in coords:
            v = bm.verts.new(c)
            vert_indices.append(v.index)
        
        bm.verts.ensure_lookup_table()
        
        for f in faces:
            try:
                bm.faces.new([bm.verts[i] for i in f])
            except:
                pass
        
        # Material för innervägg
        mat = utils.get_material_innervagg()
        obj.data.materials.append(mat)
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        # ----- SPARA KOPPLING TILL BJÄLKLAG -----
        if selected_slab:
            obj["slab_parent"] = selected_slab.name
        else:
            obj["slab_parent"] = None
        
        # Spara custom properties
        obj["typ"] = "innervagg"
        obj["tjocklek"] = p.tjocklek
        obj["hojd"] = p.hojd
        obj["start_x"] = p.start_x
        obj["start_y"] = p.start_y
        obj["langd"] = p.langd
        obj["rotation"] = p.rotation
        obj["guide_type"] = p.guide_type
        obj["base_z"] = base_z
        obj["innervagg_vertex_indices"] = vert_indices
        
        # ----- SÄTT POSITION OCH ROTATION -----
        obj.location = (start_x, start_y, base_z)
        obj.rotation_euler = (0, 0, rotation_rad)
        
        # Parent till Empty
        empty = utils.get_active_house_empty(context)
        if empty:
            obj.parent = empty
        
        # Lägg till Boolean-modifierare för guide
        utils._update_innervagg_boolean(obj, scene, p.guide_type)
        
        # Välj den nya väggen
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        self.report({'INFO'}, f"Added interior wall: {langd:.2f} m")
        return {'FINISHED'}