# ________________________________________________________________________________________________
# DÖRR - Dörrens egenskaper
# ________________________________________________________________________________________________

import bpy
import bmesh
from bpy.props import FloatProperty, StringProperty, EnumProperty, BoolProperty

from .. import utils

# Globala variabler
_updating_from_ui = False
_last_selected_dorr = None


def find_component_root(obj):
    """Hittar root_empty för en komponent genom att följa parent-kedjan uppåt"""
    current = obj
    while current:
        if current.get("komponent_namn"):
            return current
        current = current.parent
    return None


def bt_update_dorr(self, context):
    """Uppdaterar markerade dörrar när användaren ändrar parametrar"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected = context.selected_objects
    
    # Hitta markerad komponent
    selected_component = None
    for obj in selected:
        root = find_component_root(obj)
        if root and root.get("komponent_typ") == "DOOR":
            selected_component = root
            break
    
    if not selected_component:
        return
    
    # Hitta komponenten i biblioteket
    comp_name = selected_component.get("komponent_namn")
    comp_collection = utils.get_component_by_name(comp_name)
    if not comp_collection:
        return
    
    p = scene.bt_dorr
    
    # ----- SPARA PARAMETRAR -----
    selected_component["bredd"] = p.bredd
    selected_component["hojd"] = p.hojd
    selected_component["karmtjocklek"] = p.karmtjocklek
    selected_component["karmdjup"] = p.karmdjup
    selected_component["tröskelhöjd"] = p.tröskelhöjd
    selected_component["hangning"] = p.hangning
    
    comp_collection["width"] = p.bredd
    comp_collection["height"] = p.hojd
    comp_collection["karmtjocklek"] = p.karmtjocklek
    comp_collection["karmdjup"] = p.karmdjup
    comp_collection["tröskelhöjd"] = p.tröskelhöjd
    comp_collection["hangning"] = p.hangning
    
    # ----- BERÄKNA NYA KOORDINATER -----
    W = p.bredd
    H = p.hojd
    kt = p.karmtjocklek
    kd = p.karmdjup
    tröskel = p.tröskelhöjd
    # Använd indragning från 50. Place Component (sparad i root_empty)
    indragning = selected_component.get("indragning", 0.01)
    
    w_halv = W / 2.0
    x_inner = w_halv - kt
    z_inner = H - kt
    mellanrum = 0.003
    blad_w = x_inner - mellanrum
    blad_h = z_inner - tröskel - mellanrum
    
    # Karm-koordinater (16 vertices)
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
    
    # Dörrblad-koordinater (8 vertices)
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
    
    # Cutter-koordinater (8 vertices)
    cutter_depth = 0.800
    cutter_start = -0.300
    cutter_coords = [
        (-w_halv, cutter_start, -0.0001), (w_halv, cutter_start, -0.0001), 
        (w_halv, cutter_start, H), (-w_halv, cutter_start, H),
        (-w_halv, cutter_start + cutter_depth, -0.0001), (w_halv, cutter_start + cutter_depth, -0.0001), 
        (w_halv, cutter_start + cutter_depth, H), (-w_halv, cutter_start + cutter_depth, H)
    ]
    
    # ----- UPPDATERA VERTICES -----
    for obj in comp_collection.objects:
        if not obj.data:
            continue
        
        if "Karm" in obj.name:
            coords = karm_coords
        elif "Blad" in obj.name:
            coords = blad_coords
        else:
            continue
        
        mesh = obj.data
        
        if mesh.is_editmode:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                continue
        
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        
        for i, c in enumerate(coords):
            if i < len(bm.verts):
                bm.verts[i].co = c
        
        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
    
    # ----- UPPDATERA ALLA CUTTER -----
    for obj in bpy.data.objects:
        if obj.get("komponent_namn") == comp_name:
            for child in obj.children:
                if child.name.startswith("Hål_"):
                    mesh = child.data
                    if mesh.is_editmode:
                        try:
                            bpy.ops.object.mode_set(mode='OBJECT')
                        except:
                            continue
                    
                    bm = bmesh.new()
                    bm.from_mesh(mesh)
                    bm.verts.ensure_lookup_table()
                    
                    for i, c in enumerate(cutter_coords):
                        if i < len(bm.verts):
                            bm.verts[i].co = c
                    
                    bm.verts.ensure_lookup_table()
                    bm.to_mesh(mesh)
                    bm.free()
                    mesh.update()
    
    bpy.context.view_layer.update()
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


def bt_update_dorr_placering(self, context):
    """Uppdaterar dörrens position när placering ändras"""
    global _updating_from_ui
    
    if _updating_from_ui:
        return
    
    scene = context.scene
    selected = context.selected_objects
    
    # Hitta markerad komponent
    selected_component = None
    for obj in selected:
        root = find_component_root(obj)
        if root and root.get("komponent_typ") == "DOOR":
            selected_component = root
            break
    
    if not selected_component:
        return
    
    parent_obj = selected_component.parent
    if not parent_obj:
        return
    
    # Hämta väggens egenskaper
    if parent_obj.get("typ") == "innervagg":
        wall_length = parent_obj.get("langd", 5.0)
        if wall_length == 0:
            wall_length = utils.calculate_innervagg_length(parent_obj, context)
        wall_bredd = parent_obj.get("tjocklek", 0.120)
        is_interior = True
        half_thickness = wall_bredd / 2
    else:
        wall_length = parent_obj.get("vagg_langd", 5.0)
        wall_bredd = parent_obj.get("vagg_bredd", 0.15)
        is_interior = False
        half_thickness = 0
    
    # Hämta placeringsparametrar från 50. Place Component
    placering = scene.bt_component_placering
    niva = scene.bt_component_niva
    indragning = scene.bt_component_indragning
    
    # Beräkna position
    if placering == 0:
        x_pos = wall_length / 2.0
    elif placering < 0:
        x_pos = wall_length + placering
    else:
        x_pos = placering
    
    # Uppdatera position
    if is_interior:
        selected_component.location = (x_pos, -half_thickness + indragning, niva)
    else:
        selected_component.location = (x_pos, indragning, niva)
    
    # Spara värden
    selected_component["placering"] = x_pos
    selected_component["niva"] = niva
    selected_component["indragning"] = indragning


def sync_dorr_panel_from_selection(context):
    """Synkroniserar panelens properties från markerad komponent"""
    global _updating_from_ui, _last_selected_dorr
    
    scene = context.scene
    selected = context.selected_objects
    
    selected_component = None
    for obj in selected:
        root = find_component_root(obj)
        if root and root.get("komponent_typ") == "DOOR":
            selected_component = root
            break
    
    if not selected_component:
        return
    
    if selected_component == _last_selected_dorr:
        return
    
    _last_selected_dorr = selected_component
    p = scene.bt_dorr
    
    _updating_from_ui = True
    
    try:
        comp_name = selected_component.get("komponent_namn")
        comp_collection = utils.get_component_by_name(comp_name)
        if comp_collection:
            p.komponent_namn = comp_name
            p.bredd = comp_collection.get("width", 0.9)
            p.hojd = comp_collection.get("height", 2.1)
            p.karmtjocklek = comp_collection.get("karmtjocklek", 0.05)
            p.karmdjup = comp_collection.get("karmdjup", 0.10)
            p.tröskelhöjd = comp_collection.get("tröskelhöjd", 0.05)
            p.hangning = comp_collection.get("hangning", "RIGHT")
    finally:
        _updating_from_ui = False


class BT_DorrProperties(bpy.types.PropertyGroup):
    """Inställningar för dörrar"""
    
    komponent_namn: bpy.props.StringProperty(
        name="Name",
        description="Name of the component",
        default="D101"
    )
    
    bredd: FloatProperty(
        name="Bredd",
        default=0.9,
        min=0.3,
        step=10,
        update=bt_update_dorr
    )
    
    hojd: FloatProperty(
        name="Höjd",
        default=2.1,
        min=0.5,
        step=10,
        update=bt_update_dorr
    )
    
    # NIVA BORTTAGEN - styrs från 50. Place Component (Level)
    
    karmtjocklek: FloatProperty(
        name="Karmtjocklek",
        default=0.05,
        min=0.01,
        step=1,
        update=bt_update_dorr
    )
    
    karmdjup: FloatProperty(
        name="Karmdjup",
        default=0.10,
        min=0.01,
        step=1,
        update=bt_update_dorr
    )
    
    tröskelhöjd: FloatProperty(
        name="Tröskelhöjd",
        default=0.05,
        min=0.0,
        step=1,
        update=bt_update_dorr
    )
    
    hangning: EnumProperty(
        name="",
        description="Vilken sida dörren hänger på",
        items=[
            ('LEFT', "Vänsterhängd", "Gångjärn på vänster sida, handtag på höger"),
            ('RIGHT', "Högerhängd", "Gångjärn på höger sida, handtag på vänster")
        ],
        default='RIGHT',
        update=bt_update_dorr
    )
    
    placering: FloatProperty(
        name="Placering",
        description="Avstånd från vänster kant (positivt) eller höger kant (negativt). 0 = centrera",
        default=0.0,
        min=-100.0,
        step=10,
        update=bt_update_dorr_placering
    )