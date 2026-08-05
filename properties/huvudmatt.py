# ________________________________________________________________________________________________
# HUVUDMÅTT - Centrala mått för hela huset
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
from bpy.props import FloatProperty, BoolProperty, EnumProperty
from math import radians, tan, cos

from .. import utils


# ---------------------------------------------------------------------------
# UPDATE-FUNKTION
# ---------------------------------------------------------------------------

def bt_update_huvudmått(self, context):
    """Uppdaterar hela huset när huvudmått ändras"""
    import math
    import bmesh
    from math import radians, tan, cos
    
    scene = context.scene
    
    # Hämta aktuella mått
    h = scene.bt_huvudmått
    fasad_l = h.fasad_l
    fasad_b = h.fasad_b
    vagg_hojd = h.vagg_hojd
    teoretisk_bredd = h.teoretisk_vagg_bredd
    taktjocklek = h.taktjocklek
    
    # Hämta taktyp
    roof_type = h.roof_type
    single_slope_roof = (roof_type != 'GABLE')
    
    # Hämta takets inställningar
    t = scene.bt_tak
    brytavstand = t.brytavstand
    
    # ----- BERÄKNA VERKLIG NOCKHÖJD -----
    
    # Invändig höjd fram
    e = vagg_hojd
    
    # Invändig höjd bak
    if h.använd_symmetrisk_vagg_hojd:
        k = h.vagg_hojd_bak
    else:
        k = vagg_hojd
    
    # ----- TAKLUTNINGAR -----
    # Nedre taklutning fram - ALLTID från 01
    v0 = radians(h.taklutning)
    
    # Nedre taklutning bak - från 02 (eller samma som fram)
    if h.använd_symmetrisk_taklutning:
        v2 = radians(h.taklutning_bak)
    else:
        v2 = v0
    
    # Övre taklutning fram (mansard)
    if h.använd_mansard_fram:
        v1 = radians(h.taklutning_mansard)
    else:
        v1 = v0
    
    # Övre taklutning bak
    if h.använd_symmetrisk_taklutning:
        # Osymmetrisk byggnad
        if h.använd_mansard_bak:
            v3 = radians(h.taklutning_mansard_bak)
        else:
            v3 = v2
    else:
        # Symmetrisk byggnad
        if h.använd_mansard_fram:
            v3 = v1
        else:
            v3 = v0
    
    # Sätt variabler för beräkningar
    f = v0
    l = v2
    u = v1
    v = v3
    
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
    if h.använd_brytavstand_fram:
        brytavstand_hitsida = h.brytavstand_mansard
    else:
        brytavstand_hitsida = brytavstand
    
    if h.använd_brytavstand_bak:
        p = h.brytavstand_mansard_bak
    else:
        p = brytavstand_hitsida
    
    # ----- BERÄKNA INNERTAK -----
    innertak_z_fram = e - teoretisk_bredd * tan(f)
    innertak_z_bak = k - teoretisk_bredd * tan(l)
    
    # Beräkna brytpunkter
    z1 = innertak_z_fram + brytavstand_hitsida * tan(f)
    z2 = innertak_z_bak + p * tan(l)
    
    # Avstånd mellan brytpunkterna i Y-led (från utsida fasad)
    y_avstand = fasad_b - brytavstand_hitsida - p
    
    if tan(u) + tan(v) != 0:
        y1 = (y_avstand * tan(v) - z1 + z2) / (tan(u) + tan(v))
    else:
        y1 = y_avstand / 2

    # ----- PULPETTAK - justera nockposition -----
    if single_slope_roof:
        if roof_type == 'SHED_FRONT':
            # Pulpettak som lutar ner mot framsidan
            y1 = fasad_b - brytavstand_hitsida
        elif roof_type == 'SHED_BACK':
            # Pulpettak som lutar ner mot baksidan
            y1 = brytavstand_hitsida
    
    # Verklig nockhöjd (invändig)
    nock_z = z1 + y1 * tan(u)
    
    # Beräkna nockens utsida (med taktjocklek)
    if abs(u - v) < 0.001:
        nock_utsida = nock_z + taktjocklek / cos(u)
    else:
        nock_utsida = nock_z + taktjocklek / cos((u + v) / 2) * cos((u - v) / 2)
    
    # ----- BERÄKNA VÄGGHÖJD -----
    # Väggarna ska alltid vara minst vagg_hojd höga
    max_tak_hojd = max(nock_utsida, z1, z2)
    total_hojd = max(vagg_hojd, max_tak_hojd) + 0.010
    
    # ----- UPPDATERA VÄGGARNA -----
    # Använd den centrala funktionen som respekterar användarens höjd
    vagg_list = [o for o in scene.objects if o.get("typ") == "vägg"]
    
    for vagg in vagg_list:
        utils.bt_update_single_vagg_from_props(vagg, context)
    
    # ----- UPPDATERA BJÄLKLAGET -----
    # Hitta ALLA bjälklag (inte bara markerade)
    bjalklag_list = [obj for obj in scene.objects if obj.name.startswith("bjalklag")]
    
    if bjalklag_list:
        for bjalklag in bjalklag_list:
            utils.bt_update_single_bjalklag(bjalklag, context)
    
    # ----- UPPDATERA PLATTAN -----
    platta = next((o for o in scene.objects if o.name.startswith("Betongplatta")), None)
    if platta:
        indrag = scene.bt_platta.indrag
        platt_l = fasad_l - indrag * 2
        platt_b = fasad_b - indrag * 2
        
        p = scene.bt_platta
        t = p.tjocklek
        H = p.total_hojd
        fb = p.forstyvning_bredd
        
        if H - t < 0:
            return
        
        fi = (H - t) / math.tan(math.radians(p.lutning)) if p.lutning > 0 else 0
        x_min, y_min = 0, 0
        x_max, y_max = platt_l, platt_b
        x3, y3 = x_min + fb, y_min + fb
        x3b, y3b = x_max - fb, y_max - fb
        
        coords = [
            (x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0),
            (x_min, y_min, -H), (x_max, y_min, -H), (x_max, y_max, -H), (x_min, y_max, -H),
            (x3, y3, -H), (x3b, y3, -H), (x3b, y3b, -H), (x3, y3b, -H),
            (x3 + fi, y3 + fi, -t), (x3b - fi, y3 + fi, -t), (x3b - fi, y3b - fi, -t), (x3 + fi, y3b - fi, -t)
        ]
        
        mesh = platta.data
        
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
        
        platta.location = (indrag, indrag, 0)

    # ----- UPPDATERA TAKET -----
    utils.bt_update_tak(self, context)    
    tak_obj = None
    for obj in scene.objects:
        if obj.name.startswith("Tak_"):
            tak_obj = obj
            break

    if tak_obj:
        utils.bt_update_tak(self, context)
    
    # Uppdatera mallarna
    utils.bt_update_wall_guide(self, context)
    utils.bt_update_all_guides(self, context)


