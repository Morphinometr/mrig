import bpy
import re
import mathutils

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty,
                       )
from bpy.types import (Panel,
                       Menu,
                       Operator,
                       PropertyGroup,
                       )

directions_dict = {
    '<->': 'ARROW_LEFTRIGHT',
    '<-': 'BACK',
    '->': 'FORWARD'
}


def add_key(obj, bone, frame):
    datapath = bone.path_from_id()
    obj.keyframe_insert(data_path=f"{datapath}.location", frame=frame, group=bone.name, keytype='GENERATED')

    if bone.rotation_mode == 'QUATERNION':
        obj.keyframe_insert(data_path=f"{datapath}.rotation_quaternion", frame=frame, group=bone.name, keytype='GENERATED')
    elif bone.rotation_mode == 'AXIS_ANGLE':
        obj.keyframe_insert(data_path=f"{datapath}.rotation_axis_angle", frame=frame, group=bone.name, keytype='GENERATED')
    else:
        obj.keyframe_insert(data_path=f"{datapath}.rotation_euler", frame=frame, group=bone.name, keytype='GENERATED')
    
    obj.keyframe_insert(data_path=f"{datapath}.scale", frame=frame, group=bone.name, keytype='GENERATED')


def set_prop_value(obj, path, value):
    prop = obj.path_resolve(path, False).data
    paths = [x for x in re.split('\.|\[|\]', path) if x]
    path_attr = None
    if path.endswith(']'):
        paths = [x for x in re.split('\[|\]', path) if x]
        path_attr = paths[- 1]
    else:
        paths = [x for x in re.split('\.', path) if x]
        path_attr = paths[- 1]

    if '"' in path_attr:
        prop[path_attr.split('"')[1]] = value
    else:
        setattr(prop, path_attr, value)


class SpaceSwitchBase():

    @property
    def parent(self):
        return self.id_data.path_resolve(self.path_from_id().rsplit('.', 1)[0])

    @property
    def manager(self):
        return self.id_data.path_resolve(self.path_from_id().rsplit('.', 2)[0])

    @property
    def property_datapath(self):
        return self.parent.property_datapath

    @property
    def edit(self):
        return self.manager.edit

    @property
    def selected(self):
        return True

    @property
    def correct(self):
        return True

    @property
    def valid(self):
        try:
            bpy.context.active_object.path_resolve(self.property_datapath)
        except ValueError:
            return False
        return True


class CollectionPropertyGrouphBase():

    @property
    def parent(self):
        return self.id_data.path_resolve(self.path_from_id().rsplit('.', 1)[0])

    @property
    def index(self):
        indexes = re.findall(r"\[\s*\+?(-?\d+)\s*\]", self.path_from_id())
        return int(indexes[-1])


class ArmaturePropertiesManager(PropertyGroup):
    properties_name: StringProperty(
        name="Properties Name",
        default='PROPERTIES'
    )

    def has_properties(self):
        armature = self.id_data
        return self.properties_name in armature.bones

    def create_properties(self):
        armature = self.id_data
        size = armature.dimensions.z
        if self.properties_name not in armature.data.bones:
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)
            properties_bone = armature.data.edit_bones.new(self.properties_name)
            properties_bone.head = mathutils.Vector((0, 0, 0))
            properties_bone.tail = properties_bone.head + mathutils.Vector((0, size, 0))
            properties_bone.use_deform = False
        return self.properties_name

    def add_property(self, prop_name, prop_value, description='', min=0.0, max=1.0, prop=False):
        armature = self.id_data
        self.create_properties()
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE', toggle=False)
        prop_pose_bone = armature.pose.bones[self.properties_name]
        if not prop:
            if not prop_name in prop_pose_bone:
                prop_pose_bone[prop_name] = prop_value
                if not '_RNA_UI' in prop_pose_bone:
                    prop_pose_bone['_RNA_UI'] = {}
                prop_pose_bone['_RNA_UI'][prop_name] = {'min': min, 'soft_min': min, 'max': max, 'soft_max': max, 'description': description, 'default': prop_value}
        else:
            prop_pose_bone[prop_name] = bpy.props.BoolProperty(name=prop_name)
        data_path = 'pose.bones["' + self.properties_name + '"]["' + prop_name + '"]'
        return data_path


