# ________________________________________________________________________________________________
# UTILS - Gemensamma funktioner (uppdateringar, synkronisering, geometri)
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
import mathutils
from math import radians, sin, tan, cos, atan
from bpy.props import FloatProperty, BoolProperty
from mathutils import Vector, Matrix
from bpy.app.handlers import persistent

DELTA = 0.00001

# Global låsning för att förhindra cirkulära uppdateringar
_updating = False
_update_timer = None
_msgbus_owner = object()  # Unik identifierare för msgbus

def reset_update_lock():
    global _updating
    _updating = False
    return None

# ---------------------------------------------------------------------------
# 1. HÄMTA HUVUDMÅTT
# ---------------------------------------------------------------------------
def get_huvudmått(scene):
    return scene.bt_huvudmått

# ---------------------------------------------------------------------------
# 2. BERÄKNA PLATTANS MÅTT
# ---------------------------------------------------------------------------
def get_platta_mått(scene):
    h = get_huvudmått(scene)
    p = scene.bt_platta
    platt_l = h.fasad_l - p.indrag * 2
    platt_b = h.fasad_b - p.indrag * 2
    return platt_l, platt_b

# ---------------------------------------------------------------------------
# 3. REALTIDSUPPDATERING - PLATTA
# ---------------------------------------------------------------------------
def bt_update_platta(self, context):
    """Uppdaterar plattan när plattparametrar ändras"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    t_platta = next((o for o in scene.objects if o.name.startswith("Betongplatta")), None)
    if not t_platta:
        return
    
    h = get_huvudmått(scene)
    p = scene.bt_platta
    
    v2 = h.fasad_l - p.indrag * 2
    B = h.fasad_b - p.indrag * 2
    t = p.tjocklek
    ind = p.indrag
    H = p.total_hojd
    fb = p.forstyvning_bredd
    
    if H - t < 0:
        return
    
    fi = (H - t) / math.tan(math.radians(p.lutning)) if p.lutning > 0 else 0
    x_min, y_min = 0, 0
    x_max, y_max = v2, B
    x3, y3 = x_min + fb, y_min + fb
    x3b, y3b = x_max - fb, y_max - fb
    
    coords = [
        (x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0),
        (x_min, y_min, -H), (x_max, y_min, -H), (x_max, y_max, -H), (x_min, y_max, -H),
        (x3, y3, -H), (x3b, y3, -H), (x3b, y3b, -H), (x3, y3b, -H),
        (x3 + fi, y3 + fi, -t), (x3b - fi, y3 + fi, -t), (x3b - fi, y3b - fi, -t), (x3 + fi, y3b - fi, -t)
    ]
    
    mesh = t_platta.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
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
    
    t_platta.location = (ind, ind, 0)

# ---------------------------------------------------------------------------
# 4. REALTIDSUPPDATERING - VÄGG
# ---------------------------------------------------------------------------
def bt_update_single_vagg(vagg_obj, langd, bredd, hojd):
    """Uppdaterar en enskild väggs geometri (vänstra kanten vid origo)"""
    if not vagg_obj or len(vagg_obj.data.vertices) != 8:
        return
    
    # Säkerställ att alla värden är positiva
    if langd <= 0:
        langd = 1.0
    if bredd <= 0:
        bredd = 0.15
    if hojd <= 0:
        hojd = 2.5
    
    mesh = vagg_obj.data
    
    coords = [
        (0, 0, 0), (langd, 0, 0), (langd, bredd, 0), (0, bredd, 0),
        (0, 0, hojd), (langd, 0, hojd), (langd, bredd, hojd), (0, bredd, hojd)
    ]
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 8:
        bm.free()
        return
    
    for i, c in enumerate(coords):
        bm.verts[i].co = c
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    vagg_obj["vagg_langd"] = langd
    vagg_obj["vagg_bredd"] = bredd
    vagg_obj["vagg_hojd"] = hojd

def bt_update_selected_vaggar(self, context):
    """Uppdaterar markerade väggar när bredd ändras i panelen"""
    global _updating
    if _updating:
        return
    
    # Hoppa över om vi är mitt i en selection-synkronisering
    from .properties.vagg_settings import _updating_from_selection
    if _updating_from_selection:
        return
    
    scene = context.scene
    p = scene.bt_vagg
    
    # Hitta markerade väggar
    selected_vaggar = [obj for obj in context.selected_objects if obj.get("typ") == "vägg"]
    
    if not selected_vaggar:
        return
    
    for vagg in selected_vaggar:
        # Spara bredden i custom properties (0 = använd teoretisk)
        vagg["vagg_bredd"] = p.bredd
        
        # Uppdatera hela väggen
        bt_update_single_vagg_from_props(vagg, context)

def bt_update_single_vagg_from_props(vagg_obj, context):
    """Uppdaterar en vägg baserat på dess start/längd properties"""
    scene = context.scene
    h = scene.bt_huvudmått
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    teoretisk_bredd = h.teoretisk_vagg_bredd
    
    # Beräkna total höjd
    total_hojd = _calculate_total_wall_height(scene)
    
    vagg_typ = vagg_obj.get("vagg_typ", "")
    spegelvänd = vagg_obj.get("spegelvänd", False)
    vagg_position = vagg_obj.get("vagg_position", "")
    
    # Hämta väggens individuella bredd (användarens värde)
    user_bredd = vagg_obj.get("vagg_bredd", 0.0)
    
    # Använd teoretisk_bredd för geometri om user_bredd är 0
    if user_bredd == 0:
        vagg_bredd = teoretisk_bredd
    else:
        vagg_bredd = user_bredd
    
    # Hämta höjd - 0 betyder full höjd
    vagg_hojd = vagg_obj.get("vagg_hojd", 0.0)
    if vagg_hojd == 0:
        anvand_hojd = total_hojd
    else:
        anvand_hojd = vagg_hojd
    
    if vagg_typ == "gavel":
        start_y = vagg_obj.get("start_y", 0.0)
        langd_y = vagg_obj.get("langd_y", 0.0)
        
        if langd_y == 0:
            langd_y = fasad_b - start_y
        elif langd_y < 0:
            langd_y = fasad_b - start_y + langd_y
        
        if langd_y <= 0:
            langd_y = fasad_b - start_y
        
        x_dim = langd_y
        y_dim = vagg_bredd
        
        if vagg_position == "vanster":
            vagg_obj.location.x = 0
            vagg_obj.location.y = fasad_b - start_y
            vagg_obj.rotation_euler = (0, 0, math.radians(-90))
        else:
            vagg_obj.location.x = fasad_l
            vagg_obj.location.y = start_y
            vagg_obj.rotation_euler = (0, 0, math.radians(90))
        
    else:
        start_x = vagg_obj.get("start_x", teoretisk_bredd)
        langd_x = vagg_obj.get("langd_x", 0.0)
        
        if langd_x == 0:
            langd_x = fasad_l - start_x
        elif langd_x < 0:
            langd_x = fasad_l - start_x + langd_x
        
        if langd_x <= 0:
            langd_x = fasad_l - start_x
        
        x_dim = langd_x
        y_dim = vagg_bredd
        
        if vagg_typ == "fram":
            vagg_obj.location.x = start_x
            vagg_obj.location.y = 0
            vagg_obj.rotation_euler = (0, 0, 0)
        else:  # "bak"
            if spegelvänd:
                vagg_obj.location.x = start_x
            else:
                vagg_obj.location.x = fasad_l - teoretisk_bredd - start_x + teoretisk_bredd
            vagg_obj.location.y = fasad_b
            vagg_obj.rotation_euler = (0, 0, math.radians(180))
    
    # Uppdatera geometri
    bt_update_single_vagg(vagg_obj, x_dim, y_dim, anvand_hojd)
    
    # Spara custom properties - BEHÅLL användarens värde (0 eller >0)
    vagg_obj["vagg_bredd"] = user_bredd
    vagg_obj["vagg_hojd"] = vagg_hojd
    
    # Sätt skala
    if spegelvänd:
        vagg_obj.scale = (-1, 1, 1)
    else:
        vagg_obj.scale = (1, 1, 1)

def bt_update_single_vagg_spegelvänd(self, context):
    """Uppdaterar ENDAST den markerade väggen när spegelvänd-flaggan ändras"""
    global _updating
    
    if _updating:
        return
    
    _updating = True
    
    try:
        import math
        
        scene = context.scene
        h = scene.bt_huvudmått
        fasad_l = h.fasad_l
        fasad_b = h.fasad_b
        teoretisk_bredd = h.teoretisk_vagg_bredd
        
        # Hitta den markerade väggen
        t_vagg = None
        for obj in scene.objects:
            if obj.select_get() and obj.get("typ") == "vägg":
                t_vagg = obj
                break
        
        if not t_vagg:
            return
        
        # Hämta väggens egenskaper
        vagg_typ = t_vagg.get("vagg_typ", "")
        vagg_position = t_vagg.get("vagg_position", "")
        spegelvänd = t_vagg.get("spegelvänd", False)
        
        # Växla spegelvänd status
        ny_spegelvänd = not spegelvänd
        t_vagg["spegelvänd"] = ny_spegelvänd
        
        # Synkronisera med propertyn
        p = scene.bt_vagg
        p.spegelvänd = ny_spegelvänd
        
        # Hämta startvärden
        start_x = t_vagg.get("start_x", teoretisk_bredd)
        start_y = t_vagg.get("start_y", 0.0)
        
        # Uppdatera insättningspunkt baserat på spegelvänd
        if ny_spegelvänd:
            # Spegelvänd: flytta insättningspunkt till motsatt sida
            if vagg_typ == "fram":
                t_vagg["start_x"] = fasad_l - teoretisk_bredd
                t_vagg.location.x = teoretisk_bredd
                t_vagg.scale.x = -1
                
            elif vagg_typ == "bak":
                t_vagg["start_x"] = teoretisk_bredd
                t_vagg.location.x = teoretisk_bredd
                t_vagg.scale.x = -1
                
            elif vagg_typ == "gavel" and vagg_position == "vanster":
                t_vagg["start_y"] = fasad_b
                t_vagg.location.x = 0
                t_vagg.location.y = 0
                t_vagg.rotation_euler = (0, 0, math.radians(0))
                t_vagg.scale.x = -1
                
            elif vagg_typ == "gavel" and vagg_position == "hoger":
                t_vagg["start_y"] = fasad_b
                t_vagg.location.x = fasad_l
                t_vagg.location.y = fasad_b
                t_vagg.rotation_euler = (0, 0, math.radians(180))
                t_vagg.scale.x = -1
        else:
            # Återställ till ursprunglig position
            if vagg_typ == "fram":
                t_vagg["start_x"] = teoretisk_bredd
                t_vagg.location.x = teoretisk_bredd
                t_vagg.scale.x = 1
                
            elif vagg_typ == "bak":
                t_vagg["start_x"] = teoretisk_bredd
                t_vagg.location.x = fasad_l - teoretisk_bredd
                t_vagg.scale.x = 1
                
            elif vagg_typ == "gavel" and vagg_position == "vanster":
                t_vagg["start_y"] = 0.0
                t_vagg.location.x = 0
                t_vagg.location.y = fasad_b
                t_vagg.rotation_euler = (0, 0, math.radians(-90))
                t_vagg.scale.x = 1
                
            elif vagg_typ == "gavel" and vagg_position == "hoger":
                t_vagg["start_y"] = 0.0
                t_vagg.location.x = fasad_l
                t_vagg.location.y = 0
                t_vagg.rotation_euler = (0, 0, math.radians(90))
                t_vagg.scale.x = 1
        
        # Uppdatera väggens geometri
        bt_update_single_vagg_from_props(t_vagg, context)
        
    finally:
        _updating = False

# ---------------------------------------------------------------------------
# 5. CENTRAL TAKBERÄKNING
# ---------------------------------------------------------------------------

def calculate_tak_geometry(scene):
    """
    Beräknar all takgeometri baserat på aktuella inställningar.
    Returnerar en dict med alla beräknade värden.
    """
    from math import radians, sin, cos, tan
    
    h = scene.bt_huvudmått
    t = scene.bt_tak
    
    # ----- HÄMTA ALLA PARAMETRAR -----
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    vagg_bredd = h.teoretisk_vagg_bredd
    taktjocklek = h.taktjocklek
    
    # Hämta taktyp
    roof_type = h.roof_type
    single_slope_roof = (roof_type != 'GABLE')
    slope_front = (roof_type == 'SHED_FRONT')
    slope_back = (roof_type == 'SHED_BACK')
    
    # Invändig höjd fram/bak
    e = h.vagg_hojd
    if h.använd_symmetrisk_vagg_hojd:
        k = h.vagg_hojd_bak
    else:
        k = e
    
    # Taklutningar
    v0 = radians(h.taklutning)  # Nedre fram
    if h.använd_symmetrisk_taklutning:
        v2 = radians(h.taklutning_bak)  # Nedre bak
    else:
        v2 = v0
    
    # Övre fram (mansard)
    if h.använd_mansard_fram:
        v1 = radians(h.taklutning_mansard)
    else:
        v1 = v0
    
    # Övre bak (mansard)
    if h.använd_mansard_bak:
        v3 = radians(h.taklutning_mansard_bak)
    else:
        if h.använd_symmetrisk_taklutning:
            v3 = v2
        else:
            if h.använd_mansard_fram:
                v3 = v1
            else:
                v3 = v0
    
    # Takutsprång
    takutsprång_hitsida = h.takutsprång
    if h.använd_symmetrisk_takutsprång:
        m = h.takutsprång_bak
    else:
        m = takutsprång_hitsida
    
    # Gavelutsprång
    gavelutsprång_vanster = h.gavelutsprång
    if h.använd_symmetrisk_gavelutsprång:
        n = h.gavelutsprång_hoger
    else:
        n = gavelutsprång_vanster
    
    # Brytavstånd
    brytavstand = t.brytavstand
    if h.använd_brytavstand_fram:
        brytavstand_hitsida = h.brytavstand_mansard
    else:
        brytavstand_hitsida = brytavstand
    
    if h.använd_brytavstand_bak:
        p = h.brytavstand_mansard_bak
    else:
        p = brytavstand_hitsida
    
    # ----- BERÄKNA INNERTAK -----
    innertak_z_fram = e - vagg_bredd * tan(v0)
    innertak_z_bak = k - vagg_bredd * tan(v2)
    
    # Brytpunkter
    z1 = innertak_z_fram + brytavstand_hitsida * tan(v0)
    z2 = innertak_z_bak + p * tan(v2)
    
    # Nock
    y_avstand = fasad_b - brytavstand_hitsida - p
    if tan(v1) + tan(v3) != 0:
        y1 = (y_avstand * tan(v3) - z1 + z2) / (tan(v1) + tan(v3))
    else:
        y1 = y_avstand / 2
    
    # ----- PULPETTAK - justera nockposition -----
    if single_slope_roof:
        if slope_front:
            y1 = fasad_b - brytavstand_hitsida
        elif slope_back:
            y1 = brytavstand_hitsida
    
    nock_z = z1 + y1 * tan(v1)
    
    # Nock utsida (med taktjocklek)
    if abs(v1 - v3) < 0.001:
        nock_utsida = nock_z + taktjocklek / cos(v1)
    else:
        nock_utsida = nock_z + taktjocklek / cos((v1 + v3) / 2) * cos((v1 - v3) / 2)
    
    # Takets ovansida vid olika punkter
    tak_ovansida_fram = innertak_z_fram + taktjocklek / cos(v0)
    tak_ovansida_bak = innertak_z_bak + taktjocklek / cos(v2)
    tak_ovansida_bryt_fram = z1 + taktjocklek / cos((v0 - v1) / 2) * cos((v0 + v1) / 2)
    tak_ovansida_bryt_bak = z2 + taktjocklek / cos((v2 - v3) / 2) * cos((v2 + v3) / 2)
    tak_ovansida_nock = nock_z + taktjocklek / cos((v1 + v3) / 2) * cos((v1 - v3) / 2)
    
    # ----- Y-POSITIONER (14 punkter) -----
    y_pos = [0.0] * 14
    y_pos[0] = -takutsprång_hitsida
    y_pos[1] = brytavstand_hitsida
    y_pos[2] = brytavstand_hitsida + y1
    y_pos[3] = fasad_b - p
    y_pos[4] = fasad_b + m
    y_pos[5] = y_pos[4] + (taktjocklek - 0.020) * sin(v2)
    y_pos[6] = y_pos[5] + 0.050 * cos(v2)
    y_pos[7] = y_pos[6] + 0.020 * sin(v2)
    y_pos[8] = y_pos[3] + taktjocklek / cos((v2 - v3) / 2) * sin((v2 + v3) / 2)
    y_pos[9] = y_pos[2] - taktjocklek / cos((v1 + v3) / 2) * sin((v1 - v3) / 2)
    y_pos[10] = y_pos[1] - taktjocklek / cos((v0 - v1) / 2) * sin((v0 + v1) / 2)
    y_pos[13] = y_pos[0] - (taktjocklek - 0.020) * sin(v0)
    y_pos[12] = y_pos[13] - 0.050 * cos(v0)
    y_pos[11] = y_pos[12] - 0.020 * sin(v0)
    
    # ----- Z-POSITIONER (14 punkter) -----
    z_pos = [0.0] * 14
    z_pos[0] = innertak_z_fram - takutsprång_hitsida * tan(v0)
    z_pos[1] = z1
    z_pos[2] = nock_z
    z_pos[3] = z2
    z_pos[4] = innertak_z_bak - m * tan(v2)
    z_pos[5] = z_pos[4] + (taktjocklek - 0.020) * cos(v2)
    z_pos[6] = z_pos[5] - 0.050 * sin(v2)
    z_pos[7] = z_pos[6] + 0.020 * cos(v2)
    z_pos[8] = z_pos[3] + taktjocklek / cos((v2 - v3) / 2) * cos((v2 + v3) / 2)
    z_pos[9] = nock_z + taktjocklek / cos((v1 + v3) / 2) * cos((v1 - v3) / 2)
    z_pos[10] = z_pos[1] + taktjocklek / cos((v0 - v1) / 2) * cos((v0 + v1) / 2)
    z_pos[13] = z_pos[0] + (taktjocklek - 0.020) * cos(v0)
    z_pos[12] = z_pos[13] - 0.050 * sin(v0)
    z_pos[11] = z_pos[12] + 0.020 * cos(v0)
    
    # ----- PULPETTAK - justera bak -----
    if single_slope_roof:
        if slope_front:
            y_pos[2] = fasad_b
            y_pos[9] = fasad_b
            z_pos[2] = nock_z
            z_pos[9] = nock_z + taktjocklek / cos(v1)
            for i in [3, 4, 5, 6, 7, 8]:
                y_pos[i] = y_pos[2]
                z_pos[i] = z_pos[2]
        elif slope_back:
            y_pos[2] = brytavstand_hitsida
            y_pos[9] = brytavstand_hitsida
            z_pos[2] = nock_z
            z_pos[9] = nock_z + taktjocklek / cos(v1)
            for i in [0, 1, 10, 11, 12, 13]:
                y_pos[i] = 0
                z_pos[i] = nock_z
    
    # ----- FLYTTA BRYTNING TILL NÄRA NOCK (om inte mansard) -----
    fram_brytning = h.använd_brytavstand_fram or h.använd_mansard_fram
    bak_brytning = h.använd_brytavstand_bak or h.använd_mansard_bak
    
    if not fram_brytning:
        y_pos[1] = y_pos[2] - DELTA
        y_pos[10] = y_pos[9] - DELTA
        z_pos[1] = z_pos[2]
        z_pos[10] = z_pos[9]
    
    if not bak_brytning and (not fram_brytning or h.använd_symmetrisk_taklutning):
        y_pos[3] = y_pos[2] + DELTA
        y_pos[8] = y_pos[9] + DELTA
        z_pos[3] = z_pos[2]
        z_pos[8] = z_pos[9]
    
    # ----- SKAPA VERTICES FÖR HELA TAKET -----
    v_verts = []
    h_verts = []
    for i in range(14):
        v_verts.append((-gavelutsprång_vanster, y_pos[i], z_pos[i]))
        h_verts.append((fasad_l + n, y_pos[i], z_pos[i]))
    
    # ----- RETURNERA ALL DATA -----
    return {
        'fasad_l': fasad_l,
        'fasad_b': fasad_b,
        'vagg_bredd': vagg_bredd,
        'taktjocklek': taktjocklek,
        'gavelutsprång_vanster': gavelutsprång_vanster,
        'gavelutsprång_hoger': n,
        'takutsprång_fram': takutsprång_hitsida,
        'takutsprång_bak': m,
        'v0': v0, 'v1': v1, 'v2': v2, 'v3': v3,
        'e': e, 'k': k,
        'innertak_z_fram': innertak_z_fram,
        'innertak_z_bak': innertak_z_bak,
        'z1': z1, 'z2': z2,
        'nock_z': nock_z,
        'nock_utsida': nock_utsida,
        'y1': y1,
        'brytavstand_hitsida': brytavstand_hitsida,
        'brytavstand_bak': p,
        'y_pos': y_pos,
        'z_pos': z_pos,
        'v_verts': v_verts,
        'h_verts': h_verts,
        'tak_ovansida_fram': tak_ovansida_fram,
        'tak_ovansida_bak': tak_ovansida_bak,
        'tak_ovansida_bryt_fram': tak_ovansida_bryt_fram,
        'tak_ovansida_bryt_bak': tak_ovansida_bryt_bak,
        'tak_ovansida_nock': tak_ovansida_nock,
        'single_slope_roof': single_slope_roof,
        'slope_front': slope_front,
        'slope_back': slope_back,
        'fram_brytning': fram_brytning,
        'bak_brytning': bak_brytning,
    }


# ---------------------------------------------------------------------------
# 6. TAKDELAR - Definition av vilka vertices som tillhör varje takdel
# ---------------------------------------------------------------------------

TAKDELAR_INFO = {
    "Tak_Nedre_Fram": {
        "v_indices": [0, 1, 10, 11, 12, 13],
        "h_indices": [0, 1, 10, 11, 12, 13],
        "faces": [
            (0, 1, 7, 6),
            (1, 2, 8, 7),
            (2, 3, 9, 8),
            (3, 4, 10, 9),
            (4, 5, 11, 10),
            (5, 0, 6, 11),
            (0, 1, 2, 3, 4, 5),
            (6, 7, 8, 9, 10, 11)
        ]
    },
    "Tak_Övre_Fram": {
        "v_indices": [1, 2, 9, 10],
        "h_indices": [1, 2, 9, 10],
        "faces": [
            (2, 3, 7, 6),
            (4, 5, 1, 0),
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 4, 7, 3),
            (1, 2, 6, 5),
        ]
    },
    "Tak_Nedre_Bak": {
        "v_indices": [4, 3, 8, 7, 6, 5],
        "h_indices": [4, 3, 8, 7, 6, 5],
        "faces": [
            (0, 1, 7, 6),
            (1, 2, 8, 7),
            (2, 3, 9, 8),
            (3, 4, 10, 9),
            (4, 5, 11, 10),
            (5, 0, 6, 11),
            (0, 1, 2, 3, 4, 5),
            (6, 7, 8, 9, 10, 11)
        ]
    },
    "Tak_Övre_Bak": {
        "v_indices": [3, 2, 9, 8],
        "h_indices": [3, 2, 9, 8],
        "faces": [
            (2, 3, 7, 6),
            (4, 5, 1, 0),
            (0, 1, 2, 3),
            (4, 5, 6, 7),
            (0, 4, 7, 3),
            (1, 2, 6, 5),
        ]
    }
}

# ---------------------------------------------------------------------------
# 7. REALTIDSUPPDATERING - TAK
# ---------------------------------------------------------------------------

def bt_update_tak(self, context):
    """Uppdaterar taket när användaren ändrar takparametrar"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    # Hitta alla takdelar
    takdelar_obj = {}
    for obj in scene.objects:
        if obj.name.startswith("Tak_"):
            takdelar_obj[obj.name] = obj
    
    if not takdelar_obj:
        return
    
    # Beräkna takgeometri med central funktion
    geo = calculate_tak_geometry(scene)
    
    # Uppdatera varje takdel
    for namn, info in TAKDELAR_INFO.items():
        if namn not in takdelar_obj:
            continue
        
        obj = takdelar_obj[namn]
        mesh = obj.data
        
        if mesh.is_editmode:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                continue
        
        v_indices = info["v_indices"]
        h_indices = info["h_indices"]
        
        # Hämta nya vertices för denna del
        del_verts = []
        for idx in v_indices:
            del_verts.append(geo['v_verts'][idx])
        for idx in h_indices:
            del_verts.append(geo['h_verts'][idx])
        
        # Uppdatera vertices i meshen
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        
        if len(bm.verts) != len(del_verts):
            bm.free()
            continue
        
        for i, v3 in enumerate(del_verts):
            bm.verts[i].co = v3
        
        bm.verts.ensure_lookup_table()
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
    
    # Uppdatera guiderna
    bt_update_wall_guide(self, context)
    bt_update_all_guides(self, context)

