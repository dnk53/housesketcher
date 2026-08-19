# ________________________________________________________________________________________________
# GENERERA DÖRR - Skapa dörr som komponenter
# ________________________________________________________________________________________________

import bpy
import bmesh
from mathutils import Matrix

from .. import utils


def create_door_component(context, name, W, H, kt, kd, tröskel, indragning, hangning):
    """Skapar en dörr som en komponent i biblioteket"""
    
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
    
    # ----- SKAPA KARM -----
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
    
    karm_mesh = bpy.data.meshes.new(f"{unique_name}_Karm_Mesh")
    karm_obj = bpy.data.objects.new(f"{unique_name}_Karm", karm_mesh)
    comp_collection.objects.link(karm_obj)
    
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
    
    # ----- SKAPA DÖRRBLAD -----
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
    
    blad_mesh = bpy.data.meshes.new(f"{unique_name}_Blad_Mesh")
    blad_obj = bpy.data.objects.new(f"{unique_name}_Blad", blad_mesh)
    comp_collection.objects.link(blad_obj)
    
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
    
    # ----- SKAPA DÖRRHANDTAG -----
    handtag_x = -blad_w + 0.03 if hangning == 'RIGHT' else blad_w - 0.03
    handtag_pos = (handtag_x, indragning + kd / 2, 0)
    
    handtag_obj = utils.skapa_dorrhandtag(
        context,
        hangning=hangning,
        position=handtag_pos,
        parent=blad_obj
    )
    
    # Gör collectionen osynlig i viewport
    comp_collection.hide_viewport = True
    comp_collection.hide_render = True
    
    return comp_collection
    
    