class BonePairPropertiesPairs(CollectionPropertyGrouphBase, PropertyGroup):
    bone1: StringProperty()
    bone2: StringProperty()
    direction: EnumProperty(
        items=[
            ('<->', '', '', 'ARROW_LEFTRIGHT', 2),
            ('<-', '', '', 'BACK', 4),
            ('->', '', '', 'FORWARD', 8)
        ],
        options=set(),
        default='<->',
    )

    transform_tracks: EnumProperty(
        options={'ENUM_FLAG'},
        items=[
            ('LOC', 'Location', 'location', '', 2),
            ('ROT', 'Rotation', 'Rotation', '', 4),
            ('SCALE', 'Scale', 'scale', '', 8)
        ],
        default={'LOC', 'ROT', 'SCALE'},
    )

    def draw(self, context, layout):
        obj = context.active_object

        grp = layout.box()
        row = grp.row()
        split = row.split(factor=0.9)
        row2 = split.row()
        row2.prop_search(self, 'bone1', obj.data, "bones", text='')
        row2.prop(self, 'direction', text='')
        row2.prop_search(self, 'bone2', obj.data, "bones", text='')

        row3 = split.row()
        row3.prop(self, 'transform_tracks')

        op = row.operator('brt.bone_pairs_del', text='', icon='X')
        op.grp_index = self.parent.index
        op.index = self.index


