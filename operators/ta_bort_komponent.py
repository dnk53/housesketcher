# ________________________________________________________________________________________________
# OPERATOR - TA BORT KOMPONENT FRÅN VÄGG
# ________________________________________________________________________________________________

import bpy


def find_component_root(obj):
    """Hittar root_empty för en komponent genom att följa parent-kedjan uppåt"""
    current = obj
    while current:
        if current.get("komponent_namn"):
            return current
        current = current.parent
    return None


class MESH_OT_bt_ta_bort_komponent(bpy.types.Operator):
    bl_idname = "mesh.bt_ta_bort_komponent"
    bl_label = "Remove Selected Component"
    bl_description = "Remove the selected component from the wall"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # Hitta markerade objekt och deras root_empty
        roots_to_remove = set()
        
        for obj in context.selected_objects:
            root = find_component_root(obj)
            if root:
                roots_to_remove.add(root)
        
        if not roots_to_remove:
            self.report({'WARNING'}, "Markera en komponent (eller del av komponent) först!")
            return {'CANCELLED'}
        
        removed_count = 0
        
        for root_obj in roots_to_remove:
            # Hitta väggen som komponenten sitter i
            wall_obj = root_obj.parent
            
            # ----- SAMLA ALLA OBJEKT SOM SKA TAS BORT -----
            objects_to_remove = []
            
            def collect_children(obj):
                for child in obj.children:
                    objects_to_remove.append(child)
                    collect_children(child)
            
            collect_children(root_obj)
            objects_to_remove.append(root_obj)
            
            # ----- TA BORT OBJEKTEN (MEN INTE MESH-DATA) -----
            for obj in objects_to_remove:
                try:
                    if obj.name not in bpy.data.objects:
                        continue
                    
                    # Ta bort objektet men BEHÅLL mesh-datan
                    # (mesh-datan delas med andra instanser)
                    bpy.data.objects.remove(obj, do_unlink=True)
                        
                except Exception as e:
                    print(f"Kunde inte ta bort {obj.name}: {e}")
            
            # ----- UPPDATERA BOOLEAN PÅ VÄGGEN -----
            if wall_obj and wall_obj.name in bpy.data.objects:
                try:
                    hal_collection = bpy.data.collections.get("Hål")
                    if hal_collection:
                        # Rensa bort eventuella tomma objekt i collectionen
                        for obj in list(hal_collection.objects):
                            if obj.name not in bpy.data.objects:
                                hal_collection.objects.unlink(obj)
                        
                        # Om collectionen är tom, ta bort Boolean-modifieraren
                        if len(hal_collection.objects) == 0:
                            mod = wall_obj.modifiers.get("Hål_Collection")
                            if mod:
                                wall_obj.modifiers.remove(mod)
                except Exception as e:
                    print(f"Kunde inte uppdatera Boolean: {e}")
            
            removed_count += 1
        
        self.report({'INFO'}, f"Tog bort {removed_count} placerad(e) komponent(er)")
        return {'FINISHED'}