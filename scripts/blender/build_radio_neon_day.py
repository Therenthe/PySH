"""Daylight material variant of the original Blender radio facade tubes.

No original geometry, camera, night source or night PNG is modified. Run one
headless Blender process with factory startup, --python-exit-code 1 and --root.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import numpy as np

sys.path.insert(0,str(Path(__file__).parent))
import build_radio_neon as N

# Linear material values: dark stained teal, cobalt, plum and brass, with a
# restrained self-lit core. Day contrast comes from mounted dark tubing rather
# than a pale night emission reduced by a second presentation gain.
PALETTE=[(.004,.045,.055),(.004,.025,.08),(.014,.019,.10),(.055,.009,.052),
         (.065,.012,.045),(.005,.035,.065),(.004,.045,.04),(.10,.035,.004)]
CROP={'x':909,'y':136,'width':118,'height':281}


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def native_preview(image):
    """Bilinear inspection resize only; never used for runtime assets."""
    h,w=image.shape[:2]
    xs=np.clip((np.arange(800)+.5)*w/800-.5,0,w-1)
    ys=np.clip((np.arange(208)+.5)*h/208-.5,0,h-1)
    x0=xs.astype(int);y0=ys.astype(int);x1=np.minimum(x0+1,w-1);y1=np.minimum(y0+1,h-1)
    fx=(xs-x0)[None,:,None];fy=(ys-y0)[:,None,None]
    top=image[y0[:,None],x0[None,:]]*(1-fx)+image[y0[:,None],x1[None,:]]*fx
    bottom=image[y1[:,None],x0[None,:]]*(1-fx)+image[y1[:,None],x1[None,:]]*fx
    return top*(1-fy)+bottom*fy


def review_composite(base, overlays, levels, fog=False):
    bg=np.zeros_like(base);bg[:,:,:3]=(.52,.56,.58);bg[:,:,3]=1
    if fog:
        base=base.copy();base[:,:,3]*=.77
    result=N.over(bg,base)
    if fog:
        veil=np.zeros_like(base);veil[:,:,:3]=(.66,.72,.74)
        yy=np.linspace(0,1,base.shape[0])[:,None]
        veil[:,:,3]=np.clip((yy-.12)/.88,0,1)*.20
        result=N.over(result,veil)
    for overlay,level in zip(overlays,levels):
        a=overlay.copy();a[:,:,3]*=level;result=N.over(result,a)
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
    args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve()
    source=root/'assets/blender/radio-neon-day';source.mkdir(parents=True,exist_ok=True)
    private=root/'.runtime/radio-neon-day-blender';private.mkdir(parents=True,exist_ok=True)
    review_private=root/'.runtime/radio-bt-20261024/day-authoring-review';review_private.mkdir(parents=True,exist_ok=True)
    out=root/'app/ui/public/ambient';original=root/'assets/blender/radio-neon/radio-neon-wrap.blend'
    protected=[original,*[out/f'radio-neon-zone-{i+1:02d}.png' for i in range(8)]]
    protected_hashes={str(p.relative_to(root)):sha(p) for p in protected}
    bpy.ops.wm.open_mainfile(filepath=str(original));bpy.context.preferences.filepaths.save_version=0
    s=bpy.data.scenes['PySH_Radio_Neon_Wrap'];bpy.context.window.scene=s
    s.name='PySH_Radio_Neon_Day';s.render.resolution_percentage=100;s.render.image_settings.compression=100
    s.eevee.taa_render_samples=64;s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.08
    zones=[bpy.data.collections[f'NEON_ZONE_{i+1:02d}'] for i in range(8)]
    tubes=[o for c in zones for o in c.objects if o.type=='MESH']
    assert len(tubes)==45
    geometry_before={o.name:hashlib.sha256(np.asarray([v.co[:] for v in o.data.vertices],dtype=np.float64).tobytes()).hexdigest() for o in tubes}
    # Keep all existing geometry and transform values. Day paint/shader is the
    # only asset change; original collection practicals are disabled in this
    # separate file so their night intent keys cannot whiten the day tubes.
    for i,col in enumerate(zones):
        for ob in col.objects:
            if ob.type=='LIGHT':ob.data.animation_data_clear();ob.data.energy=0
            elif ob.type=='MESH':
                mat=ob.data.materials[0]
                if not mat.name.startswith('Day_'):mat.name='Day_'+mat.name
                sh=mat.node_tree.nodes['Principled BSDF']
                sh.inputs['Base Color'].default_value=(*PALETTE[i],1)
                sh.inputs['Emission Color'].default_value=(*PALETTE[i],1)
                sh.inputs['Emission Strength'].default_value=.28
                sh.inputs['Roughness'].default_value=.46
                sh.inputs['Metallic'].default_value=.25
    ld=bpy.data.lights.new('Day_Facade_Soft_Key','AREA');ld.energy=220;ld.shape='DISK';ld.size=7
    key=bpy.data.objects.new(ld.name,ld);s.collection.objects.link(key);key.location=(1,-6,8)
    from mathutils import Vector
    key.rotation_euler=(Vector((3,0,3))-key.location).to_track_quat('-Z','Y').to_euler()
    s['authoring']='Separate daylight shader variant; original 45 mounted tube meshes and camera remain exact.'
    s['runtime']='Same real PCM temporal pairs as night. No automatic light cycle. No second day attenuation.'
    s.frame_set(7)
    overlays=[];assets=[]
    for i,col in enumerate(zones):
        for j,c in enumerate(zones):c.hide_render=(i!=j)
        raw=private/f'raw-day-{i+1:02d}.png';s.render.filepath=str(raw);bpy.ops.render.render(write_still=True,scene=s.name)
        arr=N.read_rgba(raw)
        # A subpixel, dark local halo supports antialiasing without recreating
        # a night bloom cloud. RGB is taken from the Blender-rendered material.
        alpha=arr[:,:,3:4];halo=np.zeros_like(arr)
        halo[:,:,:3]=np.asarray(PALETTE[i])[None,None,:]*1.7
        halo[:,:,3:4]=np.clip(N.blur(alpha,.7)*.14,0,.12)
        finished=N.over(halo,arr);overlays.append(finished)
        crop=finished[CROP['y']:CROP['y']+CROP['height'],CROP['x']:CROP['x']+CROP['width']]
        path=out/f'radio-neon-day-zone-{i+1:02d}.png';N.save_rgba(path.stem,crop,path)
        assets.append({'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path),'width':118,'height':281})
    for col in zones:col.hide_render=False
    assert geometry_before=={o.name:hashlib.sha256(np.asarray([v.co[:] for v in o.data.vertices],dtype=np.float64).tobytes()).hexdigest() for o in tubes}
    sys.path.insert(0,str(args.audit_scripts.resolve()));import bx_audit
    gates=[{'name':ob.name,**bx_audit.deliverable([ob],profile='render')} for ob in tubes]
    assert all(g['pass'] for g in gates)
    (source/'mesh-audit.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf8')
    bpy.ops.wm.save_as_mainfile(filepath=str(source/'radio-neon-day.blend'),compress=True)
    city=out/'gothic-city-day-v3.png';base=N.read_rgba(city)
    # Illustrative samples near the currently measured .35–.39 temporal peaks.
    # These are review gains only, never runtime animation/data substitutes.
    for name,levels in [('low',[.30,.38,.24,.42,.33,.28,.36,.31]),('measured',[.55,.60,.48,.62,.54,.57,.59,.52]),('full',[1]*8)]:
        for fog in [False,True]:
            image=review_composite(base,overlays,levels,fog)
            stem=f'day-{name}-'+('fog' if fog else 'clear')
            N.save_rgba(name,image,review_private/(stem+'.png'))
            target=source if name=='measured' else review_private
            N.save_rgba(name+'_native',native_preview(image),target/(stem+'-native.png'))
    report={'schema':1,'blender':bpy.app.version_string,'source_night_sha256':sha(original),'city_day_v3_sha256':sha(city),
            'city_resolution':[1600,570],'crop_px':CROP,'crop_percent':{'left':56.8125,'top':136/5.7,'width':7.375,'height':281/5.7},
            'zones':8,'tubes':45,'mesh_vertices':sum(len(o.data.vertices) for o in tubes),'triangles':sum(len(f.vertices)-2 for o in tubes for f in o.data.polygons),
            'palette_linear':PALETTE,'emission_strength':.28,'day_runtime_gain':1,'halo_sigma_px':.7,'halo_alpha_max':.12,
            'assets':assets,'encoded_bytes':sum(a['bytes'] for a in assets),'rgba_decoded_bytes':118*281*4*8,
            'geometry_unchanged':True,'night_protected_hashes':protected_hashes,'audit':{'pass':True,'parts':45,'errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates)},
            'signal_contract':'Eight adjacent pairs of 16 measured temporal PCM amplitudes; no frequency-band claim, no synthetic runtime loop.',
            'limits':'Review fog is a documented illustrative veil, not a live weather screenshot. Actual runtime visibility/signal must be verified separately.',
            'builder_sha256':sha(Path(__file__)),'helper_sha256':sha(Path(N.__file__))}
    assert report['encoded_bytes']<=70000
    assert all(sha(root/path)==value for path,value in protected_hashes.items())
    (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
