import bpy
from bpy.types import PropertyGroup, Operator
from bpy.props import BoolProperty, IntProperty, EnumProperty, StringProperty, PointerProperty
import random
from ..core import material_layers
from ..core import blender_addon_utils

def format_mask_name(active_material_name, layer_index, mask_index):
    '''Returns a properly formatted name for a mask node created with this add-on.'''
    return "{0}_{1}_{2}".format(active_material_name, str(layer_index), str(mask_index))

def get_mask_node(node_name, layer_index, mask_index, get_changed=False):
    if bpy.context.active_object == None:
        return None
    
    active_material = bpy.context.active_object.active_material
    if active_material == None:
        return None

    match node_name:
        case 'MASK':
            mask_node_name = format_mask_name(active_material.name, layer_index, mask_index)
            if get_changed:
                mask_node_name += "~"
            return active_material.node_tree.nodes.get(mask_node_name)
    
        case 'MASK_MIX':
            mask_group_node_name = format_mask_name(active_material.name, layer_index, mask_index)
            node_tree = bpy.data.node_groups.get(mask_group_node_name)
            if node_tree:
                return node_tree.nodes.get('MASK_MIX')
            return None
        
        case 'PROJECTION':
            mask_group_node_name = format_mask_name(active_material.name, layer_index, mask_index)
            node_tree = bpy.data.node_groups.get(mask_group_node_name)
            if node_tree:
                return node_tree.nodes.get('MASK_MIX')
            return None

def add_mask_slot():
    '''Adds a new mask slot to the mask stack.'''
    masks = bpy.context.scene.matlayer_masks
    mask_stack = bpy.context.scene.matlayer_mask_stack

    mask_slot = masks.add()

    # Assign a random, unique number to the layer slot. This allows the layer slot array index to be found using the name of the layer slot as a key.
    unique_random_slot_id = str(random.randrange(0, 999999))
    while masks.find(unique_random_slot_id) != -1:
        unique_random_slot_id = str(random.randrange(0, 999999))
    mask_slot.name = unique_random_slot_id

    # If there is no layer selected, move the layer to the top of the stack.
    if bpy.context.scene.matlayer_mask_stack.selected_index < 0:
        move_index = len(masks) - 1
        move_to_index = 0
        masks.move(move_index, move_to_index)
        mask_stack.layer_index = move_to_index
        bpy.context.scene.matlayer_mask_stack.selected_index = len(masks) - 1

    # Moves the new layer above the currently selected layer and selects it.
    else: 
        move_index = len(masks) - 1
        move_to_index = max(0, min(bpy.context.scene.matlayer_mask_stack.selected_index + 1, len(masks) - 1))
        masks.move(move_index, move_to_index)
        mask_stack.layer_index = move_to_index
        bpy.context.scene.matlayer_mask_stack.selected_index = max(0, min(bpy.context.scene.matlayer_mask_stack.selected_index + 1, len(masks) - 1))

    return bpy.context.scene.matlayer_mask_stack.selected_index

def add_layer_mask(type):
    '''Adds a mask of the specified type to the selected material layer.'''
    match type:
        case 'EDGE_WEAR':
            selected_layer_index = bpy.context.scene.matlayer_layer_stack.selected_layer_index
            new_mask_slot_index = add_mask_slot()

            active_material = bpy.context.active_object.active_material
            default_node_group = blender_addon_utils.append_node_group("ML_EdgeWear", never_auto_delete=True)
            default_node_group.name = format_mask_name(active_material.name, selected_layer_index, new_mask_slot_index) + "~"

            new_layer_group_node = active_material.node_tree.nodes.new('ShaderNodeGroup')
            new_layer_group_node.node_tree = default_node_group
            new_layer_group_node.name = format_mask_name(active_material.name, selected_layer_index, new_mask_slot_index) + "~"
            new_layer_group_node.label = "Edge Wear"

    reindex_masks('ADDED_MASK', selected_layer_index, new_mask_slot_index)
    organize_mask_nodes()
    link_mask_nodes(selected_layer_index)

def reindex_masks(change_made, layer_index, affected_mask_index):
    '''Reindexes mask nodes and node trees. This should be called after a change is made that effects the mask stack order (adding, duplicating, deleting, or moving a mask).'''
    match change_made:
        case 'ADDED_MASK':
            # Increase the layer index for all layer group nodes and their node trees that exist above the affected layer.
            total_layers = len(bpy.context.scene.matlayer_masks)
            for i in range(total_layers, affected_mask_index, -1):
                mask_node = get_mask_node('MASK', layer_index, i - 1)
                if mask_node:
                    mask_node_name = format_mask_name(bpy.context.active_object.active_material.name, layer_index, int(mask_node.name) + 1)
                    mask_node.name = mask_node_name
                    mask_node.node_tree.name = mask_node_name

            new_mask_node = get_mask_node('MASK', layer_index, affected_mask_index, get_changed=True)
            if new_mask_node:
                mask_node_name = format_mask_name(bpy.context.active_object.active_material.name, layer_index, affected_mask_index)
                new_mask_node.name = mask_node_name
                new_mask_node.node_tree.name = mask_node_name

        case 'DELETED_MASK':
            # Reduce the layer index for all layer group nodes and their nodes trees that exist above the affected layer.
            mask_count = len(bpy.context.scene.matlayer_masks)
            for i in range(mask_count, affected_mask_index + 1, -1):
                mask_node = get_mask_node('MASK', layer_index, i - 1)
                mask_node.name = str(int(mask_node.name) - 1)
                mask_node.node_tree.name = format_mask_name(bpy.context.active_object.active_material.name, layer_index, int(mask_node.name) - 1)

