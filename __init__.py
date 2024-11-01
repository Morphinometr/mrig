import bpy

from . import properties
from . import operators
from . import panels

bl_info = {
    "name": "MRIG",
    "description": "",
    "author": "AquaticNightmare, Morphin",
    "version": (0, 0, 1),
    "blender": (2, 82, 0),
    "location": "3D View > Item",
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "",
    "doc_url": "",
    "tracker_url": "",
    "category": "Rigging"
}

addon_keymaps = []


def add_hotkey():

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('brt.pie_menu', type='D', value='PRESS', ctrl=False, shift=False)

    addon_keymaps.append((km, kmi))


def remove_hotkey():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)

    addon_keymaps.clear()


def register():
    properties.register()
    operators.register()
    panels.register()
    add_hotkey()


def unregister():
    panels.unregister()
    operators.unregister()
    properties.unregister()
    remove_hotkey()


if __name__ == "__main__":
    register()
