import bpy

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty,
                       )
from bpy.types import Panel, Menu

import rna_prop_ui


class BRT_MT_PieMenu(Menu):
    bl_label = 'Space Switcher'

    def draw(self, context):
        obj = context.active_object
        if obj and obj.type == 'ARMATURE':
            props = obj.data.space_switcher

            pie = self.layout.menu_pie()
            props.draw(context, pie, pie=True)


class BRT_PT_PropertiesAccess(Panel):
    bl_label = "Rig Properties"
    bl_idname = "BRT_PT_properties_panel"

    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"

    bl_parent_id = "BRT_PT_bone_pairs_info_panel"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'ARMATURE' and context.mode == 'POSE'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        armature = context.active_object
        layout.prop_search(armature.data.properties_manager, 'properties_name', armature.data, 'bones', text='')
        if armature.data.properties_manager.has_properties():
            path = f'object.pose.bones["{armature.data.properties_manager.properties_name}"]'
            rna_prop_ui.draw(col, context, path, bpy.types.PoseBone, use_edit=False)


class BRT_PT_BonePairManagerPanel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Item"
    bl_label = "Space Switcher"
    bl_idname = "BRT_PT_bone_pairs_info_panel"

    @classmethod
    def poll(self, context):
        return context.active_object and context.active_object.type == 'ARMATURE' and context.mode == 'POSE'

    def draw(self, context):
        layout = self.layout
        props = context.active_object.data.space_switcher
        props.draw(context, self.layout)


class BRT_UL_switches(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.label(text=item.name)
        row.operator('brt.delete_space_switch', text='', icon='CANCEL').index = index

    def invoke(self, context, event):
        pass


class BRT_UL_bones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        armature = context.active_object.data
        row = layout.row()
        row.prop_search(item, 'name', armature, "bones", text='')
        op = row.operator('brt.delete_enum_bone', text='', icon='CANCEL')
        op.index = item.parent.index
        op.bone_index = item.index

    def invoke(self, context, event):
        pass


class BRT_UL_simple_bones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        armature = context.active_object.data
        row = layout.row()
        row.prop_search(item, 'name', armature, "bones", text='')
        op = row.operator('brt.delete_simple_bone', text='', icon='CANCEL')
        op.index = item.parent.index
        op.bone_index = item.index

    def invoke(self, context, event):
        pass


class BRT_UL_spaces(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        row.prop(item, 'name', text='')
        op = row.operator('brt.delete_enum_space', text='', icon='CANCEL')
        op.index = item.parent.index
        op.space_index = item.index

    def invoke(self, context, event):
        pass


classes = (
    BRT_PT_BonePairManagerPanel,
    BRT_PT_PropertiesAccess,
    BRT_UL_spaces,
    BRT_UL_bones,
    BRT_UL_switches,
    BRT_UL_simple_bones,
    BRT_MT_PieMenu,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
