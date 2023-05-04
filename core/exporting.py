import os
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import BoolProperty, StringProperty
from . import material_channels
from ..core import baking
from . import texture_set_settings
from ..utilities import logging
from . import matlay_materials
from .. import preferences
from ..utilities import matlay_utils

#----------------------------- EXPORT SETTINGS -----------------------------#

class MATLAY_exporting_settings(PropertyGroup):
    export_folder: StringProperty(default="", description="Path to folder location where exported texture are saved. If empty, an export folder will be created next to your .blend file and exported textures will be automatically saved there.", name="Export Folder Path")
    export_base_color: BoolProperty(default=True, name="Export Base Color", description="Include the base color in batch exporting")
    export_subsurface: BoolProperty(default=True, name="Export Subsurface", description="Include the subsurface in batch exporting")
    export_subsurface_color: BoolProperty(default=True, name="Export Subsurface Color", description="Include the subsurface color in batch exporting")
    export_metallic: BoolProperty(default=True, name="Export Metallic", description="Include the metallic in batch exporting")
    export_specular: BoolProperty(default=True, name="Export Specular", description="Include the specular in batch exporting")
    export_roughness: BoolProperty(default=True, name="Export Roughness", description="Include the roughness in batch exporting")
    export_normals: BoolProperty(default=True, name="Export Normals", description="Include the normals in batch exporting")
    export_height: BoolProperty(default=True, name="Export Height", description="Include the height in batch exporting")
    export_emission: BoolProperty(default=True, name="Export Emission", description="Include the emission in batch exporting")

#----------------------------- EXPORT FUNCTIONS -----------------------------#

def bake_and_export_material_channel(material_channel_name, context, self):
    '''Bakes the material channel to a texture and saves the output image to a folder.'''

    # Validate the material channel name.
    if not material_channels.validate_material_channel_name(material_channel_name):
        return
    
    # Verify the object is valid to bake to and there is an applied material made by this add-on applied to the selected object.
    if matlay_materials.verify_material(context) == False or baking.verify_bake_object() == False:
        return
    
    # Ensure there is a material on the active object.
    if bpy.context.active_object.active_material == None:
        logging.popup_message_box("Selected object doesn't have an active material.", title="User Error", icon='ERROR')
        return
    
    # Force save all textures (unsaved texture will not bake to textures properly).
    for image in bpy.data.images:
        if image.filepath != '' and image.is_dirty and image.has_data:
            image.save()

    # Isolate the material channel.
    material_channels.isolate_material_channel(True, material_channel_name, context)

    # Create a new image in Blender's data and image node.
    export_image_name = bpy.context.active_object.name + "_" + material_channel_name
    export_image = bpy.data.images.get(export_image_name)
    if export_image != None:
        bpy.data.images.remove(export_image)
    export_image = bpy.ops.image.new(name=export_image_name, 
                                     width=texture_set_settings.get_texture_width(), 
                                     height=texture_set_settings.get_texture_height(), 
                                     color=(0.0, 0.0, 0.0, 1.0), 
                                     alpha=False, 
                                     generated_type='BLANK', 
                                     float=False, 
                                     use_stereo_3d=False, 
                                     tiled=False)
    export_image = bpy.data.images[export_image_name]

    # Create a folder for the exported texture files.
    matlay_image_path = os.path.join(bpy.path.abspath("//"), "Matlay")
    if os.path.exists(matlay_image_path) == False:
        os.mkdir(matlay_image_path)

    export_path = os.path.join(matlay_image_path, "Textures")
    if os.path.exists(export_path) == False:
        os.mkdir(export_path)

    export_image.filepath = export_path + "/" + export_image_name + ".png"
    export_image.file_format = 'PNG'

    material_nodes = context.active_object.active_material.node_tree.nodes
    image_node = material_nodes.new('ShaderNodeTexImage')
    image_node.image = export_image
    image_node.select = True
    material_nodes.active = image_node

    # Cache the render engine so we can reset it after baking.
    original_render_engine = bpy.context.scene.render.engine
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.render.bake.use_selected_to_active = False
    bpy.ops.object.bake(type='EMIT')

    # Reset the render engine.
    bpy.context.scene.render.engine = original_render_engine
    
    # Save the image.
    if export_image:
        if export_image.is_dirty:
            export_image.save()
        else:
            logging.popup_message_box("Exported image pixel data wasn't updated during baking.", "MatLay baking error", 'ERROR')

    # Delete the image node.
    material_nodes.remove(image_node)

    # The exported image is already saved to a folder, so it's no longer needed in blend data, remove it.
    bpy.data.images.remove(export_image)

    # De-isolate the material channel.
    material_channels.isolate_material_channel(False, material_channel_name, context)

    self.report({'INFO'}, "Finished exporting textures. You can find any exported textures in {0}".format(export_path))

    # Delete unused images.
    addon_preferences = context.preferences.addons[preferences.ADDON_NAME].preferences
    if addon_preferences.auto_delete_unused_images:
        matlay_utils.delete_unused_layer_images(self, context)
    
