# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Intellisense",
    "author": "Mackraken, tintwotin",
    "version": (0, 3),
    "blender": (2, 80, 0),
    "location": "Ctrl + Shift + Space, Edit and Context menus",
    "description": "Adds intellisense to the Text Editor",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Text Editor",
}

import bpy


def complete(context):
    from console import intellisense
    from console_python import get_console

    sc = context.space_data
    text = sc.text

    region = context.region
    for area in context.screen.areas:
        if area.type == "CONSOLE":
            region = area.regions[1]
            break

    console = get_console(hash(region))[0]

    line = text.current_line.body
    cursor = text.current_character

    #result = intellisense.expand(line, cursor, console.locals, bpy.app.debug)
    result = intellisense.expand(line, cursor, console.locals,private=False)
    result=list(result) #result[0] may be lenger than line 
    #print('>>>>-----',result)

    if len(result)>1:
        fcur=result[1]
        if fcur>cursor:
            prefix=result[0][cursor:fcur]
            options=result[2].split("\n")
            for i in range(len(options)):  
                options[i]=options[i].lstrip()
                pos=options[i].find(prefix)
                #print('>>>><<<<<<-----',pos,prefix,options[i][:100])
                if pos==-1:
                    options[i]=prefix+options[i]
                else: #prefix maybe contained
                    options[i]=options[i][pos:]
            result[2]='\n'.join(options)
    #result = intellisense.complete(line, cursor, {'bpy.ops.mesh':bpy.ops.mesh},private=False)

    #print('>>>>',result)
    return result


class TEXT_OT_intellisense_options(bpy.types.Operator):
    '''Options'''
    bl_idname = "text.intellioptions"
    bl_label = "Intellisense Options"

    text: bpy.props.StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        sc = context.space_data
        print('>>>',sc)
        text = sc.text

        #print('---',self.text)
        comp = self.text
        line = text.current_line.body

        lline = len(line)
        lcomp = len(comp)

        #intersect text
        intersect = [-1, -1]

        for i in range(lcomp):
            val1 = comp[0:i + 1]
            for j in range(lline):
                val2 = line[lline - j - 1::]
                
                if val1 == val2:
                    intersect = [i, j]
                    break

        comp = comp.strip()
        if intersect[0] > -1:
            newline = line[0:lline - intersect[1] - 1] + comp
        else:
            newline = line + comp
        #print('==',comp)
        bpy.ops.text.insert(text=comp)

        #text.current_line.body = newline
        #bpy.ops.text.move(type='LINE_END')

        return {'FINISHED'}

#tool panel ui
class TEXT_PT_intellisense_panel(bpy.types.Panel):
    bl_label = "Intellisense"
    bl_space_type = "TEXT_EDITOR"
    bl_category = "Text"
    bl_context="text_edit"
    bl_region_type="UI"

    text: bpy.props.StringProperty()

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        text = self.text

        col = layout.column()

        col.operator("text.intellisense", text="Intellisense")
        col.menu("text.intellisenseMenu", text="Options")


#right button menus
class TEXT_MT_intellisenseMenu(bpy.types.Menu):
    '''Intellisense Menu'''
    bl_label = "Intellisense!!"
    bl_idname = "text.intellisenseMenu"

    text = ""
    def draw(self, context):
        layout = self.layout
        #print('>>>>draw',context)
        options = complete(context)
        options = options[2].split("\n")

        options=[ s.lstrip() for s in options ]
        while("" in options) :
            options.remove("")

        att = False

        for op in options:
            if op.find("attribute")>-1:
                att = True
            if not att:
                op = op.lstrip()
            
            layout.operator("text.intellioptions", text=op).text = op


class TEXT_OT_Intellisense(bpy.types.Operator):
    '''Text Editor Intellisense'''
    bl_idname = "text.intellisense"
    bl_label = "Text Editor Intellisense"

    text = ""

    #   @classmethod
    #   def poll(cls, context):
    #	   return context.active_object is not None

    def execute(self, context):
        sc = context.space_data
        text = sc.text

        if text.current_character > 0:
            result = complete(context)

            if result[2] == "":
                text.current_line.body = result[0]
                bpy.ops.text.move(type='LINE_END')
            else:
                bpy.ops.wm.call_menu(name=TEXT_MT_intellisenseMenu.bl_idname)

        return {'FINISHED'}


classes = [
    TEXT_OT_Intellisense,
    TEXT_OT_intellisense_options,
    TEXT_MT_intellisenseMenu,
    TEXT_PT_intellisense_panel,
]


def panel_append(self, context):
    self.layout.separator()
    self.layout.menu("text.intellisenseMenu")


addon_keymaps = []


def register():
    for c in classes:
        bpy.utils.register_class(c)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(
            name='Text Generic', space_type='TEXT_EDITOR')
        kmi = km.keymap_items.new(
            "text.intellisense",
            type='TAB',
            value='PRESS',
            #ctrl=True,
            #shift=True,
        )
        addon_keymaps.append((km, kmi))

    bpy.types.TEXT_MT_edit.append(panel_append)
    bpy.types.TEXT_MT_text.append(panel_append)
    bpy.types.TEXT_MT_context_menu.append(panel_append)
    pass


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    bpy.types.TEXT_MT_edit.remove(panel_append)
    bpy.types.TEXT_MT_text.remove(panel_append)
    bpy.types.TEXT_MT_context_menu.remove(panel_append)


if __name__ == "__main__":
    register()

