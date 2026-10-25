"""Blender-authored sky assets for PySH; does not alter the VariantaBack scene.

blender -b --factory-startup --python-exit-code 1 -P this_file -- --root REPO
Moon surface reuses the credited NASA SVS reference already in this repository.
All models, procedural cloud volumes and stars are authored locally, seed 231127.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys

import bpy
import numpy as np
from mathutils import Vector


def mesh(name,vertices,faces,material,scene):
    data=bpy.data.meshes.new(name)
    data.from_pydata(vertices,[],faces)
    data.validate();data.update()
    obj=bpy.data.objects.new(name,data)
    scene.collection.objects.link(obj)
    data.materials.append(material)
    obj['pysh_authored_sky']=True
    return obj


def sphere(name,scene,material,center=(0,0,0),scale=(1,1,1),segments=64,rings=32):
    vertices=[(center[0],center[1],center[2]-scale[2])]
    for ring in range(1,rings):
        phi=math.pi*ring/rings
        for side in range(segments):
            angle=side*math.tau/segments
            vertices.append((center[0]+scale[0]*math.sin(phi)*math.cos(angle),center[1]+scale[1]*math.sin(phi)*math.sin(angle),center[2]-scale[2]*math.cos(phi)))
    vertices.append((center[0],center[1],center[2]+scale[2]))
    faces=[]
    for side in range(segments):faces.append((0,1+(side+1)%segments,1+side))
    for ring in range(rings-2):
        for side in range(segments):
            a=1+ring*segments+side;b=1+ring*segments+(side+1)%segments
            faces.append((a,b,b+segments,a+segments))
    end=len(vertices)-1;start=end-segments
    for side in range(segments):faces.append((start+side,start+(side+1)%segments,end))
    obj=mesh(name,vertices,faces,material,scene)
    for face in obj.data.polygons:face.use_smooth=True
    return obj


def material(name,color,emission=0,roughness=.85):
    result=bpy.data.materials.new(name)
    shader=result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value=(*color,1)
    shader.inputs['Roughness'].default_value=roughness
    shader.inputs['Specular IOR Level'].default_value=.1
    shader.inputs['Emission Color'].default_value=(*color,1)
    shader.inputs['Emission Strength'].default_value=emission
    return result


def scene(name,width,height):
    result=bpy.data.scenes.new(name)
    result.render.engine='BLENDER_EEVEE'
    result.render.resolution_x=width;result.render.resolution_y=height;result.render.resolution_percentage=100
    result.render.image_settings.file_format='PNG';result.render.image_settings.color_mode='RGBA';result.render.image_settings.compression=60
    result.render.film_transparent=True
    result.world=bpy.data.worlds.new(name+'_world')
    result.world.use_nodes=True
    result.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    result.view_settings.view_transform='AgX'
    bpy.context.window.scene=result
    return result


def camera(target_scene,position,target,scale):
    data=bpy.data.cameras.new(target_scene.name+'_Camera')
    ob=bpy.data.objects.new(data.name,data);target_scene.collection.objects.link(ob)
    ob.location=position;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;target_scene.camera=ob
    return ob


def lamp(target_scene,name,kind,position,color,energy,size=5):
    data=bpy.data.lights.new(name,kind);data.color=color;data.energy=energy
    if kind=='AREA':data.shape='DISK';data.size=size
    if kind=='SUN':data.angle=.009
    ob=bpy.data.objects.new(name,data);target_scene.collection.objects.link(ob)
    ob.location=position;ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob


def render(target_scene,path):
    bpy.context.window.scene=target_scene
    target_scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True,scene=target_scene.name)


def soften_alpha(target_scene,pixels=1):
    tree=bpy.data.node_groups.new(target_scene.name+'_Soft_Alpha','CompositorNodeTree')
    tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor')
    layers=tree.nodes.new('CompositorNodeRLayers');layers.scene=target_scene
    blur=tree.nodes.new('CompositorNodeBlur')
    blur.inputs['Type'].default_value='Gaussian'
    blur.inputs['Size'].default_value=(pixels,pixels)
    tree.links.new(layers.outputs['Image'],blur.inputs['Image'])
    output=tree.nodes.new('NodeGroupOutput');tree.links.new(blur.outputs['Image'],output.inputs['Image'])
    target_scene.compositing_node_group=tree
    target_scene.render.use_compositing=True


def finish_sprite(path,sigma=1,solar_halo=False):
    """Blender offline composite: filter premultiplied pixels, not straight RGB.

    Filtering straight RGBA can amplify near-transparent bright volume samples
    into a speckled white fringe. A quiet alpha floor removes that sampling noise.
    """
    source=bpy.data.images.load(str(path),check_existing=False)
    width,height=source.size
    rgba=np.asarray(source.pixels[:],dtype=np.float32).reshape(height,width,4)
    def blur(values,radius):
        extent=math.ceil(radius*3)
        positions=np.arange(-extent,extent+1,dtype=np.float32)
        kernel=np.exp(-positions**2/(2*radius**2));kernel/=kernel.sum()
        result=values
        for axis in (0,1):
            padding=[(0,0)]*values.ndim;padding[axis]=(extent,extent)
            padded=np.pad(result,padding,mode='constant')
            result=np.apply_along_axis(lambda row:np.convolve(row,kernel,mode='valid'),axis,padded)
        return result
    alpha=blur(rgba[:,:,3],sigma)
    premultiplied=blur(rgba[:,:,:3]*rgba[:,:,3:4],sigma)
    color=np.divide(premultiplied,alpha[:,:,None],out=np.zeros_like(premultiplied),where=alpha[:,:,None]>.0001)
    edge=np.clip((alpha-.006)/.035,0,1);edge=edge*edge*(3-2*edge)
    cleaned=alpha*edge
    if solar_halo:
        halo=.09*blur(cleaned,5)*(1-cleaned)
        combined=cleaned+halo
        color=np.divide(color*cleaned[:,:,None]+np.asarray([.95,.63,.2])*halo[:,:,None],combined[:,:,None],out=np.zeros_like(color),where=combined[:,:,None]>.0001)
        cleaned=combined
    output=bpy.data.images.new(path.stem+'_finished',width=width,height=height,alpha=True)
    output.colorspace_settings.name='sRGB'
    output.pixels.foreach_set(np.dstack((color,cleaned)).astype(np.float32).ravel())
    output.filepath_raw=str(path);output.file_format='PNG';output.save()
    bpy.data.images.remove(source);bpy.data.images.remove(output)


def atlas(paths,columns,destination):
    images=[bpy.data.images.load(str(path),check_existing=False) for path in paths]
    width,height=images[0].size
    rows=math.ceil(len(images)/columns)
    pixels=np.zeros((rows*height,columns*width,4),dtype=np.float32)
    for index,image in enumerate(images):
        # Blender pixel rows start at the bottom; CSS atlas indexing starts at top.
        x=index%columns;y=rows-1-index//columns
        pixels[y*height:(y+1)*height,x*width:(x+1)*width]=np.asarray(image.pixels[:],dtype=np.float32).reshape(height,width,4)
    output=bpy.data.images.new(destination.stem,width=columns*width,height=rows*height,alpha=True)
    output.colorspace_settings.name='sRGB'
    output.pixels.foreach_set(pixels.ravel())
    output.filepath_raw=str(destination);output.file_format='PNG';output.save()
    for image in images:bpy.data.images.remove(image)
    return [columns*width,rows*height]


def moon(root,out,private):
    target=scene('PySH_3D_Moon',144,144)
    matte=material('Lunar_regolith',(.58,.58,.56),roughness=1)
    shader=matte.node_tree.nodes.get('Principled BSDF')
    tex=matte.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image=bpy.data.images.load(str(root/'app/ui/public/assets/moon-surface-nasa.jpg'))
    tex.image.pack()
    neutral=matte.node_tree.nodes.new('ShaderNodeRGBToBW')
    matte.node_tree.links.new(tex.outputs['Color'],neutral.inputs['Color'])
    matte.node_tree.links.new(neutral.outputs['Val'],shader.inputs['Base Color'])
    earth=matte.node_tree.nodes.new('ShaderNodeMix')
    earth.data_type='RGBA';earth.blend_type='MULTIPLY';earth.inputs['Factor'].default_value=1
    matte.node_tree.links.new(tex.outputs['Color'],earth.inputs[6]);earth.inputs[7].default_value=(.07,.12,.18,1)
    matte.node_tree.links.new(earth.outputs[2],shader.inputs['Emission Color']);shader.inputs['Emission Strength'].default_value=.16
    bump=matte.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.006
    height=matte.node_tree.nodes.new('ShaderNodeTexImage')
    height.image=tex.image.copy();height.image.name='NASA_reference_relief_noncolor';height.image.colorspace_settings.name='Non-Color';height.image.pack()
    matte.node_tree.links.new(height.outputs['Color'],bump.inputs['Height']);matte.node_tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    body=sphere('Moon_Geometry',target,matte,segments=128,rings=64)
    uv=body.data.uv_layers.new(name='NASA_front_projection')
    for polygon in body.data.polygons:
        for index in polygon.loop_indices:
            vertex=body.data.vertices[body.data.loops[index].vertex_index].co
            uv.data[index].uv=(.5+vertex.x*.425,.5+vertex.z*.425)
    camera(target,(0,-6,0),(0,0,0),2.2)
    sun=lamp(target,'Physical_solar_illumination','SUN',(0,-7,0),(.94,.97,1),2.2)
    target.view_settings.exposure=.8
    # Weak earthshine leaves a genuinely dark unlit limb, not a second full Moon.
    lamp(target,'Earthshine','AREA',(0,-5,0),(.38,.47,.62),20,6)
    frames=[]
    target.frame_start=0;target.frame_end=127;target.render.fps=24
    for index in range(128):
        phase=index/128*math.tau
        # phase0=new,32=firstquarter,64=full,96=lastquarter; +X is waxing.
        sun.location=(7*math.sin(phase),7*math.cos(phase),0)
        sun.rotation_euler=(-sun.location).to_track_quat('-Z','Y').to_euler()
        sun.keyframe_insert(data_path='location',frame=index)
        sun.keyframe_insert(data_path='rotation_euler',frame=index)
        target.frame_set(index)
        path=private/f'moon-{index:03}.png';render(target,path);frames.append(path)
    dimensions=atlas(frames,16,out/'moon-phases-blender-v1.png')
    target['phase_layout']='16 columns,8 rows;128 phases;0=new,32=firstquarter,64=full,96=lastquarter'
    target['surface_credit']='NASA SVS/Ernie Wright; existing credited reference, packed in source'
    return {'frames':128,'tile':[144,144],'atlas':dimensions,'max_illumination_rounding_error':math.pi/256}


def cloud_volume():
    mat=bpy.data.materials.new('Procedural_cloud_water_droplets')
    tree=mat.node_tree;tree.nodes.clear()
    out=tree.nodes.new('ShaderNodeOutputMaterial')
    volume=tree.nodes.new('ShaderNodeVolumePrincipled')
    volume.inputs['Color'].default_value=(.83,.88,.92,1)
    volume.inputs['Anisotropy'].default_value=.35
    coordinates=tree.nodes.new('ShaderNodeTexCoord')
    noise=tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.8;noise.inputs['Detail'].default_value=4;noise.inputs['Roughness'].default_value=.67
    geometry=tree.nodes.new('ShaderNodeNewGeometry')
    tree.links.new(geometry.outputs['Position'],noise.inputs['Vector'])
    ramp=tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.36;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.73;ramp.color_ramp.elements[1].color=(2.6,2.6,2.6,1)
    tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac'])
    # A smooth radial falloff removes the hard primitive-container boundary.
    distance=tree.nodes.new('ShaderNodeVectorMath');distance.operation='DISTANCE';distance.inputs[1].default_value=(.5,.5,.5)
    tree.links.new(coordinates.outputs['Generated'],distance.inputs[0])
    edge=tree.nodes.new('ShaderNodeMapRange');edge.clamp=True;edge.interpolation_type='SMOOTHERSTEP';edge.inputs['From Min'].default_value=.17;edge.inputs['From Max'].default_value=.5;edge.inputs['To Min'].default_value=1;edge.inputs['To Max'].default_value=0
    tree.links.new(distance.outputs['Value'],edge.inputs['Value'])
    density=tree.nodes.new('ShaderNodeMath');density.operation='MULTIPLY'
    tree.links.new(ramp.outputs['Color'],density.inputs[0]);tree.links.new(edge.outputs['Result'],density.inputs[1]);tree.links.new(density.outputs['Value'],volume.inputs['Density'])
    tree.links.new(volume.outputs['Volume'],out.inputs['Volume'])
    return mat


def clouds(out):
    rng=random.Random(231127)
    target=scene('PySH_3D_Cloud_Bank',768,256)
    # Cycles resolves the soft density edges without EEVEE's coarse volume tiles.
    target.render.engine='CYCLES';target.cycles.samples=96;target.cycles.use_denoising=True
    mat=cloud_volume()
    for index in range(11):
        if index<5:
            x=-3.1+index*1.45;peak=-.2;size=(rng.uniform(1.3,1.6),1.1,rng.uniform(.5,.7))
        else:
            x=[-2.65,-1.8,-1.1,.25,.9,2.2][index-5]
            peak=[.05,.7,.85,.48,.18,-.05][index-5]
            size=([.58,.8,.7,.6,.75,.45][index-5],.8,rng.uniform(.65,.9))
        sphere('Cloud_volume_'+str(index),target,mat,center=(x,rng.uniform(-.4,.4),peak),scale=size,segments=40,rings=24)
    camera(target,(0,-10,1.5),(0,0,0),10.7)
    key=lamp(target,'Day_sun','SUN',(-3,-4,7),(1,.95,.85),3.5)
    fill=lamp(target,'Sky_bounce','AREA',(4,4,5),(.5,.7,1),180,8)
    # Outdoor clouds receive hemispherical sky light even with transparent film.
    sky=target.world.node_tree.nodes['Background']
    sky.inputs['Color'].default_value=(.68,.8,1,1);sky.inputs['Strength'].default_value=.35
    soften_alpha(target,5)
    target.view_settings.exposure=1.15
    render(target,out/'clouds-day-blender-v1.png');finish_sprite(out/'clouds-day-blender-v1.png',1.2)
    key.data.color=(.57,.72,.94);key.data.energy=2.2;fill.data.energy=90;target.view_settings.exposure=.55
    sky.inputs['Color'].default_value=(.36,.5,.75,1);sky.inputs['Strength'].default_value=.07
    render(target,out/'clouds-night-blender-v1.png');finish_sprite(out/'clouds-night-blender-v1.png',1.2)
    return {'size':[768,256],'volumes':11,'density':'world-space procedural noise with smooth radial edge falloff','frames':2,'engine':'Cycles96samplesdenoised'}


def wing(name,scene,mat,outline,z=.04,thickness=.07):
    # Mirroring the span reverses winding; retain outward normals on both wings.
    if sum(outline[i][0]*outline[(i+1)%len(outline)][1]-outline[(i+1)%len(outline)][0]*outline[i][1] for i in range(len(outline)))<0:
        outline=list(reversed(outline))
    vertices=[(x,y,z) for x,y in outline]+[(x,y,z+thickness) for x,y in outline]
    count=len(outline)
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    return mesh(name,vertices,faces,mat,scene)


def aircraft(out,glider=False):
    kind='glider' if glider else 'airliner'
    target=scene('PySH_3D_'+kind,256,128)
    metal=material(kind+'_ivory',(.54,.62,.64),roughness=.48)
    dark=material(kind+'_cockpit',(.035,.07,.09),roughness=.35)
    blue=material(kind+'_tail',(.055,.18,.2),roughness=.5)
    sphere('Streamlined_fuselage',target,metal,scale=(3.15,.27 if glider else .42,.29 if glider else .43))
    sphere('Cockpit',target,dark,center=(1.7,0,.23),scale=(.55,.23,.18))
    for side in [-1,1]:
        span=4.4 if glider else 3.4
        wing('Main_wing_'+str(side),target,metal,[(.55,side*.15),(-.45,side*.15),(-2.0,side*span),(-1.5,side*span)])
        wing('Tailplane_'+str(side),target,metal,[(-2,.05*side),(-2.9,.05*side),(-3.15,side*1.18),(-2.74,side*1.18)],z=.25,thickness=.045)
        if not glider:
            sphere('Engine_'+str(side),target,metal,center=(.2,side*1.27,-.35),scale=(.76,.22,.22))
            sphere('Engine_intake_'+str(side),target,dark,center=(.86,side*1.27,-.35),scale=(.025,.18,.18))
    mesh('Vertical_tail', [(-2.1,-.06,.2),(-3.05,-.06,.2),(-3.05,-.06,1.35),(-2.65,-.06,1.35),(-2.1,.06,.2),(-3.05,.06,.2),(-3.05,.06,1.35),(-2.65,.06,1.35)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],blue,target)
    camera(target,(1,-8,7),(0,0,.1),12.6 if glider else 10.5)
    key=lamp(target,'Aircraft_sun','AREA',(-3,-4,7),(1,.95,.84),1100,5)
    fill=lamp(target,'Aircraft_fill','AREA',(3,1,5),(.5,.72,.9),450,6)
    render(target,out/(kind+'-day-blender-v1.png'))
    key.data.color=(.55,.7,1);key.data.energy=480;fill.data.energy=130
    render(target,out/(kind+'-night-blender-v1.png'))
    from bpy_extras.object_utils import world_to_camera_view
    def project(point):
        value=world_to_camera_view(target,target.camera,Vector(point))
        return [round(value.x*256,3),round((1-value.y)*128,3)]
    wing_pairs=[(project((-1.75,side*span*.965,.1)),project((.05,side*.32,.1)),side) for side in [-1,1]]
    wing_pairs.sort(key=lambda pair:pair[0][1])
    anchors={'nose':project((3.12,0,0)),'tail':project((-3.1,0,0)),'upperWingTip':wing_pairs[0][0],'lowerWingTip':wing_pairs[1][0],'upperWingRoot':wing_pairs[0][1],'lowerWingRoot':wing_pairs[1][1]}
    return {'size':[256,128],'wings_sweep_toward_tail':True,'nose_axis':'+X','kind':kind,'rasterAnchors':anchors,'upperLight':'port-red' if wing_pairs[0][2]<0 else 'starboard-green','lowerLight':'port-red' if wing_pairs[1][2]<0 else 'starboard-green'}


def stars(out,private):
    target=scene('PySH_3D_Star_Glint',48,48)
    core=material('Stellar_core',(.83,.93,1),emission=3)
    ray=material('Stellar_optical_glint',(.35,.57,.75),emission=1)
    sphere('Unresolved_stellar_point',target,core,scale=(.36,.36,.36),segments=32,rings=16)
    glints=[]
    for axis in range(4):
        angle=axis*math.pi/2
        x,z=math.cos(angle),math.sin(angle)
        points=[(-z*.022,-.01,x*.022),(x*.9,0,z*.9),(z*.022,.01,-x*.022)]
        glints.append(mesh('Glint_ray_'+str(axis),points,[(0,1,2)],ray,target))
    camera(target,(0,-3,0),(0,0,0),2.3)
    frames=[]
    for index,scale in enumerate([.24,.45,.7,1]):
        for glint in glints:glint.scale=(scale,scale,scale)
        path=private/f'star-{index}.png';render(target,path);frames.append(path)
    return {'size':atlas(frames,2,out/'star-glints-blender-v1.png'),'frames':4,'tile':[48,48]}


def sun(out):
    target=scene('PySH_3D_Sun',192,192)
    target.render.engine='CYCLES';target.cycles.samples=64;target.cycles.use_denoising=True
    mat=material('Solar_photosphere',(1,.9,.65),emission=6)
    tree=mat.node_tree;shader=tree.nodes.get('Principled BSDF')
    geometry=tree.nodes.new('ShaderNodeNewGeometry')
    facing=tree.nodes.new('ShaderNodeVectorMath');facing.operation='DOT_PRODUCT';facing.inputs[1].default_value=(0,-1,0)
    tree.links.new(geometry.outputs['Normal'],facing.inputs[0])
    color=tree.nodes.new('ShaderNodeValToRGB');color.color_ramp.elements[0].color=(.65,.48,.2,1);color.color_ramp.elements[1].color=(1,.96,.75,1)
    tree.links.new(facing.outputs['Value'],color.inputs['Fac']);tree.links.new(color.outputs['Color'],shader.inputs['Base Color']);tree.links.new(color.outputs['Color'],shader.inputs['Emission Color'])
    noise=tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
    bump=tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.08;bump.inputs['Distance'].default_value=.008
    tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);tree.links.new(bump.outputs['Normal'],shader.inputs['Normal'])
    sphere('Photosphere_sphere',target,mat,segments=96,rings=48)
    camera(target,(0,-6,0),(0,0,0),2.5);soften_alpha(target,1)
    render(target,out/'sun-blender-v1.png');finish_sprite(out/'sun-blender-v1.png',.65,solar_halo=True)
    return {'size':[192,192],'limb_darkening':True,'corona':'quiet deterministic Blender offline alpha composite','surface':'procedural fine granulation'}


def meteor(out):
    target=scene('PySH_3D_Meteor_Streak',256,32)
    material_tail=material('Meteor_optical_trail',(.38,.65,.85),emission=1)
    tree=material_tail.node_tree;shader=tree.nodes.get('Principled BSDF')
    coordinates=tree.nodes.new('ShaderNodeTexCoord');separate=tree.nodes.new('ShaderNodeSeparateXYZ');tree.links.new(coordinates.outputs['Generated'],separate.inputs['Vector'])
    ramp=tree.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].color=(.7,.88,1,1);tree.links.new(separate.outputs['X'],ramp.inputs['Fac']);tree.links.new(ramp.outputs['Color'],shader.inputs['Emission Color'])
    vertices=[]
    for ring in range(20):
        x=-4.4+ring*8.6/19;radius=.003+.052*(ring/19)**1.6
        vertices.extend((x,math.cos(side*math.tau/12)*radius,math.sin(side*math.tau/12)*radius) for side in range(12))
    faces=[(ring*12+side,ring*12+(side+1)%12,(ring+1)*12+(side+1)%12,(ring+1)*12+side) for ring in range(19) for side in range(12)]
    mesh('Tapered_3D_optical_trail',vertices,faces,material_tail,target)
    core=material('Meteor_head',(.8,.94,1),emission=3);sphere('Meteor_leading_head',target,core,center=(4.2,0,0),scale=(.12,.08,.08),segments=24,rings=12)
    camera(target,(0,-4,0),(0,0,0),9.4)
    render(target,out/'meteor-blender-v1.png')
    return {'size':[256,32],'head_direction':'+X','head_relative_x':4.2/9.4+.5}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    opts=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);root=opts.root.resolve()
    out=root/'app/ui/public/ambient/sky3d';out.mkdir(parents=True,exist_ok=True)
    private=root/'.runtime/blender-sky';private.mkdir(parents=True,exist_ok=True)
    source=root/'assets/blender/sky3d';source.mkdir(parents=True,exist_ok=True)
    bpy.context.preferences.filepaths.save_version=0
    report={'blender':bpy.app.version_string,'seed':231127,'phase':moon(root,out,private),'clouds':clouds(out),'airliner':aircraft(out),'glider':aircraft(out,True),'stars':stars(out,private),'sun':sun(out),'meteor':meteor(out)}
    bpy.context.window.scene=bpy.data.scenes['PySH_3D_Moon']
    bpy.context.scene.frame_set(64)
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-ambient-sky-v1.blend'),compress=True)
    (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
