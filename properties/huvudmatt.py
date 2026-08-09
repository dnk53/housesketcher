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
    
    # Hitta aktivt hus
    active_empty = utils.get_active_house_empty(context)
    if not active_empty:
        return
    
    # Hämta aktuella mått från scene (dessa är globala)
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
    # ... [all befintlig beräkningskod] ...
    
    # Uppdatera Empty med nya mått
    utils.update_house_data(active_empty, scene)
    
    # ----- UPPDATERA ENDAST OBJEKT SOM HÖR TILL DET AKTIVA HUSET -----
    
    # UPPDATERA YTTERVÄGGAR
    for vagg in scene.objects:
        if vagg.get("typ") == "vägg" and vagg.parent == active_empty:
            utils.bt_update_single_vagg_from_props(vagg, context)
    
    # UPPDATERA INNERVÄGGAR
    for innervagg in scene.objects:
        if innervagg.get("typ") == "innervagg" and innervagg.parent == active_empty:
            utils.bt_update_single_innervagg(innervagg, context)
    
    # UPPDATERA BJÄLKLAG
    for bjalklag in scene.objects:
        if bjalklag.name.startswith("bjalklag") and bjalklag.parent == active_empty:
            utils.bt_update_single_bjalklag(bjalklag, context)
    
    # UPPDATERA PLATTAN
    for platta in scene.objects:
        if platta.name.startswith("Betongplatta") and platta.parent == active_empty:
            # Beräkna plattans mått
            indrag = scene.bt_platta.indrag
            platt_l = fasad_l - indrag * 2
            platt_b = fasad_b - indrag * 2
            
            p_platta = scene.bt_platta
            t_platta = p_platta.tjocklek
            H_platta = p_platta.total_hojd
            fb = p_platta.forstyvning_bredd
            
            if H_platta - t_platta < 0:
                return
            
            fi = (H_platta - t_platta) / math.tan(math.radians(p_platta.lutning)) if p_platta.lutning > 0 else 0
            x_min, y_min = 0, 0
            x_max, y_max = platt_l, platt_b
            x3, y3 = x_min + fb, y_min + fb
            x3b, y3b = x_max - fb, y_max - fb
            
            coords = [
                (x_min, y_min, 0), (x_max, y_min, 0), (x_max, y_max, 0), (x_min, y_max, 0),
                (x_min, y_min, -H_platta), (x_max, y_min, -H_platta), (x_max, y_max, -H_platta), (x_min, y_max, -H_platta),
                (x3, y3, -H_platta), (x3b, y3, -H_platta), (x3b, y3b, -H_platta), (x3, y3b, -H_platta),
                (x3 + fi, y3 + fi, -t_platta), (x3b - fi, y3 + fi, -t_platta), (x3b - fi, y3b - fi, -t_platta), (x3 + fi, y3b - fi, -t_platta)
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
    
    # ----- UPPDATERA MALLARNA -----
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
        name="Roof Angle",
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
        name="Upper Roof Angle",
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
        name="Roof Angle Back",
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
        name="Upper Roof Angle Back",
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