class MATLAY_OT_export(Operator):
    bl_idname = "matlay.export"
    bl_label = "Batch Export"
    bl_description = "Bakes all checked and active material channels to textures in succession and saves all baked images to a texture folder. Note that this function (especially on slower computers, or when using a CPU for rendering) can take a few minutes"

    @ classmethod
    def poll(cls, context):
        return context.active_object
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_base_color and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.color_channel_toggle:
            bake_and_export_material_channel('COLOR', context, self)
        if bpy.context.scene.matlay_export_settings.export_subsurface and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_channel_toggle:
            bake_and_export_material_channel('SUBSURFACE', context, self)
        if bpy.context.scene.matlay_export_settings.export_subsurface_color and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_color_channel_toggle:
            bake_and_export_material_channel('SUBSURFACE_COLOR', context, self)
        if bpy.context.scene.matlay_export_settings.export_metallic and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.metallic_channel_toggle:
            bake_and_export_material_channel('METALLIC', context, self)
        if bpy.context.scene.matlay_export_settings.export_specular and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.specular_channel_toggle:
            bake_and_export_material_channel('SPECULAR', context, self)
        if bpy.context.scene.matlay_export_settings.export_roughness and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.roughness_channel_toggle:
            bake_and_export_material_channel('ROUGHNESS', context, self)
        if bpy.context.scene.matlay_export_settings.export_normals and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.normal_channel_toggle:
            bake_and_export_material_channel('NORMAL', context, self)
        if bpy.context.scene.matlay_export_settings.export_height and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.height_channel_toggle:
            bake_and_export_material_channel('HEIGHT', context, self)
        if bpy.context.scene.matlay_export_settings.export_emission and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.emission_channel_toggle:
            bake_and_export_material_channel('EMISSION', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_base_color(Operator):
    bl_idname = "matlay.export_base_color"
    bl_label = "Export Base Color"
    bl_description = "Bakes the MatLay base color channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.color_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_base_color and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.color_channel_toggle:
            bake_and_export_material_channel('COLOR', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_subsurface(Operator):
    bl_idname = "matlay.export_subsurface"
    bl_label = "Export Subsurface"
    bl_description = "Bakes the MatLay subsurface and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_subsurface and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_channel_toggle:
            bake_and_export_material_channel('SUBSURFACE', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_subsurface_color(Operator):
    bl_idname = "matlay.export_subsurface_color"
    bl_label = "Export Subsurface COLOR"
    bl_description = "Bakes the MatLay subsurface color and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_color_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_subsurface_color and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.subsurface_color_channel_toggle:
            bake_and_export_material_channel('SUBSURFACE_COLOR', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_metallic(Operator):
    bl_idname = "matlay.export_metallic"
    bl_label = "Export Metallic Channel"
    bl_description = "Bakes the MatLay metallic channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.metallic_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_metallic and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.metallic_channel_toggle:
            bake_and_export_material_channel('METALLIC', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_specular(Operator):
    bl_idname = "matlay.export_specular"
    bl_label = "Export Specular"
    bl_description = "Bakes the MatLay specular and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.specular_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_specular and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.specular_channel_toggle:
            bake_and_export_material_channel('SPECULAR', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_roughness(Operator):
    bl_idname = "matlay.export_roughness"
    bl_label = "Export Roughness"
    bl_description = "Bakes the MatLay roughness channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.roughness_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_roughness and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.roughness_channel_toggle:
            bake_and_export_material_channel('ROUGHNESS', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_normals(Operator):
    bl_idname = "matlay.export_normals"
    bl_label = "Export Normals"
    bl_description = "Bakes the MatLay normal channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.normal_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_normals and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.normal_channel_toggle:
            bake_and_export_material_channel('NORMAL', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_height(Operator):
    bl_idname = "matlay.export_height"
    bl_label = "Export Height"
    bl_description = "Bakes the MatLay height channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.height_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_height and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.height_channel_toggle:
            bake_and_export_material_channel('HEIGHT', context, self)
        return {'FINISHED'}

class MATLAY_OT_export_emission(Operator):
    bl_idname = "matlay.export_emission"
    bl_label = "Export Emission"
    bl_description = "Bakes the MatLay emission channel and saves the result to the export folder"

    @ classmethod
    def poll(cls, context):
        return context.active_object and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.emission_channel_toggle
    
    def execute(self, context):
        if bpy.context.scene.matlay_export_settings.export_emission and bpy.context.scene.matlay_texture_set_settings.global_material_channel_toggles.emission_channel_toggle:
            bake_and_export_material_channel('EMISSION', context, self)
        return {'FINISHED'}