# ---------------------------------------------------------------------------
# 8. GUIDES - SKAPA FUNKTIONER
# ---------------------------------------------------------------------------

def create_wall_guide(context, fasad_l, fasad_b, vagg_hojd, taklutning, gavelutsprång, takutsprång, taktjocklek, teoretisk_bredd):
    """
    Creates a guide volume from floor (Z=0) up to the underside of the roof (interior).
    Used with Boolean INTERSECT to trim walls to the roof shape.
    """
    try:
        from math import radians, tan
        
        # Hämta huvudmått
        h = context.scene.bt_huvudmått
        
        # Hämta taktyp
        roof_type = h.roof_type
        single_slope_roof = (roof_type != 'GABLE')
        slope_front = (roof_type == 'SHED_FRONT')
        slope_back = (roof_type == 'SHED_BACK')
        
        # ----- HÄMTA VÄRDEN -----
        e = h.vagg_hojd
        if h.använd_symmetrisk_vagg_hojd:
            k = h.vagg_hojd_bak
        else:
            k = h.vagg_hojd
        
        v0 = radians(h.taklutning)
        if h.använd_symmetrisk_taklutning:
            v2 = radians(h.taklutning_bak)
        else:
            v2 = v0
        
        if h.använd_mansard_fram:
            v1 = radians(h.taklutning_mansard)
        else:
            v1 = v0
        
        if h.använd_mansard_bak:
            v3 = radians(h.taklutning_mansard_bak)
        else:
            if h.använd_symmetrisk_taklutning:
                v3 = v2
            else:
                if h.använd_mansard_fram:
                    v3 = v1
                else:
                    v3 = v0
        
        takutsprång_hitsida = h.takutsprång
        if h.använd_symmetrisk_takutsprång:
            m = h.takutsprång_bak
        else:
            m = takutsprång_hitsida
        
        gavelutsprång_vanster = h.gavelutsprång
        if h.använd_symmetrisk_gavelutsprång:
            n = h.gavelutsprång_hoger
        else:
            n = gavelutsprång_vanster

        t = context.scene.bt_tak
        brytavstand = t.brytavstand
        vagg_bredd = teoretisk_bredd
        
        if h.använd_brytavstand_fram:
            brytavstand_hitsida = h.brytavstand_mansard
        else:
            brytavstand_hitsida = brytavstand
        
        if h.använd_brytavstand_bak:
            p = h.brytavstand_mansard_bak
        else:
            p = brytavstand_hitsida
        
        # ----- BERÄKNA TAKETS UNDERSIDA (INVÄNDIGT) -----
        innertak_z_fram = e - vagg_bredd * tan(v0)
        innertak_z_bak = k - vagg_bredd * tan(v2)
        
        z1 = innertak_z_fram + brytavstand_hitsida * tan(v0)
        z2 = innertak_z_bak + p * tan(v2)
        
        y_avstand = fasad_b - brytavstand_hitsida - p
        
        if tan(v1) + tan(v3) != 0:
            y1 = (y_avstand * tan(v3) - z1 + z2) / (tan(v1) + tan(v3))
        else:
            y1 = y_avstand / 2
        
        if single_slope_roof:
            if slope_front:
                y1 = fasad_b - brytavstand_hitsida
            elif slope_back:
                y1 = brytavstand_hitsida
        
        nock_z = z1 + y1 * tan(v1)
        
        # Skapa vertices
        verts = []
        
        def add_vert(x, y, z):
            verts.append((x, y, z))
            return len(verts) - 1
        
        # Vänster gavel (0-6)
        add_vert(-gavelutsprång_vanster, -0.0001, 0.0)
        add_vert(-gavelutsprång_vanster, -0.0001, innertak_z_fram)
        add_vert(-gavelutsprång_vanster, brytavstand_hitsida, z1)
        add_vert(-gavelutsprång_vanster, brytavstand_hitsida + y1, nock_z)
        add_vert(-gavelutsprång_vanster, fasad_b - p, z2)
        add_vert(-gavelutsprång_vanster, fasad_b + 0.0001, innertak_z_bak)
        add_vert(-gavelutsprång_vanster, fasad_b + 0.0001, 0.0)
        
        # Höger gavel (7-13)
        add_vert(fasad_l + n, -0.0001, 0.0)
        add_vert(fasad_l + n, -0.0001, innertak_z_fram)
        add_vert(fasad_l + n, brytavstand_hitsida, z1)
        add_vert(fasad_l + n, brytavstand_hitsida + y1, nock_z)
        add_vert(fasad_l + n, fasad_b - p, z2)
        add_vert(fasad_l + n, fasad_b + 0.0001, innertak_z_bak)
        add_vert(fasad_l + n, fasad_b + 0.0001, 0.0)
        
        # Faces
        faces = [
            (0, 6, 13, 7),  # Golv
            (0, 1, 8, 7),   # Framsida
            (6, 5, 12, 13), # Baksida
            (1, 2, 9, 8),   # Tak 1
            (2, 3, 10, 9),  # Tak 2
            (3, 4, 11, 10), # Tak 3
            (4, 5, 12, 11), # Tak 4
            (0, 1, 2, 3, 4, 5, 6),   # Vänster gavel
            (7, 8, 9, 10, 11, 12, 13) # Höger gavel
        ]
        
        # Skapa mesh
        mesh = bpy.data.meshes.new("Wall_Guide_Mesh")
        obj = bpy.data.objects.new("Wall_Guide", mesh)
        
        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        
        for face in faces:
            try:
                bm.faces.new([bm.verts[i] for i in face])
            except:
                pass
        
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        return obj
        
    except Exception as e:
        print(f"Error in create_wall_guide: {e}")
        return None


