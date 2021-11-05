# Copyright (c) 2021 Logan Fairbairn
# logan-fairbairn@outlook.com
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

# This file imports and registers all required modules.

import bpy

# Import addon preferences (settings).
from . coater_preferences import *

# Import layer functionality.
from . layers import *
from . layer_stack import *
from . layer_operators import *
from . draw_layer_stack import *
from . menu_add_layer import *
from . menu_add_mask import *

# Import baking functionality.
from . baking import *

# Import Exporting functionality.
from . coater_export import *

# Import UI.
from . coater_ui import *
from . swap_tool_color import *

# Import additional functions.
from . apply_color_grid import COATER_OT_apply_color_grid
from . export_to_image_editor import *
from . toggle_texture_paint_mode import *
from . coater_settings import *

bl_info = {
    "name": "Coater",
    "author": "Logan Fairbairn",
    "version": (0, 1),
    "blender": (2, 93, 5),
    "location": "View3D > Sidebar > Coater",
    "description": "Replaces node based texturing workflow with a layer stack workflow.",
    "warning": "",
    "doc_url": "",
    "category": "Material Editing",
}

# List of classes to be registered.
classes = (
    #Addon Preferences
    COATER_AddonPreferences,
    
    # Baking
    COATER_OT_bake,
    COATER_OT_bake_ambient_occlusion,
    COATER_OT_bake_curvature,
    COATER_OT_bake_edges,

    # Exporting
    COATER_OT_export,
    COATER_OT_export_base_color,
    COATER_OT_export_roughness,
    COATER_OT_export_metallic,
    COATER_OT_export_normals,

    # Layers
    COATER_layer_stack,
    COATER_layers,

    # Layer Menus
    COATER_OT_add_layer_menu,
    COATER_OT_add_mask_menu,

    # Layer Operations
    COATER_UL_layer_list,
    COATER_OT_add_color_layer,
    COATER_OT_add_image_layer,
    COATER_OT_add_image_mask,
    COATER_OT_delete_layer_mask,
    COATER_OT_import_mask_image,
    COATER_OT_add_empty_image_layer,
    COATER_OT_delete_layer,
    COATER_OT_move_layer_up,
    COATER_OT_move_layer_down,
    COATER_OT_merge_layer,
    COATER_OT_duplicate_layer,
    COATER_OT_toggle_channel_preview,
    COATER_OT_import_color_image,
    COATER_OT_refresh_layers,

    # Main Panel & General Settings
    COATER_panel_properties,
    COATER_PT_Panel,

    # Color Swap
    COATER_OT_swap_primary_color,
    
    # Misc functions
    COATER_OT_image_editor_export,
    COATER_OT_toggle_texture_paint_mode,
    COATER_OT_apply_color_grid,
    COATER_OT_open_settings
)

def register():
    # Register properties, operators and pannels.
    for cls in classes:
        bpy.utils.register_class(cls)

    # Panel Properties
    bpy.types.Scene.coater_panel_properties = bpy.props.PointerProperty(type=COATER_panel_properties)

    # Layer Stack Properties
    bpy.types.Scene.coater_layer_stack = bpy.props.PointerProperty(type=COATER_layer_stack)
    bpy.types.Scene.coater_layers = bpy.props.CollectionProperty(type=COATER_layers)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # TODO: Unregister pointers??

if __name__ == "__main__":
    register()