class BonePairProperties(CollectionPropertyGrouphBase, SpaceSwitchBase, PropertyGroup):
    pairs: CollectionProperty(type=BonePairPropertiesPairs,)

    group1_name: StringProperty()
    group2_name: StringProperty()

    @property
    def valid(self):
        try:
            bpy.context.active_object.path_resolve(self.property_datapath)
        except ValueError:
            return False
        return True

    @property
    def selected(self):
        pose_bones = {x.name for x in bpy.context.selected_pose_bones}
        if bpy.context.active_pose_bone:
            pose_bones.update({bpy.context.active_pose_bone.name})
        return any(x.bone1 in pose_bones or x.bone2 in pose_bones for x in self.pairs)

    def copy_tm(self, context, reversed_op):
        active_obj = context.active_object
        new_sel_bones = []
        old_sel_bones = []

        new_value = 1.0 if not reversed_op else 0.0
        current_value = context.active_object.path_resolve(self.property_datapath)

        if current_value == new_value:
            return

        keying_dict = {}

        bone_matrixes = {}

        # collect bones to keyframe
        for x in self.pairs:
            direction = x.direction

            if direction == '->' and not reversed_op or direction == '<-' and reversed_op or direction == '<->':
                bone1 = x.bone1 if not reversed_op else x.bone2
                bone2 = x.bone2 if not reversed_op else x.bone1

                copy_from = active_obj.pose.bones[bone1]
                copy_to = active_obj.pose.bones[bone2]

                bone_matrixes[copy_to.name] = copy_from.matrix.copy()
                new_sel_bones.append(copy_to)

                keying_dict[copy_to] = x.transform_tracks

            if direction == '<-' and not reversed_op or direction == '->' and reversed_op or direction == '<->':
                bone1 = x.bone1 if not reversed_op else x.bone2
                bone2 = x.bone2 if not reversed_op else x.bone1

                pose_bone1 = active_obj.pose.bones[bone1]

                old_sel_bones.append(pose_bone1)

                keying_dict[pose_bone1] = x.transform_tracks

            bpy.context.view_layer.update()

        # KEYFRAME OLD BONES (NOT VISIBLE)

        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            try:  # fails if invisible, maybe there is a control bone in a mch layer?
                ks = context.scene.keying_sets_all
                if ks and ks.active and active_obj.data.space_switcher.use_active_keyset:
                    bpy.ops.pose.select_all(action='DESELECT')
                    for x in old_sel_bones:
                        if bpy.app.version < (5,1,0):
                            x.bone.select = True
                        else:
                            x.select =True
                    bpy.ops.anim.keyframe_insert_menu(type=ks.active)
                else:
                    for x in old_sel_bones:
                        bpy.ops.pose.select_all(action='DESELECT')
                        if bpy.app.version < (5,1,0):
                            x.bone.select = True
                        else:
                            x.select =True
                        key_channels = keying_dict[x]
                        if 'ROT' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Rotation')
                        if 'LOC' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Location')
                        if 'SCALE' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Scaling')
            except ValueError:
                print('Error when adding keyframe to bones')
                pass

        if self.property_datapath:
            driver_prop_correct = True
            try:
                active_obj.path_resolve(self.property_datapath)
            except:
                driver_prop_correct = False

            if driver_prop_correct:
                if type(active_obj.path_resolve(self.property_datapath)) == int:
                    new_value = int(new_value)
                if type(active_obj.path_resolve(self.property_datapath)) == int or type(active_obj.path_resolve(self.property_datapath)) == float:
                    self.parent.set_prop_value(new_value)
                    if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                        active_obj.keyframe_insert(data_path=self.property_datapath)
                else:
                    print("data path references a property that is not a number")
            else:
                print('driver prop incorrect')

        for bone, matrix in bone_matrixes.items():
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.mode_set(mode='POSE')
            active_obj.pose.bones[bone].matrix = matrix

        # KEYFRAME NEW BONES (VISIBLE)
        if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
            try:  # fails if invisible, maybe there is a control bone in a mch layer?
                ks = context.scene.keying_sets_all
                if ks and ks.active and active_obj.data.space_switcher.use_active_keyset:
                    bpy.ops.pose.select_all(action='DESELECT')
                    for x in new_sel_bones:
                        if bpy.app.version < (5,1,0):
                            x.bone.select = True
                        else:
                            x.select =True
                    bpy.ops.anim.keyframe_insert_menu(type=ks.active)
                else:
                    for x in new_sel_bones:
                        bpy.ops.pose.select_all(action='DESELECT')
                        if bpy.app.version < (5,1,0):
                            x.bone.select = True
                        else:
                            x.select =True
                        key_channels = keying_dict[x]
                        if 'ROT' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Rotation')
                        if 'LOC' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Location')
                        if 'SCALE' in key_channels:
                            bpy.ops.anim.keyframe_insert_menu(type='Scaling')
            except ValueError:
                print('Error when adding keyframe to bones')
                pass

        bpy.ops.pose.select_all(action='DESELECT')
        for x in new_sel_bones:
            if bpy.app.version < (5,1,0):
                x.bone.select = True
            else:
                x.select =True
            active_obj.data.bones.active = x.bone

    def remove_hide_drivers(self, context):
        armature = self.id_data
        for x in self.pairs:
            data_bone1 = armature.bones[x.bone1]
            data_bone1.driver_remove('hide', -1)
            data_bone1.hide = False
            data_bone2 = armature.bones[x.bone2]
            data_bone2.driver_remove('hide', -1)
            data_bone2.hide = False

    def setup_hide_drivers(self, context):
        active_obj = context.active_object
        armature = self.id_data
        driver_prop_correct = True
        try:
            active_obj.path_resolve(self.property_datapath, False)
        except:
            driver_prop_correct = False
        if self.property_datapath and driver_prop_correct:
            for x in self.pairs:
                data_bone1 = armature.bones[x.bone1]

                driver = data_bone1.driver_add('hide').driver
                v = driver.variables.new()
                v.name = 'hide'
                v.targets[0].id = active_obj
                v.targets[0].data_path = self.property_datapath
                driver.expression = 'hide'

                data_bone2 = armature.bones[x.bone2]

                driver = data_bone2.driver_add('hide').driver
                v = driver.variables.new()
                v.name = 'hide'
                v.targets[0].id = active_obj
                v.targets[0].data_path = self.property_datapath
                driver.expression = '1-hide'

    def draw(self, layout, context, edit=False):
        armature = self.id_data

        row = layout.row()

        if edit:
            row = layout.row()
            add_pair = row.operator('brt.bone_pairs_add')
            add_pair.index = self.index

        if len(self.pairs) > 0:

            row2 = layout.row(align=True)
            if edit:
                for x in self.pairs:
                    x.draw(context, layout)

                row2.prop(self, 'group1_name', text='')
                row2.prop(self, 'group2_name', text='')

                driver_prop_correct = True
                try:
                    context.active_object.path_resolve(self.property_datapath, False)
                except:
                    driver_prop_correct = False
                row = layout.row(align=True)
                row.enabled = driver_prop_correct
                op = row.operator('brt.bone_pairs_setup_hide_drivers').index = self.index
                op = row.operator('brt.bone_pairs_remove_hide_drivers', text='', icon='X').index = self.index
            else:
                current_value = self.parent.prop_value

                taxt1 = self.group1_name if self.group1_name else 'SELECT'
                taxt2 = self.group2_name if self.group2_name else 'SELECT'
                bones_setup_correctly = True
                for x in self.pairs:
                    if not(x.bone1 in self.id_data.bones and x.bone2 in self.id_data.bones):
                        bones_setup_correctly = False
                        break

                if bones_setup_correctly:
                    a_to_b = row2.operator("brt.bone_pairs_copy_tm", text=taxt1, icon='RESTRICT_SELECT_OFF', depress=current_value < 0.5)
                    a_to_b.reversed_op = True
                    a_to_b.index = self.index
                    b_to_a = row2.operator("brt.bone_pairs_copy_tm", text=taxt2, icon='RESTRICT_SELECT_OFF', depress=current_value > 0.5)
                    b_to_a.reversed_op = False
                    b_to_a.index = self.index
                else:
                    layout.label(text='Some bones could not be found')


