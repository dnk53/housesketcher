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
            # Använd bjälklagets överyta (location.z + tjocklek)
            slab_thickness = selected_slab.get("tjocklek", 0.30)
            base_z = selected_slab.location.z + slab_thickness
        else:
            base_z = 0.0
        
        # Beräkna innermått (insida av väggar) - används för "hela vägen"
        inner_l = fasad_l - teoretisk_bredd * 2
        inner_b = fasad_b - teoretisk_bredd * 2

        # Beräkna startpunkt
        if p.start_x == 0:
            start_x = fasad_l / 2  # Mitt på byggnaden
        else:
            start_x = p.start_x    # Absolut position från vänster

        if p.start_y == 0:
            start_y = fasad_b / 2  # Mitt på byggnaden
        else:
            start_y = p.start_y    # Absolut position från fram

        # Beräkna längd
        langd = p.langd
        rotation_rad = math.radians(p.rotation)
        
        if langd == 0:
            # Beräkna längd baserat på rotation
            if abs(p.rotation) < 1 or abs(p.rotation - 180) < 1 or abs(p.rotation + 180) < 1:
                # X-led: till höger/vänster gavel
                langd = inner_l
            elif abs(p.rotation - 90) < 1 or abs(p.rotation + 90) < 1:
                # Y-led: till fram/bakvägg
                langd = inner_b
            else:
                # Godtycklig vinkel: 5 meter
                langd = 5.0
        
        # Beräkna ändpunkt
        end_x = start_x + langd * math.cos(rotation_rad)
        end_y = start_y + langd * math.sin(rotation_rad)
        
        # Beräkna väggens centrum och riktning
        center_x = (start_x + end_x) / 2
        center_y = (start_y + end_y) / 2
        dx = end_x - start_x
        dy = end_y - start_y
        wall_length = math.sqrt(dx*dx + dy*dy)
        
        if wall_length < 0.001:
            self.report({'WARNING'}, "Wall length is too small!")
            return {'CANCELLED'}
        
        # Normalisera riktning
        dx /= wall_length
        dy /= wall_length
        
        # Vinkelrät riktning (för bredd)
        px = -dy
        py = dx
        
        # Hälften av bredd och längd
        half_width = p.tjocklek / 2
        half_length = wall_length / 2
        
        # Beräkna höjd
        if p.hojd == 0:
            # Full höjd - beräkna från tak
            total_hojd = utils._calculate_total_wall_height(scene)
        else:
            total_hojd = p.hojd
        
        # Skapa vertices för väggen (8 hörn)
        coords = [
            # Botten (4 hörn)
            center_x + (-half_length * dx - half_width * px),
            center_y + (-half_length * dy - half_width * py),
            base_z,
            
            center_x + (half_length * dx - half_width * px),
            center_y + (half_length * dy - half_width * py),
            base_z,
            
            center_x + (half_length * dx + half_width * px),
            center_y + (half_length * dy + half_width * py),
            base_z,
            
            center_x + (-half_length * dx + half_width * px),
            center_y + (-half_length * dy + half_width * py),
            base_z,
            
            # Topp (4 hörn)
            center_x + (-half_length * dx - half_width * px),
            center_y + (-half_length * dy - half_width * py),
            base_z + total_hojd,
            
            center_x + (half_length * dx - half_width * px),
            center_y + (half_length * dy - half_width * py),
            base_z + total_hojd,
            
            center_x + (half_length * dx + half_width * px),
            center_y + (half_length * dy + half_width * py),
            base_z + total_hojd,
            
            center_x + (-half_length * dx + half_width * px),
            center_y + (-half_length * dy + half_width * py),
            base_z + total_hojd,
        ]
        
        # Faces (6 sidor)
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
        for i in range(0, len(coords), 3):
            bm.verts.new((coords[i], coords[i+1], coords[i+2]))
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
        
        # Spara custom properties
        obj["typ"] = "innervagg"
        obj["tjocklek"] = p.tjocklek
        obj["hojd"] = p.hojd
        obj["start_x"] = p.start_x
        obj["start_y"] = p.start_y
        obj["langd"] = p.langd
        obj["rotation"] = p.rotation
        obj["guide_type"] = p.guide_type
        obj["base_z"] = base_z  # <-- Spara basnivå
        
        # Parent till Referenspunkt
        empty = bpy.data.objects.get("Referenspunkt")
        if empty:
            obj.parent = empty
        
        # Lägg till Boolean-modifierare för guide
        utils._update_innervagg_boolean(obj, scene, p.guide_type)
        
        # Välj den nya väggen
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.objects.active = obj
        obj.select_set(True)
        
        self.report({'INFO'}, f"Added interior wall: {wall_length:.2f} m")
        return {'FINISHED'}