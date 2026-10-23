"""Original, Blender-authored aircraft miniatures, baked for the Pi compositor.

blender -b --factory-startup --python-exit-code 1 -P this_file -- --root REPO
No downloaded models, airline marks or runtime WebGL. Nose is +X/right, Z is up.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
import bmesh
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


def mat(name, color, metal=0.12, emission=0):
    material = bpy.data.materials.new(name)
    node = material.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color, 1)
    node.inputs['Metallic'].default_value = metal
    node.inputs['Roughness'].default_value = .37
    node.inputs['Emission Color'].default_value = (*color, 1)
    node.inputs['Emission Strength'].default_value = emission
    return material


def finish(obj, name, material, smooth=False):
    obj.name = name
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    bm = bmesh.new(); bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data); bm.free()
    for face in obj.data.polygons:
        face.use_smooth = smooth
    return obj


def ellipsoid(name, center, radius, material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=center)
    obj = bpy.context.object
    obj.scale = radius
    return finish(obj, name, material, True)


def prism(name, polygon, thickness, material, vertical=False):
    # Convex closed extruded planforms: actual airfoils/tail surfaces, not SVGs.
    if vertical:
        vertices = [(x, -thickness/2, z) for x,z in polygon] + [(x, thickness/2, z) for x,z in polygon]
    else:
        vertices = [(x,y,-thickness/2) for x,y in polygon] + [(x,y,thickness/2) for x,y in polygon]
    n = len(polygon)
    faces = [tuple(reversed(range(n))), tuple(range(n,2*n))]
    faces.extend((i, (i+1)%n, (i+1)%n+n, i+n) for i in range(n))
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces); data.update()
    obj = bpy.data.objects.new(name,data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    finish(obj,name,material)
    obj.select_set(False)
    bevel = obj.modifiers.new('Manufactured softened edges', 'BEVEL')
    bevel.width = min(thickness*.24,.035); bevel.segments = 2
    return obj


def tube(name, a, b, radius, material, end_radius=None):
    delta=Vector(b)-Vector(a)
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=radius,
                                  radius2=radius if end_radius is None else end_radius,
                                  depth=delta.length, location=(Vector(a)+Vector(b))/2)
    obj=bpy.context.object
    obj.rotation_euler=delta.to_track_quat('Z','Y').to_euler()
    return finish(obj,name,material,True)


def fuselage(name, rings, material):
    count=32
    vertices=[(x,ry*math.cos(i*math.tau/count),z+rz*math.sin(i*math.tau/count))
              for x,ry,rz,z in rings for i in range(count)]
    faces=[tuple(reversed(range(count))),tuple(range((len(rings)-1)*count,len(rings)*count))]
    faces.extend((j*count+i,j*count+(i+1)%count,(j+1)*count+(i+1)%count,(j+1)*count+i)
                 for j in range(len(rings)-1) for i in range(count))
    data=bpy.data.meshes.new(name); data.from_pydata(vertices,[],faces); data.update()
    obj=bpy.data.objects.new(name,data); bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active=obj; obj.select_set(True)
    finish(obj,name,material,True); obj.select_set(False)
    return obj


def add_wings(prefix, root, span, sweep, chord, tip_chord, z, material):
    result=[]
    for sign in (-1,1):
        leading=root; tip=root-sweep
        obj=prism(prefix+('_port' if sign<0 else '_starboard'),
                  [(leading,sign*.03),(tip,sign*span),(tip-tip_chord,sign*span),
                   (leading-chord,sign*.03)],.10,material)
        obj.location.z=z; result.append(obj)
    return result


def windows(length, radius, z, material, prefix):
    # Closed inset-like glazing patches intersect the body instead of hovering.
    for index in range(length):
        x=-2.7+index*.43
        ellipsoid(prefix+str(index),(x,-radius,z),(.10,.045,.105),material)


def airplane(kind, materials):
    white,navy,glass,metal,amber=materials
    nav={}
    if kind=='airliner':
        fuselage('Narrowbody_pressure_fuselage',[
            (-6,.045,.045,.05),(-5.5,.20,.22,.06),(-4.25,.49,.51,0),
            (-2.8,.56,.57,0),(3.5,.56,.57,0),(4.6,.46,.44,-.04),
            (5.4,.24,.24,-.10),(5.9,.025,.025,-.10)],white)
        add_wings('Swept_low_wing',1.1,5.1,2.5,2.65,.72,-.24,metal)
        add_wings('Swept_stabilizer',-4.05,2.15,.95,1.45,.40,.25,metal)
        fin=prism('Conventional_tail_fin',[(-5.6,.12),(-5.4,2.35),(-4.45,2.35),(-3.7,.12)],.17,navy,True)
        for sign in (-1,1):
            ellipsoid('Underwing_turbofan_'+str(sign),(.30,sign*1.72,-.68),(1.00,.35,.35),white)
            ellipsoid('Dark_engine_intake_'+str(sign),(1.08,sign*1.72,-.68),(.08,.29,.29),glass)
            # Pylon physically intersects wing/nacelle.
            tube('Engine_pylon_'+str(sign),(.1,sign*1.72,-.20),(.1,sign*1.72,-.5),.13,metal)
            tip=ellipsoid('Upturned_winglet_'+str(sign),(-1.95,sign*5.03,.05),(.27,.07,.38),navy)
        windows(17,.545,.16,glass,'Cabin_window_')
        ellipsoid('Flightdeck_glazing',(4.62,-.37,.18),(.51,.13,.19),glass)
        nav={'nose':(5.9,0,-.1),'tail':(-5.4,0,1.9),'port':(-1.8,-5.1,-.20),'starboard':(-1.8,5.1,-.20),
             'finTop':(-5.1,0,2.35),'finBase':(-5.1,0,.12)}
    elif kind=='turboprop':
        fuselage('Regional_tapered_fuselage',[
            (-4.8,.03,.03,.12),(-4.0,.20,.24,.08),(-2.6,.42,.46,0),
            (2.55,.43,.46,0),(3.35,.34,.33,-.08),(3.95,.06,.08,-.13)],white)
        add_wings('High_straight_wing',.85,4.7,.38,1.45,.81,.35,white)
        add_wings('T_tail_horizontal',-3.3,1.8,.45,1.12,.45,1.82,navy)
        prism('Tall_T_tail_fin',[(-4.45,.07),(-4.15,1.9),(-3.38,1.9),(-2.83,.07)],.14,navy,True)
        for sign in (-1,1):
            ellipsoid('Turboprop_nacelle_'+str(sign),(1.0,sign*1.75,.17),(.94,.23,.25),navy)
            tube('Spinner_'+str(sign),(1.4,sign*1.75,.17),(2.02,sign*1.75,.17),.17,metal,.015)
            # Two broad, crossed, true3D propeller blades remain legible at distance.
            for angle in (.2,math.pi/2+.2):
                p=tube('Propeller_blade_'+str(sign)+str(angle),(1.78,sign*1.75-.77*math.cos(angle),.17-.77*math.sin(angle)),
                       (1.78,sign*1.75+.77*math.cos(angle),.17+.77*math.sin(angle)),.045,metal)
        windows(12,.416,.12,glass,'Regional_window_')
        ellipsoid('Regional_flightdeck',(3.05,-.29,.12),(.48,.13,.19),glass)
        nav={'nose':(3.95,0,-.13),'tail':(-4.0,0,1.8),'port':(.1,-4.7,.35),'starboard':(.1,4.7,.35),
             'finTop':(-3.9,0,1.9),'finBase':(-3.9,0,.10)}
    else:
        fuselage('Business_jet_slender_fuselage',[
            (-4.9,.025,.025,.13),(-3.6,.24,.28,.04),(-2.1,.36,.38,0),
            (2.30,.36,.38,0),(3.20,.27,.28,-.04),(4.0,.015,.025,-.10)],white)
        add_wings('Business_swept_wing',.15,3.65,2.0,1.50,.43,-.13,white)
        add_wings('Business_T_tail',-3.5,1.62,.72,1.0,.32,1.60,navy)
        prism('Business_fin',[(-4.5,.10),(-4.25,1.65),(-3.60,1.65),(-2.9,.1)],.13,navy,True)
        for sign in (-1,1):
            ellipsoid('Rear_engine_'+str(sign),(-2.85,sign*.62,.38),(.84,.25,.25),metal)
            ellipsoid('Rear_intake_'+str(sign),(-2.12,sign*.62,.38),(.07,.20,.20),glass)
            tube('Rear_engine_mount_'+str(sign),(-2.7,sign*.2,.35),(-2.7,sign*.57,.35),.13,metal)
            ellipsoid('Business_winglet_'+str(sign),(-1.95,sign*3.6,.13),(.15,.055,.33),navy)
        windows(9,.351,.10,glass,'Business_window_')
        ellipsoid('Business_flightdeck',(2.85,-.23,.12),(.43,.10,.16),glass)
        nav={'nose':(4,0,-.1),'tail':(-4.25,0,1.6),'port':(-1.9,-3.6,-.1),'starboard':(-1.9,3.6,-.1),
             'finTop':(-3.9,0,1.65),'finBase':(-3.9,0,.1)}
    return nav,[]


def helicopter(kind, materials):
    white,navy,glass,metal,amber=materials
    police=kind=='police-helicopter'
    # Night footage must still read as police blue/white, rather than a black blob.
    body=mat('Police_blue_airframe',(.065,.25,.43),.22) if police else amber
    # Different airframe proportions, cabin/tail construction and equipment.
    ellipsoid('Police_twin_cabin' if police else 'TV_compact_cabin',(.55,0,0),(2.35,.77,.84) if police else (1.85,.69,.77),body)
    ellipsoid('Continuous_bubble_windscreen',(1.65,-.14,.24),(1.08,.70,.58),glass)
    ellipsoid('Roof_engine_cowling',(-.35,0,.74),(1.03,.43,.40),metal)
    tube('Tapered_tail_boom',(-1.25,0,.20),(-5.3,0,.66),.36,body,.09)
    fin=prism('Vertical_tail_fin',[(-5.65,.48),(-5.55,1.72),(-4.94,1.62),(-4.53,.5)],.12,body,True)
    add_wings('Tail_stabilizer',-4.2,.86,.15,.59,.38,.48,metal)
    for sign in (-1,1):
        tube('Skid_rail_'+str(sign),(-1.35,sign*.70,-1.12),(2.05,sign*.70,-1.12),.06,metal)
        tube('Skid_front_curve_'+str(sign),(2.05,sign*.7,-1.12),(2.39,sign*.7,-.95),.06,metal)
        for x in (-.8,1.25):
            tube('Skid_support_'+str(sign)+str(x),(x,sign*.40,-.45),(x,sign*.7,-1.12),.055,metal)
    tube('Rotor_mast',(-.25,0,.72),(-.25,0,1.74),.09,metal)
    ellipsoid('Rotor_hub',(-.25,0,1.74),(.24,.24,.13),metal)
    rotor=[]
    for blade in range(4):
        # Four physically modeled blades, rotated as rigid parts around the mast.
        ob=prism('Main_rotor_blade_'+str(blade),[(.08,-.10),(4.75,-.16),(4.75,.12),(.08,.12)],.035,metal)
        ob.location=(-.25,0,1.77); ob.rotation_euler.z=blade*math.pi/2
        rotor.append(ob)
    tube('Tail_rotor_axle',(-5.20,-.05,.88),(-5.20,-.24,.88),.07,metal)
    for angle in (0,math.pi/2):
        tube('Tail_rotor_'+str(angle),(-5.20-.57*math.cos(angle),-.25,.88-.57*math.sin(angle)),
             (-5.20+.57*math.cos(angle),-.25,.88+.57*math.sin(angle)),.045,metal)
    if police:
        # Distinct white cabin stripe, blue strobes and searchlight turret.
        ellipsoid('White_police_side_band',(.35,-.725,-.05),(1.45,.115,.25),white)
        ellipsoid('Stabilized_searchlight',(1.62,-.31,-.80),(.38,.34,.34),metal)
        ellipsoid('Searchlight_lens',(1.84,-.53,-.84),(.20,.17,.20),
                  mat('Warm_searchlight_lens',(.82,.75,.56),emission=.5))
        ellipsoid('Blue_roof_beacon',(.5,-.32,.88),(.17,.15,.13),mat('Blue_beacon',(.04,.25,.95),emission=2.4))
        ellipsoid('Police_sensor_gimbal',(.65,-.50,-.80),(.20,.20,.20),metal)
    else:
        ellipsoid('Broadcast_white_door',(.3,-.650,-.05),(.62,.07,.42),white)
        ellipsoid('Television_gyro_camera',(1.40,-.39,-.86),(.40,.37,.34),metal)
        ellipsoid('Camera_optics',(1.58,-.70,-.86),(.23,.10,.22),glass)
        tube('Microwave_antenna_stem',(-.95,0,.91),(-.95,0,1.35),.045,metal)
        ellipsoid('Microwave_broadcast_dish',(-.95,-.02,1.36),(.31,.09,.23),white)
    return {'nose':(2.7,0,.05),'tail':(-5.5,0,1.1),'beacon':(.5,-.32,.88),'rotor':(-.25,0,1.77),
            'rotorTop':(-.25,0,1.77),'skidBottom':(.5,-.7,-1.12)},rotor


def lighting(scene,night):
    for ob in [o for o in scene.objects if o.type=='LIGHT']:
        bpy.data.objects.remove(ob,do_unlink=True)
    for name,position,color,energy,size in [
        ('Sky_key',(2,-8,12),(.64,.77,1) if night else (1,.91,.75),1200 if night else 1900,9),
        ('Sky_fill',(-7,-4,2),(.36,.50,.74),430 if night else 700,8),
        ('Edge_sky',(-1,7,7),(.50,.67,1) if night else (.64,.79,1),1700 if night else 1700,7)]:
        data=bpy.data.lights.new(name,'AREA'); data.energy=energy; data.color=color; data.shape='DISK'; data.size=size
        ob=bpy.data.objects.new(name,data); scene.collection.objects.link(ob); ob.location=position
        ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.exposure=-.35 if night else .1


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--review',action='store_true'); parser.add_argument('--only',default='')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=args.root.resolve(); output=root/'app/ui/public/ambient/aircraft'; output.mkdir(parents=True,exist_ok=True)
    source=root/'assets/blender/aircraft'; source.mkdir(parents=True,exist_ok=True)
    review=root/'.runtime/aircraft-blender-review'; review.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    materials=(mat('Pearl_airframe',(.72,.78,.80)),mat('Deep_navy_livery',(.035,.13,.22)),
               mat('Smoked_blue_glazing',(.035,.10,.15),.45),mat('Brushed_aluminium',(.28,.36,.40),.58),
               mat('Broadcast_saffron',(.80,.36,.055)))
    variants=['airliner','turboprop','business-jet','tv-helicopter','police-helicopter']
    report={'schema':1,'blender':bpy.app.version_string,'contract':{'width':160,'height':80,'nose':'right','up':'image-top','travel_mirror':'scaleX only','helicopter_frames':3},'models':{}}
    for index,kind in enumerate(variants):
        if args.only and kind!=args.only: continue
        scene=bpy.data.scenes.new('PySH_aircraft_'+kind); bpy.context.window.scene=scene
        scene.render.engine='BLENDER_EEVEE'; scene.render.film_transparent=True
        scene.render.resolution_x=160; scene.render.resolution_y=80; scene.render.resolution_percentage=100
        scene.render.image_settings.file_format='PNG'; scene.render.image_settings.color_mode='RGBA'; scene.render.image_settings.compression=80
        scene.world=bpy.data.worlds.new(kind+'_sky'); scene.world.use_nodes=True
        scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.15
        scene.view_settings.view_transform='AgX'
        nav,rotor=helicopter(kind,materials) if 'helicopter' in kind else airplane(kind,materials)
        meshes=[o for o in scene.objects if o.type=='MESH']
        camera_data=bpy.data.cameras.new(kind+'_orthographic'); camera_data.type='ORTHO'
        camera=bpy.data.objects.new(kind+'_camera',camera_data); scene.collection.objects.link(camera)
        target=Vector((-.7,0,.25)) if rotor else Vector((0,0,.35))
        camera.location=target+Vector((0,-20,6.3 if not rotor else 5.0))
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        camera_data.ortho_scale=14.0 if kind=='airliner' else (13.0 if rotor else 11.4)
        scene.camera=camera; bpy.context.view_layer.update()
        # Per-part audit: intentional assemblies overlap; individual solids must be healthy.
        sys.path.append(str(Path.home()/'.codex/skills/scenario-blender-expert/scripts'))
        import bx_audit
        gates={ob.name:bx_audit.deliverable([ob],profile='render') for ob in meshes}
        errors=[{'object':n,'errors':g['errors']} for n,g in gates.items() if g['errors']]
        if errors: raise RuntimeError(json.dumps(errors))
        assembly=bx_audit.deliverable(meshes,profile='render')
        if assembly['errors']:
            raise RuntimeError(json.dumps({'model':kind,'assembly_errors':assembly['errors']}))
        files=[]
        for theme in ('day','night'):
            lighting(scene,theme=='night')
            for frame in range(3 if rotor else 1):
                for i,ob in enumerate(rotor): ob.rotation_euler.z=i*math.pi/2+frame*math.pi/6
                suffix=f'-{frame}' if rotor else ''
                path=output/f'{kind}-{theme}{suffix}-v1.png'
                scene.render.filepath=str(path); bpy.ops.render.render(write_still=True)
                image=bpy.data.images.load(str(path),check_existing=False)
                pixels=np.array(image.pixels[:]).reshape((80,160,4))
                yy,xx=np.where(pixels[:,:,3]>0)
                bounds=[int(xx.min()),int(79-yy.max()),int(xx.max()+1),int(80-yy.min())]
                bpy.data.images.remove(image)
                assert 0<bounds[0]<bounds[2]<160 and 0<bounds[1]<bounds[3]<80,(kind,frame,bounds)
                files.append({'path':path.relative_to(root).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                    'encoded_bytes':path.stat().st_size,'decoded_bytes':160*80*4,'alpha_bounds':bounds})
        for i,ob in enumerate(rotor): ob.rotation_euler.z=i*math.pi/2
        bpy.context.view_layer.update()
        projected={name:[round(point.x,5),round(1-point.y,5)] for name,position in nav.items()
                   for point in [world_to_camera_view(scene,camera,Vector(position))]}
        report['models'][kind]={'mesh_objects':len(meshes),'vertices':sum(len(o.data.vertices) for o in meshes),
            'polygons':sum(len(o.data.polygons) for o in meshes),'gate_errors':errors,
            'assembly_gate':assembly,'nav_points':projected,'files':files,
            'gate_scope':'closed parts and whole render assembly; not a watertight printable mesh'}
        if args.review:
            import bx_review
            bx_review.review(meshes,str(review/kind),views=('front','top','threequarter'),modes=('silhouette','matcap'),res=260)
            bpy.context.window.scene=scene
    blend=source/'pysh-aircraft-v1.blend'
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
    all_files=[f for model in report['models'].values() for f in model['files']]
    report['totals']={'sprite_count':len(all_files),'encoded_bytes':sum(f['encoded_bytes'] for f in all_files),'decoded_bytes':sum(f['decoded_bytes'] for f in all_files)}
    if not args.only:
        assert len(report['models'])==5 and len(all_files)==18
        assert report['totals']['decoded_bytes']<1024*1024
    report['blend_sha256']=hashlib.sha256(blend.read_bytes()).hexdigest()
    anchors={'width':160,'height':80,'nose':'right','models':{
        name:model['nav_points'] for name,model in report['models'].items()}}
    (output/'anchors-v1.json').write_text(json.dumps(anchors,indent=2)+'\n',encoding='utf-8')
    generated=root/'app/ui/src/aircraftAnchors.ts'
    generated.write_text('// Generated by scripts/blender/build_ambient_aircraft.py; do not edit.\n'
        +'export const aircraftAnchors = '+json.dumps(anchors['models'],indent=2)+' as const;\n',encoding='utf-8')
    (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('PYSH_AIRCRAFT_RESULT '+json.dumps(report['totals']))


if __name__=='__main__': main()