def organize_mask_nodes():
    '''Organizes the position of all mask nodes in the active materials node tree.'''
    selected_layer_index = bpy.context.scene.matlayer_layer_stack.selected_layer_index
    layer_node = material_layers.get_material_layer_node('LAYER', selected_layer_index)
    
    position_y = layer_node.location[1] - 600
    masks = bpy.context.scene.matlayer_masks
    for i in range(0, len(masks)):
        mask_node = get_mask_node('MASK', selected_layer_index, i)
        if mask_node:
            mask_node.location = (layer_node.location[0], position_y)
            mask_node.width = 300
            position_y -= 600

def link_mask_nodes(layer_index):
    '''Links existing mask nodes together and to their respective material layer.'''
    if not bpy.context.active_object:
        return

    if not bpy.context.active_object.active_material:
        return

    active_material = bpy.context.active_object.active_material
    node_tree = active_material.node_tree
    masks = bpy.context.scene.matlayer_masks
    mask_count = len(masks)

    # Disconnect all mask group nodes.
    for i in range(0, mask_count):
        mask_node = get_mask_node('MASK', layer_index, i)
        if mask_node:
            for input in mask_node.inputs:
                for link in input.links:
                    node_tree.links.remove(link)

    # Re-connect all layer group nodes.
    for i in range(0, mask_count):
        mask_node = get_mask_node('MASK', layer_index, i)
        next_mask_node = get_mask_node('MASK', layer_index, i + 1)
        if next_mask_node:
            last_input_index = len(next_mask_node.inputs)
            node_tree.links.new(mask_node.outputs[0], next_mask_node.inputs[last_input_index])

    # Connect the last layer node.
    layer_node = material_layers.get_material_layer_node('LAYER', layer_index)
    last_mask_node = get_mask_node('MASK', layer_index, mask_count - 1)
    if last_mask_node and last_mask_node:
        node_tree.links.new(last_mask_node.outputs[0], layer_node.inputs.get('LayerMask'))

class MATLAYER_mask_stack(PropertyGroup):
    '''Properties for the layer stack.'''
    selected_index: IntProperty(default=-1, description="Selected material filter index")

class MATLAYER_masks(PropertyGroup):
    hidden: BoolProperty(name="Hidden", description="Show if the layer is hidden")

class MATLAYER_UL_mask_list(bpy.types.UIList):
    '''Draws the mask stack.'''

    def draw_item(self, context, layout, data, item, icon, active_data, index):
        self.use_filter_show = False
        self.use_filter_reverse = True

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            row = layout.row(align=True)

            # Hidden Icon
            row = layout.row(align=True)
            row.ui_units_x = 1
            if item.hidden == True:
                row.prop(item, "hidden", text="", emboss=False, icon='HIDE_ON')

            elif item.hidden == False:
                row.prop(item, "hidden", text="", emboss=False, icon='HIDE_OFF')

            # Layer Name
            selected_layer_index = bpy.context.scene.matlayer_layer_stack.selected_layer_index
            masks = bpy.context.scene.matlayer_masks
            item_index = masks.find(item.name)
            mask_node = get_mask_node('MASK', selected_layer_index, item_index)
            if mask_node:
                row = layout.row()
                row.ui_units_x = 3
                row.prop(mask_node, "label", text="", emboss=False)

            # Layer opacity and blending mode (for the selected material channel).
            mask_mix_node = get_mask_node('MASK_MIX', selected_layer_index, item_index)
            if mask_mix_node:
                row = layout.row(align=True)
                row.ui_units_x = 2

                split = layout.split()
                col = split.column(align=True)
                col.ui_units_x = 1.6
                col.scale_y = 0.5
                col.prop(mask_mix_node.inputs[0], "default_value", text="", emboss=True)
                col.prop(mask_mix_node, "blend_type", text="")

class MATLAYER_OT_add_black_layer_mask(Operator):
    bl_label = "Add Black Layer Mask"
    bl_idname = "matlayer.add_black_layer_mask"
    bl_description = "Adds an default image based node group mask with to the selected material layer and fills the image slot with a black image"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}
    
class MATLAYER_OT_add_white_layer_mask(Operator):
    bl_label = "Add White Layer Mask"
    bl_idname = "matlayer.add_white_layer_mask"
    bl_description = "Adds an default image based node group mask with to the selected material layer and fills the image slot with a white image"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}

class MATLAYER_OT_add_edge_wear_mask(Operator):
    bl_label = "Add Edge Wear Mask"
    bl_idname = "matlayer.add_edge_wear_mask"
    bl_description = "Adds a mask that simulates edge wear to the selected material layer"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        add_layer_mask('EDGE_WEAR')
        return {'FINISHED'}

class MATLAYER_OT_move_layer_mask_up(Operator):
    bl_label = "Move Layer Mask Up"
    bl_idname = "matlayer.move_layer_mask_up"
    bl_description = "Moves the selected layer mask up on the mask stack"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}

class MATLAYER_OT_move_layer_mask_down(Operator):
    bl_label = "Move Layer Mask Down"
    bl_idname = "matlayer.move_layer_mask_down"
    bl_description = "Moves the selected layer mask down on the mask stack"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}

class MATLAYER_OT_duplicate_layer_mask(Operator):
    bl_label = "Duplicate Layer Mask"
    bl_idname = "matlayer.duplicate_layer_mask"
    bl_description = "Duplicates the selected mask"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}

class MATLAYER_OT_delete_layer_mask(Operator):
    bl_label = "Delete Layer Mask"
    bl_idname = "matlayer.delete_layer_mask"
    bl_description = "Deletes the selected mask from the selected material layer"
    bl_options = {'REGISTER', 'UNDO'}

    # Disable when there is no active object.
    @ classmethod
    def poll(cls, context):
        return context.active_object

    # Runs when the add layer button in the popup is clicked.
    def execute(self, context):
        return {'FINISHED'}
