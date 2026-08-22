# ________________________________________________________________________________________________
# GENERERA DÖRR - Skapa dörr som komponenter (karm + blad + handtag i en mesh)
# ________________________________________________________________________________________________

import bpy
import bmesh
from mathutils import Matrix, Vector

from .. import utils


def create_door_component(context, name, W, H, kt, kd, tröskel, indragning, hangning):
    """Skapar en dörr som en komponent i biblioteket (alla delar i en mesh)"""
    
    w_halv = W / 2.0
    x_inner = w_halv - kt
    z_inner = H - kt
    mellanrum = 0.003
    blad_w = x_inner - mellanrum
    blad_h = z_inner - tröskel - mellanrum
    
    # Hämta eller skapa Components-collection
    components_collection = utils.get_components_collection()
    
    # Generera unikt namn
    existing_names = [coll.name for coll in components_collection.children]
    unique_name = utils.generate_unique_component_name(name, existing_names)
    
    # Skapa collection för komponenten
    comp_collection = bpy.data.collections.new(unique_name)
    comp_collection["type"] = "DOOR"
    comp_collection["width"] = W
    comp_collection["height"] = H
    comp_collection["karmtjocklek"] = kt
    comp_collection["karmdjup"] = kd
    comp_collection["tröskelhöjd"] = tröskel
    comp_collection["indragning"] = indragning
    comp_collection["hangning"] = hangning
    
    components_collection.children.link(comp_collection)
    
    # ----- KARM-KOORDINATER (16 vertices, index 0-15) -----
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
    
    # ----- DÖRRBLAD-KOORDINATER (8 vertices, index 16-23) -----
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
        (16, 17, 21, 20), (17, 18, 22, 21), (18, 19, 23, 22),
        (19, 16, 20, 23), (20, 21, 22, 23), (16, 19, 18, 17),
    ]
    
    # ----- HANDTAG (sticker ut 50 mm på var sida om dörrbladet) -----
    handtag_x = blad_w - 0.04 if hangning == 'RIGHT' else -blad_w + 0.04
    handtag_y = indragning + kd / 2
    handtag_z = tröskel + blad_h / 2
    
    # Dörrbladet är kd = 0.04 m (40 mm) tjockt
    # Handtaget ska vara 0.14 m (140 mm) långt = 50 mm + 40 mm + 50 mm
    handtag_bredd = 0.025  # 25 mm tjockt
    handtag_langd = 0.14   # 140 mm långt (50 mm på var sida)
    
    handtag_coords = [
        (handtag_x - handtag_bredd, handtag_y - handtag_langd/2, handtag_z - handtag_bredd),
        (handtag_x + handtag_bredd, handtag_y - handtag_langd/2, handtag_z - handtag_bredd),
        (handtag_x + handtag_bredd, handtag_y + handtag_langd/2, handtag_z - handtag_bredd),
        (handtag_x - handtag_bredd, handtag_y + handtag_langd/2, handtag_z - handtag_bredd),
        (handtag_x - handtag_bredd, handtag_y - handtag_langd/2, handtag_z + handtag_bredd),
        (handtag_x + handtag_bredd, handtag_y - handtag_langd/2, handtag_z + handtag_bredd),
        (handtag_x + handtag_bredd, handtag_y + handtag_langd/2, handtag_z + handtag_bredd),
        (handtag_x - handtag_bredd, handtag_y + handtag_langd/2, handtag_z + handtag_bredd),
    ]
    
    handtag_faces = [
        (24, 25, 29, 28), (25, 26, 30, 29), (26, 27, 31, 30),
        (27, 24, 28, 31), (28, 29, 30, 31), (24, 27, 26, 25),
    ]
    
    # ----- SLÅ IHOP ALLT -----
    all_coords = karm_coords + blad_coords + handtag_coords
    all_faces = karm_faces + blad_faces + handtag_faces
    
    # ----- SKAPA MESH -----
    mesh = bpy.data.meshes.new(f"{unique_name}_Mesh")
    obj = bpy.data.objects.new(f"{unique_name}", mesh)
    comp_collection.objects.link(obj)
    
    bm = bmesh.new()
    vert_indices = []
    
    for c in all_coords:
        v = bm.verts.new(c)
        vert_indices.append(v.index)
    
    bm.verts.ensure_lookup_table()
    
    for f in all_faces:
        try:
            bm.faces.new([bm.verts[i] for i in f])
        except:
            pass
    
    # Material: index 0 = karm, index 1 = blad, index 2 = handtag
    mk = utils.get_material_dorrkarm()
    md = utils.get_material_dorrblad()
    mh = utils.get_material_handtag()
    obj.data.materials.append(mk)
    obj.data.materials.append(md)
    obj.data.materials.append(mh)
    
    # Tilldela material baserat på face-index
    for i, face in enumerate(bm.faces):
        if i < len(karm_faces):
            face.material_index = 0  # Karm
        elif i < len(karm_faces) + len(blad_faces):
            face.material_index = 1  # Blad
        else:
            face.material_index = 2  # Handtag
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # SPARA VERTEX-INDICES
    obj["vertex_indices"] = vert_indices
    obj["vertex_count"] = len(all_coords)
    
    # Gör collectionen osynlig i viewport
    comp_collection.hide_viewport = True
    comp_collection.hide_render = True
    
    return comp_collection