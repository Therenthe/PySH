"""Offline Blender neon facade, aligned to the existing city-v2 camera.

Eight independent, cropped RGBA layers are driven by real audio at runtime;
the keyed light sequence in the source is an authoring demonstration only.
No city/sky/source asset is replaced. Run headless/factory with --root REPO.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zlib

import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view


PALETTE = [(0.08,.86,.65),(.055,.72,.82),(.16,.53,.94),(.43,.28,.86),
           (.58,.31,.84),(.18,.66,.76),(.08,.83,.61),(.84,.51,.16)]


def material(name, color, strength=3.8):
    mat=bpy.data.materials.new(name)
    sh=mat.node_tree.nodes['Principled BSDF']
    sh.inputs['Base Color'].default_value=(*color,1)
    sh.inputs['Emission Color'].default_value=(*color,1)
    sh.inputs['Emission Strength'].default_value=strength
    sh.inputs['Roughness'].default_value=.3
    return mat


def tube(name, points, mat, collection, radius=.020):
    curve=bpy.data.curves.new(name, 'CURVE');curve.dimensions='3D'
    curve.resolution_u=2;curve.bevel_depth=radius;curve.bevel_resolution=2
    curve.use_fill_caps=True
    spl=curve.splines.new('POLY');spl.points.add(len(points)-1)
    for p,co in zip(spl.points,points):p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);collection.objects.link(obj)
    curve.materials.append(mat)
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    bpy.ops.object.convert(target='MESH');obj=bpy.context.view_layer.objects.active
    obj.select_set(False)
    for p in obj.data.polygons:p.use_smooth=True
    obj['pysh_original_geometry']=True
    return obj


def blur(a, sigma):
    ext=math.ceil(sigma*3);p=np.arange(-ext,ext+1,dtype=np.float32)
    k=np.exp(-p*p/(2*sigma*sigma));k/=k.sum()
    result=a
    for axis in (0,1):
        padding=[(0,0)]*a.ndim;padding[axis]=(ext,ext)
        result=np.apply_along_axis(lambda r:np.convolve(r,k,mode='valid'),axis,np.pad(result,padding))
    return result


def save_rgba(name, arr, path):
    h,w,_=arr.shape
    # Preserve Blender's baked display RGB and straight alpha verbatim. Saving
    # a generated float Image datablock unpremultiplies it a second time on
    # this Blender version, whitening the low-alpha neon. PNG is only a
    # lossless encoding here; geometry and lighting were rendered by Blender.
    pixels=np.round(np.clip(arr,0,1)*255).astype(np.uint8)
    pixels[pixels[:,:,3]==0,:3]=0
    raw=b''.join(b'\0'+row.tobytes() for row in pixels)
    def chunk(kind,data):
        return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data)&0xffffffff)
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw,9))+chunk(b'IEND',b''))


def read_rgba(path):
    im=bpy.data.images.load(str(path),check_existing=False)
    im.colorspace_settings.name='Non-Color'
    w,h=im.size;a=np.asarray(im.pixels[:],dtype=np.float32).reshape(h,w,4)
    bpy.data.images.remove(im)
    return np.flipud(a).copy()


def over(dst, src):
    sa=src[:,:,3:4];da=dst[:,:,3:4]
    a=sa+da*(1-sa)
    rgb=np.divide(src[:,:,:3]*sa+dst[:,:,:3]*da*(1-sa),np.maximum(a,1e-8))
    return np.concatenate((rgb,a),axis=2)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path)
    p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve()
    source=root/'assets/blender/radio-neon';source.mkdir(parents=True,exist_ok=True)
    out=root/'app/ui/public/ambient';private=root/'.runtime/radio-neon-blender';private.mkdir(parents=True,exist_ok=True)
    existing=root/'assets/blender/pysh-gothic-city-v2.blend'
    source_hash=hashlib.sha256(existing.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(existing))
    bpy.context.preferences.filepaths.save_version=0
    old=bpy.data.scenes['PySH_Gothic_City_v2']
    scene=bpy.data.scenes.new('PySH_Radio_Neon_Wrap');bpy.context.window.scene=scene
    scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=48
    scene.render.resolution_x=1600;scene.render.resolution_y=570;scene.render.resolution_percentage=100
    scene.render.film_transparent=True;scene.render.image_settings.file_format='PNG'
    scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8'
    scene.render.image_settings.compression=100
    scene.world=bpy.data.worlds.new('Neon_Unlit_World');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=0
    scene.view_settings.view_transform='AgX'
    scene.camera=old.camera.copy();scene.camera.data=old.camera.data.copy();scene.collection.objects.link(scene.camera)
    zones=[];all_tubes=[];lights=[]
    x0=2.19;w=1.62;face=-.165
    # Eight bays carry a continuous waveform; its three repeats wrap the
    # facade at studio-floor heights. Side returns and crown contours attach
    # the light to the existing art-deco mass rather than floating in the sky.
    for i in range(8):
        col=bpy.data.collections.new(f'NEON_ZONE_{i+1:02d}');scene.collection.children.link(col)
        mat=material(f'Neon_Zone_{i+1:02d}',PALETTE[i]);parts=[]
        left=x0+i*w/8;right=x0+(i+1)*w/8
        for row,z in enumerate([2.10,3.05,4.12]):
            points=[]
            for j in range(19):
                x=left+(right-left)*j/18
                u=(x-x0)/w
                # Oscillating tube physically fixed to masonry. Runtime only
                # modulates its intensity using measured temporal audio.
                wave=math.sin(u*math.tau*3.0)*(.12+.14*math.sin(u*math.pi)**2)
                points.append((x,face,z+wave))
            parts.append(tube(f'Zone_{i+1:02d}_Wave_{row}',points,mat,col,.020))
        # Segmented lower and upper cornices carry the same real audio pair.
        for level in [1.56,4.94]:
            parts.append(tube(f'Zone_{i+1:02d}_Cornice_{level}',[(left,face-.008,level),(right-.012,face-.008,level)],mat,col,.017))
        if i in (0,7):
            x=left if i==0 else right
            parts.append(tube(f'Zone_{i+1:02d}_Corner',[(x,face+.45,1.56),(x,face,1.56),(x,face,4.94),(x,face+.45,4.94)],mat,col,.022))
        # Upper setbacks follow the actual crown sizes, one part on each side.
        if i in (1,3,5):
            tier=(i-1)//2;tw=1.7*(.78-tier*.19)
            yy=.64-(.88-tier*.16)/2-.035;zz=5.3+tier*.26+.23
            parts.append(tube(f'Zone_{i+1:02d}_Crown_{tier}',[(3-tw/2,yy+.24,zz),(3-tw/2,yy,zz),(3+tw/2,yy,zz),(3+tw/2,yy+.24,zz)],mat,col,.018))
        # A local practical light, keyed only for source-scene intent tests.
        ld=bpy.data.lights.new(f'Zone_{i+1:02d}_Facade_Reflection','POINT');ld.color=PALETTE[i];ld.shadow_soft_size=.16
        ob=bpy.data.objects.new(ld.name,ld);col.objects.link(ob);ob.location=((left+right)/2,face-.18,3.3)
        for frame,energy in [(1,0),(7,5+i),(11,1.2),(17,7-i*.4),(25,0)]:
            ld.energy=energy;ld.keyframe_insert(data_path='energy',frame=frame)
        lights.append(ob)
        zones.append({'collection':col,'parts':parts,'light':ob});all_tubes.extend(parts)
    scene.render.fps=24;scene.frame_start=1;scene.frame_end=25;scene.frame_set(7)
    bpy.context.view_layer.update()
    verts=[ob.matrix_world@v.co for ob in all_tubes for v in ob.data.vertices]
    projected=[world_to_camera_view(scene,scene.camera,v) for v in verts]
    # Locked padding leaves ample alpha for the 3 px near-glow and 6 px aura.
    pad=12
    minx=max(0,math.floor(min(v.x for v in projected)*1600)-pad)
    maxx=min(1600,math.ceil(max(v.x for v in projected)*1600)+pad)
    miny=max(0,math.floor(min(1-v.y for v in projected)*570)-pad)
    maxy=min(570,math.ceil(max(1-v.y for v in projected)*570)+pad)
    crop={'x':minx,'y':miny,'width':maxx-minx,'height':maxy-miny}
    meta={'schema':1,'city_resolution':[1600,570],'crop_px':crop,
          'crop_percent':{'left':minx/16,'top':miny/5.7,'width':crop['width']/16,'height':crop['height']/5.7},
          'assets':[f'radio-neon-zone-{i+1:02d}.png' for i in range(8)],
          'signal':'Each zone is one adjacent pair of the 16 real temporal audio bins; not a frequency spectrum or automatic loop.',
          'source_city_sha256':source_hash,'radio_building':{'index':10,'world_center':[3,.64],'height':5.3,'width':1.7,'facade_y':.04},
          'night_gain':1,'day_gain':.20,'transparent':True}
    (source/'layout.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf8')
    print('LAYOUT '+json.dumps(meta),flush=True)
    scene['authoring']='Original Blender tubular facade neon, motivated local facade practicals; independent measured-audio zones.'
    scene['runtime_animation']='No authored runtime auto-cycle. Keyed light energies are source-intent samples only.'
    scene['crop_px']=list(crop.values())
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'radio-neon-wrap.blend'),compress=True)
    # Stage 1 is literal geometry with no image-space glow. The complete source
    # remains editable; only the isolated transparent overlay is exported.
    render=bpy.ops.render.render
    rendered=[];combined=np.zeros((570,1600,4),dtype=np.float32)
    for i,zone in enumerate(zones):
        for j,z in enumerate(zones):z['collection'].hide_render=(i!=j)
        scene.render.filepath=str(private/f'raw-{i+1:02d}.png');render(write_still=True,scene=scene.name)
        a=read_rgba(Path(scene.render.filepath))
        # Blender offline finishing works in premultiplied display RGBA. A
        # short local halo supplies the baked practical spill; no page filter,
        # live blur or large GPU layer is required on the Raspberry.
        alpha=a[:,:,3:4];premul=a[:,:,:3]*alpha
        soft=blur(alpha,1.5)*.50+blur(alpha,4.0)*.34
        glow=np.zeros_like(a);glow[:,:,:3]=np.asarray(PALETTE[i])[None,None,:]*1.5
        glow[:,:,3:4]=np.clip(soft,0,.42)
        finished=over(glow,a)
        combined=over(combined,finished)
        cropped=finished[miny:maxy,minx:maxx]
        path=out/meta['assets'][i];save_rgba(f'Neon_Baked_{i+1}',cropped,path)
        rendered.append({'name':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgba_decoded_bytes':crop['width']*crop['height']*4})
    for z in zones:z['collection'].hide_render=False
    save_rgba('Neon_All_Composite',combined,source/'all-zones-overlay.png')
    base=read_rgba(out/'gothic-city-night-v2.png');composite=over(base,combined)
    save_rgba('City_Neon_Review_Full',composite,source/'city-neon-review.png')
    # Full-size crop and a city native-height test are both inspection assets.
    save_rgba('Neon_Facade_Review',composite[max(0,miny-20):min(570,maxy+20),max(0,minx-40):min(1600,maxx+40)],source/'facade-review.png')
    sys.path.insert(0,str(args.audit_scripts.resolve()))
    import bx_audit
    # Each tube is a separately mounted closed prop. Architectural gaps between
    # separate tubes are intentional, so run the closed-part gate per tube.
    gates=[{'name':ob.name,**bx_audit.deliverable([ob],profile='render')} for ob in all_tubes]
    assert all(g['pass'] for g in gates),json.dumps([g for g in gates if not g['pass']])
    report={**meta,'blender':bpy.app.version_string,'zones':8,'tubes':len(all_tubes),'mesh_vertices':sum(len(o.data.vertices) for o in all_tubes),
            'triangles':sum(len(f.vertices)-2 for o in all_tubes for f in o.data.polygons),'materials':8,'source_intent_practical_lights':8,
            'assets':rendered,'encoded_bytes':sum(a['bytes'] for a in rendered),'rgba_decoded_bytes':sum(a['rgba_decoded_bytes'] for a in rendered),
            'audit':{'profile':'render','scope':'each separately mounted closed tube, not city architecture','parts':len(gates),'pass':True,'errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates)},
            'limits':'Offline raster overlay; no realtime Blender/WebGL. Runtime/native signal and performance acceptance separate. Local halo approximates reflected practical spill, not a dynamic relight of the existing city.',
            'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (source/'mesh-audit.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf8')
    (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'radio-neon-wrap.blend'),compress=True)
    assert hashlib.sha256(existing.read_bytes()).hexdigest()==source_hash
    print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
