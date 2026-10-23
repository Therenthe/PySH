"""Original PySH 2.5D city and weather sprite authoring, Blender 5.2 LTS.

Run: blender -b --factory-startup --python-exit-code 1 -P this_file -- --root REPO
No downloaded models, textures, account data or add-ons. Deterministic seed 231026.
The .blend is the editable source; transparent renders are the lightweight UI assets.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

SEED = 231026
RNG = random.Random(SEED)
BUCKETS = {}
MATERIALS = {}


def material(name, color, emission=0.0):
    mat = bpy.data.materials.new(name)
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = .78
    shader.inputs["Emission Color"].default_value = (*color, 1)
    shader.inputs["Emission Strength"].default_value = emission
    if name.startswith(('stone','front','viaduct','roof')):
        noise=mat.node_tree.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=18 if name!='roof-copper' else 7
        noise.inputs['Detail'].default_value=2
        ramp=mat.node_tree.nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color=(*[c*.72 for c in color],1)
        ramp.color_ramp.elements[1].color=(*[c*1.16 for c in color],1)
        mat.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
        mat.node_tree.links.new(ramp.outputs['Color'],shader.inputs['Base Color'])
        bump=mat.node_tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=.16
        bump.inputs['Distance'].default_value=.022
        mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    MATERIALS[name] = mat
    return name


def poly(mat, points, faces):
    verts, indices = BUCKETS.setdefault(mat, ([], []))
    start = len(verts)
    verts.extend(points)
    indices.extend(tuple(start + i for i in face) for face in faces)


def box(mat, x, y, z, w, d, h):
    if min(w, d, h) <= 0:
        return
    x0, x1 = x-w/2, x+w/2
    y0, y1 = y-d/2, y+d/2
    poly(mat, [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z),
               (x0,y0,z+h),(x1,y0,z+h),(x1,y1,z+h),(x0,y1,z+h)],
         [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])


def cone(mat, x, y, z, radius, h, top=0, sides=12):
    points = [(x+radius*math.cos(i*math.tau/sides), y+radius*math.sin(i*math.tau/sides), z) for i in range(sides)]
    if top == 0:
        points.append((x,y,z+h))
        poly(mat,points,[tuple(reversed(range(sides)))]+[(i,(i+1)%sides,sides) for i in range(sides)])
        return
    points += [(x+top*math.cos(i*math.tau/sides), y+top*math.sin(i*math.tau/sides), z+h) for i in range(sides)]
    faces = [tuple(reversed(range(sides))), tuple(range(sides, sides*2))]
    faces += [(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
    poly(mat, points, faces)


def arch_window(x, y, z, w, h, lit):
    # A pointed gothic arch, with a stone surround and a recessed light pane.
    outline = [(x-w/2,y,z),(x+w/2,y,z),(x+w/2,y,z+h*.7),(x,y,z+h),(x-w/2,y,z+h*.7)]
    poly("stone-trim", outline, [(0,1,2,3,4)])
    inset = [(x-w*.34,y-.014,z+.04),(x+w*.34,y-.014,z+.04),(x+w*.34,y-.014,z+h*.67),(x,y-.014,z+h*.87),(x-w*.34,y-.014,z+h*.67)]
    poly("window-warm" if lit else "window-dark", inset, [(0,1,2,3,4)])
    box("stone-trim",x,y-.025,z+.04,.025,.035,h*.72)


def flush(prefix):
    objects = []
    for name, (verts, faces) in BUCKETS.items():
        mesh = bpy.data.meshes.new(prefix+name)
        mesh.from_pydata(verts, [], faces)
        mesh.validate()
        mesh.update()
        ob = bpy.data.objects.new(prefix+name, mesh)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(MATERIALS[name])
        ob["pysh_authored"] = True
        if name in ('stone-blue','stone-charcoal','stone-slate','front-stone','viaduct'):
            bevel=ob.modifiers.new('Authored small stone edge catches','BEVEL')
            bevel.width=.018
            bevel.segments=2
            bevel.limit_method='ANGLE'
        objects.append(ob)
    BUCKETS.clear()
    return objects


def camera(scene, position, target, scale):
    data = bpy.data.cameras.new(scene.name+"_camera")
    ob = bpy.data.objects.new(scene.name+"_camera", data)
    scene.collection.objects.link(ob)
    ob.location = position
    ob.rotation_euler = (Vector(target)-ob.location).to_track_quat('-Z', 'Y').to_euler()
    data.type = 'ORTHO'
    data.ortho_scale = scale
    scene.camera = ob
    return ob


def light(scene, name, kind, position, color, energy, size=10):
    data = bpy.data.lights.new(name, kind)
    data.color, data.energy = color, energy
    if kind == 'AREA':
        data.shape, data.size = 'DISK', size
    ob = bpy.data.objects.new(name, data)
    scene.collection.objects.link(ob)
    ob.location = position
    ob.rotation_euler = (Vector((0,0,2))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob


def settings(scene, width, height):
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.image_settings.compression = 55
    scene.world = bpy.data.worlds.new(scene.name+"_world")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.16,.22,.28,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35
    scene.view_settings.view_transform = 'AgX'
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 1032


def build_city():
    # Distant stepped silhouettes provide depth without filling the sky.
    for i in range(33):
        x=-13+i*.82
        height=RNG.uniform(1.4,3.7)
        width=RNG.uniform(.5,1.0)
        box("distant-stone",x,2.6,0,width,1,height)
        box("distant-trim",x,2.6,height,width*.66,.85,.2)
        if i%5==0:
            cone("distant-trim",x,2.6,height+.2,.17,.55)
    # Four distinct rhythms: tall art deco, pointed gothic, civic clock and mills.
    positions=[(-12,2.9,1.1),(-10.8,3.8,1.25),(-9.3,2.4,.95),(-8.1,5.1,1.6),(-6.6,3.2,1.0),(-5.4,4.2,1.25),(-3.9,2.5,1.25),(-2.3,6.1,1.85),(-.5,3.15,1.3),(1.1,4.0,1.5),(3.0,5.3,1.7),(4.7,3.1,1.3),(6.3,4.1,1.5),(8.0,3.0,1.2),(9.7,4.6,1.6),(11.5,3.1,1.15)]
    for idx,(x,h,w) in enumerate(positions):
        y=.4+(idx%3)*.24
        d=1.15
        stone="stone-blue" if idx%3==0 else "stone-charcoal" if idx%3==1 else "stone-slate"
        box(stone,x,y,0,w,d,h)
        box("stone-trim",x,y,h-.13,w+.08,d+.08,.14)
        # Vertical buttresses and cornices carry the mature, architectural detail.
        for side in [-1,1]:
            box("stone-trim",x+side*w*.43,y-.63,.15,.065,.12,h-.08)
        for level in range(1,int(h/.64)):
            box("stone-trim",x,y-.625,level*.64,w,.06,.045)
        cols=max(2,int(w/.26))
        rows=int((h-.45)/.52)
        for row in range(rows):
            for col in range(cols):
                wx=x-w*.35+(col/(cols-1))*w*.7
                wz=.24+row*.52
                lit=RNG.random()<.43
                if idx in (3,7,10) and row>=rows-2:
                    arch_window(wx,y-.65,wz,.17,.39,lit)
                else:
                    box("window-warm" if lit else "window-dark",wx,y-.645,wz,.1,.022,.25)
        # Stepped crowns, slender spires, parapets, roofs and antenna landmarks.
        if idx in (3,7,10,14):
            for tier in range(3):
                tw=w*(.78-tier*.19)
                box(stone,x,y,h+tier*.26,tw,.88-tier*.16,.27)
                box("stone-trim",x,y,h+tier*.26+.23,tw+.04,.9-tier*.16,.055)
            cone("roof-copper",x,y,h+.78,w*.15,.55 if idx==7 else .42)
            cone("metal",x,y,h+1.15,.018,.45)
        elif idx%3==0:
            cone("roof-copper",x,y,h,w*.4,.48,sides=4)
        elif idx%3==1:
            for bx in [-.32,.32]:
                cone("roof-copper",x+bx*w,y,h,.13,.55)
        else:
            box("roof-copper",x,y,h,w*.78,.8,.18)
        if idx in (3,10):
            # Landmark masts used as the 2D radio/Bluetooth anchor references.
            mast_h=.85
            cone("metal",x,y-.35,h+.1,.025,mast_h)
            for j in range(3):
                box("metal",x,y-.35,h+.35+j*.18,.38-j*.075,.035,.026)
        if idx==5:
            # Civic clock tower: circular dial and hands, visually separate from
            # the monumental stepped office towers. Decorative, not a second UI clock.
            cone('stone-trim',x,y,h,.28,.22,top=.24,sides=12)
            for j in range(24):
                a=j*math.tau/24
                box('stone-trim',x+math.cos(a)*.3,y-.66,h-.54+math.sin(a)*.3,.045,.035,.045)
            box('window-warm',x,y-.69,h-.58,.035,.025,.24)
            box('window-warm',x+.07,y-.69,h-.58,.16,.025,.035)
        if idx in (2,8,13):
            # Water tanks, ventilation stacks and rooftop hardware at a smaller scale.
            cone('roof-copper',x,y,h+.13,.2,.38,top=.2,sides=10)
            cone('metal',x,y,h+.51,.23,.13)
    # Low street foreground: townhouses, doors, shop windows and lamps.
    for i in range(24):
        x=-13+i*1.13
        h=RNG.uniform(.8,1.65)
        face='front-stone' if i%3==0 else 'stone-charcoal' if i%3==1 else 'stone-slate'
        box(face,x,-1.15,.04,1.06,.7,h)
        box("roof-copper",x,-1.15,h+.04,1.12,.76,.1)
        if i%4==0:
            arch_window(x-.25,-1.52,.2,.25,.65,True)
            box('window-dark',x+.22,-1.515,.2,.34,.02,.55)
            for shutter in range(7):
                box('metal',x+.22,-1.54,.22+shutter*.07,.34,.025,.018)
        elif i%4==1:
            box('window-warm',x-.15,-1.52,.22,.52,.025,.43)
            box('metal',x-.15,-1.55,.21,.035,.025,.47)
            box('window-dark',x+.31,-1.52,.2,.15,.025,.53)
            box('roof-copper',x,-1.63,.72,1.04,.33,.045)
        elif i%4==2:
            for wx in [-.26,.26]:
                box('window-dark',x+wx,-1.52,.2,.25,.025,.4)
                box('stone-trim',x+wx,-1.55,.19,.29,.035,.05)
        else:
            for wx in [-.3,0,.3]:
                arch_window(x+wx,-1.52,.22,.18,.45,RNG.random()<.45)
        if h>1.2:
            for wx in [-.32,0,.32]:
                box('window-warm' if RNG.random()<.3 else 'window-dark',x+wx,-1.52,h-.35,.12,.025,.2)
        for line in range(1,int(h/.26)):
            box('stone-trim',x,-1.525,line*.26,1.05,.02,.014)
        if i%5==0:
            box('metal',x+.23,-1.1,h+.1,.13,.16,.32)
        if i%3==0:
            cone("metal",x-.45,-1.9,.1,.018,1.2)
            box("window-warm",x-.45,-1.9,1.25,.075,.075,.12)
    # Elevated metro: arches, heavy masonry piers, double steel rails.
    for i in range(24):
        x=-13+i*1.14
        box("viaduct",x,-2.35,0,.15,.35,.48)
        # Curved arch underside assembled as an original mesh strip.
        points=[]
        for j in range(13):
            t=math.pi-j*math.pi/12
            xx=x+.57+math.cos(t)*.5
            zz=.18+math.sin(t)*.26
            points.extend([(xx,-2.55,zz),(xx,-2.55,zz+.075)])
        poly("viaduct",points,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(12)])
    box("viaduct",0,-2.35,.48,28,.55,.14)
    for y in [-2.65,-2.32]:
        box("metal",0,y,.64,28,.025,.035)
    for i in range(52):
        box('metal',-14+i*.55,-2.65,.5,.024,.026,.18)
    box("front-stone",0,-2.2,-.2,29,1.4,.19)


def build_metro():
    for car in range(4):
        x=(car-1.5)*1.1
        box("train-body",x,0,0,1.03,.4,.38)
        box("metal",x,0,.37,1.0,.4,.045)
        box("train-accent",x,-.205,.08,1.01,.025,.05)
        for win in range(5):
            box("window-warm",x-.37+win*.18,-.216,.18,.12,.025,.12)
        for wx in [-.31,.31]:
            cone("metal",x+wx,-.15,-.06,.08,.08,sides=12)


def build_warning_funnel(phase):
    # Original finite mesh with a changing curved center, widening toward clouds.
    # This is a warning illustration, never a simulated live meteorological model.
    rings,sides=30,40
    vertices=[]
    for ring in range(rings):
        t=ring/(rings-1)
        z=-1.3+t*2.6
        radius=.035+.35*t**1.8
        x=math.sin(t*4+phase)*.085*(1-t)
        for side in range(sides):
            angle=side*math.tau/sides+phase+t*3
            ripple=1+.055*math.sin(side*.85+ring*.8+phase)
            vertices.append((x+math.cos(angle)*radius*ripple,math.sin(angle)*radius*ripple,z))
    faces=[]
    for ring in range(rings-1):
        for side in range(sides):
            a=ring*sides+side
            b=ring*sides+(side+1)%sides
            faces.append((a,b,b+sides,a+sides))
    poly('warning-cloud',vertices,faces)
    # Uneven cloud shoulders soften the top into the storm deck rather than
    # reading as a hard-edged cone or spotlight.
    for puff in range(5):
        cx=(puff-2)*.14
        points=[]
        sphere_sides,sphere_rings=20,10
        for ring in range(sphere_rings+1):
            phi=.001+(math.pi-.002)*ring/sphere_rings
            for side in range(sphere_sides):
                theta=side*math.tau/sphere_sides
                points.append((cx+math.sin(phi)*math.cos(theta)*(.19+puff%2*.025),math.sin(phi)*math.sin(theta)*.17,1.23+math.cos(phi)*(.1+puff%2*.025)))
        polygons=[]
        for ring in range(sphere_rings):
            for side in range(sphere_sides):
                a=ring*sphere_sides+side
                b=ring*sphere_sides+(side+1)%sphere_sides
                polygons.append((a,b,b+sphere_sides,a+sphere_sides))
        poly('warning-cloud',points,polygons)


def build_warning_water():
    vertices=[]
    columns,rows=101,18
    for row in range(rows):
        y=(row/(rows-1)-.5)*2
        for col in range(columns):
            x=(col/(columns-1)-.5)*12
            z=.035*math.sin(x*3.5+y*5)+.018*math.sin(x*9-y*7)
            vertices.append((x,y,z))
    faces=[]
    for row in range(rows-1):
        for col in range(columns-1):
            a=row*columns+col
            faces.append((a,a+1,a+1+columns,a+columns))
    poly('warning-water',vertices,faces)


def render(scene, destination):
    bpy.context.window.scene = scene
    scene.render.filepath = str(destination)
    bpy.ops.render.render(write_still=True,scene=scene.name)


def main():
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--preview',action='store_true')
    opts=parser.parse_args(args)
    root=opts.root.resolve()
    out=root/'app/ui/public/ambient'
    source=root/'assets/blender'
    out.mkdir(parents=True,exist_ok=True)
    source.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene
    scene.name='PySH_Gothic_City'
    settings(scene,1600,570)
    for name,col in {
        'stone-blue':(.105,.16,.2),'stone-charcoal':(.095,.115,.135),'stone-slate':(.14,.18,.19),
        'stone-trim':(.22,.27,.29),'roof-copper':(.11,.19,.185),'metal':(.07,.095,.12),
        'distant-stone':(.16,.22,.27),'distant-trim':(.18,.25,.3),'front-stone':(.065,.09,.115),
        'viaduct':(.12,.15,.18),'window-dark':(.055,.09,.12),'window-warm':(.8,.57,.27),
        'train-body':(.3,.38,.4),'train-accent':(.12,.35,.3),
        'particle':(.64,.78,.88),
        'warning-cloud':(.18,.25,.29),'warning-water':(.15,.31,.37),
    }.items():
        material(name,col,1.3 if name=='window-warm' else .35 if name=='particle' else 0)
    build_city()
    city_objects=flush('City_')
    camera(scene,(0,-42,14),(0,0,3.7),28.6)
    key=light(scene,'Moon_Key','AREA',(-8,-10,14),(.55,.7,1),650,10)
    fill=light(scene,'Ambient_Fill','AREA',(10,5,8),(.36,.55,.7),280,15)
    rim=light(scene,'Roof_Rim','AREA',(5,1,12),(.4,.65,.68),700,8)
    scene['pysh_brief']='800x480 Pi4 quiet gothic diorama; 1600x570 RGBA, original geometry, no real alerts inferred.'
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    def anchor(point):
        value=world_to_camera_view(scene,scene.camera,Vector(point))
        return [round(value.x*100,3),round((1-value.y)*100,3)]
    scene['radio_anchor_percent']=anchor((3,.64,6.9))
    scene['bluetooth_anchor_percent']=anchor((-8.1,.4,6.65))
    scene['metro_motion']='CSS composite follows authored 43s beat: hidden 0-8%, crossing9-49%, hidden50-100%'
    bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-gothic-city-v1.blend'),compress=True)
    if opts.preview:
        scene.render.resolution_percentage=50
    render(scene,out/'gothic-city-night-v1.png')
    key.data.color=(1,.9,.76)
    key.data.energy=3200
    fill.data.energy=1800
    rim.data.energy=950
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.65
    MATERIALS['window-warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.08
    render(scene,out/'gothic-city-day-v1.png')
    # Independent train prop and three individually rendered weather sprites.
    prop=bpy.data.scenes.new('PySH_Metro')
    settings(prop,512,96)
    bpy.context.window.scene=prop
    build_metro()
    metro=flush('Metro_')
    rig=bpy.data.objects.new('Metro_Passage_Control',None)
    prop.collection.objects.link(rig)
    for ob in metro:
        ob.parent=rig
    # Source animation keys match the frontend's presentation beat. Render the
    # isolated neutral prop; the UI reuses this authored motion as a flat layer.
    for frame,x in [(1,-16),(83,-16),(94,-15),(506,16),(516,16),(1032,16)]:
        rig.location.x=x
        rig.keyframe_insert(data_path='location',frame=frame)
    if rig.animation_data and rig.animation_data.action:
        from bpy_extras.anim_utils import action_get_channelbag_for_slot
        channelbag=action_get_channelbag_for_slot(rig.animation_data.action,rig.animation_data.action_slot)
        for curve in channelbag.fcurves:
            for keyframe in curve.keyframe_points:
                keyframe.interpolation='LINEAR'
    prop.frame_set(293)
    rig.location.x=0
    camera(prop,(0,-12,2),(0,0,.15),5)
    light(prop,'Metro_key','AREA',(-2,-5,6),(.7,.85,1),450,5)
    MATERIALS['window-warm'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=1.3
    render(prop,out/'metro-v1.png')
    for kind in ['raindrop','snowflake','ice']:
        sprite=bpy.data.scenes.new('PySH_'+kind)
        settings(sprite,64,128 if kind=='raindrop' else 64)
        bpy.context.window.scene=sprite
        if kind=='raindrop':
            cone('particle',0,0,-.9,.035,1.8,top=.002,sides=10)
        elif kind=='ice':
            cone('particle',0,0,-.15,.17,.3,top=.06,sides=8)
        else:
            # Six-arm crystal, with small bifurcations to keep the small sprite organic.
            for arm in range(6):
                theta=arm*math.tau/6
                for step in range(8):
                    r=.04+step*.055
                    box('particle',math.cos(theta)*r,0,math.sin(theta)*r,.045,.035,.045)
                for side in [-1,1]:
                    for step in range(4):
                        r=step*.04
                        angle=theta+side*.7
                        box('particle',math.cos(theta)*.23+math.cos(angle)*r,0,math.sin(theta)*.23+math.sin(angle)*r,.035,.035,.035)
        flush('Sprite_'+kind+'_')
        camera(sprite,(0,-5,0),(0,0,0),2.1 if kind=='raindrop' else 1.1)
        light(sprite,'Sprite_key_'+kind,'AREA',(-1,-3,2),(.8,.9,1),100,3)
        render(sprite,out/(kind+'-v1.png'))
    for frame in range(3):
        warning=bpy.data.scenes.new('PySH_Warning_Funnel_'+str(frame))
        settings(warning,128,320)
        bpy.context.window.scene=warning
        cloud=MATERIALS['warning-cloud']
        cloud.surface_render_method='DITHERED'
        cloud_shader=cloud.node_tree.nodes.get('Principled BSDF')
        cloud_shader.inputs['Roughness'].default_value=1
        cloud_shader.inputs['Specular IOR Level'].default_value=.1
        if frame==0:
            noise=cloud.node_tree.nodes.new('ShaderNodeTexNoise')
            noise.inputs['Scale'].default_value=9
            noise.inputs['Detail'].default_value=3
            ramp=cloud.node_tree.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].position=.2
            ramp.color_ramp.elements[0].color=(.05,.05,.05,1)
            ramp.color_ramp.elements[1].position=.8
            ramp.color_ramp.elements[1].color=(.75,.75,.75,1)
            cloud.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
            cloud.node_tree.links.new(ramp.outputs['Color'],cloud_shader.inputs['Alpha'])
        build_warning_funnel(frame*math.tau/3)
        pieces=flush('Warning_Funnel_'+str(frame)+'_')
        for ob in pieces:
            for face in ob.data.polygons:
                face.use_smooth=True
        camera(warning,(0,-6,0),(0,0,0),3.0)
        light(warning,'Warning_Funnel_Key_'+str(frame),'AREA',(-1,-4,4),(.6,.77,.9),350,4)
        render(warning,out/('tornado-'+str(frame)+'-v1.png'))
    water=bpy.data.scenes.new('PySH_Warning_Flood')
    settings(water,800,120)
    bpy.context.window.scene=water
    build_warning_water()
    flush('Warning_Water_')
    shader=MATERIALS['warning-water'].node_tree.nodes.get('Principled BSDF')
    shader.inputs['Roughness'].default_value=.24
    shader.inputs['Metallic'].default_value=.35
    camera(water,(0,-8,4),(0,0,0),12.5)
    light(water,'Warning_Water_Key','AREA',(-4,-2,6),(.65,.8,1),1100,4)
    render(water,out/'flood-ripple-v1.png')
    bpy.context.window.scene=scene
    # Restore the authored night look in the editable scene.
    key.data.color=(.55,.7,1)
    key.data.energy,fill.data.energy,rim.data.energy=650,280,700
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    scene.render.resolution_percentage=100
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-gothic-city-v1.blend'),compress=True)
    report={'blender':bpy.app.version_string,'seed':SEED,'city_objects':len(city_objects),'city_vertices':sum(len(o.data.vertices) for o in city_objects),'city_polygons':sum(len(o.data.polygons) for o in city_objects),'transparent':True,'resolution':[1600,570],'radio_anchor':list(scene['radio_anchor_percent']),'bluetooth_anchor':list(scene['bluetooth_anchor_percent']),'assets':[p.name for p in out.glob('*-v1.png') if p.name not in ['city-facades-v1.png','night-starfield-v1.png']]}
    (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':
    main()