def create_exterior_guide(context, fasad_l, fasad_b, vagg_hojd, taklutning, gavelutsprång, takutsprång, taktjocklek, teoretisk_bredd):
    """
    Creates a guide that follows the exterior of the walls and the outside of the roof.
    Used for connecting other buildings to the exterior walls.
    """
    try:
        geo = calculate_tak_geometry(context.scene)
        
        y_fram = -0.0001
        y_bak = geo['fasad_b'] + 0.0001
        y_bryt_fram = geo['brytavstand_hitsida'] - geo['taktjocklek'] / cos((geo['v0'] - geo['v1']) / 2) * sin((geo['v0'] + geo['v1']) / 2)
        y_bryt_bak = geo['fasad_b'] - geo['brytavstand_bak'] + geo['taktjocklek'] / cos((geo['v2'] - geo['v3']) / 2) * sin((geo['v2'] + geo['v3']) / 2)
        y_nock = geo['brytavstand_hitsida'] + geo['y1']
        
        verts = []
        
        # Vänster sida
        x_vanster = -0.0001
        verts.append((x_vanster, y_fram, 0.0))
        verts.append((x_vanster, y_fram, geo['tak_ovansida_fram'] + 0.0001))
        verts.append((x_vanster, y_bryt_fram, geo['tak_ovansida_bryt_fram'] + 0.0001))
        verts.append((x_vanster, y_nock, geo['tak_ovansida_nock'] + 0.0001))
        verts.append((x_vanster, y_bryt_bak, geo['tak_ovansida_bryt_bak'] + 0.0001))
        verts.append((x_vanster, y_bak, geo['tak_ovansida_bak'] + 0.0001))
        verts.append((x_vanster, y_bak, 0.0))
        
        # Höger sida
        x_hoger = geo['fasad_l'] + 0.0001
        verts.append((x_hoger, y_fram, 0.0))
        verts.append((x_hoger, y_fram, geo['tak_ovansida_fram'] + 0.0001))
        verts.append((x_hoger, y_bryt_fram, geo['tak_ovansida_bryt_fram'] + 0.0001))
        verts.append((x_hoger, y_nock, geo['tak_ovansida_nock'] + 0.0001))
        verts.append((x_hoger, y_bryt_bak, geo['tak_ovansida_bryt_bak'] + 0.0001))
        verts.append((x_hoger, y_bak, geo['tak_ovansida_bak'] + 0.0001))
        verts.append((x_hoger, y_bak, 0.0))
        
        faces = [
            (0, 6, 13, 7),
            (0, 1, 8, 7),
            (6, 5, 12, 13),
            (1, 2, 9, 8),
            (2, 3, 10, 9),
            (3, 4, 11, 10),
            (4, 5, 12, 11),
            (0, 1, 2, 3, 4, 5, 6),
            (7, 8, 9, 10, 11, 12, 13)
        ]
        
        mesh = bpy.data.meshes.new("Exterior_Guide_Mesh")
        obj = bpy.data.objects.new("Exterior_Guide", mesh)
        
        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        
        for face in faces:
            try:
                bm.faces.new([bm.verts[i] for i in face])
            except:
                pass
        
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        return obj
        
    except Exception as e:
        print(f"Error in create_exterior_guide: {e}")
        return None


