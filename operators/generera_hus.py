# ________________________________________________________________________________________________
# OPERATOR - GENERERA HUS (PLATTA + 4 VÄGGAR + TAK + MALLAR)
# ________________________________________________________________________________________________

import bpy
import bmesh
import math
from math import radians, sin, tan, cos
from mathutils import Matrix, Euler, Vector

class MESH_OT_bt_skapa_hus(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_hus"
    bl_label = "Generera hus"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        
        # Hämta huvudmått
        h = context.scene.bt_huvudmått
        fasad_l = h.fasad_l
        fasad_b = h.fasad_b
        vagg_hojd = h.vagg_hojd
        teoretisk_bredd = h.teoretisk_vagg_bredd
        taktjocklek = h.taktjocklek
        # single_slope_roof = h.single_slope_roof
        # Hämta taktyp
        roof_type = h.roof_type
        single_slope_roof = (roof_type != 'GABLE')
        
        # Hämta takets inställningar
        t = context.scene.bt_tak
        brytavstand = t.brytavstand
        
        # ----- BERÄKNA VERKLIG NOCKHÖJD -----
        from math import radians, tan
        
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
        innertak_z_fram = e - teoretisk_bredd * tan(v0)
        innertak_z_bak = k - teoretisk_bredd * tan(v2)
        
        # Beräkna brytpunkter
        z1 = innertak_z_fram + brytavstand_hitsida * tan(v0)
        z2 = innertak_z_bak + p * tan(v2)
        
        # Avstånd mellan brytpunkterna i Y-led (från utsida fasad)
        y_avstand = fasad_b - brytavstand_hitsida - p
        
        if tan(v1) + tan(v3) != 0:
            y1 = (y_avstand * tan(v3) - z1 + z2) / (tan(v1) + tan(v3))
        else:
            y1 = y_avstand / 2
            
            
        if single_slope_roof and v0 >=0:
            y1 = fasad_b - brytavstand_hitsida
        
        
        # Verklig nockhöjd (invändig)
        nock_z = z1 + y1 * tan(v1)
        
        # Beräkna nockens utsida (med taktjocklek)
        if abs(v1 - v3) < 0.001:
            nock_utsida = nock_z + taktjocklek / cos(v1)
        else:
            nock_utsida = nock_z + taktjocklek / cos((v1 + v3) / 2) * cos((v1 - v3) / 2)
        
        # ----- BERÄKNA VÄGGHÖJD -----
        # Väggarna ska alltid vara minst vagg_hojd höga
        # Och minst lika höga som den högsta punkten på taket (nock eller brytpunkt)
        max_tak_hojd = max(nock_utsida, z1, z2)
        total_hojd = max(vagg_hojd, max_tak_hojd) + 0.010
        
        # ----- HÄMTA PLATTANS INSTÄLLNINGAR -----
        p_platta = context.scene.bt_platta
        indrag = p_platta.indrag
        platt_tjocklek = p_platta.tjocklek
        
        # Plattans mått = fasadmått minus indrag på båda sidor
        platt_l = fasad_l - indrag * 2
        platt_b = fasad_b - indrag * 2
        
        # Skapa collection för huset
        hus_collection = bpy.data.collections.get("Hus")
        if not hus_collection:
            hus_collection = bpy.data.collections.new("Hus")
            context.scene.collection.children.link(hus_collection)
        
        # Skapa collection för väggar
        vagg_collection = bpy.data.collections.get("Väggar")
        if not vagg_collection:
            vagg_collection = bpy.data.collections.new("Väggar")
            hus_collection.children.link(vagg_collection)

        # 0. SKAPA REFERENSPUNKT
        print("SKAPAR EMPTY NU")
        empty = bpy.data.objects.new("Referenspunkt", None)
        bpy.context.collection.objects.link(empty)
        empty.empty_display_type = 'PLAIN_AXES'
        empty.location = (0, 0, 0)
        
        # ----- SPARA ALLA HUSMÅTT PÅ EMPTY -----
        empty["fasad_l"] = fasad_l
        empty["fasad_b"] = fasad_b
        empty["vagg_hojd"] = vagg_hojd
        empty["taklutning"] = h.taklutning
        empty["roof_type"] = h.roof_type
        empty["taktjocklek"] = h.taktjocklek
        empty["teoretisk_bredd"] = h.teoretisk_vagg_bredd
        empty["gavelutsprång"] = h.gavelutsprång
        empty["takutsprång"] = h.takutsprång
        
        # Asymmetriska mått
        empty["använd_symmetrisk_vagg_hojd"] = h.använd_symmetrisk_vagg_hojd
        empty["vagg_hojd_bak"] = h.vagg_hojd_bak
        empty["använd_symmetrisk_taklutning"] = h.använd_symmetrisk_taklutning
        empty["taklutning_bak"] = h.taklutning_bak
        empty["använd_symmetrisk_takutsprång"] = h.använd_symmetrisk_takutsprång
        empty["takutsprång_bak"] = h.takutsprång_bak
        empty["använd_symmetrisk_gavelutsprång"] = h.använd_symmetrisk_gavelutsprång
        empty["gavelutsprång_hoger"] = h.gavelutsprång_hoger
        
        # Mansard-mått
        empty["använd_mansard_fram"] = h.använd_mansard_fram
        empty["taklutning_mansard"] = h.taklutning_mansard
        empty["använd_brytavstand_fram"] = h.använd_brytavstand_fram
        empty["brytavstand_mansard"] = h.brytavstand_mansard
        empty["använd_mansard_bak"] = h.använd_mansard_bak
        empty["taklutning_mansard_bak"] = h.taklutning_mansard_bak
        empty["använd_brytavstand_bak"] = h.använd_brytavstand_bak
        empty["brytavstand_mansard_bak"] = h.brytavstand_mansard_bak
        
        # 1. SKAPA PLATTA
        if hasattr(p_platta, 'fasad_l'):
            old_fasad_l = p_platta.fasad_l
            old_fasad_b = p_platta.fasad_b
            p_platta.fasad_l = platt_l
            p_platta.fasad_b = platt_b
        
        bpy.ops.mesh.bt_skapa_platta()
        
        if hasattr(p_platta, 'fasad_l') and old_fasad_l is not None:
            p_platta.fasad_l = old_fasad_l
            p_platta.fasad_b = old_fasad_b
        
        # Hitta den nyskapade plattan
        ny_platta = None
        for obj in context.scene.objects:
            if obj.select_get() and obj.name.startswith("Betongplatta"):
                ny_platta = obj
                break
        
        if ny_platta:
            hus_collection.objects.link(ny_platta)
            if ny_platta.name in context.scene.collection.objects:
                context.scene.collection.objects.unlink(ny_platta)
            ny_platta.location = (indrag, indrag, 0)
            ny_platta.parent = empty
        # 2. SKAPA DE 4 VÄGGARNA
        from .. import utils
        
        vagg_z = 0.0
        
        # Längd för fram- och bakvägg: fasad_l - teoretisk_bredd * 2
        langsida_langd = fasad_l - teoretisk_bredd * 2
        
        # ===== FRAMVÄGG =====
        fram_vagg = utils.skapa_vagg_global(
            namn="Vägg_Fram",
            langd=langsida_langd,
            bredd=teoretisk_bredd,
            hojd=total_hojd,
            position=(teoretisk_bredd, 0, vagg_z),
            rotation=0,
            spegelvänd=False,
            context=context,
            collection=vagg_collection,
            nockhojd=0
        )
        fram_vagg["vagg_typ"] = "fram"
        fram_vagg["vagg_position"] = "fram"
        fram_vagg["start_x"] = teoretisk_bredd
        fram_vagg["langd_x"] = -teoretisk_bredd
        fram_vagg["vagg_bredd"] = 0.0
        fram_vagg["vagg_hojd"] = 0.0
        fram_vagg["spegelvänd"] = False
        fram_vagg.parent = empty

        # ===== BAKVÄGG =====
        bak_vagg = utils.skapa_vagg_global(
            namn="Vägg_Bak",
            langd=langsida_langd,
            bredd=teoretisk_bredd,
            hojd=total_hojd,
            position=(fasad_l - teoretisk_bredd, fasad_b, vagg_z),
            rotation=180,
            spegelvänd=False,
            context=context,
            collection=vagg_collection,
            nockhojd=0
        )
        bak_vagg["vagg_typ"] = "bak"
        bak_vagg["vagg_position"] = "bak"
        bak_vagg["start_x"] = teoretisk_bredd
        bak_vagg["langd_x"] = -teoretisk_bredd
        bak_vagg["vagg_bredd"] = 0.0
        bak_vagg["vagg_hojd"] = 0.0
        bak_vagg["spegelvänd"] = False
        bak_vagg.parent = empty

        # ===== VÄNSTER GAVEL =====
        vanster_gavel = utils.skapa_vagg_global(
            namn="Vägg_Vänster_Gavel",
            langd=fasad_b,
            bredd=teoretisk_bredd,
            hojd=total_hojd,
            position=(0, fasad_b, vagg_z),
            rotation=-90,
            spegelvänd=False,
            context=context,
            collection=vagg_collection,
            nockhojd=0
        )
        vanster_gavel["vagg_typ"] = "gavel"
        vanster_gavel["vagg_position"] = "vanster"
        vanster_gavel["start_y"] = 0.0
        vanster_gavel["langd_y"] = 0.0
        vanster_gavel["vagg_bredd"] = 0.0
        vanster_gavel["vagg_hojd"] = 0.0
        vanster_gavel["spegelvänd"] = False
        vanster_gavel.parent = empty

        # ===== HÖGER GAVEL =====
        hoger_gavel = utils.skapa_vagg_global(
            namn="Vägg_Höger_Gavel",
            langd=fasad_b,
            bredd=teoretisk_bredd,
            hojd=total_hojd,
            position=(fasad_l, 0, vagg_z),
            rotation=90,
            spegelvänd=False,
            context=context,
            collection=vagg_collection,
            nockhojd=0
        )
        hoger_gavel["vagg_typ"] = "gavel"
        hoger_gavel["vagg_position"] = "hoger"
        hoger_gavel["start_y"] = 0.0
        hoger_gavel["langd_y"] = 0.0
        hoger_gavel["vagg_bredd"] = 0.0
        hoger_gavel["vagg_hojd"] = 0.0
        hoger_gavel["spegelvänd"] = False
        hoger_gavel.parent = empty


        
        # 3. SKAPA TAK
        bpy.ops.mesh.bt_skapa_tak()
        
        # Hitta taket (takdelarna)
        tak_obj = None
        for obj in context.scene.objects:
            if obj.name.startswith("Tak_"):
                tak_obj = obj
                break
        
        # ----- SÄTT RÄTT EMPTY PÅ TAKET -----
        if tak_obj:
            tak_obj.parent = empty
            tak_obj.location = (0, 0, 0)
            tak_obj.matrix_parent_inverse = empty.matrix_world.inverted()
        
        # 4. SKAPA MALLAR
        if tak_obj:
            # Skapa collection för mallar
            mall_collection = bpy.data.collections.get("Guides")
            if not mall_collection:
                mall_collection = bpy.data.collections.new("Guides")
                context.scene.collection.children.link(mall_collection)
                # Avmarkera kryssrutan (disable) för hela collectionen
                for layer_collection in context.view_layer.layer_collection.children:
                    if layer_collection.name == "Guides":
                        layer_collection.exclude = True
                        break
            
            # 4a. Wall_Guide (takets undersida)
            wall_guide = utils.create_wall_guide(
                context,
                fasad_l=fasad_l,
                fasad_b=fasad_b,
                vagg_hojd=vagg_hojd,
                taklutning=h.taklutning,
                gavelutsprång=h.gavelutsprång,
                takutsprång=h.takutsprång,
                taktjocklek=taktjocklek,
                teoretisk_bredd=teoretisk_bredd
            )
            
            if wall_guide:
                wall_guide.display_type = 'WIRE'
                wall_guide.hide_render = True
                wall_guide.name = "Wall_Guide"
                wall_guide.parent = empty
                mall_collection.objects.link(wall_guide)
                
                # Boolean-modifierare på väggar
                for vagg in [fram_vagg, hoger_gavel, bak_vagg, vanster_gavel]:
                    mod = vagg.modifiers.new(name="Wall_Guide_Boolean", type='BOOLEAN')
                    mod.operation = 'INTERSECT'
                    mod.object = wall_guide
                    mod.solver = 'EXACT'
                
            # 4b. Exterior_Guide (väggars utsida + takets utsida)
            exterior_guide = utils.create_exterior_guide(
                context,
                fasad_l=fasad_l,
                fasad_b=fasad_b,
                vagg_hojd=vagg_hojd,
                taklutning=h.taklutning,
                gavelutsprång=h.gavelutsprång,
                takutsprång=h.takutsprång,
                taktjocklek=taktjocklek,
                teoretisk_bredd=teoretisk_bredd
            )
            
            if exterior_guide:
                exterior_guide.display_type = 'WIRE'
                exterior_guide.hide_render = True
                exterior_guide.name = "Exterior_Guide"
                exterior_guide.parent = empty
                mall_collection.objects.link(exterior_guide)
            
            # 4c. Interior_Guide (väggars insida + takets insida)
            Interior_Guide = utils.create_interior_guide(
                context,
                fasad_l=fasad_l,
                fasad_b=fasad_b,
                vagg_hojd=vagg_hojd,
                taklutning=h.taklutning,
                gavelutsprång=h.gavelutsprång,
                takutsprång=h.takutsprång,
                taktjocklek=taktjocklek,
                teoretisk_bredd=teoretisk_bredd
            )
            
            if Interior_Guide:
                Interior_Guide.display_type = 'WIRE'
                Interior_Guide.hide_render = True
                Interior_Guide.name = "Interior_Guide"
                Interior_Guide.parent = empty
                mall_collection.objects.link(Interior_Guide)
        
        # ----- SKAPA STANDARDKOMPONENTER -----
        try:
            from ..komponenter import generera_fonster, generera_dorr
            
            components_collection = utils.get_components_collection()
            existing_names = [coll.name for coll in components_collection.children]
            
            # Räkna hur många fönster och dörrar som finns
            window_count = len([c for c in components_collection.children if c.get("type") == "WINDOW"])
            door_count = len([c for c in components_collection.children if c.get("type") == "DOOR"])
            
            # Skapa standardfönster om inga fönster finns
            if window_count == 0:
                generera_fonster.create_window_component(
                    context,
                    name="W100",
                    W=1.20,
                    H=1.50,
                    kt=0.05,
                    kd=0.10,
                    indragning=0.01
                )
                print("Skapade standardfönster: W100")
            
            # Skapa standarddörr om inga dörrar finns
            if door_count == 0:
                generera_dorr.create_door_component(
                    context,
                    name="D100",
                    W=0.90,
                    H=2.10,
                    kt=0.05,
                    kd=0.10,
                    tröskel=0.05,
                    indragning=0.01,
                    hangning="RIGHT"
                )
                print("Skapade standarddörr: D100")
                
        except Exception as e:
            print(f"Kunde inte skapa standardkomponenter: {e}")
        
        # ----- AVMARKERA ALLT OCH MARKERA EMPTY -----
        bpy.ops.object.select_all(action='DESELECT')
        empty.select_set(True)
        context.view_layer.objects.active = empty
        
        self.report({'INFO'}, f"Skapade hus: L={fasad_l:.1f}, B={fasad_b:.1f}, H={vagg_hojd:.1f}, Nock={nock_utsida:.2f}")
        return {'FINISHED'}