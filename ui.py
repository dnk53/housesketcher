# ________________________________________________________________________________________________
# UI - ANVÄNDARGRÄNSSNITT (Kollapsbara sektioner)
# ________________________________________________________________________________________________

import bpy


def get_component_items(self, context):
    """Returnerar komponenter med mått i dropdown"""
    items = []
    
    comp_coll = bpy.data.collections.get("Components")
    if not comp_coll:
        return [("", "Inga komponenter", "")]
    
    for coll in comp_coll.children:
        comp_type = coll.get("type")
        if comp_type not in ["WINDOW", "DOOR"]:
            continue
        
        # Hämta mått
        if comp_type == "WINDOW":
            width = coll.get("width", 1.2)
            height = coll.get("height", 1.5)
            label = f"{coll.name} ({width:.2f}x{height:.2f})"
        elif comp_type == "DOOR":
            width = coll.get("width", 0.9)
            height = coll.get("height", 2.1)
            label = f"{coll.name} ({width:.2f}x{height:.2f})"
        else:
            label = coll.name
        
        items.append((coll.name, label, ""))
    
    # Sortera i bokstavsordning
    items.sort(key=lambda x: x[1])
    return items


class VIEW3D_PT_huvudpanel(bpy.types.Panel):
    bl_label = "HouseSketcher"
    bl_idname = "VIEW3D_PT_huvudpanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'HouseSketcher'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        active = context.active_object

        # ----- MINIMERA OCH GENERERA HUS (PÅ SAMMA RAD) -----
        box_main = layout.box()
        row_main = box_main.row()
        row_main.scale_y = 1.0
        row_main.alignment = 'EXPAND'

        row_main.operator("mesh.bt_skapa_hus", text="New Building")
        row_main.operator("mesh.bt_dolj_alla_menyer", text="Collapse All")

        # ----- 00. MAIN DIMENSIONS -----
        box0 = layout.box()
        row0 = box0.row()
        row0.prop(scene, "bt_show_huvudmått", text="", icon='TRIA_DOWN' if scene.bt_show_huvudmått else 'TRIA_RIGHT', emboss=False)
        row0.label(text="00. Main Dimensions")

        if scene.bt_show_huvudmått:
            col0 = box0.column()
            p = scene.bt_huvudmått
            col0.prop(p, "fasad_l")
            col0.prop(p, "fasad_b")
            col0.prop(p, "vagg_hojd")
            col0.prop(p, "taklutning")
            col0.prop(p, "roof_type", text="")

        # ----- 01. SECONDARY DIMENSIONS -----
        box1 = layout.box()
        row1 = box1.row()
        row1.prop(scene, "bt_show_symmetrisk", text="", icon='TRIA_DOWN' if scene.bt_show_symmetrisk else 'TRIA_RIGHT', emboss=False)
        row1.label(text="01. Secondary Dimensions")

        if scene.bt_show_symmetrisk:
            col1 = box1.column()
            p = scene.bt_huvudmått
            col1.prop(p, "taktjocklek")
            col1.prop(p, "teoretisk_vagg_bredd")
            col1.prop(p, "takutsprång")
            col1.prop(p, "gavelutsprång")

        # ----- 02. SPECIAL DIMENSIONS -----
        box2 = layout.box()
        row2 = box2.row()
        row2.prop(scene, "bt_show_osymmetrisk", text="", icon='TRIA_DOWN' if scene.bt_show_osymmetrisk else 'TRIA_RIGHT', emboss=False)
        row2.label(text="02. Special Dimensions")

        if scene.bt_show_osymmetrisk:
            col2 = box2.column()
            p = scene.bt_huvudmått
            
            # ----- Asymmetric Settings (kollapsbar) -----
            box_asym = col2.box()
            row_asym = box_asym.row()
            row_asym.prop(scene, "bt_show_asymmetric", text="", icon='TRIA_DOWN' if scene.bt_show_asymmetric else 'TRIA_RIGHT', emboss=False)
            row_asym.label(text="Asymmetric Settings")
            
            if scene.bt_show_asymmetric:
                col_asym = box_asym.column()
                
                row = col_asym.row()
                row.prop(p, "använd_symmetrisk_vagg_hojd", text="")
                sub = row.column()
                sub.prop(p, "vagg_hojd_bak")
                sub.enabled = p.använd_symmetrisk_vagg_hojd
                
                row = col_asym.row()
                row.prop(p, "använd_symmetrisk_taklutning", text="")
                sub = row.column()
                sub.prop(p, "taklutning_bak")
                sub.enabled = p.använd_symmetrisk_taklutning
                
                row = col_asym.row()
                row.prop(p, "använd_symmetrisk_takutsprång", text="")
                sub = row.column()
                sub.prop(p, "takutsprång_bak")
                sub.enabled = p.använd_symmetrisk_takutsprång
                
                row = col_asym.row()
                row.prop(p, "använd_symmetrisk_gavelutsprång", text="")
                sub = row.column()
                sub.prop(p, "gavelutsprång_hoger")
                sub.enabled = p.använd_symmetrisk_gavelutsprång
            
            # ----- Mansard Settings (kollapsbar) -----
            box_man = col2.box()
            row_man = box_man.row()
            row_man.prop(scene, "bt_show_mansard", text="", icon='TRIA_DOWN' if scene.bt_show_mansard else 'TRIA_RIGHT', emboss=False)
            row_man.label(text="Mansard Settings")
            
            if scene.bt_show_mansard:
                col_man = box_man.column()
                
                row = col_man.row()
                row.prop(p, "använd_mansard_fram", text="")
                sub = row.column()
                sub.prop(p, "taklutning_mansard")
                sub.enabled = p.använd_mansard_fram
                
                row = col_man.row()
                row.prop(p, "använd_brytavstand_fram", text="")
                sub = row.column()
                sub.prop(p, "brytavstand_mansard")
                sub.enabled = p.använd_brytavstand_fram
                
                col_man.separator()
                
                row = col_man.row()
                row.prop(p, "använd_mansard_bak", text="")
                sub = row.column()
                sub.prop(p, "taklutning_mansard_bak")
                sub.enabled = p.använd_mansard_bak
                
                row = col_man.row()
                row.prop(p, "använd_brytavstand_bak", text="")
                sub = row.column()
                sub.prop(p, "brytavstand_mansard_bak")
                sub.enabled = p.använd_brytavstand_bak

        # ----- 10. CONCRETE SLAB -----
        box3 = layout.box()
        row3 = box3.row()
        row3.prop(scene, "bt_show_platta", text="", icon='TRIA_DOWN' if scene.bt_show_platta else 'TRIA_RIGHT', emboss=False)
        row3.label(text="10. Concrete Slab")

        if scene.bt_show_platta:
            col3 = box3.column()
            p = scene.bt_platta
            col3.prop(p, "indrag")
            col3.prop(p, "tjocklek")
            col3.prop(p, "total_hojd")
            col3.prop(p, "forstyvning_bredd")
            col3.prop(p, "lutning")

        # ----- 20. WALLS -----
        box4 = layout.box()
        row4 = box4.row()
        row4.prop(scene, "bt_show_vagg", text="", icon='TRIA_DOWN' if scene.bt_show_vagg else 'TRIA_RIGHT', emboss=False)
        row4.label(text="20. Walls")

        if scene.bt_show_vagg:
            col4 = box4.column()
            p = scene.bt_vagg
            s = scene.bt_vagg_settings
            
            col4.prop(p, "bredd")
            col4.prop(p, "spegelvänd")
            
            col4.separator()
            
            if active and active.get("typ") == "vägg":
                vagg_typ = active.get("vagg_typ", "")
                
                if vagg_typ == "gavel":
                    col4.prop(s, "start_y")
                    col4.prop(s, "langd_y")
                else:
                    col4.prop(s, "start_x")
                    col4.prop(s, "langd_x")
                
                col4.prop(s, "vagg_hojd")
            else:
                col4.prop(s, "start_x")
                col4.prop(s, "langd_x")
                col4.prop(s, "vagg_hojd")
                col4.label(text="Select a wall to edit", icon='INFO')

        # ----- 21. INTERIOR WALLS -----
        box8 = layout.box()
        row8 = box8.row()
        row8.prop(scene, "bt_show_innervagg", text="", icon='TRIA_DOWN' if scene.bt_show_innervagg else 'TRIA_RIGHT', emboss=False)
        row8.label(text="21. Interior Walls")

        if scene.bt_show_innervagg:
            col8 = box8.column()
            p = scene.bt_innervagg
            
            col8.prop(p, "tjocklek")
            col8.prop(p, "hojd")
            col8.prop(p, "guide_type", text="")
            
            col8.separator()
            
            col8.prop(p, "start_x")
            col8.prop(p, "start_y")
            col8.prop(p, "langd")
            col8.prop(p, "rotation")
            
            col8.separator()
            col8.operator("mesh.bt_skapa_innervagg", text="Add Interior Wall")
    
        # ----- 30. SLAB -----
        box5 = layout.box()
        row5 = box5.row()
        row5.prop(scene, "bt_show_bjalklag", text="", icon='TRIA_DOWN' if scene.bt_show_bjalklag else 'TRIA_RIGHT', emboss=False)
        row5.label(text="30. Slab")

        if scene.bt_show_bjalklag:
            col5 = box5.column()
            p = scene.bt_bjalklag
            
            col5.prop(p, "guide_type", text="")
            col5.prop(p, "start_x")
            col5.prop(p, "start_y")
            col5.prop(p, "langd_x")
            col5.prop(p, "bredd_y")
            col5.prop(p, "niva_z")
            col5.prop(p, "tjocklek")
            
            col5.separator()
            col5.operator("mesh.bt_skapa_bjalklag", text="Add Slab")

        # ----- 40. WINDOWS -----
        box6 = layout.box()
        row6 = box6.row()
        row6.prop(scene, "bt_show_fonster", text="", icon='TRIA_DOWN' if scene.bt_show_fonster else 'TRIA_RIGHT', emboss=False)
        row6.label(text="40. Windows")

        if scene.bt_show_fonster:
            col6 = box6.column()
            p = scene.bt_fonster
            
            col6.prop(p, "komponent_namn")
            col6.prop(p, "bredd")
            col6.prop(p, "hojd")
            col6.prop(p, "karmtjocklek")
            col6.prop(p, "karmdjup")
            # col6.prop(p, "indragning")
            
            col6.separator()
            col6.operator("mesh.bt_skapa_fonster", text="Create Window Component")

        # ----- 41. DOORS -----
        box7 = layout.box()
        row7 = box7.row()
        row7.prop(scene, "bt_show_dorr", text="", icon='TRIA_DOWN' if scene.bt_show_dorr else 'TRIA_RIGHT', emboss=False)
        row7.label(text="41. Doors")

        if scene.bt_show_dorr:
            col7 = box7.column()
            p = scene.bt_dorr
            
            col7.prop(p, "komponent_namn")
            col7.prop(p, "hangning")
            col7.prop(p, "bredd")
            col7.prop(p, "hojd")
            col7.prop(p, "karmtjocklek")
            col7.prop(p, "karmdjup")
            col7.prop(p, "tröskelhöjd")
            # col7.prop(p, "indragning")
            col7.separator()
            col7.operator("mesh.bt_skapa_dorr", text="Create Door Component")


        # ----- 50. PLACE COMPONENT -----
        box9 = layout.box()
        row9 = box9.row()
        row9.prop(scene, "bt_show_komponenter", text="", icon='TRIA_DOWN' if scene.bt_show_komponenter else 'TRIA_RIGHT', emboss=False)
        row9.label(text="50. Place Component")

        if scene.bt_show_komponenter:
            col9 = box9.column()
            
            # Dropdown med komponenter
            col9.prop(scene, "bt_selected_component", text="")
            
            # Placering
            col9.prop(scene, "bt_component_placering", text="Placement")
            
            # Nivå (höjd över golv)
            col9.prop(scene, "bt_component_niva", text="Level")
            
            # Indragning från utsida
            col9.prop(scene, "bt_component_indragning", text="Inset")
            
            # Knappar
            row = col9.row()
            row.operator("mesh.bt_placera_komponent", text="Place in Wall")
            row.operator("mesh.bt_ta_bort_komponent", text="Remove Selected")