def create_interior_guide(context, fasad_l, fasad_b, vagg_hojd, taklutning, gavelutsprång, takutsprång, taktjocklek, teoretisk_bredd):
    """
    Creates a guide that follows the interior of the walls and the interior wall height.
    Used for creating floor slabs and interior walls.
    """
    try:
        geo = calculate_tak_geometry(context.scene)
        
        vagg_bredd = geo['vagg_bredd']
        e = geo['e'] - 0.0001
        k = geo['k'] - 0.0001
        
        brytavstand_insida_fram = geo['brytavstand_hitsida'] - vagg_bredd
        brytavstand_insida_bak = geo['brytavstand_bak'] - vagg_bredd
        
        z1_inner = e + brytavstand_insida_fram * tan(geo['v0'])
        z2_inner = k + brytavstand_insida_bak * tan(geo['v2'])
        
        y_bryt_fram_inner = vagg_bredd + brytavstand_insida_fram + 0.0001
        y_bryt_bak_inner = geo['fasad_b'] - vagg_bredd - brytavstand_insida_bak - 0.0001
        
        y_avstand_inner = geo['fasad_b'] - geo['brytavstand_hitsida'] - geo['brytavstand_bak']
        if tan(geo['v1']) + tan(geo['v3']) != 0:
            y1_inner = (y_avstand_inner * tan(geo['v3']) - z1_inner + z2_inner) / (tan(geo['v1']) + tan(geo['v3']))
        else:
            y1_inner = y_avstand_inner / 2
        
        nock_z_inner = z1_inner + y1_inner * tan(geo['v1'])
        y_nock_inner = geo['brytavstand_hitsida'] + y1_inner
        
        y_fram_inner = vagg_bredd + 0.0001
        y_bak_inner = geo['fasad_b'] - vagg_bredd - 0.0001
        
        verts = []
        
        # Vänster sida
        x_vanster_inner = vagg_bredd + 0.0001
        verts.append((x_vanster_inner, y_fram_inner, 0.0))
        verts.append((x_vanster_inner, y_fram_inner, e))
        verts.append((x_vanster_inner, y_bryt_fram_inner, z1_inner))
        verts.append((x_vanster_inner, y_nock_inner, nock_z_inner))
        verts.append((x_vanster_inner, y_bryt_bak_inner, z2_inner))
        verts.append((x_vanster_inner, y_bak_inner, k))
        verts.append((x_vanster_inner, y_bak_inner, 0.0))
        
        # Höger sida
        x_hoger_inner = geo['fasad_l'] - vagg_bredd - 0.0001
        verts.append((x_hoger_inner, y_fram_inner, 0.0))
        verts.append((x_hoger_inner, y_fram_inner, e))
        verts.append((x_hoger_inner, y_bryt_fram_inner, z1_inner))
        verts.append((x_hoger_inner, y_nock_inner, nock_z_inner))
        verts.append((x_hoger_inner, y_bryt_bak_inner, z2_inner))
        verts.append((x_hoger_inner, y_bak_inner, k))
        verts.append((x_hoger_inner, y_bak_inner, 0.0))
        
        faces = [
            (0, 6, 13, 7),
            (0, 1, 8, 7),
            (6, 5, 12, 13),
            (1, 2, 9, 8),
            (2, 3, 10, 9),
            (3, 4, 11, 10),
            (4, 5, 12, 11),
            (0, 1, 2, 3, 4, 5, 6),
            (7, 8, 9, 10, 11, 12, 13)
        ]
        
        mesh = bpy.data.meshes.new("Interior_Guide_Mesh")
        obj = bpy.data.objects.new("Interior_Guide", mesh)
        
        bm = bmesh.new()
        for v in verts:
            bm.verts.new(v)
        bm.verts.ensure_lookup_table()
        
        for face in faces:
            try:
                bm.faces.new([bm.verts[i] for i in face])
            except:
                pass
        
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        
        bm.to_mesh(mesh)
        bm.free()
        mesh.update()
        
        return obj
        
    except Exception as e:
        print(f"Error in create_interior_guide: {e}")
        return None


# ---------------------------------------------------------------------------
# 9. GUIDES - UPPDATERINGSFUNKTIONER
# ---------------------------------------------------------------------------

