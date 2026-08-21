# ________________________________________________________________________________________________
# OPERATOR - GENERERA DÖRR (som komponent + placera i vägg)
# ________________________________________________________________________________________________

import bpy
import bmesh
from ..komponenter import generera_dorr as komponent_dorr
from .. import utils


class MESH_OT_bt_skapa_dorr(bpy.types.Operator):
    bl_idname = "mesh.bt_skapa_dorr"
    bl_label = "Create Door Component"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        p = context.scene.bt_dorr
        
        # Validera namn
        name = p.komponent_namn.strip()
        if not name:
            self.report({'ERROR'}, "Du måste ange ett namn för komponenten!")
            return {'CANCELLED'}
        
        # Kontrollera att namnet är unikt
        components_collection = utils.get_components_collection()
        existing_names = [coll.name for coll in components_collection.children]
        
        if name in existing_names:
            self.report({'ERROR'}, f"Namnet '{name}' finns redan! Använd ett unikt namn.")
            return {'CANCELLED'}
        
        # ----- SPARA VÄGG-REFERENSER INNAN VI SKAPAR KOMPONENTEN -----
        selected_objects = list(context.selected_objects)
        
        wall_refs = []
        for obj in selected_objects:
            if obj.get("typ") in ["vägg", "innervagg"]:
                wall_refs.append(obj)
                continue
            
            current = obj
            while current:
                if current.get("typ") in ["vägg", "innervagg"]:
                    wall_refs.append(current)
                    break
                current = current.parent
        
        if not wall_refs and context.active_object:
            current = context.active_object
            while current:
                if current.get("typ") in ["vägg", "innervagg"]:
                    wall_refs.append(current)
                    break
                current = current.parent
        
        # ----- SKAPA KOMPONENTEN I BIBLIOTEKET -----
        comp_collection = komponent_dorr.create_door_component(
            context,
            name=name,
            W=p.bredd,
            H=p.hojd,
            kt=p.karmtjocklek,
            kd=p.karmdjup,
            tröskel=p.tröskelhöjd,
            indragning=0.01,
            hangning=p.hangning
        )
        
        # ----- PLACERA I MARKERAD VÄGG -----
        placed_count = 0
        last_placed = None
        
        if wall_refs:
            placering = context.scene.bt_component_placering
            niva = context.scene.bt_component_niva
            indragning = context.scene.bt_component_indragning
            
            for wall_obj in wall_refs:
                if wall_obj.get("typ") == "innervagg":
                    wall_length = wall_obj.get("langd", 5.0)
                    if wall_length == 0:
                        wall_length = utils.calculate_innervagg_length(wall_obj, context)
                    wall_bredd = wall_obj.get("tjocklek", 0.120)
                    is_interior = True
                else:
                    wall_length = wall_obj.get("vagg_langd", 5.0)
                    wall_bredd = wall_obj.get("vagg_bredd", 0.15)
                    is_interior = False
                
                if placering == 0:
                    x_pos = wall_length / 2.0
                elif placering < 0:
                    x_pos = wall_length + placering
                else:
                    x_pos = placering
                
                root_empty = utils.place_component_in_wall(
                    context,
                    comp_collection,
                    wall_obj,
                    x_pos,
                    is_interior,
                    wall_bredd,
                    niva,
                    indragning
                )
                placed_count += 1
                last_placed = root_empty
        
        # ----- EFTER ALLT ÄR KLART: MARKERA DEN SISTA KOMPONENTEN -----
        if placed_count > 0 and last_placed:
            bpy.ops.object.select_all(action='DESELECT')
            last_placed.select_set(True)
            context.view_layer.objects.active = last_placed
            context.scene.bt_show_komponenter = True
            self.report({'INFO'}, f"Skapade och placerade {placed_count} dörrkomponent(er)")
        else:
            self.report({'WARNING'}, f"Skapade dörrkomponent: {name} (markera en vägg för att placera den)")
        
        return {'FINISHED'}