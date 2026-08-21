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
    
    # ----- SKAPA KARM MED GLAS (EN MESH) -----
    coords = [
        # 0-3: Ytterram fram
        (-w_halv, indragning, 0), (w_halv, indragning, 0), (w_halv, indragning, H), (-w_halv, indragning, H),
        # 4-7: Innerram fram
        (-x_inner, indragning, kt), (x_inner, indragning, kt), (x_inner, indragning, z_inner), (-x_inner, indragning, z_inner),
        # 8-11: Ytterram bak
        (-w_halv, indragning + kd, 0), (w_halv, indragning + kd, 0), (w_halv, indragning + kd, H), (-w_halv, indragning + kd, H),
        # 12-15: Innerram bak
        (-x_inner, indragning + kd, kt), (x_inner, indragning + kd, kt), (x_inner, indragning + kd, z_inner), (-x_inner, indragning + kd, z_inner),
        # 16-19: Glas (mitten av karmen)
        (-x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, z_inner), (-x_inner, indragning + y_glas, z_inner)
    ]
    
    faces = [
        # Karm-ytor (material 0 = karm)
        (0, 1, 5, 4),  # fram-vänster
        (1, 2, 6, 5),  # fram-topp
        (2, 3, 7, 6),  # fram-höger
        (3, 0, 4, 7),  # fram-botten
        (8, 9, 13, 12),  # bak-vänster
        (9, 10, 14, 13),  # bak-topp
        (10, 11, 15, 14),  # bak-höger
        (11, 8, 12, 15),  # bak-botten
        (0, 1, 9, 8),  # vänster-sida
        (1, 2, 10, 9),  # topp-sida
        (2, 3, 11, 10),  # höger-sida
        (3, 0, 8, 11),  # botten-sida
        (4, 5, 13, 12),  # innre vänster
        (5, 6, 14, 13),  # innre topp
        (6, 7, 15, 14),  # innre höger
        (7, 4, 12, 15),  # innre botten
        # Glas (material 1 = glas)
        (16, 17, 18, 19),
    ]
    
    mesh = bpy.data.meshes.new(f"{unique_name}_Mesh")
    obj = bpy.data.objects.new(f"{unique_name}", mesh)
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
    
    # Material: index 0 = karm, index 1 = glas
    mk = utils.get_material_fonsterkarm()
    mg = utils.get_material_glas()
    obj.data.materials.append(mk)
    obj.data.materials.append(mg)
    
    # Tilldela material baserat på face-index
    for i, face in enumerate(bm.faces):
        face.material_index = 1 if i == 16 else 0  # Sista facen = glas
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # INGA vertex_indices BEHÖVS - Blender håller ordning på vertices
    
    # Gör collectionen osynlig i viewport
    comp_collection.hide_viewport = True
    comp_collection.hide_render = True
    
    return comp_collection