class EnumSpaceSwitchBone(CollectionPropertyGrouphBase, PropertyGroup):
    name: StringProperty()


class EnumSpaceSwitchSpace(CollectionPropertyGrouphBase, PropertyGroup):
    name: StringProperty()


last_spaces = []


class EnumSpaceSwitchProperties(CollectionPropertyGrouphBase, SpaceSwitchBase, PropertyGroup):
    bones: CollectionProperty(type=EnumSpaceSwitchBone)
    spaces: CollectionProperty(type=EnumSpaceSwitchSpace)

    selected_bone: IntProperty()
    selected_space: IntProperty()

    @property
    def selected(self):
        pose_bones = {x.name for x in bpy.context.selected_pose_bones}
        if bpy.context.active_pose_bone:
            pose_bones.update({bpy.context.active_pose_bone.name})
        return any(x.name in pose_bones for x in self.bones)

    @property
    def current_space(self):
        return bpy.context.active_object.path_resolve(self.property_datapath)

    def get_spaces_enum(self, context):
        global last_spaces
        ans = [(str(i), f'{i} : {x.name}', x.name) for i, x in enumerate(self.spaces)]
        ans.sort(key=lambda x: int(int(x[0]) != self.current_space))
        if not ans:
            ans = [('__NONE__', 'None', 'None')]
        last_spaces = ans
        return ans

    def changed_space(self, context):
        if self.current_space != int(self.set_space):
            new_space = int(self.set_space)
            frame_num = context.scene.frame_current
            obj = context.active_object

            transforms = {x.name: obj.pose.bones[x.name].matrix.copy() for x in self.bones}

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:
                self.parent.set_prop_value(self.parent.prop_value, set_key=True, frame=frame_num - 1)

                for bone in [obj.pose.bones[x.name] for x in self.bones]:
                    add_key(obj, bone, frame_num - 1)

                self.parent.set_prop_value(int(self.set_space), set_key=True, frame=frame_num)
            else:
                self.parent.set_prop_value(int(self.set_space))

            bones = {x.name: obj.pose.bones[x.name] for x in self.bones}

            bpy.ops.object.mode_set(mode='EDIT')
            self.parent.set_prop_value(new_space)
            bpy.ops.object.mode_set(mode='POSE')
            
            for x, value in transforms.items():

                bone = bones[x]

                local_mat = bone.matrix.inverted() @ value
                bone.matrix_basis = bone.matrix_basis @ local_mat

            if bpy.context.scene.tool_settings.use_keyframe_insert_auto:

                for x in [obj.pose.bones[x.name] for x in self.bones]:
                    add_key(obj, bone, frame_num)
                
        self['set_space'] = 0

    set_space: EnumProperty(items=get_spaces_enum, update=changed_space, options={'LIBRARY_EDITABLE', 'SKIP_SAVE'}, override={'LIBRARY_OVERRIDABLE'})

    @property
    def valid(self):
        try:
            bpy.context.active_object.path_resolve(self.property_datapath)
        except ValueError:
            return False
        return True

    def draw(self, layout, context, edit=False):
        armature = self.id_data
        row = layout.split(factor=0.5)
        col1 = row.column()
        col2 = row.column()
        if edit:
            col1.operator('brt.add_enum_bone').index = self.index
            col1.template_list("BRT_UL_bones", "", self, "bones", self, "selected_bone", rows=3)
            col2.operator('brt.add_enum_space').index = self.index
            col2.template_list("BRT_UL_spaces", "", self, "spaces", self, "selected_space", rows=3)
        else:
            if self.valid:
                # using prop(expand = True) function with a dynamic enum is bugged
                # this keeps the 0 to 1 order
                for i in range(len(self.spaces)):
                    layout.prop_enum(self, 'set_space', str(i))
            else:
                layout.label(text='Property path is not valid')


