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
from bpy.types import Operator


class BRT_OT_CopyTransformFromPreviousFrame(Operator):
    bl_label = "Copy Transform From Previous Frame"
    bl_idname = "brt.copy_tm_from_previous_frame"
    bl_description = ""

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE' and context.selected_pose_bones

    def execute(self, context):
        context.scene.frame_current = context.scene.frame_current -1
        bpy.context.view_layer.update()
        orig_tms = {x: x.matrix.copy() for x in context.selected_pose_bones}

        context.scene.frame_current = context.scene.frame_current +1
        bpy.context.view_layer.update()
        for bone, tm in orig_tms.items():
            bone.matrix = tm
            bpy.context.view_layer.update()

        return {'FINISHED'}

class BRT_OT_AddBonePairManagerPair(Operator):
    bl_label = "+"
    bl_idname = "brt.bone_pairs_add"
    bl_description = ""

    index: IntProperty(default=-1)

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        armature = context.active_object
        armature.data.space_switcher.space_switches[self.index].pair_type_properties.pairs.add()
        return {'FINISHED'}


class BRT_OT_AddSpaceSwitch(Operator):
    bl_label = "+"
    bl_idname = "brt.add_space_switch"
    bl_description = ""

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE'

    def execute(self, context):
        obj = context.active_object
        switch = obj.data.space_switcher.space_switches.add()
        return {'FINISHED'}


class BRT_OT_AddEnumBone(Operator):
    bl_label = "Add Bone"
    bl_idname = "brt.add_enum_bone"

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].enum_type_properties.bones.add()
        return {'FINISHED'}


class BRT_OT_AddSimpleBone(Operator):
    bl_label = "Add Bone"
    bl_idname = "brt.add_simple_bone"

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].simple_type_properties.bones.add()
        return {'FINISHED'}


class BRT_OT_DeleteSimpleBone(Operator):
    bl_label = "Delete Bone"
    bl_idname = "brt.delete_simple_bone"

    index: IntProperty()
    bone_index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].simple_type_properties.bones.remove(self.bone_index)
        return {'FINISHED'}


class BRT_OT_DeleteEnumBone(Operator):
    bl_label = "Delete Bone"
    bl_idname = "brt.delete_enum_bone"

    index: IntProperty()
    bone_index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].enum_type_properties.bones.remove(self.bone_index)
        return {'FINISHED'}


class BRT_OT_AddEnumSpace(Operator):
    bl_label = "Add Space"
    bl_idname = "brt.add_enum_space"

    index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].enum_type_properties.spaces.add()
        return {'FINISHED'}


class BRT_OT_DeleteEnumSpace(Operator):
    bl_label = "Delete Space"
    bl_idname = "brt.delete_enum_space"

    index: IntProperty()
    space_index: IntProperty()

    def execute(self, context):
        obj = context.active_object
        obj.data.space_switcher.space_switches[self.index].enum_type_properties.spaces.remove(self.space_index)
        return {'FINISHED'}


class BRT_OT_DelBonePairManagerPair(Operator):
    bl_label = "-"
    bl_idname = "brt.bone_pairs_del"
    bl_description = ""

    index: IntProperty(default=-1)
    grp_index: IntProperty(default=0)

    def get_index(self, context):
        index = self.index
        armature = context.active_object
        if self.index == -1:
            index = len(armature.data.space_switcher.pair_groups[self.grp_index].pairs) - 1
        return index

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        armature = context.active_object
        if len(armature.data.space_switcher.space_switches[self.grp_index].pair_type_properties.pairs) > 0:
            armature.data.space_switcher.space_switches[self.grp_index].pair_type_properties.pairs.remove(self.get_index(context))
        return {'FINISHED'}


class BRT_OT_DelBonePairGroupManager(Operator):
    bl_label = "+"
    bl_idname = "brt.delete_space_switch"
    bl_description = ""

    index: IntProperty(default=-1)

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        armature = context.active_object
        armature.data.space_switcher.space_switches.remove(self.index)
        return {'FINISHED'}


class BRT_OT_BonePairManagerCopyTm(Operator):
    bl_label = "a to b"
    bl_idname = "brt.bone_pairs_copy_tm"
    bl_description = ""
    bl_options = {"UNDO"}

    reversed_op: BoolProperty()

    index: IntProperty(default=0)

    @classmethod
    def poll(cls, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        props = context.active_object.data.space_switcher.space_switches[self.index].pair_type_properties
        props.copy_tm(context, self.reversed_op)

        return {'FINISHED'}


class BRT_OT_BonePairManagerSetupHideDrivers(Operator):
    bl_label = "Setup Hide Drivers"
    bl_idname = "brt.bone_pairs_setup_hide_drivers"
    bl_description = ""

    index: IntProperty(default=0)

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        props = context.active_object.data.space_switcher.space_switches[self.index].pair_type_properties
        props.setup_hide_drivers(context)

        return {'FINISHED'}


class BRT_OT_BonePairManagerRemoveHideDrivers(Operator):
    bl_label = "Remove Hide Drivers"
    bl_idname = "brt.bone_pairs_remove_hide_drivers"
    bl_description = ""

    index: IntProperty(default=0)

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):
        props = context.active_object.data.space_switcher.pair_groups[self.index]
        props.remove_hide_drivers(context)

        return {'FINISHED'}


class BRT_OT_EditBonePairKeySet(Operator):
    bl_label = "Edit Bone Pair KeySet"
    bl_idname = "brt.edit_bone_pair_keyset"
    bl_description = ""

    index: IntProperty(default=-1)
    grp_index: IntProperty(default=0)

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE'

    def execute(self, context):

        armature = context.active_object
        pair = armature.data.space_switcher.pair_groups[self.grp_index].pairs[self.index]

        def draw(self, context):
            self.layout.prop(pair, 'transform_tracks')

        bpy.context.window_manager.popup_menu(draw, title="Edit which tracks will be keyed when using auto-key", icon='INFO')

        return {'FINISHED'}


class BRT_OT_PieMenu(Operator):
    bl_idname = 'brt.pie_menu'
    bl_label = 'Space Switcher'
    bl_description = 'Calls pie menu'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        armature = context.active_object
        return armature and armature.type == 'ARMATURE' and armature.mode == 'POSE'

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name="BRT_MT_PieMenu")
        return {'FINISHED'}


classes = (
    BRT_OT_BonePairManagerCopyTm,
    BRT_OT_AddBonePairManagerPair,
    BRT_OT_DelBonePairManagerPair,
    BRT_OT_DelBonePairGroupManager,
    BRT_OT_BonePairManagerSetupHideDrivers,
    BRT_OT_BonePairManagerRemoveHideDrivers,
    BRT_OT_EditBonePairKeySet,
    BRT_OT_AddSpaceSwitch,
    BRT_OT_AddEnumSpace,
    BRT_OT_AddEnumBone,
    BRT_OT_DeleteEnumSpace,
    BRT_OT_DeleteEnumBone,
    BRT_OT_AddSimpleBone,
    BRT_OT_DeleteSimpleBone,
    BRT_OT_PieMenu,
    BRT_OT_CopyTransformFromPreviousFrame,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
