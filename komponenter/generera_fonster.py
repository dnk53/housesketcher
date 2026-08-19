# ________________________________________________________________________________________________
# GENERERA FÖNSTER - Skapa fönster som komponenter
# ________________________________________________________________________________________________

import bpy
import bmesh
from mathutils import Matrix

from .. import utils


def create_window_component(context, name, W, H, kt, kd, indragning):
    """Skapar ett fönster som en komponent i biblioteket"""
    
    w_halv = W / 2.0
    x_inner = w_halv - kt
    z_inner = H - kt
    y_glas = kd / 2.0
    
    # Hämta eller skapa Components-collection
    components_collection = utils.get_components_collection()
    
    # Generera unikt namn
    existing_names = [coll.name for coll in components_collection.children]
    unique_name = utils.generate_unique_component_name(name, existing_names)
    
    # Skapa collection för komponenten
    comp_collection = bpy.data.collections.new(unique_name)
    comp_collection["type"] = "WINDOW"
    comp_collection["width"] = W
    comp_collection["height"] = H
    comp_collection["karmtjocklek"] = kt
    comp_collection["karmdjup"] = kd
    comp_collection["indragning"] = indragning
    
    components_collection.children.link(comp_collection)
    
    # ----- SKAPA KARM -----
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
    
    mesh = bpy.data.meshes.new(f"{unique_name}_Mesh")
    obj = bpy.data.objects.new(f"{unique_name}_Karm", mesh)
    comp_collection.objects.link(obj)
    
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
    mk = utils.get_material_fonsterkarm()
    obj.data.materials.append(mk)
    for face_idx, face in enumerate(bm.faces):
        face.material_index = 0 if face_idx < 16 else 1
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # ----- SKAPA GLAS -----
    mesh_glas = bpy.data.meshes.new(f"{unique_name}_Glas_Mesh")
    glas_obj = bpy.data.objects.new(f"{unique_name}_Glas", mesh_glas)
    comp_collection.objects.link(glas_obj)
    
    glas_coords = [
        (-x_inner, indragning + y_glas, kt),
        (x_inner, indragning + y_glas, kt),
        (x_inner, indragning + y_glas, z_inner),
        (-x_inner, indragning + y_glas, z_inner),
    ]
    glas_faces = [(0, 1, 2, 3)]
    
    bm_g = bmesh.new()
    for c in glas_coords:
        bm_g.verts.new(c)
    bm_g.verts.ensure_lookup_table()
    for f in glas_faces:
        bm_g.faces.new([bm_g.verts[i] for i in f])
    
    mg = utils.get_material_glas()
    glas_obj.data.materials.append(mg)
    
    bm_g.to_mesh(mesh_glas)
    bm_g.free()
    mesh_glas.update()
    
    # Gör collectionen osynlig i viewport
    comp_collection.hide_viewport = True
    comp_collection.hide_render = True
    
    return comp_collection
    
    