def bt_update_wall_guide(self, context):
    """Updates Wall_Guide when roof parameters change"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    # Hitta guiden
    guide_obj = None
    for obj in scene.objects:
        if obj.name == "Wall_Guide":
            guide_obj = obj
            break
    
    if not guide_obj:
        return
    
    # Hämta huvudmått
    h = scene.bt_huvudmått
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    vagg_bredd = h.teoretisk_vagg_bredd
    taktjocklek = h.taktjocklek
    
    # Hämta taktyp
    roof_type = h.roof_type
    single_slope_roof = (roof_type != 'GABLE')
    slope_front = (roof_type == 'SHED_FRONT')
    slope_back = (roof_type == 'SHED_BACK')
    
    from math import radians, tan
    
    e = h.vagg_hojd
    if h.använd_symmetrisk_vagg_hojd:
        k = h.vagg_hojd_bak
    else:
        k = h.vagg_hojd
    
    v0 = radians(h.taklutning)
    if h.använd_symmetrisk_taklutning:
        v2 = radians(h.taklutning_bak)
    else:
        v2 = v0
    
    if h.använd_mansard_fram:
        v1 = radians(h.taklutning_mansard)
    else:
        v1 = v0
    
    if h.använd_mansard_bak:
        v3 = radians(h.taklutning_mansard_bak)
    else:
        if h.använd_symmetrisk_taklutning:
            v3 = v2
        else:
            if h.använd_mansard_fram:
                v3 = v1
            else:
                v3 = v0
    
    takutsprång_hitsida = h.takutsprång
    if h.använd_symmetrisk_takutsprång:
        m = h.takutsprång_bak
    else:
        m = takutsprång_hitsida
    
    gavelutsprång_vanster = h.gavelutsprång
    if h.använd_symmetrisk_gavelutsprång:
        n = h.gavelutsprång_hoger
    else:
        n = gavelutsprång_vanster

    t = scene.bt_tak
    brytavstand = t.brytavstand
    
    if h.använd_brytavstand_fram:
        brytavstand_hitsida = h.brytavstand_mansard
    else:
        brytavstand_hitsida = brytavstand
    
    if h.använd_brytavstand_bak:
        p = h.brytavstand_mansard_bak
    else:
        p = brytavstand_hitsida
    
    innertak_z_fram = e - vagg_bredd * tan(v0)
    innertak_z_bak = k - vagg_bredd * tan(v2)
    
    z1 = innertak_z_fram + brytavstand_hitsida * tan(v0)
    z2 = innertak_z_bak + p * tan(v2)
    
    y_avstand = fasad_b - brytavstand_hitsida - p
    
    if tan(v1) + tan(v3) != 0:
        y1 = (y_avstand * tan(v3) - z1 + z2) / (tan(v1) + tan(v3))
    else:
        y1 = y_avstand / 2
    
    if single_slope_roof:
        if slope_front:
            y1 = fasad_b - brytavstand_hitsida
        elif slope_back:
            y1 = brytavstand_hitsida
    
    nock_z = z1 + y1 * tan(v1)
    
    # Uppdatera vertices
    mesh = guide_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 14:
        bm.free()
        return
    
    # Vänster sida (0-6)
    bm.verts[0].co = (-gavelutsprång_vanster, -0.0001, 0.0)
    bm.verts[1].co = (-gavelutsprång_vanster, -0.0001, innertak_z_fram)
    bm.verts[2].co = (-gavelutsprång_vanster, brytavstand_hitsida, z1)
    bm.verts[3].co = (-gavelutsprång_vanster, brytavstand_hitsida + y1, nock_z)
    bm.verts[4].co = (-gavelutsprång_vanster, fasad_b - p, z2)
    bm.verts[5].co = (-gavelutsprång_vanster, fasad_b + 0.0001, innertak_z_bak)
    bm.verts[6].co = (-gavelutsprång_vanster, fasad_b + 0.0001, 0.0)
    
    # Höger sida (7-13)
    bm.verts[7].co = (fasad_l + n, -0.0001, 0.0)
    bm.verts[8].co = (fasad_l + n, -0.0001, innertak_z_fram)
    bm.verts[9].co = (fasad_l + n, brytavstand_hitsida, z1)
    bm.verts[10].co = (fasad_l + n, brytavstand_hitsida + y1, nock_z)
    bm.verts[11].co = (fasad_l + n, fasad_b - p, z2)
    bm.verts[12].co = (fasad_l + n, fasad_b + 0.0001, innertak_z_bak)
    bm.verts[13].co = (fasad_l + n, fasad_b + 0.0001, 0.0)
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def bt_update_exterior_guide(self, context):
    """Updates Exterior_Guide when roof parameters change"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    guide_obj = None
    for obj in scene.objects:
        if obj.name == "Exterior_Guide":
            guide_obj = obj
            break
    
    if not guide_obj:
        return
    
    geo = calculate_tak_geometry(scene)
    _update_exterior_guide(guide_obj, geo)


def bt_update_interior_guide(self, context):
    """Updates Interior_Guide when roof parameters change"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    guide_obj = None
    for obj in scene.objects:
        if obj.name == "Interior_Guide":
            guide_obj = obj
            break
    
    if not guide_obj:
        return
    
    geo = calculate_tak_geometry(scene)
    _update_interior_guide(guide_obj, geo)


def bt_update_all_guides(self, context):
    """Updates all guides (Wall_Guide, Exterior_Guide, Interior_Guide)"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    wall_guide = None
    exterior_guide = None
    interior_guide = None
    
    for obj in scene.objects:
        if obj.name == "Wall_Guide":
            wall_guide = obj
        elif obj.name == "Exterior_Guide":
            exterior_guide = obj
        elif obj.name == "Interior_Guide":
            interior_guide = obj
    
    if not wall_guide or not exterior_guide or not interior_guide:
        return
    
    geo = calculate_tak_geometry(scene)
    
    _update_exterior_guide(exterior_guide, geo)
    _update_interior_guide(interior_guide, geo)


def _update_exterior_guide(guide_obj, geo):
    """Updates Exterior_Guide with calculated geometry"""
    mesh = guide_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 14:
        bm.free()
        return
    
    y_fram = -0.0001
    y_bak = geo['fasad_b'] + 0.0001
    y_bryt_fram = geo['brytavstand_hitsida'] - geo['taktjocklek'] / cos((geo['v0'] - geo['v1']) / 2) * sin((geo['v0'] + geo['v1']) / 2)
    y_bryt_bak = geo['fasad_b'] - geo['brytavstand_bak'] + geo['taktjocklek'] / cos((geo['v2'] - geo['v3']) / 2) * sin((geo['v2'] + geo['v3']) / 2)
    y_nock = geo['brytavstand_hitsida'] + geo['y1']
    
    x_vanster = -0.0001
    bm.verts[0].co = (x_vanster, y_fram, 0.0)
    bm.verts[1].co = (x_vanster, y_fram, geo['tak_ovansida_fram'] + 0.0001)
    bm.verts[2].co = (x_vanster, y_bryt_fram, geo['tak_ovansida_bryt_fram'] + 0.0001)
    bm.verts[3].co = (x_vanster, y_nock, geo['tak_ovansida_nock'] + 0.0001)
    bm.verts[4].co = (x_vanster, y_bryt_bak, geo['tak_ovansida_bryt_bak'] + 0.0001)
    bm.verts[5].co = (x_vanster, y_bak, geo['tak_ovansida_bak'] + 0.0001)
    bm.verts[6].co = (x_vanster, y_bak, 0.0)
    
    x_hoger = geo['fasad_l'] + 0.0001
    bm.verts[7].co = (x_hoger, y_fram, 0.0)
    bm.verts[8].co = (x_hoger, y_fram, geo['tak_ovansida_fram'] + 0.0001)
    bm.verts[9].co = (x_hoger, y_bryt_fram, geo['tak_ovansida_bryt_fram'] + 0.0001)
    bm.verts[10].co = (x_hoger, y_nock, geo['tak_ovansida_nock'] + 0.0001)
    bm.verts[11].co = (x_hoger, y_bryt_bak, geo['tak_ovansida_bryt_bak'] + 0.0001)
    bm.verts[12].co = (x_hoger, y_bak, geo['tak_ovansida_bak'] + 0.0001)
    bm.verts[13].co = (x_hoger, y_bak, 0.0)
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def _update_interior_guide(guide_obj, geo):
    """Updates Interior_Guide with calculated geometry"""
    mesh = guide_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 14:
        bm.free()
        return
    
    vagg_bredd = geo['vagg_bredd']
    e = geo['e'] - 0.0001
    k = geo['k'] - 0.0001
    
    brytavstand_insida_fram = geo['brytavstand_hitsida'] - vagg_bredd
    brytavstand_insida_bak = geo['brytavstand_bak'] - vagg_bredd
    
    z1_inner = e + brytavstand_insida_fram * tan(geo['v0'])
    z2_inner = k + brytavstand_insida_bak * tan(geo['v2'])
    
    y_bryt_fram_inner = vagg_bredd + brytavstand_insida_fram + 0.0001
    y_bryt_bak_inner = geo['fasad_b'] - vagg_bredd - brytavstand_insida_bak - 0.0001
    
    y_avstand_inner = geo['fasad_b'] - geo['brytavstand_hitsida'] - geo['brytavstand_bak']
    if tan(geo['v1']) + tan(geo['v3']) != 0:
        y1_inner = (y_avstand_inner * tan(geo['v3']) - z1_inner + z2_inner) / (tan(geo['v1']) + tan(geo['v3']))
    else:
        y1_inner = y_avstand_inner / 2
    
    nock_z_inner = z1_inner + y1_inner * tan(geo['v1'])
    y_nock_inner = geo['brytavstand_hitsida'] + y1_inner
    
    y_fram_inner = vagg_bredd + 0.0001
    y_bak_inner = geo['fasad_b'] - vagg_bredd - 0.0001
    
    x_vanster_inner = vagg_bredd + 0.0001
    bm.verts[0].co = (x_vanster_inner, y_fram_inner, 0.0)
    bm.verts[1].co = (x_vanster_inner, y_fram_inner, e)
    bm.verts[2].co = (x_vanster_inner, y_bryt_fram_inner, z1_inner)
    bm.verts[3].co = (x_vanster_inner, y_nock_inner, nock_z_inner)
    bm.verts[4].co = (x_vanster_inner, y_bryt_bak_inner, z2_inner)
    bm.verts[5].co = (x_vanster_inner, y_bak_inner, k)
    bm.verts[6].co = (x_vanster_inner, y_bak_inner, 0.0)
    
    x_hoger_inner = geo['fasad_l'] - vagg_bredd - 0.0001
    bm.verts[7].co = (x_hoger_inner, y_fram_inner, 0.0)
    bm.verts[8].co = (x_hoger_inner, y_fram_inner, e)
    bm.verts[9].co = (x_hoger_inner, y_bryt_fram_inner, z1_inner)
    bm.verts[10].co = (x_hoger_inner, y_nock_inner, nock_z_inner)
    bm.verts[11].co = (x_hoger_inner, y_bryt_bak_inner, z2_inner)
    bm.verts[12].co = (x_hoger_inner, y_bak_inner, k)
    bm.verts[13].co = (x_hoger_inner, y_bak_inner, 0.0)
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()

# ---------------------------------------------------------------------------
# 10. REALTIDSUPPDATERING - BJÄLKLAG
# ---------------------------------------------------------------------------
def compute_bjalklag_matt(scene):
    """Beräknar bjälklagets mått baserat på inställningarna"""
    h = scene.bt_huvudmått
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    
    p = scene.bt_bjalklag
    
    start_x = p.start_x
    start_y = p.start_y
    
    if p.langd_x == 0:
        langd_x = fasad_l - start_x
    elif p.langd_x < 0:
        langd_x = fasad_l - start_x + p.langd_x
    else:
        langd_x = p.langd_x
    
    if p.bredd_y == 0:
        bredd_y = fasad_b - start_y
    elif p.bredd_y < 0:
        bredd_y = fasad_b - start_y + p.bredd_y
    else:
        bredd_y = p.bredd_y
    
    H = p.tjocklek
    pos_z = p.niva_z - H
    
    return langd_x, bredd_y, H, start_x, start_y, pos_z

