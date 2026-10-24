"""Original Blender city continuity and five grounded doorway journeys.

Use factory/headless Blender5.2 with --python-exit-code1. All old assets remain
immutable. Preview two support treatments before rendering the selected one.
The transparent sky deliberately contains no recorded weather or service state.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

sys.path.insert(0, str(Path(__file__).parent))
import build_radio_entry as R
import build_radio_neon as N

DESTINATIONS = {
    'media': {'x': -10.3, 'label': 'CINEMA', 'accent': (.72,.27,.12)},
    'audio': {'x': -8.1, 'label': 'AUDIO', 'accent': (.26,.57,.8)},
    'settings': {'x': -2.3, 'label': 'HUB', 'accent': (.72,.57,.31)},
    'radio': {'x': 3.0, 'label': 'RADIO', 'accent': (.35,.75,.63)},
    'network': {'x': 6.3, 'label': 'Wi-Fi', 'accent': (.20,.65,.54)},
}
KEYS = [1, 31, 46, 57, 60]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    p=argparse.ArgumentParser();p.add_argument('--root', type=Path, required=True)
    p.add_argument('--preview-only', action='store_true');p.add_argument('--variant', choices=['platform','retaining'], default='retaining')
    p.add_argument('--ffmpeg', type=Path);p.add_argument('--destinations', default=','.join(DESTINATIONS))
    p.add_argument('--palettes', default='day,night',help='Limit regeneration after an initial full export.')
    p.add_argument('--audit-scripts', type=Path, default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve()
    names=args.destinations.split(',');assert all(n in DESTINATIONS for n in names)
    palettes=args.palettes.split(',');assert palettes and all(n in ['day','night'] for n in palettes)
    if not args.preview_only:assert args.ffmpeg and args.ffmpeg.is_file()
    source=root/'assets/blender/city-destinations';source.mkdir(parents=True, exist_ok=True)
    private=root/'.runtime/city-destinations-authoring'/args.variant;private.mkdir(parents=True, exist_ok=True)
    out=root/'app/ui/public/ambient';original=root/'assets/blender/city-v3/pysh-city-v3.blend';old_hash=sha(original)
    bpy.ops.wm.open_mainfile(filepath=str(original));bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;scene.name='PySH_City_Destinations'
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=60;scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.compression=65
    scene.eevee.taa_render_samples=24 if args.preview_only else 48;scene.eevee.ray_tracing_options.denoise_temporal=False
    materials={n:m for n,m in bpy.data.materials.items()};base_shader={}
    for name,m in materials.items():
        sh=m.node_tree.nodes.get('Principled BSDF') if m.node_tree else None
        if sh:base_shader[name]={s:tuple(sh.inputs[s].default_value) if s in ['Base Color','Emission Color'] else float(sh.inputs[s].default_value) for s in ['Base Color','Emission Color','Emission Strength']}
    stone=R.mat('District slate',(.09,.125,.14),rough=.8)
    ground=R.mat('Street asphalt',(.045,.061,.066),rough=.92)
    trim=R.mat('District limestone',(.29,.33,.32),rough=.7)
    brass=R.mat('Brushed brass',(.36,.25,.12),metal=.62,rough=.4)
    iron=R.mat('Rail steel',(.10,.14,.15),metal=.65,rough=.36)
    black=R.mat('Portal threshold',(0,0,0));nt=black.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.0001,.00015,.0002,1);nt.links.new(em.outputs[0],nt.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    window=R.mat('Entrance glazing',(.016,.035,.043),metal=.35,rough=.2)
    warm=R.mat('Street practical',(.8,.53,.25),emit=1.5)
    sign_materials={n:R.mat('Letter enamel '+n,(.36,.25,.12),metal=.62,rough=.4) for n in ['audio','radio','network']}
    authored=[];front=[];dynamic=[];hinges={}
    def box(name,loc,size,mat,**kw):
        o=R.cube('District_'+name,loc,size,mat,**kw);authored.append(o);return o
    def ball(name,loc,size,mat,**kw):
        o=R.sphere('District_'+name,loc,size,mat,**kw);authored.append(o);return o
    # Real mass continues beyond both sides and beneath the orthographic crop.
    # It replaces the transparent34-row strip, not with a CSS painted patch.
    box('ContinuousGround',(0,-.8,-2.1),(48,16,3.85),ground)
    box('StreetDeck',(0,-.8,-.13),(48,7.5,.17),stone)
    for y in [-2.65,-2.32]:box('ExtendedRail_'+str(y),(0,y,.66),(48,.035,.035),iron)
    box('ExtendedRailBed',(0,-2.485,.52),(48,.57,.18),stone)
    for i in range(63):
        x=-24+i*.78;box('RailSleeper_'+str(i),(x,-2.485,.625),(.12,.43,.035),iron)
    # Distinct partial blocks at either edge imply streets continuing offscreen.
    for side,x in [(-1,-14.6),(1,14.5)]:
        mat=materials['stone-brick' if side<0 else 'stone-limestone']
        box('EdgeBlock_'+str(side),(x,.9,1.55),(3.0,1.8,3.1),mat)
        box('EdgeCornice_'+str(side),(x,.9,3.12),(3.12,1.9,.13),trim)
        box('EdgeSetback_'+str(side),(x+side*.5,.9,3.65),(1.6,1.5,1.0),stone)
        for col in range(7):
            xx=x-1.22+col*.4
            for row in range(5):
                box(f'EdgeWindow_{side}_{col}_{row}',(xx,-.018,.38+row*.48),(.14,.025,.23),materials['window-amber' if (col+row)%3==0 else 'window-dark'])
    # The second iteration has a coherent retaining structure, not floating arches.
    if args.variant=='retaining':
        box('RetainingBackwall',(0,-2.02,.08),(48,.28,.87),stone)
        box('RetainingFooting',(0,-3.02,-.50),(48,.46,1.10),stone)
        for i in range(42):
            x=-23+i*1.14
            box('FoundationPier_'+str(i),(x,-2.85,-.02),(.22,.42,.93),trim)
        # Foreground abutments cover the train only where the rails enter masonry.
        for side,x in [(-1,-13.5),(1,13.5)]:
            for dx,w,h in [(0,1.0,1.28),(side*.9,.85,1.50),(side*1.75,1.0,1.85)]:
                ob=box(f'RailAbutment_{side}_{dx}',(x+dx,-2.91,h/2-.02),(w,.45,h),stone);front.append(ob)
                ob=box(f'RailAbutmentCap_{side}_{dx}',(x+dx,-2.91,h+.01),(w+.06,.49,.09),trim);front.append(ob)
    # Entrances are annexes attached to existing landmark masses. Their front
    # faces reach the sidewalk so the old small shops cannot swallow the doors.
    for name,d in DESTINATIONS.items():
        before=set(scene.objects)
        x=d['x'];accent=R.mat(name+' practical',d['accent'],emit=.9)
        block=materials['stone-oxblood' if name=='media' else 'stone-limestone' if name=='settings' else 'stone-blue' if name=='audio' else 'stone-charcoal']
        box(name+'_Annex',(x,-.60,.94),(1.52,2.04,1.88),block,bevel=.015)
        # Unlit opaque back is a real vestibule surface, not a recorded fade.
        box(name+'_Vestibule',(x,-1.66,.92),(.98,.04,1.67),black)
        for sign in [-1,1]:
            box(name+'_Pier_'+str(sign),(x+sign*.62,-1.69,.99),(.20,.22,1.97),stone,bevel=.012)
            box(name+'_Flute_'+str(sign),(x+sign*.62,-1.814,1.03),(.035,.025,1.65),brass)
            box(name+'_Sconce_'+str(sign),(x+sign*.62,-1.84,1.26),(.07,.055,.28),accent,bevel=.01)
        box(name+'_Lintel',(x,-1.69,2.01),(1.58,.25,.14),trim,bevel=.015)
        box(name+'_Landing',(x,-1.99,.045),(1.76,.66,.09),stone,bevel=.012)
        box(name+'_Step',(x,-2.29,.022),(1.86,.18,.045),trim,bevel=.008)
        if name=='media':
            for j in range(3):box(name+'_Marquee_'+str(j),(x,-1.83-j*.045,2.11+j*.065),(1.86-j*.12,.60,.055),accent if j==1 else trim,bevel=.01)
        elif name=='audio':
            for dx in [-.42,-.21,0,.21,.42]:box(name+'_AcousticFin_'+str(dx),(x+dx,-1.81,2.22),(.06,.18,.35),brass,bevel=.007)
        elif name=='network':
            for side in [-1,1]:box(name+'_GlassFin_'+str(side),(x+side*.78,-1.58,1.02),(.065,.48,2.08),accent,bevel=.012)
            box(name+'_NetworkCanopy',(x,-1.83,2.16),(1.86,.58,.09),stone,bevel=.015)
        elif name=='settings':
            for dx in [-.80,-.63,.63,.80]:box(name+'_CivicPilaster_'+str(dx),(x+dx,-1.64,1.04),(.065,.30,2.08),trim)
            box(name+'_CivicPediment',(x,-1.70,2.17),(1.91,.40,.20),stone,bevel=.025)
        else:
            for j in range(3):box(name+'_RadioCanopy_'+str(j),(x,-1.75-j*.05,2.10+j*.05),(1.70-j*.10,.55,.045),trim,bevel=.01)
        if name=='settings':
            # Original closed twelve-tooth gear, readable without an English sign.
            count=48;points=[]
            for yy in [-1.995,-1.955]:
                for inner in [False,True]:
                    for i in range(count):
                        angle=i*math.tau/count;r=.075 if inner else (.18 if i%4 in [1,2] else .15)
                        points.append((x+r*math.cos(angle),yy,2.15+r*math.sin(angle)))
            faces=[]
            for i in range(count):
                j=(i+1)%count
                faces.extend([(i,j,count+j,count+i),(count*2+j,count*2+i,count*3+i,count*3+j),(i,count*2+i,count*2+j,j),(count+j,count*3+j,count*3+i,count+i)])
            mesh=bpy.data.meshes.new('District_SettingsGear');mesh.from_pydata(points,[],faces);mesh.update()
            ob=bpy.data.objects.new(mesh.name,mesh);scene.collection.objects.link(ob);mesh.materials.append(brass);authored.append(ob)
        else:
            curve=bpy.data.curves.new(name+'_Sign','FONT');curve.body=d['label'];curve.align_x='CENTER';curve.size=.17 if name=='media' else .18;curve.extrude=.003
            ob=bpy.data.objects.new('District_'+name+'_Sign',curve);scene.collection.objects.link(ob)
            # Lettering sits on the front of its canopy, never inside the slab.
            ob.location=(x,{'media':-2.25,'radio':-2.15,'network':-2.15}.get(name,-1.965),2.105 if name=='media' else 2.05);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(sign_materials.get(name,brass))
        hinges[name]=[]
        for sign in [-1,1]:
            rig=R.empty('District_'+name+'_DoorHinge_'+str(sign),(x+sign*.48,-1.72,.12));hinges[name].append(rig)
            center=-sign*.24
            box(name+'_DoorGlass_'+str(sign),(center,0,.74),(.46,.035,1.48),window,parent=rig,bevel=.004)
            for dx in [-.23,.23]:box(name+'_DoorStile_'+str(sign)+'_'+str(dx),(center+dx,-.026,.74),(.026,.05,1.52),brass,parent=rig,bevel=.005)
            for z in [.02,.43,1.10,1.47]:box(name+'_DoorRail_'+str(sign)+'_'+str(z),(center,-.026,z),(.47,.05,.025),brass,parent=rig)
            box(name+'_Handle_'+str(sign),(center-sign*.13,-.067,.71),(.024,.065,.23),accent,parent=rig,bevel=.009)
        # The preserved shop awnings reach y−1.875. Move the attached vestibule
        # in front of them; a late camera ray gate caught one crossing the door.
        parts=set(scene.objects)-before;group=R.empty('District_'+name+'_PortalRoot')
        for ob in parts:
            if ob.parent is None:ob.parent=group
        group.location.y=-.45
    # Cars, metro and walking coats are all keyed Blender geometry in each shot.
    tire=R.mat('Tire rubber',(.01,.014,.016),rough=.86)
    for i,(x0,x1,y,color) in enumerate([(-8,4,-1.95,(.07,.17,.17)),(7,-2,-1.91,(.3,.22,.11))]):
        rig=R.empty('District_Car_'+str(i));dynamic.append(rig);paint=R.mat('Car paint'+str(i),color,metal=.3,rough=.3)
        box('CarBody'+str(i),(0,0,.17),(.8,.32,.23),paint,parent=rig,bevel=.045)
        box('CarCabin'+str(i),(-.02,0,.35),(.39,.28,.18),paint,parent=rig,bevel=.04)
        box('CarWindow'+str(i),(-.02,-.148,.36),(.27,.018,.09),window,parent=rig,bevel=.015)
        for dx in [-.25,.25]:
            for yy in [-.16,.16]:ball(f'CarWheel{i}_{dx}_{yy}',(dx,yy,.10),(.095,.04,.095),tire,parent=rig)
        R.animate_travel(rig,(x0,y,.04),(x1,y,.04))
    train=R.empty('District_Metro');dynamic.append(train)
    for i in range(4):
        xx=(i-1.5)*.75;box('MetroBody'+str(i),(xx,0,.19),(.70,.30,.29),stone,parent=train,bevel=.04)
        for dx in [-.22,-.07,.08,.23]:box(f'MetroWindow{i}_{dx}',(xx+dx,-.159,.23),(.10,.018,.10),warm,parent=train,bevel=.006)
        for dx in [-.22,.22]:box(f'MetroBogie{i}_{dx}',(xx+dx,0,.035),(.13,.27,.06),tire,parent=train)
    for i in range(2):
        rig=R.empty('District_Walker_'+str(i));dynamic.append(rig);coat=R.mat('Walkercoat'+str(i),(.10,.045,.035) if i==0 else (.035,.07,.10),rough=.8)
        ball('WalkerCoat'+str(i),(0,0,.34),(.09,.07,.15),coat,parent=rig);ball('WalkerHead'+str(i),(0,0,.54),(.05,.05,.06),trim,parent=rig)
        for sign in [-1,1]:
            hip=R.empty(f'District_Walker{i}_Hip{sign}',(sign*.04,0,.23),parent=rig)
            ball(f'WalkerLeg{i}_{sign}',(0,0,-.105),(.025,.03,.11),coat,parent=hip)
            for f in range(1,61):hip.rotation_euler.y=math.sin((f-1)*math.tau/18+i)*.36*sign;hip.keyframe_insert(data_path='rotation_euler',frame=f)
            R.frames_linear(hip)
        R.animate_travel(rig,(-.8+i*3,-1.70,.06),(.2+i*2,-1.70,.06))
    lights={o.name:(tuple(o.data.color),o.data.energy) for o in scene.objects if o.type=='LIGHT'}
    original_world=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value
    def theme(day,active=None):
        for n,values in base_shader.items():
            sh=materials[n].node_tree.nodes['Principled BSDF']
            for s,v in values.items():sh.inputs[s].default_value=v
            if day and n.startswith('window'):sh.inputs['Base Color'].default_value=(.12,.17,.18,1);sh.inputs['Emission Strength'].default_value=.05
            elif day and n in ['shop-warm','lamp-warm','civic-lamp']:sh.inputs['Emission Strength'].default_value=.05
        for o in scene.objects:
            if o.type!='LIGHT':continue
            color,energy=lights[o.name];o.data.color=color;o.data.energy=energy
            if day:
                if o.name=='Moon_key':o.data.color=(1,.89,.74);o.data.energy=3400
                elif o.name=='Urban_fill':o.data.energy=1200
                elif o.name=='Roof_rim':o.data.energy=800
                elif o.name.startswith('Street_practical'):o.data.energy=0
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55 if day else original_world
        warm.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.12 if day else 1.5
        for n in DESTINATIONS:bpy.data.materials['Entry_'+n+' practical'].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.12 if day else .9
        # Soft architectural lettering, not a service-state emission. Home
        # lights all three; an entrance shot favors only its chosen doorway.
        for name,material in sign_materials.items():
            lit=not day and (active is None or active==name);color=(.72,.78,.74) if lit else (.36,.25,.12)
            sh=material.node_tree.nodes['Principled BSDF'];sh.inputs['Base Color'].default_value=(*color,1);sh.inputs['Emission Color'].default_value=(*color,1);sh.inputs['Emission Strength'].default_value=.45 if lit else 0
    def descendants(root):return [root]+list(root.children_recursive)
    def show_actors(show):
        for rig in dynamic:
            for o in descendants(rig):o.hide_render=not show
    camera=scene.camera;original_camera=(camera.location.copy(),camera.rotation_euler.copy(),camera.data.copy())
    def city_camera():
        camera.animation_data_clear();camera.data.animation_data_clear();camera.location=original_camera[0];camera.rotation_euler=original_camera[1];camera.data.type='ORTHO';camera.data.ortho_scale=28.6
    action_map={};journey_cameras=[]
    def shot(name):
        x=DESTINATIONS[name]['x'];camera.animation_data_clear();camera.data.animation_data_clear();camera.data.type='PERSP';camera.data.lens=54;camera.data.sensor_width=36;camera.data.clip_start=.008;camera.data.clip_end=200
        controls=[Vector((0,-42,18.5)),Vector((x*.22,-25,10.8)),Vector((x,-4.85,1.8)),Vector((x+.035,-3.60,.99))]
        positions=[]
        for f in range(1,61):
            u=((f-1)/59)**2.0;t=.5-.5*math.cos(math.pi*u);weights=[(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3]
            camera.location=sum((controls[i]*weights[i] for i in range(4)),Vector());target=(x*(1-(1-t)**3),-1.90,.99+7.21*(1-t)**2);aim(camera,target)
            camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f);positions.append(list(camera.location))
        R.frames_linear(camera)
        camera.animation_data.action.name='Journey_'+name+'_Camera';camera.animation_data.action.use_fake_user=True
        action_map[name]={'camera':camera.animation_data.action.name,'doors':{}}
        for dest,rigs in hinges.items():
            for index,rig in enumerate(rigs):
                rig.animation_data_clear();sign=-1 if index==0 else 1
                for f,angle in [(1,0),(25,0),(45,sign*math.radians(76)),(60,sign*math.radians(84))]:rig.rotation_euler.z=angle if dest==name else 0;rig.keyframe_insert(data_path='rotation_euler',frame=f)
                R.frames_linear(rig)
                rig.animation_data.action.name=f'Journey_{name}_Door_{dest}_{index}';rig.animation_data.action.use_fake_user=True
                action_map[name]['doors'][rig.name]=rig.animation_data.action.name
        R.animate_travel(train,(x-6,-2.485,.67),(x-2,-2.485,.67))
        return positions
    def render(path,width,height,frame=1):
        path.parent.mkdir(parents=True,exist_ok=True);scene.render.resolution_x=width;scene.render.resolution_y=height;scene.render.resolution_percentage=100;scene.frame_set(frame);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    # Gate all newly authored closed parts; no original master is modified.
    sys.path.insert(0,str(args.audit_scripts));import bx_audit
    gates=[{'name':o.name,**bx_audit.deliverable([o],profile='render')} for o in authored];assert all(r['pass'] for r in gates)
    mesh={'parts':len(gates),'errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates),'pass':True}
    # Static Home exports always share the exact prior native-coordinate camera.
    show_actors(False);city_camera();scene.frame_set(1);bpy.context.view_layer.update()
    anchors={}
    for n,d in DESTINATIONS.items():
        def point(p):
            v=world_to_camera_view(scene,camera,Vector(p));return [round(v.x*100,4),round((1-v.y)*100,4)]
        anchors[n]={'world_x':d['x'],'door_center_percent':point((d['x'],-2.19,.98)),'base_percent':point((d['x'],-2.19,.04)),'portal_bounds_percent':[point((d['x']-.88,-2.35,2.30)),point((d['x']+.88,-2.35,.04))]}
    rail=world_to_camera_view(scene,camera,Vector((0,-2.485,.675)));rail_percent=[round(rail.x*100,4),round((1-rail.y)*100,4)]
    front_rail=world_to_camera_view(scene,camera,Vector((0,-2.65,.6775)));front_baseline=(1-front_rail.y)*100
    # Losslessly trim empty padding from the prior genuine Blender vehicle
    # render. Its body/look/visible size stay unchanged; wheel baseline is now
    # the sprite baseline rather than21 transparent source rows above it.
    old_metro=root/'app/ui/public/ambient/metro-v2.png';metro=N.read_rgba(old_metro);ys,xs=np.where(metro[:,:,3]>0)
    bounds=[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1];cropped=metro[bounds[1]:bounds[3],bounds[0]:bounds[2]]
    metro_height=208*.085*cropped.shape[0]/metro.shape[0];metro_width=metro_height*cropped.shape[1]/cropped.shape[0]
    metro_contract={'original':old_metro.name,'original_sha256':sha(old_metro),'lossless_alpha_bounds':bounds,'resolution':[cropped.shape[1],cropped.shape[0]],'visible_size_at_800':[metro_width,metro_height],'css_width_percent':metro_width/8,'css_track_bottom_percent':100-front_baseline,'front_wheel_baseline_y_at_480':272+front_baseline*2.08,'motion':'Use fullviewport travel calc(100vw +10px), not old600% of image width; the trimmed element is narrower. Foreground abutment layer must paint after train.'}
    N.save_rgba('metro-trim',cropped,private/'metro-trim.png' if args.preview_only else out/'metro-v4.png')
    for day in [True,False]:
        name='day' if day else 'night'
        if name not in palettes:continue
        theme(day);path=(private/f'city-{name}.png') if args.preview_only else out/f'gothic-city-{name}-v4.png';render(path,800 if args.preview_only else 1600,285 if args.preview_only else 570)
        rgba=N.read_rgba(path);assert np.min(rgba[-1,:,3])>.999,'Ground must cover the entire bottom row';assert np.min(rgba[-8:,:,3])>.999,'No floating foundation strip'
        if front:
            # Foreground abutments exported independently for actual occlusion
            # of the existing inexpensive runtime train sprite.
            old_visibility={o:o.hide_render for o in scene.objects if o.type not in ['LIGHT','CAMERA']}
            for o in old_visibility:o.hide_render=o not in front
            render(private/f'rail-front-{name}.png' if args.preview_only else out/f'gothic-city-rail-front-{name}-v4.png',800 if args.preview_only else 1600,285 if args.preview_only else 570)
            for o,value in old_visibility.items():o.hide_render=value
    report={'schema':1,'blender':bpy.app.version_string,'variant':args.variant,'resolution':[1600,570],'runtime_city_size':[800,208],'anchors':anchors,'rail_top_percent':rail_percent,'metro':metro_contract,'mesh':mesh,'source_original_sha256':old_hash,'builder_sha256':sha(Path(__file__)),'sky_transparent':True,'bottom_rows_opaque':8,'destinations':list(DESTINATIONS),'regenerated_destinations':names,'regenerated_palettes':palettes,'night_lettering':'Soft ivory architectural material on AUDIO/RADIO/Wi-Fi, selected doorway favored during its shot; no service-state change.','duration_seconds':2.5,'frames':60,'fps':24,'audio':False,'motion':'Original Blender perspective camera, hinged doors, cars, metro, walkers. No service state baked.'}
    if not args.preview_only:
        city_camera();theme(False);scene.frame_set(1);scene.render.resolution_x=1600;scene.render.resolution_y=570;scene.render.filepath='//renders/';bpy.ops.wm.save_as_mainfile(filepath=str(source/'city-destinations.blend'),compress=True)
        (source/'mesh-audit.json').write_text(json.dumps(mesh,indent=2)+'\n',encoding='utf-8')
        clips=[]
        for name in DESTINATIONS:
            show_actors(True);positions=shot(name)
            for day in [True,False]:
                palette='day' if day else 'night'
                if name not in names or palette not in palettes:continue
                theme(day,active=name);folder=private/name/palette
                for f in range(1,61):
                    path=folder/f'{f:04d}.png';render(path,800,480,f)
                    if f==46:N.save_rgba(name+palette+str(f),N.read_rgba(path)[::2,::2],source/f'key-{name}-{palette}-{f:02d}.png')
                    if f==1:assert np.max(N.read_rgba(path)[:20,:,3])<.001,'Opening sky must remain transparent'
                    if f==60:assert np.min(N.read_rgba(path)[:,:,3])>.999,'Threshold must fill the ending frame'
                destination=out/f'city-entry-{name}-{palette}-v1.webm'
                result=subprocess.run([str(args.ffmpeg),'-hide_banner','-y','-framerate','24','-i',str(folder/'%04d.png'),'-c:v','libvpx','-pix_fmt','yuva420p','-auto-alt-ref','0','-lag-in-frames','0','-crf','12','-b:v','1800k','-deadline','good','-cpu-used','2','-an',str(destination)],capture_output=True,text=True)
                (private/f'encode-{name}-{palette}.log').write_text(result.stderr,encoding='utf-8');result.check_returncode();clips.append({'name':destination.name,'bytes':destination.stat().st_size,'sha256':sha(destination)})
            report.setdefault('camera_positions',{})[name]=positions
            saved_camera=camera.copy();saved_camera.data=camera.data.copy();saved_camera.name='JourneyCamera_'+name;scene.collection.objects.link(saved_camera);journey_cameras.append(saved_camera)
        # A partial material refinement retains the complete five-shot contract.
        clips=[]
        for name in DESTINATIONS:
            for palette in ['day','night']:
                path=out/f'city-entry-{name}-{palette}-v1.webm';assert path.is_file(),'Partial export requires the initial complete asset set.'
                clips.append({'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path)})
        report['clips']=clips;report['encoded_clip_bytes']=sum(c['bytes'] for c in clips)
        report['static_assets']=[{'name':p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in out.glob('gothic-city-*-v4.png')]
        city_camera();theme(False);show_actors(False);scene.frame_set(1);scene.render.resolution_x=1600;scene.render.resolution_y=570;scene['journey_actions_json']=json.dumps(action_map)
        scene['journey_camera_names']=[o.name for o in journey_cameras]
        scene.render.filepath='//renders/';bpy.ops.wm.save_as_mainfile(filepath=str(source/'city-destinations.blend'),compress=True)
        (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    else:
        # Preview keys for one doorway, so composition/occlusion is fixed early.
        show_actors(True)
        for name in names:
            shot(name);theme(False,active=name)
            for f in ([1,31,46,56,57,58,60] if name=='media' else [46]):render(private/f'pilot-{name}-{f:02d}.png',400,240,f)
    (private/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');assert sha(original)==old_hash
    print('RESULT '+json.dumps({k:v for k,v in report.items() if k!='camera_positions'}),flush=True)


if __name__=='__main__':main()
