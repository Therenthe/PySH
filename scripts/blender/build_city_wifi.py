"""Bake an original rooftop Wi-Fi access point against the existing city camera.

blender -b --factory-startup --python-exit-code 1 -P this_file -- --root REPO
Only the small prop is rendered; the preserved city source and PNGs are untouched.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def material(name, color, emission=0):
    mat = bpy.data.materials.new(name)
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Roughness'].default_value = .58
    node.inputs['Metallic'].default_value = .38
    node.inputs['Emission Color'].default_value = (*color, 1)
    node.inputs['Emission Strength'].default_value = emission
    return mat


def box(name, center, size, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel = obj.modifiers.new('Manufactured rounded metal edges', 'BEVEL')
    bevel.width = .014
    bevel.segments = 2
    obj.data.materials.append(mat)
    return obj


def arc(name, radius, width, center, mat):
    # A closed, extruded metal arc, not a runtime SVG or a flat floating badge.
    x, y, z = center
    steps = 32
    verts = []
    for yy in [y-.035, y+.035]:
        for rr in [radius-width/2, radius+width/2]:
            for i in range(steps+1):
                a = math.radians(40+100*i/steps)
                verts.append((x+rr*math.cos(a), yy, z+rr*math.sin(a)))
    n = steps+1
    faces = []
    for i in range(steps):
        faces.extend([(i,i+1,n+i+1,n+i),
                      (2*n+i,3*n+i,3*n+i+1,2*n+i+1),
                      (i,2*n+i,2*n+i+1,i+1),
                      (n+i,n+i+1,3*n+i+1,3*n+i)])
    faces.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(mat)
    # Recalculate outward normals on the portable closed render prop.
    import bmesh
    bm = bmesh.new(); bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh); bm.free()
    return obj


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    opts = parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root = opts.root.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/pysh-gothic-city-v1.blend'))
    scene = bpy.data.scenes['PySH_Gothic_City']
    bpy.context.window.scene = scene
    for obj in scene.objects:
        if obj.type == 'MESH':
            obj.hide_render = True
    scene.name = 'PySH_Rooftop_WiFi'
    bpy.context.preferences.filepaths.save_version = 0
    out = root/'app/ui/public/ambient'
    source = root/'assets/blender/city-wifi'
    source.mkdir(parents=True, exist_ok=True)
    metal = material('WiFi weatherproof powder coated metal', (.13,.23,.25))
    edge = material('WiFi silver edge catches', (.35,.48,.47))
    dark = material('WiFi dark vents', (.028,.055,.063))
    glow = material('WiFi enamel signal face', (.22,.47,.39), .04)
    x,y,roof = 6.3,.4,4.58
    owned = []
    # Feet reach the pitched roof apex, so this reads as rooftop hardware.
    for side in [-1,1]:
        owned.append(box(f'WiFi roof mount {side}', (x+side*.24,y,roof+.055), (.065,.34,.12), metal))
    owned.append(box('WiFi access point cabinet', (x,y,roof+.18), (.72,.38,.22), metal))
    owned.append(box('WiFi cabinet silver cap', (x,y,roof+.3), (.77,.42,.045), edge))
    for i in range(5):
        owned.append(box(f'WiFi ventilation slot {i}', (x-.2+i*.1,y-.197,roof+.19), (.035,.018,.055), dark))
    owned.append(box('WiFi signal mast', (x,y+.025,roof+.58), (.048,.07,.56), edge))
    for side in [-1,1]:
        aerial=box(f'WiFi aerial {side}', (x+side*.34,y+.045,roof+.47), (.032,.045,.4), metal)
        aerial.rotation_euler.y = side*math.radians(13)
        bpy.context.view_layer.objects.active=aerial
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        owned.append(aerial)
    center=(x,y-.105,roof+.66)
    signals=[]
    for i,r in enumerate([.22,.43,.64]):
        signal=arc(f'WiFi signal arc {i+1}',r,.055,center,glow)
        owned.append(signal);signals.append(signal)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.065,location=center)
    dot=bpy.context.object;dot.name='WiFi association lamp';dot.data.materials.append(glow)
    owned.append(dot)
    for obj in owned:
        obj['pysh_authored']=True
    bpy.context.view_layer.update()
    points=[world_to_camera_view(scene,scene.camera,obj.matrix_world@Vector(corner)) for obj in owned for corner in obj.bound_box]
    width,height=1600,570
    # Crop on exact full-city raster pixels. CSS places the crop by its full-city
    # percentages, preserving alignment through 800x480 and sidebar changes.
    x0=math.floor(min(p.x for p in points)*width)-7
    x1=math.ceil(max(p.x for p in points)*width)+7
    y0=math.floor(min(p.y for p in points)*height)-7
    y1=math.ceil(max(p.y for p in points)*height)+7
    scene.render.resolution_x=width;scene.render.resolution_y=height
    scene.render.resolution_percentage=100
    scene.render.use_border=True;scene.render.use_crop_to_border=True
    scene.render.border_min_x=x0/width;scene.render.border_max_x=x1/width
    scene.render.border_min_y=y0/height;scene.render.border_max_y=y1/height
    scene.render.image_settings.compression=90
    scene.render.film_transparent=True
    scene.eevee.taa_render_samples=64
    scene['pysh_brief']='Original small Wi-Fi rooftop access point on x6.3 building; association and active route are separate runtime states.'
    scene['wifi_crop_pixels']=[x0,height-y1,x1-x0,y1-y0]
    scene['wifi_crop_percent']=[100*x0/width,100*(height-y1)/height,100*(x1-x0)/width,100*(y1-y0)/height]
    dotpos=world_to_camera_view(scene,scene.camera,Vector(center))
    scene['wifi_lamp_percent']=[100*(dotpos.x*width-x0)/(x1-x0),100*(y1-dotpos.y*height)/(y1-y0)]
    # Use the existing city's night/day light rig; do not rerender the architecture.
    for theme in ['night','day']:
        if theme=='day':
            scene.objects['Moon_Key'].data.color=(1,.9,.76)
            scene.objects['Moon_Key'].data.energy=3200
            scene.objects['Ambient_Fill'].data.energy=1800
            scene.objects['Roof_Rim'].data.energy=950
            scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
        scene.render.filepath=str(out/f'city-wifi-{theme}-v1.png')
        bpy.ops.render.render(write_still=True)
    # A Blender-rendered emission overlay shares exact crop and original geometry.
    for obj in owned:
        obj.hide_render=obj not in signals
    glow.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=2
    scene.render.filepath=str(out/'city-wifi-emission-v1.png')
    bpy.ops.render.render(write_still=True)
    for obj in owned:obj.hide_render=False
    glow.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.04
    # Independent complete-prop gate (disconnected but intentionally assembled
    # materials are rendered together); per-part closed mesh checks stay explicit.
    sys.path.append(str(Path.home()/'.codex/skills/scenario-blender-expert/scripts'))
    import bx_audit
    audits={obj.name:bx_audit.audit(obj) for obj in owned}
    gates={obj.name:bx_audit.deliverable([obj],profile='render') for obj in owned}
    errors={name:gate['errors'] for name,gate in gates.items() if not gate['pass']}
    if errors:
        raise RuntimeError('Wi-Fi render prop gate failed: '+json.dumps(errors,default=str))
    report={'blender':bpy.app.version_string,'city_source':'assets/blender/pysh-gothic-city-v1.blend',
            'roof_world':[x,y,roof],'crop_pixels':list(scene['wifi_crop_pixels']),
            'crop_percent':list(scene['wifi_crop_percent']),'lamp_percent':list(scene['wifi_lamp_percent']),
            'vertices':sum(len(obj.data.vertices) for obj in owned),
            'polygons':sum(len(obj.data.polygons) for obj in owned),
            'audit':{name:{key:value for key,value in audit.items() if key in ['zero_area_faces','loose_verts','loose_edges','flipped_faces','non_manifold_edges']} for name,audit in audits.items()},
            'render_profile_gates':{name:{'pass':gate['pass'],'errors':gate['errors'],'warnings':gate['warnings']} for name,gate in gates.items()},
            'assets':[f'city-wifi-{name}-v1.png' for name in ['day','night','emission']],
            'runtime':'Three small RGBA crops; no runtime WebGL. Active route animation, standby static lamp, off/unknown unlit.'}
    (source/'build-report.json').write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-city-wifi-v1.blend'),compress=True)
    print('RESULT '+json.dumps({key:report[key] for key in ['crop_pixels','crop_percent','lamp_percent','vertices','polygons']}))


if __name__=='__main__':main()