def bt_update_single_bjalklag(bjalklag_obj, context):
    """Uppdaterar ett enskilt bjälklags geometri baserat på dess egna parametrar"""
    scene = context.scene
    h = scene.bt_huvudmått
    
    # Hämta parametrar från objektet
    start_x = bjalklag_obj.get("start_x", 0.0)
    start_y = bjalklag_obj.get("start_y", 0.0)
    langd_x = bjalklag_obj.get("langd_x", 0.0)
    bredd_y = bjalklag_obj.get("bredd_y", 0.0)
    H = bjalklag_obj.get("tjocklek", 0.30)
    niva_z = bjalklag_obj.get("niva_z", 3.0)
    
    # Beräkna faktiska mått baserat på byggnadens mått
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    
    # Hantera positiva/negativa värden för längd
    if langd_x == 0:
        langd_x = fasad_l - start_x
    elif langd_x < 0:
        langd_x = fasad_l - start_x + langd_x
    
    # Hantera positiva/negativa värden för bredd
    if bredd_y == 0:
        bredd_y = fasad_b - start_y
    elif bredd_y < 0:
        bredd_y = fasad_b - start_y + bredd_y
    
    pos_z = niva_z - H
    
    if langd_x <= 0 or bredd_y <= 0 or H <= 0:
        return
    
    # Skapa koordinater
    coords = [
        (0, 0, 0), (langd_x, 0, 0), (langd_x, bredd_y, 0), (0, bredd_y, 0),
        (0, 0, H), (langd_x, 0, H), (langd_x, bredd_y, H), (0, bredd_y, H)
    ]
    
    mesh = bjalklag_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 8:
        bm.free()
        return
    
    for i, c in enumerate(coords):
        bm.verts[i].co = c
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # Uppdatera position
    bjalklag_obj.location = (start_x, start_y, pos_z)
    
    # ----- UPPDATERA BOOLEAN-MODIFIERARE -----
    guide_type = bjalklag_obj.get("guide_type", "INTERIOR")
    
    # Hitta guiden
    guide_obj = None
    if guide_type == 'INTERIOR':
        for obj in scene.objects:
            if obj.name == "Interior_Guide":
                guide_obj = obj
                break
    elif guide_type == 'EXTERIOR':
        for obj in scene.objects:
            if obj.name == "Exterior_Guide":
                guide_obj = obj
                break
    elif guide_type == 'WALL':
        for obj in scene.objects:
            if obj.name == "Wall_Guide":
                guide_obj = obj
                break
    
    # Ta bort befintlig Boolean-modifierare
    old_mod = None
    for mod in bjalklag_obj.modifiers:
        if mod.type == 'BOOLEAN' and mod.name.startswith("Guide_"):
            old_mod = mod
            break
    
    if old_mod:
        bjalklag_obj.modifiers.remove(old_mod)
    
    # Om ingen guide eller 'NONE', avbryt
    if guide_type == 'NONE' or not guide_obj:
        return
    
    # Lägg till ny Boolean-modifierare
    bm_mod = bjalklag_obj.modifiers.new(name=f"Guide_{guide_type}", type='BOOLEAN')
    bm_mod.operation = 'INTERSECT'
    bm_mod.object = guide_obj
    bm_mod.solver = 'EXACT'

