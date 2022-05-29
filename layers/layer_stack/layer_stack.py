# This file contains properties for the layer stack.

import bpy
from bpy.types import PropertyGroup

def update_layer_channel(self, context):
    bpy.ops.coater.refresh_layers()

def update_layer_index(self, context):
    '''Runs when the layer index is updated.'''
    layer_index = context.scene.coater_layer_stack.layer_index
    
    # TODO: Select the current layer image.
    '''
    bpy.context.scene.tool_settings.image_paint.mode = 'IMAGE'
    layer_image = layer_nodes.get_layer_image(context, layer_index)
    if layer_image != None:
        context.scene.tool_settings.image_paint.canvas = layer_image
    '''

class COATER_layer_stack(PropertyGroup):
    '''Properties for the layer stack.'''
    # TODO: Rename this to selected_layer_index.
    layer_index: bpy.props.IntProperty(default=-1, update=update_layer_index)
    channel_preview: bpy.props.BoolProperty(name="", default=False)
    node_default_width: bpy.props.IntProperty(default=250)
    node_spacing: bpy.props.IntProperty(default=80)

    # TODO: Rename this material_channel, change the enum value to the enum defined in material_channel_nodes module.
    channel: bpy.props.EnumProperty(
        items=[('BASE_COLOR', "Base Color", "Set to show all layers for the materials base color channel"),
               ('METALLIC', "Metallic", "Set to show all layers in the materials metallic channel"),
               ('ROUGHNESS', "Roughness", "Set to show all layers in the materials roughness channel"),
               ('NORMAL', "Normal", "Set to show all layers in the materials normal channel"),
               ('HEIGHT', "Height", "Set to show all layers in the materials height channel"),
               ('EMISSION', 'Emission', "Set to show all layers in the materials emission channel"),
               ('SCATTERING', 'Scattering', "Set to show all layers in the materials scattering channel")],
        name="Material Channel",
        description="Type of the layer",
        default=None,
        options={'HIDDEN'},
        update=update_layer_channel
    )

    # Tabs for layer properties.
    layer_properties_tab: bpy.props.EnumProperty(
        items=[('PROJECTION', "PROJECTION", "Layer Projection Properties"),
               ('MATERIAL', "MATERIAL", "Layer Material Properties"),
               ('MASKS', "MASKS", "Layer Mask Properties")],
        name="Layer Properties Tab",
        description="Currently selected layer properties user interface tab to display",
        default=None,
        options={'HIDDEN'},
    )