class SimpleWidgetProperties(CollectionPropertyGrouphBase, SpaceSwitchBase, PropertyGroup):
    bones: CollectionProperty(type=EnumSpaceSwitchBone)

    selected_bone: IntProperty()

    @property
    def selected(self):
        pose_bones = {x.name for x in bpy.context.selected_pose_bones}
        if bpy.context.active_pose_bone:
            pose_bones.update({bpy.context.active_pose_bone.name})
        return any(x.name in pose_bones for x in self.bones)

    @property
    def valid(self):
        try:
            bpy.context.active_object.path_resolve(self.property_datapath)
        except ValueError:
            return False
        return True

    def draw(self, layout, context, edit=False):
        armature = self.id_data
        if edit:
            layout.operator('brt.add_simple_bone').index = self.index
            layout.template_list("BRT_UL_simple_bones", "", self, "bones", self, "selected_bone", rows=3)
        else:
            if not self.valid:
                layout.label(text='Property path is not valid')


class SpaceSwitchProperties(CollectionPropertyGrouphBase, PropertyGroup):
    enum_type_properties: PointerProperty(type=EnumSpaceSwitchProperties)
    pair_type_properties: PointerProperty(type=BonePairProperties)
    simple_type_properties: PointerProperty(type=SimpleWidgetProperties)

    space_switch_type: EnumProperty(items=[
        ('PAIR', 'Pairing', 'Allows copying location rotation and scale from some bones to other bones (useful for FK/IK switching)'),
        ('ENUM', 'Enum', 'Used with an integer property, for switching between parents while keeping the same transformation'),
        ('SIMPLE', 'Simple', 'Shows the desired property when the desired bones are selected, makes the rig UI cleaner'),
    ], name='Type', options=set())

    name: StringProperty(name='Name')
    property_datapath: StringProperty(name='Datapath')

    @property
    def selected(self):
        return self.child_properties.selected

    @property
    def correct(self):
        return self.child_properties.correct

    @property
    def edit(self):
        return self.manager.edit

    @property
    def child_properties(self):
        if self.space_switch_type == 'PAIR':
            return self.pair_type_properties
        elif self.space_switch_type == 'ENUM':
            return self.enum_type_properties
        elif self.space_switch_type == 'SIMPLE':
            return self.simple_type_properties

    @property
    def manager(self):
        return self.id_data.path_resolve(self.path_from_id().split('.', 2)[0])

    @property
    def prop_value(self):
        return bpy.context.active_object.path_resolve(self.property_datapath)

    def set_prop_value(self, value, set_key=False, frame=None):
        obj = bpy.context.active_object
        prop = obj.path_resolve(self.property_datapath, False).data
        paths = [x for x in re.split('\.|\[|\]', self.property_datapath) if x]
        path_attr = None
        if self.property_datapath.endswith(']'):
            paths = [x for x in re.split('\[|\]', self.property_datapath) if x]
            path_attr = paths[- 1]
        else:
            paths = [x for x in re.split('\.', self.property_datapath) if x]
            path_attr = paths[- 1]

        if '"' in path_attr:
            prop[path_attr.split('"')[1]] = value
        else:
            setattr(prop, path_attr, value)

        if set_key:
            if frame is None:
                frame = bpy.context.scene.frame_current
            obj.keyframe_insert(data_path=self.property_datapath, index=-1, frame=frame)

    def draw(self, context, layout, edit=False):
        obj = context.active_object
        if edit:

            col = layout.column()
            col.use_property_split = True
            col.prop(self, 'name', text='Name (Optional)')
            col.prop(self, 'property_datapath', icon='RNA', text='Datapath')
            col.prop(self, 'space_switch_type')
        else:
            row = layout.split(factor=0.5)
            row.alignment = 'RIGHT'

            path_attr = None
            if self.property_datapath:
                if self.property_datapath.endswith(']'):
                    path_split = [x for x in re.split(r'\[|\]', self.property_datapath) if x]
                    path_attr = path_split[- 1]
                    if '"' in path_attr:
                        path_attr = f'[{path_attr}]'
                else:
                    path_split = [x for x in re.split('\.', self.property_datapath) if x]
                    path_attr = path_split[- 1]
            try:
                if self.name:
                    row.label(text=self.name)
                elif self.child_properties.valid and self.property_datapath:
                    row.label(text=''.join([x for x in path_attr if x not in {'"', '[', ']'}]))
                else:
                    row.label(text='No Name')
                row.prop(obj.path_resolve(self.property_datapath, False).data, path_attr, text='')
            except ValueError:
                row.label(text=f'Property path is not correct')
                pass

        self.child_properties.draw(layout, context, edit)