def bt_update_bjalklag(self, context):
    """Uppdaterar markerade bjälklag när parametrar ändras i panelen"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    
    # Hitta markerade bjälklag
    bjalklag_list = [obj for obj in context.selected_objects if obj.name.startswith("bjalklag")]
    
    if not bjalklag_list:
        return
    
    p = scene.bt_bjalklag
    
    for bjalklag in bjalklag_list:
        # Uppdatera objektets parametrar från panelen
        bjalklag["start_x"] = p.start_x
        bjalklag["start_y"] = p.start_y
        bjalklag["langd_x"] = p.langd_x
        bjalklag["bredd_y"] = p.bredd_y
        bjalklag["niva_z"] = p.niva_z
        bjalklag["tjocklek"] = p.tjocklek
        bjalklag["guide_type"] = p.guide_type
        
        # Uppdatera geometri (inklusive Boolean)
        bt_update_single_bjalklag(bjalklag, context)

# ---------------------------------------------------------------------------
# 11. REALTIDSUPPDATERING - FÖNSTER
# ---------------------------------------------------------------------------
def bt_update_single_fonster(fonster_obj, values):
    W = values.get("bredd", 1.2)
    H = values.get("hojd", 1.4)
    kt = values.get("karmtjocklek", 0.05)
    kd = values.get("karmdjup", 0.10)
    indragning = values.get("indragning", 0.05)
    brostning = values.get("brostning", 0.9)
    
    w_halv, x_inner, z_inner, y_glas = W / 2.0, (W / 2.0) - kt, H - kt, kd / 2.0
    
    fonster_obj.location.z = brostning
    
    coords = [
        (-w_halv, indragning, 0), (w_halv, indragning, 0), (w_halv, indragning, H), (-w_halv, indragning, H),
        (-x_inner, indragning, kt), (x_inner, indragning, kt), (x_inner, indragning, z_inner), (-x_inner, indragning, z_inner),
        (-w_halv, indragning + kd, 0), (w_halv, indragning + kd, 0), (w_halv, indragning + kd, H), (-w_halv, indragning + kd, H),
        (-x_inner, indragning + kd, kt), (x_inner, indragning + kd, kt), (x_inner, indragning + kd, z_inner), (-x_inner, indragning + kd, z_inner),
        (-x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, kt), (x_inner, indragning + y_glas, z_inner), (-x_inner, indragning + y_glas, z_inner)
    ]
    
    mesh = fonster_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
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
    
    # Uppdatera cuttern om den finns
    cutter_obj = None
    for child in fonster_obj.children:
        if child.name.startswith("Hål_Fönster"):
            cutter_obj = child
            break
    
    if cutter_obj:
        parent_obj = fonster_obj.parent
        wall_bredd = 0.15
        if parent_obj and parent_obj.get("typ") == "vägg":
            wall_bredd = parent_obj.get("vagg_bredd", 0.15)
        cutter_depth = wall_bredd + 0.2
        
        cc = [
            (-w_halv, indragning - 0.1, 0), (w_halv, indragning - 0.1, 0), (w_halv, indragning - 0.1, H), (-w_halv, indragning - 0.1, H),
            (-w_halv, cutter_depth, 0), (w_halv, cutter_depth, 0), (w_halv, cutter_depth, H), (-w_halv, cutter_depth, H)
        ]
        
        m_cut = cutter_obj.data
        
        if m_cut.is_editmode:
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except:
                return
        
        bm_c = bmesh.new()
        bm_c.from_mesh(m_cut)
        bm_c.verts.ensure_lookup_table()
        
        for i, c in enumerate(cc):
            if i < len(bm_c.verts):
                bm_c.verts[i].co = c
        
        bm_c.verts.ensure_lookup_table()
        bm_c.to_mesh(m_cut)
        bm_c.free()
        m_cut.update()

def bt_update_fonster(self, context):
    global _updating
    if _updating:
        return
    
    scene = context.scene
    selected_fonster = [o for o in context.selected_objects if o.name.startswith("Fönster_")]
    
    if not selected_fonster:
        return
    
    p = scene.bt_fonster
    
    values = {
        "bredd": p.bredd,
        "hojd": p.hojd,
        "karmtjocklek": p.karmtjocklek,
        "karmdjup": p.karmdjup,
        "indragning": p.indragning,
        "brostning": p.brostning
    }
    
    for fonster in selected_fonster:
        fonster["fonster_bredd"] = p.bredd
        fonster["fonster_hojd"] = p.hojd
        fonster["karmtjocklek"] = p.karmtjocklek
        fonster["karmdjup"] = p.karmdjup
        fonster["indragning"] = p.indragning
        fonster["brostning"] = p.brostning
        
        bt_update_single_fonster(fonster, values)

# ---------------------------------------------------------------------------
# 12. REALTIDSUPPDATERING - DÖRR
# ---------------------------------------------------------------------------
def bt_update_dorr(self, context):
    """Uppdaterar markerade dörrar när dörrparametrar ändras"""
    global _updating
    if _updating:
        return
    
    scene = context.scene
    selected_dorrar = [o for o in context.selected_objects if o.get("typ") == "dorr"]
    
    if not selected_dorrar:
        return
    
    p = scene.bt_dorr
    
    values = {
        "bredd": p.bredd,
        "hojd": p.hojd,
        "karmtjocklek": p.karmtjocklek,
        "karmdjup": p.karmdjup,
        "indragning": p.indragning,
        "tröskelhöjd": p.tröskelhöjd
    }
    
    for dorr in selected_dorrar:
        dorr["dorr_bredd"] = p.bredd
        dorr["dorr_hojd"] = p.hojd
        dorr["karmtjocklek"] = p.karmtjocklek
        dorr["karmdjup"] = p.karmdjup
        dorr["indragning"] = p.indragning
        dorr["tröskelhöjd"] = p.tröskelhöjd
        dorr["hangning"] = p.hangning
        
        bt_update_single_dorr(dorr, values)


def bt_update_single_dorr(dorr_obj, values):
    """Uppdaterar en enskild dörrs geometri"""
    
    W = values.get("bredd", 0.9)
    H = values.get("hojd", 2.1)
    kt = values.get("karmtjocklek", 0.05)
    kd = values.get("karmdjup", 0.10)
    indragning = values.get("indragning", 0.05)
    tröskel = values.get("tröskelhöjd", 0.05)
    
    w_halv = W / 2.0
    x_inner = w_halv - kt
    z_inner = H - kt
    mellanrum = 0.003
    blad_w = x_inner - mellanrum
    blad_h = z_inner - tröskel - mellanrum
    
    # Uppdatera dörrbladets geometri
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
    
    mesh = dorr_obj.data
    
    if mesh.is_editmode:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except:
            return
    
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.verts.ensure_lookup_table()
    
    if len(bm.verts) != 8:
        bm.free()
        return
    
    for i, c in enumerate(blad_coords):
        if i < len(bm.verts):
            bm.verts[i].co = c
    
    bm.verts.ensure_lookup_table()
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # Uppdatera custom properties
    dorr_obj["dorr_bredd"] = W
    dorr_obj["dorr_hojd"] = H
    dorr_obj["karmtjocklek"] = kt
    dorr_obj["karmdjup"] = kd
    dorr_obj["indragning"] = indragning
    dorr_obj["tröskelhöjd"] = tröskel
    
    # Uppdatera karm
    for child in dorr_obj.children:
        if child.name.startswith("Karm_"):
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
            
            mesh_karm = child.data
            
            if mesh_karm.is_editmode:
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    continue
            
            bm_k = bmesh.new()
            bm_k.from_mesh(mesh_karm)
            bm_k.verts.ensure_lookup_table()
            
            for i, c in enumerate(karm_coords):
                if i < len(bm_k.verts):
                    bm_k.verts[i].co = c
            
            bm_k.verts.ensure_lookup_table()
            bm_k.to_mesh(mesh_karm)
            bm_k.free()
            mesh_karm.update()
        
        # Uppdatera handtag
        elif child.name.startswith("Handtag_Fram") or child.name.startswith("Handtag_Bak"):
            hangning = dorr_obj.get("hangning", "RIGHT")
            if hangning == 'RIGHT':
                handtag_x = -blad_w + 0.03
            else:
                handtag_x = blad_w - 0.03
            child.location = (handtag_x, 0, 0)
        
        # Uppdatera cutter
        elif child.name.startswith("Hål_Dörr"):
            cutter_start = indragning - 0.1
            parent_obj = dorr_obj.parent
            wall_bredd = 0.15
            if parent_obj and parent_obj.get("typ") == "vägg":
                wall_bredd = parent_obj.get("vagg_bredd", 0.15)
            cutter_depth = wall_bredd + 0.2
            
            cc = [
                (-w_halv, cutter_start, -0.0001), (w_halv, cutter_start, -0.0001), 
                (w_halv, cutter_start, H), (-w_halv, cutter_start, H),
                (-w_halv, cutter_start + cutter_depth, -0.0001), 
                (w_halv, cutter_start + cutter_depth, -0.0001),
                (w_halv, cutter_start + cutter_depth, H), 
                (-w_halv, cutter_start + cutter_depth, H)
            ]
            
            mesh_cut = child.data
            
            if mesh_cut.is_editmode:
                try:
                    bpy.ops.object.mode_set(mode='OBJECT')
                except:
                    continue
            
            bm_c = bmesh.new()
            bm_c.from_mesh(mesh_cut)
            bm_c.verts.ensure_lookup_table()
            
            for i, c in enumerate(cc):
                if i < len(bm_c.verts):
                    bm_c.verts[i].co = c
            
            bm_c.verts.ensure_lookup_table()
            bm_c.to_mesh(mesh_cut)
            bm_c.free()
            mesh_cut.update()

# ---------------------------------------------------------------------------
# 13. BAKGRUNDSSYNKRONISERING
# ---------------------------------------------------------------------------
def bt_master_synk_handler(scene, depsgraph=None):
    """Hanterar automatisk uppdatering vid scenändringar"""
    global _updating
    if _updating:
        return
    
    _updating = True
    
    try:
        pass
    finally:
        _updating = False

# ---------------------------------------------------------------------------
# 14. SELECTION-HANDLER
# ---------------------------------------------------------------------------
def bt_selection_handler(scene, depsgraph=None):
    """Hanterar selection-ändringar"""
    from .properties.fonster import sync_fonster_panel_from_selection
    from .properties.dorr import sync_dorr_panel_from_selection
    from .properties.bjalklag import sync_bjalklag_panel_from_selection
    from .properties.vagg_settings import sync_vagg_panel_from_selection
    
    context = bpy.context
    if context:
        sync_fonster_panel_from_selection(context)
        sync_dorr_panel_from_selection(context)
        sync_bjalklag_panel_from_selection(context)
        sync_vagg_panel_from_selection(context)
    
    bt_update_spegelvänd_from_selection(scene)

# ---------------------------------------------------------------------------
# 15. HJÄLPFUNKTION - SKAPA VÄGG (global position, utan Empty)
# ---------------------------------------------------------------------------
def skapa_vagg_global(namn, langd, bredd, hojd, position, rotation, spegelvänd, context, collection=None, nockhojd=0):
    """Skapar en vägg på en specifik global position (utan Empty-parent)"""
    
    # Om nockhojd > 0, använd total_hojd = hojd + nockhojd
    if nockhojd > 0:
        total_hojd = hojd + nockhojd
        coords = [
            (0, 0, 0), (langd, 0, 0), (langd, bredd, 0), (0, bredd, 0),
            (0, 0, total_hojd), (langd, 0, total_hojd), (langd, bredd, total_hojd), (0, bredd, total_hojd)
        ]
    else:
        coords = [
            (0, 0, 0), (langd, 0, 0), (langd, bredd, 0), (0, bredd, 0),
            (0, 0, hojd), (langd, 0, hojd), (langd, bredd, hojd), (0, bredd, hojd)
        ]
    
    faces = [
        (0, 3, 2, 1), (4, 5, 6, 7),  # botten, topp
        (0, 1, 5, 4), (1, 2, 6, 5),  # fram (Y=0, utsida), höger
        (2, 3, 7, 6), (3, 0, 4, 7)   # bak (Y=bredd, insida), vänster
    ]
    
    # Skapa mesh och objekt
    mesh = bpy.data.meshes.new(f"{namn}_mesh")
    obj = bpy.data.objects.new(namn, mesh)
    
    if collection:
        collection.objects.link(obj)
    else:
        context.collection.objects.link(obj)
    
    bm = bmesh.new()
    for c in coords:
        bm.verts.new(c)
    bm.verts.ensure_lookup_table()
    for v0 in faces:
        try:
            bm.faces.new([bm.verts[i] for i in v0])
        except:
            pass
    
    # Material
    mat_red = get_material_tegel()
    mat_white = get_material_vit()
    
    obj.data.materials.append(mat_red)    # index 0
    obj.data.materials.append(mat_white)  # index 1
    
    # Insida är ALLTID face 4 (bak, Y=bredd)
    for i, face in enumerate(bm.faces):
        if i == 4:
            face.material_index = 1  # vitt (insida)
        else:
            face.material_index = 0  # rött (utsida)
    
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    
    # Sätt position och rotation
    obj.location = position
    obj.rotation_euler = (0, 0, math.radians(rotation))
    
    # Sätt skala baserat på spegelvänd
    if spegelvänd:
        obj.scale = (-1, 1, 1)
    else:
        obj.scale = (1, 1, 1)
    
    # Spara custom properties
    obj["typ"] = "vägg"
    obj["vagg_namn"] = namn
    obj["vagg_langd"] = langd
    obj["vagg_bredd"] = 0.0  # 0 = använd teoretisk
    obj["vagg_hojd"] = hojd
    obj["vagg_nockhojd"] = nockhojd
    obj["vagg_rotation"] = rotation
    obj["spegelvänd"] = spegelvänd
    
    return obj

# ---------------------------------------------------------------------------
# 16. HJÄLPFUNKTIONER FÖR SPEGELVÄND OCH LÅSNING
# ---------------------------------------------------------------------------
def bt_update_spegelvänd_from_selection(scene):
    """Uppdaterar spegelvänd-propertyn baserat på markerad vägg"""
    global _updating
    
    selected = bpy.context.selected_objects
    vagg = None
    for obj in selected:
        if obj.get("typ") == "vägg":
            vagg = obj
            break
    
    if vagg:
        current_status = vagg.get("spegelvänd", False)
        if scene.bt_vagg.spegelvänd != current_status:
            if not _updating:
                _updating = True
                scene.bt_vagg.spegelvänd = current_status
                _updating = False

def _calculate_total_wall_height(scene):
    """Beräknar den totala vägghöjden (max av vägghöjd och nockhöjd)"""
    h = scene.bt_huvudmått
    
    # Använd den centrala takberäkningen
    geo = calculate_tak_geometry(scene)
    
    # Hämta nockhöjd från geo
    nock_utsida = geo.get('nock_utsida', h.vagg_hojd)
    z1 = geo.get('z1', h.vagg_hojd)
    z2 = geo.get('z2', h.vagg_hojd)
    
    max_tak_hojd = max(nock_utsida, z1, z2)
    return max(h.vagg_hojd, max_tak_hojd) + 0.010

# ---------------------------------------------------------------------------
# 17. MSGBUS - För effektiv uppdatering av guider
# ---------------------------------------------------------------------------

def bt_setup_msgbus():
    """Sätter upp msgbus-lyssnare för takparametrar"""
    global _msgbus_owner
    
    try:
        bpy.msgbus.clear_by_owner(_msgbus_owner)
    except:
        pass
    
    def on_tak_changed(*args):
        try:
            bt_update_wall_guide(None, bpy.context)
            bt_update_all_guides(None, bpy.context)
        except Exception as e:
            print(f"Error updating guides: {e}")
    
    def on_huvudmatt_changed(*args):
        try:
            bt_update_tak(None, bpy.context)
        except Exception as e:
            print(f"Error updating roof: {e}")
    
    try:
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Scene, "bt_tak"),
            owner=_msgbus_owner,
            args=(),
            notify=on_tak_changed,
            options={'PERSISTENT'}
        )
        
        bpy.msgbus.subscribe_rna(
            key=(bpy.types.Scene, "bt_huvudmått"),
            owner=_msgbus_owner,
            args=(),
            notify=on_huvudmatt_changed,
            options={'PERSISTENT'}
        )
        
        print("msgbus subscription active for roof parameters")
        
    except Exception as e:
        print(f"Could not set up msgbus: {e}")

def bt_clear_msgbus():
    """Rensa msgbus-prenumerationer"""
    global _msgbus_owner
    try:
        bpy.msgbus.clear_by_owner(_msgbus_owner)
        print("msgbus subscription cleared")
    except:
        pass

# ---------------------------------------------------------------------------
# 18. SKAPA DÖRRHANDTAG
# ---------------------------------------------------------------------------
def skapa_dorrhandtag(context, hangning="RIGHT", position=(0, 0, 0), parent=None):
    """Skapar ett dörrhandtag med två brickor (övre och nedre) och ett handtag."""
    
    pos = Vector(position)
    dorr_tjocklek = 0.080
    halv_dorr = dorr_tjocklek / 2.0
    bricka_tjocklek = 0.005
    halv_bricka = bricka_tjocklek / 2.0
    handtag_offset = halv_dorr + halv_bricka
    
    if hangning == "RIGHT":
        handtag_sida = 0.070
    else:
        handtag_sida = -0.070
    
    p00 = pos + Vector((0.000, 0.000, 0.890))
    p01 = pos + Vector((0.000, 0.000, 0.990))
    handtag_ut = 0.070
    
    collection = bpy.data.collections.get("Dörrhandtag")
    if not collection:
        collection = bpy.data.collections.new("Dörrhandtag")
        context.scene.collection.children.link(collection)
    
    mat = get_material_handtag()
    
    # Fram - handtag
    curve_data = bpy.data.curves.new("Handtag_Curve_Fram", 'CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = 0.010
    curve_data.bevel_resolution = 8
    curve_data.resolution_u = 12
    curve_data.use_fill_caps = True
    
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    
    spline.bezier_points[0].co = (0, handtag_offset, 0)
    spline.bezier_points[0].handle_left_type = 'AUTO'
    spline.bezier_points[0].handle_right_type = 'AUTO'
    spline.bezier_points[1].co = (0, handtag_offset + handtag_ut, 0)
    spline.bezier_points[1].handle_left_type = 'AUTO'
    spline.bezier_points[1].handle_right_type = 'AUTO'
    spline.bezier_points[2].co = (handtag_sida, handtag_offset + handtag_ut, 0)
    spline.bezier_points[2].handle_left_type = 'AUTO'
    spline.bezier_points[2].handle_right_type = 'AUTO'
    
    handtag_fram_obj = bpy.data.objects.new("Dörrhandtag_Fram", curve_data)
    collection.objects.link(handtag_fram_obj)
    handtag_fram_obj.location = p00
    handtag_fram_obj.data.materials.append(mat)
    
    # Bak - handtag
    curve_data_bak = bpy.data.curves.new("Handtag_Curve_Bak", 'CURVE')
    curve_data_bak.dimensions = '3D'
    curve_data_bak.bevel_depth = 0.010
    curve_data_bak.bevel_resolution = 8
    curve_data_bak.resolution_u = 12
    curve_data_bak.use_fill_caps = True
    
    spline_bak = curve_data_bak.splines.new('BEZIER')
    spline_bak.bezier_points.add(2)
    
    spline_bak.bezier_points[0].co = (0, -handtag_offset, 0)
    spline_bak.bezier_points[0].handle_left_type = 'AUTO'
    spline_bak.bezier_points[0].handle_right_type = 'AUTO'
    spline_bak.bezier_points[1].co = (0, -(handtag_offset + handtag_ut), 0)
    spline_bak.bezier_points[1].handle_left_type = 'AUTO'
    spline_bak.bezier_points[1].handle_right_type = 'AUTO'
    spline_bak.bezier_points[2].co = (handtag_sida, -(handtag_offset + handtag_ut), 0)
    spline_bak.bezier_points[2].handle_left_type = 'AUTO'
    spline_bak.bezier_points[2].handle_right_type = 'AUTO'
    
    handtag_bak_obj = bpy.data.objects.new("Dörrhandtag_Bak", curve_data_bak)
    collection.objects.link(handtag_bak_obj)
    handtag_bak_obj.location = p00
    handtag_bak_obj.data.materials.append(mat)
    
    # Brickor
    bpy.ops.mesh.primitive_cylinder_add(radius=0.020, depth=bricka_tjocklek, location=p00 + Vector((0, halv_dorr, 0)))
    bricka_nedre_fram = context.active_object
    bricka_nedre_fram.name = "Rosett_Nedre_Fram"
    collection.objects.link(bricka_nedre_fram)
    bricka_nedre_fram.rotation_euler = (math.radians(90), 0, 0)
    bricka_nedre_fram.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.020, depth=bricka_tjocklek, location=p01 + Vector((0, halv_dorr, 0)))
    bricka_ovre_fram = context.active_object
    bricka_ovre_fram.name = "Rosett_Ovre_Fram"
    collection.objects.link(bricka_ovre_fram)
    bricka_ovre_fram.rotation_euler = (math.radians(90), 0, 0)
    bricka_ovre_fram.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.020, depth=bricka_tjocklek, location=p00 + Vector((0, -halv_dorr, 0)))
    bricka_nedre_bak = context.active_object
    bricka_nedre_bak.name = "Rosett_Nedre_Bak"
    collection.objects.link(bricka_nedre_bak)
    bricka_nedre_bak.rotation_euler = (math.radians(90), 0, 0)
    bricka_nedre_bak.data.materials.append(mat)
    
    bpy.ops.mesh.primitive_cylinder_add(radius=0.020, depth=bricka_tjocklek, location=p01 + Vector((0, -halv_dorr, 0)))
    bricka_ovre_bak = context.active_object
    bricka_ovre_bak.name = "Rosett_Ovre_Bak"
    collection.objects.link(bricka_ovre_bak)
    bricka_ovre_bak.rotation_euler = (math.radians(90), 0, 0)
    bricka_ovre_bak.data.materials.append(mat)
    
    if parent:
        handtag_fram_obj.parent = parent
        handtag_bak_obj.parent = parent
        bricka_nedre_fram.parent = parent
        bricka_ovre_fram.parent = parent
        bricka_nedre_bak.parent = parent
        bricka_ovre_bak.parent = parent
    
    return handtag_fram_obj

# ---------------------------------------------------------------------------
# 19. MATERIAL-FUNKTIONER
# ---------------------------------------------------------------------------
def get_material_tegel():
    mat = bpy.data.materials.get("Vägg_Utsida_Tegel")
    if not mat:
        mat = bpy.data.materials.new(name="Vägg_Utsida_Tegel")
        mat.use_fake_user = True
        mat.diffuse_color = (0.5, 0.3, 0.2, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.5, 0.3, 0.2, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.7
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_vit():
    mat = bpy.data.materials.get("Vägg_Insida_Vit")
    if not mat:
        mat = bpy.data.materials.new(name="Vägg_Insida_Vit")
        mat.use_fake_user = True
        mat.diffuse_color = (0.95, 0.95, 0.95, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_betong():
    mat = bpy.data.materials.get("Betong_Grå")
    if not mat:
        mat = bpy.data.materials.new(name="Betong_Grå")
        mat.use_fake_user = True
        mat.diffuse_color = (0.7, 0.7, 0.7, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_bjalklag():
    mat = bpy.data.materials.get("Bjälklag_Betong")
    if not mat:
        mat = bpy.data.materials.new(name="Bjälklag_Betong")
        mat.use_fake_user = True
        mat.diffuse_color = (0.6, 0.6, 0.6, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.6, 0.6, 0.6, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.9
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_tak():
    mat = bpy.data.materials.get("Tak_Mörkgrå")
    if not mat:
        mat = bpy.data.materials.new(name="Tak_Mörkgrå")
        mat.use_fake_user = True
        mat.diffuse_color = (0.3, 0.3, 0.3, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        rgb_node = nodes.new('ShaderNodeRGB')
        rgb_node.outputs[0].default_value = (0.3, 0.3, 0.3, 1.0)
        rgb_node.location = (-200, 0)
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Roughness'].default_value = 0.7
        bsdf.location = (0, 0)
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(rgb_node.outputs['Color'], bsdf.inputs['Base Color'])
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_innertak():
    mat = bpy.data.materials.get("Innertak_Vit")
    if not mat:
        mat = bpy.data.materials.new(name="Innertak_Vit")
        mat.use_fake_user = True
        mat.diffuse_color = (0.95, 0.95, 0.95, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.8
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_fonsterkarm():
    mat = bpy.data.materials.get("Fönsterkarm_Vit")
    if not mat:
        mat = bpy.data.materials.new(name="Fönsterkarm_Vit")
        mat.use_fake_user = True
        mat.diffuse_color = (0.95, 0.95, 0.95, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.95, 0.95, 0.95, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.4
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_glas():
    mat = bpy.data.materials.get("Fönsterglas_Blå")
    if not mat:
        mat = bpy.data.materials.new(name="Fönsterglas_Blå")
        mat.use_fake_user = True
        mat.diffuse_color = (0.6, 0.8, 1.0, 0.6)
        mat.blend_method = 'BLEND'
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.6, 0.8, 1.0, 1.0)
        bsdf.inputs['Alpha'].default_value = 0.5
        bsdf.inputs['Roughness'].default_value = 0.1
        bsdf.inputs['IOR'].default_value = 1.45
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_dorrkarm():
    mat = bpy.data.materials.get("Dörrkarm_Vit")
    if not mat:
        mat = bpy.data.materials.new(name="Dörrkarm_Vit")
        mat.use_fake_user = True
        mat.diffuse_color = (0.9, 0.9, 0.9, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.3
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_dorrblad():
    mat = bpy.data.materials.get("Dörr_Grå")
    if not mat:
        mat = bpy.data.materials.new(name="Dörr_Grå")
        mat.use_fake_user = True
        mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.6
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

def get_material_handtag():
    mat = bpy.data.materials.get("Handtag_Mässing")
    if not mat:
        mat = bpy.data.materials.new(name="Handtag_Mässing")
        mat.use_fake_user = True
        mat.diffuse_color = (0.8, 0.6, 0.2, 1.0)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        nodes.clear()
        bsdf = nodes.new('ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = (0.8, 0.6, 0.2, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.3
        bsdf.inputs['Metallic'].default_value = 0.8
        output = nodes.new('ShaderNodeOutputMaterial')
        output.location = (200, 0)
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return mat

# ---------------------------------------------------------------------------
# 20. SÄTT UPDATE-FUNKTIONER
# ---------------------------------------------------------------------------
def set_update_functions():
    """Sätter update-funktioner för properties som behöver dem"""
    pass