# ---------------------------------------------------------------------------
# PROPERTYGROUP
# ---------------------------------------------------------------------------

class BT_HuvudmåttProperties(bpy.types.PropertyGroup):
    """Centrala mått som styr alla delar av huset"""
    
    # ----- 00. HUVUDMÅTT -----
    fasad_l: FloatProperty(
        name="Length",
        description="Building length from gable to gable",
        default=18.0,
        soft_min=3.0,
        soft_max=120.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    fasad_b: FloatProperty(
        name="Width",
        description="Building width from front to back",
        default=12.0,
        soft_min=3.0,
        soft_max=120.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    taktjocklek: FloatProperty(
        name="Roof Thickness",
        description="Distance from roof exterior to load-bearing structure",
        default=0.20,
        soft_min=0.10,
        soft_max=0.60,
        step=1,
        update=bt_update_huvudmått
    )
    
    teoretisk_vagg_bredd: FloatProperty(
        name="Wall Thickness",
        description="Distance from facade exterior to load-bearing structure",
        default=0.15,
        soft_min=0.10,
        soft_max=0.60,
        step=1,
        update=bt_update_huvudmått
    )

    # ----- TAKTYP -----
    roof_type: EnumProperty(
        name="Roof Type",
        description="Type of roof",
        items=[
            ('GABLE', "Gable Roof", "Double slope roof with ridge at the top"),
            ('SHED_FRONT', "Shed Roof (Front)", "Single slope roof sloping down to the front"),
            ('SHED_BACK', "Shed Roof (Back)", "Single slope roof sloping down to the back")
        ],
        default='GABLE',
        update=bt_update_huvudmått
    )
    
    # ----- 01. SYMMETRISK BYGGNAD -----
    vagg_hojd: FloatProperty(
        name="Height",
        description="Interior height where roof and wall meet",
        default=4.0,
        soft_min=2.5,
        soft_max=25.0,
        step=10,
        update=bt_update_huvudmått
    )
    
    taklutning: FloatProperty(
        name="Roof Angle",  # <-- ÄNDRAD
        description="Angle of the lower roof (at eaves) in degrees",
        default=30.0,
        soft_min=-80.0,
        soft_max=80.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    takutsprång: FloatProperty(
        name="Roof Overhang",
        description="Horizontal distance from wall to underside of roof overhang",
        default=0.3,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        update=bt_update_huvudmått
    )
    
    gavelutsprång: FloatProperty(
        name="Gable Overhang",
        description="Distance from gable wall to outside of gable overhang",
        default=0.3,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        update=bt_update_huvudmått
    )
    
    använd_mansard_fram: BoolProperty(
        name="Use Mansard Front",
        description="Use mansard roof on front side",
        default=False,
        update=bt_update_huvudmått
    )
    
    taklutning_mansard: FloatProperty(
        name="Upper Roof Angle",  # <-- ÄNDRAD
        description="Angle of the mansard roof upper part, front side",
        default=15.0,
        soft_min=-80.0,
        soft_max=80.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    använd_brytavstand_fram: BoolProperty(
        name="Use Break Front",
        description="Use break distance on front side",
        default=False,
        update=bt_update_huvudmått
    )
    
    brytavstand_mansard: FloatProperty(
        name="Break Distance Front",
        description="Distance from wall outside to break point interior, front side",
        default=1.5,
        soft_min=0.0,
        soft_max=10.0,
        step=10,
        update=bt_update_huvudmått
    )
    
    # ----- 02. OSYMMETRISK BYGGNAD -----
    använd_symmetrisk_vagg_hojd: BoolProperty(
        name="Use Asymmetric Height",
        description="Use asymmetric height on back side",
        default=False,
        update=bt_update_huvudmått
    )
    
    använd_symmetrisk_taklutning: BoolProperty(
        name="Use Asymmetric Roof Angle",
        description="Use asymmetric roof angle on back side",
        default=False,
        update=bt_update_huvudmått
    )
    
    använd_symmetrisk_takutsprång: BoolProperty(
        name="Use Asymmetric Overhang",
        description="Use asymmetric roof overhang on back side",
        default=False,
        update=bt_update_huvudmått
    )
    
    använd_symmetrisk_gavelutsprång: BoolProperty(
        name="Use Asymmetric Gable",
        description="Use asymmetric gable overhang on right side",
        default=False,
        update=bt_update_huvudmått
    )
    
    vagg_hojd_bak: FloatProperty(
        name="Height Back",
        description="Interior height where roof and wall meet on back side",
        default=4.0,
        soft_min=2.5,
        soft_max=25.0,
        step=10,
        update=bt_update_huvudmått
    )
    
    taklutning_bak: FloatProperty(
        name="Roof Angle Back",  # <-- ÄNDRAD
        description="Angle of the lower roof on back side in degrees",
        default=20.0,
        soft_min=-60.0,
        soft_max=60.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    takutsprång_bak: FloatProperty(
        name="Roof Overhang Back",
        description="Horizontal distance from wall to underside of roof overhang on back side",
        default=0.3,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        update=bt_update_huvudmått
    )
    
    gavelutsprång_hoger: FloatProperty(
        name="Gable Overhang Right",
        description="Distance from right gable wall to outside of gable overhang",
        default=0.3,
        soft_min=-1.0,
        soft_max=1.0,
        step=1,
        update=bt_update_huvudmått
    )
    
    använd_mansard_bak: BoolProperty(
        name="Use Mansard Back",
        description="Use mansard roof on back side",
        default=False,
        update=bt_update_huvudmått
    )
    
    taklutning_mansard_bak: FloatProperty(
        name="Upper Roof Angle Back",  # <-- ÄNDRAD
        description="Angle of the mansard roof upper part, back side",
        default=15.0,
        soft_min=-60.0,
        soft_max=60.0,
        step=100,
        update=bt_update_huvudmått
    )
    
    använd_brytavstand_bak: BoolProperty(
        name="Use Break Back",
        description="Use break distance on back side",
        default=False,
        update=bt_update_huvudmått
    )
    
    brytavstand_mansard_bak: FloatProperty(
        name="Break Distance Back",
        description="Distance from wall outside to break point interior, back side",
        default=1.5,
        soft_min=0.0,
        soft_max=10.0,
        step=10,
        update=bt_update_huvudmått
    )