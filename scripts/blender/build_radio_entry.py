"""Original 3D radio entry shot, derived from the preserved city-v3 source.

Blender headless/factory, --python-exit-code 1, --root REPO [--preview-only].
The sky is transparent: no recorded or invented weather/celestial imagery.
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

sys.path.insert(0,str(Path(__file__).parent))
import build_radio_neon as N

KEYS=[1,16,31,46,56,57,60]
FACES=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def mat(name,color,emit=0,metal=0,rough=.65):
    m=bpy.data.materials.new('Entry_'+name)
    sh=m.node_tree.nodes['Principled BSDF']
    sh.inputs['Base Color'].default_value=(*color,1)
    sh.inputs['Roughness'].default_value=rough;sh.inputs['Metallic'].default_value=metal
    sh.inputs['Emission Color'].default_value=(*color,1);sh.inputs['Emission Strength'].default_value=emit
    return m


def cube(name,loc,size,material,parent=None,bevel=0):
    x,y,z=size;coords=[(-x/2,-y/2,-z/2),(x/2,-y/2,-z/2),(x/2,y/2,-z/2),(-x/2,y/2,-z/2),
                            (-x/2,-y/2,z/2),(x/2,-y/2,z/2),(x/2,y/2,z/2),(-x/2,y/2,z/2)]
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(coords,[],FACES);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.scene.collection.objects.link(obj)
    obj.location=loc;obj.parent=parent;mesh.materials.append(material)
    if bevel:
        mod=obj.modifiers.new('Soft machined edges','BEVEL');mod.width=bevel;mod.segments=3
    obj['entry_original']=True
    return obj


def sphere(name,loc,size,material,parent=None):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(0,0,0))
    obj=bpy.context.object;obj.name=name
    for v in obj.data.vertices:
        v.co.x*=size[0];v.co.y*=size[1];v.co.z*=size[2]
    obj.location=loc;obj.parent=parent;obj.data.materials.append(material)
    for p in obj.data.polygons:p.use_smooth=True
    obj['entry_original']=True
    return obj


def empty(name,loc=(0,0,0),parent=None):
    ob=bpy.data.objects.new(name,None);bpy.context.scene.collection.objects.link(ob);ob.location=loc;ob.parent=parent
    return ob


def frames_linear(obj):
    if not obj.animation_data or not obj.animation_data.action:return
    from bpy_extras.anim_utils import action_get_channelbag_for_slot
    bag=action_get_channelbag_for_slot(obj.animation_data.action,obj.animation_data.action_slot)
    for fc in bag.fcurves:
        for p in fc.keyframe_points:p.interpolation='LINEAR'


def animate_travel(rig,starts,ends):
    for f,pos in [(1,starts),(60,ends)]:
        rig.location=pos;rig.keyframe_insert(data_path='location',frame=f)
    frames_linear(rig)


def keylight(scene,name,loc,color,energy,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=loc
    ob.rotation_euler=(Vector((3,-.2,1))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--preview-only',action='store_true')
    p.add_argument('--ffmpeg',type=Path,help='Existing full FFmpeg with PNG/image2 and libvpx VP8 support; required for movie build.')
    p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve()
    if not args.preview_only and (args.ffmpeg is None or not args.ffmpeg.is_file()):raise RuntimeError('Provide --ffmpeg pointing to an existing full build with PNG/image2/libvpx support.')
    source=root/'assets/blender/radio-entry';source.mkdir(parents=True,exist_ok=True)
    private=root/'.runtime/radio-entry-authoring';private.mkdir(parents=True,exist_ok=True)
    out=root/'app/ui/public/ambient';old=root/'assets/blender/city-v3/pysh-city-v3.blend'
    old_hash=digest(old);bpy.ops.wm.open_mainfile(filepath=str(old));bpy.context.preferences.filepaths.save_version=0
    scene=bpy.data.scenes['PySH_City_v3'];scene.name='PySH_Radio_Entry'
    bpy.context.window.scene=scene;scene.render.resolution_x=800;scene.render.resolution_y=480;scene.render.resolution_percentage=100
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=60
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.compression=65
    scene.eevee.taa_render_samples=32 if args.preview_only else 48;scene.eevee.use_raytracing=True
    scene.eevee.ray_tracing_options.denoise_temporal=False
    materials={name:m for name,m in bpy.data.materials.items()}
    base_shader={name:{socket:tuple(m.node_tree.nodes['Principled BSDF'].inputs[socket].default_value) if socket in ['Base Color','Emission Color'] else float(m.node_tree.nodes['Principled BSDF'].inputs[socket].default_value) for socket in ['Base Color','Emission Color','Emission Strength']} for name,m in materials.items() if m.use_nodes and m.node_tree.nodes.get('Principled BSDF')}
    brass=mat('Brushed brass',(.34,.22,.095),metal=.65,rough=.38)
    stone=mat('Dressed dark limestone',(.095,.13,.145),rough=.75)
    trim=mat('Porcelain cornice',(.33,.38,.36),rough=.6)
    lacquer=mat('Deep petrol door',(.018,.055,.06),metal=.25,rough=.28)
    glass=mat('Door dark glass',(.01,.025,.03),metal=.4,rough=.19)
    warm=mat('Warm entrance practical',(.9,.57,.25),emit=2.0,rough=.35)
    cyan=mat('Porcelain transom',(.45,.82,.73),emit=.65,rough=.4)
    threshold=mat('Threshold darkness',(0,0,0),emit=0)
    # Use unlit black for the final threshold. It is an opaque three-dimensional
    # vestibule back wall, rather than a scene-wide recorded fade or fake sky.
    nt=threshold.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.00015,.00022,.00025,1)
    nt.links.new(em.outputs[0],nt.nodes.new('ShaderNodeOutputMaterial').inputs['Surface'])
    authored=[]
    def box(*a,**kw):
        ob=cube(*a,**kw);authored.append(ob);return ob
    def ball(*a,**kw):
        ob=sphere(*a,**kw);authored.append(ob);return ob
    # Believable double-height Deco portal, mounted just in front of the
    # preserved x3.0/y0.64 radio facade. The original city is never overwritten.
    box('Entry_Street_Ground',(0,-1.3,-.055),(29,6.5,.1),stone)
    box('Entry_Granite_Landing',(3,-.52,.045),(1.65,.95,.09),stone,bevel=.015)
    box('Entry_Step_One',(3,-1.0,.025),(1.76,.22,.05),trim,bevel=.008)
    box('Entry_Vestibule_Dark_Back',(3,-.205,1.0),(1.06,.035,1.76),threshold)
    for side,x in [('Left',2.37),('Right',3.63)]:
        box('Entry_'+side+'_Stone_Pier',(x,-.27,1.03),(.24,.20,1.96),stone,bevel=.018)
        for dx in [-.07,.07]:box('Entry_'+side+'_Brass_Flute',(x+dx,-.381,1.08),(.018,.024,1.62),brass,bevel=.004)
        box('Entry_'+side+'_Sconce_Back',(x,-.405,1.35),(.11,.045,.43),brass,bevel=.008)
        box('Entry_'+side+'_Sconce_Glass',(x,-.44,1.35),(.065,.045,.31),warm,bevel=.01)
        for dz in [-.1,0,.1]:box('Entry_'+side+'_Sconce_Rib',(x,-.472,1.35+dz),(.09,.015,.014),brass)
    box('Entry_Lintel',(3,-.27,2.02),(1.63,.28,.19),stone,bevel=.018)
    for j in range(3):box(f'Entry_Tiered_Canopy_{j}',(3,-.44-j*.07,2.10+j*.055),(1.72-j*.10,.54+j*.03,.055),trim,bevel=.01)
    box('Entry_Transom_Frame',(3,-.347,1.83),(1.04,.055,.25),brass,bevel=.008)
    box('Entry_Transom_Glass',(3,-.38,1.83),(.96,.025,.18),cyan,bevel=.005)
    for dx in [-.32,-.16,0,.16,.32]:box('Entry_Transom_Mullion',(3+dx,-.4,1.83),(.012,.018,.17),brass)
    # Original lettering is local Blender curve geometry; no external font.
    font=bpy.data.curves.new('Entry_RADIO_Lettering','FONT');font.body='RADIO';font.size=.165;font.align_x='CENTER';font.extrude=.004;font.bevel_depth=.001
    lettering=bpy.data.objects.new(font.name,font);scene.collection.objects.link(lettering);lettering.location=(3,-.598,2.22);lettering.rotation_euler=(math.pi/2,0,0);font.materials.append(brass)
    # Actual hinged leaves open before arrival. Parent transforms provide a
    # three-dimensional swing, never an image scale/opacity door replacement.
    hinges=[]
    for side,sign in [('L',-1),('R',1)]:
        pivot=empty('Entry_Door_Hinge_'+side,(3+sign*.50,-.30,.12));hinges.append(pivot)
        center=-sign*.25
        box('Entry_Door_'+side+'_Glass',(center,0,.755),(.48,.033,1.51),glass,parent=pivot,bevel=.004)
        for dx in [-.242,.242]:box('Entry_Door_'+side+'_Stile',(center+dx,-.027,.755),(.028,.05,1.56),brass,parent=pivot,bevel=.005)
        for z in [.015,.41,1.08,1.51]:box('Entry_Door_'+side+'_Rail',(center,-.026,z),(.49,.05,.027),brass,parent=pivot,bevel=.004)
        box('Entry_Door_'+side+'_Handle',(center-sign*.14,-.065,.71),(.025,.07,.24),warm,parent=pivot,bevel=.008)
        for f,angle in [(1,0),(25,0),(45,sign*math.radians(76)),(60,sign*math.radians(84))]:
            pivot.rotation_euler.z=angle;pivot.keyframe_insert(data_path='rotation_euler',frame=f)
        frames_linear(pivot)
    # Modest street life is in the actual 3D scene throughout camera travel.
    # It is atmospheric city activity, not a claim about device/service state.
    tire=mat('Tires',(.008,.012,.014),rough=.8);chrome=mat('Nickel',(.26,.30,.29),metal=.8,rough=.3)
    cars=[]
    for i,(start,end,y,color) in enumerate([(-6.5,5.5,-1.75,(.06,.16,.16)),(8,-3,-1.40,(.38,.28,.15))]):
        body=mat(f'Sedan_{i}_Paint',color,metal=.25,rough=.3);rig=empty(f'Entry_Car_{i}');cars.append(rig)
        box(f'Car{i}_Body',(0,0,.17),(.80,.34,.22),body,parent=rig,bevel=.06)
        box(f'Car{i}_Cabin',(-.025,0,.34),(.40,.29,.20),body,parent=rig,bevel=.07)
        box(f'Car{i}_Window',(-.025,-.151,.36),(.28,.018,.10),glass,parent=rig,bevel=.022)
        for dx in [-.26,.26]:
            for yy in [-.17,.17]:ball(f'Car{i}_Wheel',(dx,yy,.105),(.10,.045,.10),tire,parent=rig)
        for dx in [-.4,.4]:box(f'Car{i}_Bumper',(dx,-.01,.13),(.035,.34,.045),chrome,parent=rig,bevel=.012)
        for yy in [-.115,.115]:box(f'Car{i}_Headlight',(.403,yy,.22),(.025,.055,.05),warm,parent=rig,bevel=.008)
        animate_travel(rig,(start,y,.04),(end,y,.04))
    # Compact four-car tram on the real foreground viaduct.
    train=empty('Entry_Metro_Passage');trainmat=mat('Metro Enamel',(.12,.25,.25),metal=.2,rough=.35)
    for i in range(4):
        xx=(i-1.5)*.75
        box(f'Metro_{i}_Body',(xx,0,.19),(.70,.32,.30),trainmat,parent=train,bevel=.045)
        box(f'Metro_{i}_Roof',(xx,0,.36),(.66,.30,.05),stone,parent=train,bevel=.025)
        for wx in [-.22,-.07,.08,.23]:box(f'Metro_{i}_Window',(xx+wx,-.17,.23),(.10,.02,.10),warm,parent=train,bevel=.01)
        for wx in [-.22,.22]:box(f'Metro_{i}_Bogie',(xx+wx,0,.035),(.13,.27,.06),tire,parent=train,bevel=.015)
    animate_travel(train,(-7.5,-2.35,.70),(6.2,-2.35,.70))
    # Two coat silhouettes walk on the recessed sidewalk. Alternating hip and
    # shoulder pivots are genuine keyed motion; they stay outside the doorway.
    pedestrians=[];limbs=[]
    skin=mat('Pedestrian skin',(.28,.18,.125),rough=.8)
    for i,(x0,x1,y,col) in enumerate([(1.2,2.15,-.68,(.11,.045,.035)),(5.8,4.65,-.8,(.035,.07,.10))]):
        rig=empty(f'Entry_Pedestrian_{i}');pedestrians.append(rig);coat=mat(f'Coat_{i}',col,rough=.85)
        ball(f'Walker{i}_Coat',(0,0,.34),(.10,.07,.16),coat,parent=rig)
        ball(f'Walker{i}_Head',(0,0,.56),(.055,.052,.064),skin,parent=rig)
        for side,sgn in [('L',-1),('R',1)]:
            hip=empty(f'Walker{i}_{side}_Hip',(sgn*.045,0,.23),parent=rig)
            ball(f'Walker{i}_{side}_Leg',(0,0,-.105),(.026,.03,.115),coat,parent=hip)
            box(f'Walker{i}_{side}_Shoe',(0,-.025,-.21),(.055,.09,.035),tire,parent=hip,bevel=.012)
            shoulder=empty(f'Walker{i}_{side}_Shoulder',(sgn*.09,0,.44),parent=rig)
            ball(f'Walker{i}_{side}_Arm',(0,0,-.10),(.024,.026,.115),coat,parent=shoulder)
            limbs.extend([hip,shoulder])
            for f in range(1,61):
                angle=math.sin((f-1)*math.tau/18+i)*.38*sgn
                hip.rotation_euler.y=angle;hip.keyframe_insert(data_path='rotation_euler',frame=f)
                shoulder.rotation_euler.y=-angle*.65;shoulder.keyframe_insert(data_path='rotation_euler',frame=f)
            frames_linear(hip);frames_linear(shoulder)
        animate_travel(rig,(x0,y,.08),(x1,y,.08))
    camera=scene.camera;camera.data.type='PERSP';camera.data.lens=54;camera.data.sensor_width=36;camera.data.clip_start=.008;camera.data.clip_end=200
    # One continuous eased cubic approach. It has no intermediate zero-speed
    # holds and it descends over the foreground viaduct into the door gap.
    control=[Vector((0,-42,18.5)),Vector((1,-25,10.8)),Vector((3,-2.8,1.75)),Vector((3.28,-1.70,.99))]
    camera_positions=[]
    for f in range(1,61):
        u=((f-1)/59)**1.65;t=.5-.5*math.cos(math.pi*u)
        camera.location=sum((control[i]*c for i,c in enumerate([(1-t)**3,3*(1-t)**2*t,3*(1-t)*t*t,t**3])),Vector())
        target=Vector((2.96*(1-(1-t)**3),.03,.99+7.21*(1-t)**2))
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.keyframe_insert(data_path='location',frame=f);camera.keyframe_insert(data_path='rotation_euler',frame=f)
        camera.data.lens=54+2*t**4;camera.data.keyframe_insert(data_path='lens',frame=f)
        camera_positions.append(tuple(camera.location))
    frames_linear(camera)
    entrance_key=keylight(scene,'Entry_Entrance_Key',(3,-2.8,3.6),(1,.72,.45),95,2.5)
    # Tiny motivated local practicals; no radio/BT/Wi-Fi symbol or fake signal.
    for x in [2.37,3.63]:
        light=bpy.data.lights.new('Entry_Sconce_Practical','POINT');light.energy=4;light.color=(1,.65,.32);light.shadow_soft_size=.10
        ob=bpy.data.objects.new(light.name,light);scene.collection.objects.link(ob);ob.location=(x,-.55,1.37)
    source_settings={o.name:(tuple(o.data.color),o.data.energy) for o in scene.objects if o.type=='LIGHT'}
    world_strength=scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value
    def theme(day):
        for name,values in base_shader.items():
            sh=materials[name].node_tree.nodes['Principled BSDF']
            for socket,value in values.items():sh.inputs[socket].default_value=value
            if day and name.startswith('window'):
                sh.inputs['Base Color'].default_value=(.12,.17,.18,1);sh.inputs['Emission Strength'].default_value=.05
            elif day and name in ['shop-warm','lamp-warm','civic-lamp']:sh.inputs['Emission Strength'].default_value=.05
        for ob in scene.objects:
            if ob.type!='LIGHT':continue
            color,energy=source_settings[ob.name];ob.data.color=color;ob.data.energy=energy
            if day:
                if ob.name=='Moon_key':ob.data.color=(1,.89,.74);ob.data.energy=3400
                elif ob.name=='Urban_fill':ob.data.energy=1200
                elif ob.name=='Roof_rim':ob.data.energy=800
                elif ob.name.startswith('Street_practical'):ob.data.energy=0
                elif ob.name.startswith('Entry_'):ob.data.energy=energy*.22
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55 if day else world_strength
        warm.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.20 if day else 2
        cyan.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=.15 if day else .65
    # Measure the authored motion and each separate closed prop. The imported
    # city has its own existing architectural gate; it is not re-exported.
    sys.path.insert(0,str(args.audit_scripts.resolve()));import bx_audit
    checks=[{'name':o.name,**bx_audit.deliverable([o],profile='render')} for o in authored]
    failures=[r for r in checks if not r['pass']]
    if failures:raise RuntimeError(json.dumps(failures))
    (source/'mesh-audit.json').write_text(json.dumps({'parts':len(checks),'pass':True,'errors':0,'warnings':sum(len(r['warnings']) for r in checks),'gates':checks},indent=2)+'\n',encoding='utf8')
    deltas=[(Vector(camera_positions[i])-Vector(camera_positions[i-1])).length for i in range(1,60)]
    motion={'camera_positions':camera_positions,'distance':sum(deltas),'max_step':max(deltas),'nonzero_interior_steps':all(d>0 for d in deltas),'camera_transform_keys':60,
            'door_hinges':2,'car_rigs':2,'metro_rigs':1,'walking_rigs':2,'swinging_limbs':len(limbs),'frames':60,'fps':24,'duration_seconds':2.5,
            'camera_progress_power':1.65,'black_tail_target_frames':3,
            'beats':[{'frame':1,'beat':'wide city matching Home footprint'},{'frame':16,'beat':'descending approach, urban parallax'},{'frame':31,'beat':'street life, portal recognition'},{'frame':46,'beat':'street-level portal approach'},{'frame':56,'beat':'portal fills the view'},{'frame':60,'beat':'opaque dark vestibule threshold'}]}
    (source/'motion-audit.json').write_text(json.dumps(motion,indent=2)+'\n',encoding='utf8')
    theme(False);scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(source/'radio-entry.blend'),compress=True)
    contract={'schema':1,'resolution':[800,480],'frames':60,'fps':24,'duration_seconds':2.5,'codec':'VP8','container':'WebM','alpha':True,'audio':False,
              'first_frame':'Wide perspective city near Home lower208px framing; root applies subtle transition rather than assuming exact orthographic match.',
              'end_frame':'Opaque dark vestibule fills view before Radio handoff.','weather':'No sky/celestial/weather pixels. Transparent footage retains actual live sky underneath.',
              'city_source_sha256':old_hash,'door_world':{'center':[3,-.3,.99],'original_radio_center':[3,.64],'front_face_y':.04},
              'signal':'No decorative service beacons or fake device/audio-state emissions in clip.','builder_sha256':digest(Path(__file__))}
    (source/'contract.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
    # Stage gate: five full-size keys before any full-sequence rendering.
    for day in [True,False]:
        name='day' if day else 'night';theme(day)
        frames=KEYS if args.preview_only else range(1,61)
        folder=private/name;folder.mkdir(exist_ok=True)
        for f in frames:
            scene.frame_set(f);scene.render.filepath=str(folder/f'{f:04d}.png');bpy.ops.render.render(write_still=True,scene=scene.name)
            if f in [1,31,46,60]:
                # Keep only small review keys in source; full raw frames stay
                # ignored. Native800 review frames are retained privately.
                im=N.read_rgba(Path(scene.render.filepath))
                small=im[::2,::2];N.save_rgba(f'key-{name}-{f}',small,source/f'key-{name}-{f:02d}.png')
    if not args.preview_only:
        outputs=[]
        for name in ['day','night']:
            path=out/f'radio-entry-{name}-v1.webm'
            cmd=[str(args.ffmpeg),'-hide_banner','-y','-framerate','24','-i',str(private/name/'%04d.png'),'-c:v','libvpx','-pix_fmt','yuva420p','-auto-alt-ref','0','-lag-in-frames','0','-crf','12','-b:v','1800k','-deadline','good','-cpu-used','2','-an',str(path)]
            result=subprocess.run(cmd,capture_output=True,text=True);(private/f'encode-{name}.log').write_text(result.stderr,encoding='utf8');result.check_returncode()
            outputs.append({'name':path.name,'bytes':path.stat().st_size,'sha256':digest(path)})
        contract['assets']=outputs;contract['encoded_bytes']=sum(p['bytes'] for p in outputs)
        (source/'build-report.json').write_text(json.dumps(contract,indent=2)+'\n',encoding='utf8')
    assert digest(old)==old_hash
    print('RESULT '+json.dumps({'preview_only':args.preview_only,'contract':contract,'mesh_parts':len(checks),'motion':{k:v for k,v in motion.items() if k!='camera_positions'}}),flush=True)


if __name__=='__main__':main()