class SpaceSwitchesManager(PropertyGroup):
    space_switches: CollectionProperty(type=SpaceSwitchProperties, name='Space Switches')

    edit: BoolProperty(default=False, name='Edit')
    only_selected: BoolProperty(default=True, name='Show only selected', description='Show only the space switches related to the selected bones')
    use_active_keyset: BoolProperty(default=False, name='Use Active Keyset')

    selected_space: IntProperty()

    def draw(self, context, layout, pie=False):
        if not pie:
            layout = layout.column(align=True)
            row = layout.row()
            row.alignment = 'RIGHT'
            row.prop(self, 'only_selected', icon='HIDE_OFF', text='')
            row.prop(self, 'edit', icon='TOOL_SETTINGS', text='')

        if self.edit and not pie:
            layout.template_list("BRT_UL_switches", "", self, "space_switches", self, "selected_space", rows=3)
            layout.operator('brt.add_space_switch', icon='ADD', text='')

            if self.selected_space < len(self.space_switches):
                box = layout.box()
                self.space_switches[self.selected_space].draw(context, box, edit=True)
        else:
            for x in self.space_switches:
                if x.selected or (not pie and not self.only_selected):
                    box = layout.box()
                    x.draw(context, box)


classes = (
    EnumSpaceSwitchBone,
    EnumSpaceSwitchSpace,
    EnumSpaceSwitchProperties,
    SimpleWidgetProperties,

    BonePairPropertiesPairs,
    BonePairProperties,

    SpaceSwitchProperties,

    SpaceSwitchesManager,

    ArmaturePropertiesManager,

)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Armature.space_switcher = PointerProperty(type=SpaceSwitchesManager)
    bpy.types.Armature.properties_manager = PointerProperty(type=ArmaturePropertiesManager)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    del bpy.types.Armature.space_switcher
    del bpy.types.Armature.properties_manager
