"""Standalone Blender Bluetooth rune and independently sequenced service waves.

No rectangular BT plate. Daytime tubes use dark cobalt/teal rather than pale
night emission. All twenty layers retain the installed v1 camera and crops.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from build_city_beacons import build as build_v1
from build_radio_neon import tube,read_rgba,save_rgba,blur,over

CROPS={'bluetooth':{'x':290,'y':45,'width':114,'height':105},'radio':{'x':908,'y':9,'width':119,'height':151}}
PARTS=['hardware','core','ring-1','ring-2','ring-3']
PALETTES={'day':{'bluetooth':(.007,.055,.25),'radio':(.006,.105,.085)},'night':{'bluetooth':(.025,.42,.98),'radio':(.20,.85,.57)}}


def collection(scene,name):
 c=bpy.data.collections.new(name);scene.collection.children.link(c);return c


def remove(obj,parts):
 parts.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)


def move(obj,col):
 for old in list(obj.users_collection):old.objects.unlink(obj)
 col.objects.link(obj)


def make_layers(scene):
 hardware,emission,parts=build_v1(scene);layers={}
 for name in hardware:
  layers[name]={'hardware':hardware[name]}
  for part in PARTS[1:]:layers[name][part]=collection(scene,f'{name}_{part}')
 for obj in list(parts):
  if obj.name.startswith(('BT_sign_outer_housing','BT_sign_dark_face','BT_engraved_glyph','BT_lit_glyph','BT_signal_arc','BT_connected_practical')):remove(obj,parts)
 # Extruded physical dark backing follows the rune alone; no filled panel.
 x=-8.1;y=-.165;z=7.25;points=[(x+dx,y,z+dz) for dx,dz in [(-.28,-.33),(.28,.28),(0,.54),(0,-.54),(.28,-.28),(-.28,.33)]]
 under=bpy.data.materials.new('BT_sculpted_back_bevel');sh=under.node_tree.nodes['Principled BSDF'];sh.inputs['Base Color'].default_value=(.012,.025,.043,1);sh.inputs['Metallic'].default_value=.48;sh.inputs['Roughness'].default_value=.32
 parts.append(tube('BT_open_rune_back_bevel',points,under,layers['bluetooth']['hardware'],.047))
 parts.append(tube('BT_open_rune_neon_core',[(px,py-.025,pz) for px,py,pz in points],bpy.data.materials['Bluetooth illuminated cobalt cyan'],layers['bluetooth']['core'],.035))
 for band in range(3):
  rr=.48+band*.18
  for side in [-1,1]:
   points=[(x+side*(rr*math.cos(-.62+1.24*j/24)+.035),y-.025,z+rr*.74*math.sin(-.62+1.24*j/24)) for j in range(25)]
   parts.append(tube(f'BT_open_wave_{band+1}_{side}',points,bpy.data.materials['Bluetooth illuminated cobalt cyan'],layers['bluetooth'][f'ring-{band+1}'],.031))
 for obj in list(emission['radio'].objects):
  if obj.name.startswith('Radio_transmission_arc'):
   band=int(obj.name.rsplit('_',1)[1]);move(obj,layers['radio'][f'ring-{band+1}'])
   # Old geometry was less than1px native. Reauthor closed tube wave at a
   # legible 0.032world radius, keeping the original camera/mast/crop.
   side=-1 if '_-1_' in obj.name else 1;rr=.31+band*.23
   points=[(3+side*(.09+rr*math.cos(-.62+1.24*j/24)),.51,8.18+rr*.62*math.sin(-.62+1.24*j/24)) for j in range(25)]
   remove(obj,parts);parts.append(tube(f'Radio_wave_{band+1}_{side}',points,bpy.data.materials['Radio transmission sage'],layers['radio'][f'ring-{band+1}'],.032))
  else:move(obj,layers['radio']['core'])
 return layers,parts


def palette(state):
 for name,material in [('bluetooth','Bluetooth illuminated cobalt cyan'),('radio','Radio transmission sage')]:
  sh=bpy.data.materials[material].node_tree.nodes['Principled BSDF'];color=PALETTES[state][name]
  sh.inputs['Base Color'].default_value=(*color,1);sh.inputs['Emission Color'].default_value=(*color,1)
  sh.inputs['Emission Strength'].default_value=.08 if state=='day' else 2.2
  sh.inputs['Metallic'].default_value=.08 if state=='day' else .15;sh.inputs['Roughness'].default_value=.55 if state=='day' else .30
 sh=bpy.data.materials['Radio obstruction lamp'].node_tree.nodes['Principled BSDF'];color=(.20,.035,.012) if state=='day' else (.95,.19,.075)
 sh.inputs['Base Color'].default_value=(*color,1);sh.inputs['Emission Color'].default_value=(*color,1);sh.inputs['Emission Strength'].default_value=.05 if state=='day' else 2.6


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--preview',action='store_true');p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
 args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve();source=root/'assets/blender/city-beacons-v2';source.mkdir(parents=True,exist_ok=True)
 out=root/'app/ui/public/ambient';private=root/'.runtime/city-beacons-v2-20261024';private.mkdir(parents=True,exist_ok=True)
 oldpath=root/'assets/blender/pysh-gothic-city-v2.blend';source_hash=hashlib.sha256(oldpath.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(oldpath));bpy.context.preferences.filepaths.save_version=0
 old=bpy.data.scenes['PySH_Gothic_City_v2'];scene=bpy.data.scenes.new('PySH_Open_Service_Beacons_v2');bpy.context.window.scene=scene
 scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24 if args.preview else 64
 scene.render.resolution_x=1600;scene.render.resolution_y=570;scene.render.resolution_percentage=100;scene.render.film_transparent=True
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=100;scene.view_settings.view_transform='AgX'
 scene.world=bpy.data.worlds.new('Service_beacon_world_v2');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
 scene.camera=old.camera.copy();scene.camera.data=old.camera.data.copy();scene.collection.objects.link(scene.camera)
 ld=bpy.data.lights.new('Cool rooftop sky key','AREA');ld.color=(.65,.78,1);ld.energy=900;ld.shape='DISK';ld.size=8
 key=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(key);key.location=(0,-10,15);key.rotation_euler=(Vector((0,0,5))-key.location).to_track_quat('-Z','Y').to_euler()
 practical=bpy.data.lights.new('Radio rooftop inspection practical','POINT');practical.color=(.36,.59,.69);practical.energy=24;practical.shadow_soft_size=.30
 ob=bpy.data.objects.new(practical.name,practical);scene.collection.objects.link(ob);ob.location=(3,-.25,7.15)
 layers,parts=make_layers(scene);bpy.context.view_layer.update()
 for name,collections in layers.items():
  crop=CROPS[name]
  for col in collections.values():
   for ob in col.objects:
    for vertex in ob.data.vertices:
     v=world_to_camera_view(scene,scene.camera,ob.matrix_world@vertex.co);px,py=v.x*1600,(1-v.y)*570
     assert crop['x']+2<=px<=crop['x']+crop['width']-2 and crop['y']+2<=py<=crop['y']+crop['height']-2,(name,px,py)
 layouts={name:{'crop_px':crop,'crop_percent':{'left':crop['x']/16,'top':crop['y']/5.7,'width':crop['width']/16,'height':crop['height']/5.7},'parts':PARTS,'filename':f'city-beacon-{name}-{{part}}-{{day|night}}-v2.png'} for name,crop in CROPS.items()}
 (source/'layout.json').write_text(json.dumps({'schema':2,'resolution':[1600,570],'props':layouts},indent=2)+'\n',encoding='utf-8');print('LAYOUT '+json.dumps(layouts),flush=True)
 arrays={};assets=[]
 for state in ['day','night']:
  palette(state);ld.energy=1250 if state=='day' else 900;ld.color=(1,.94,.83) if state=='day' else (.65,.78,1);practical.energy=0 if state=='day' else 24;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6 if state=='day' else .18
  for name,collections in layers.items():
   crop=CROPS[name];x,y,w,h=(crop[k] for k in ['x','y','width','height'])
   for part in PARTS:
    for prop,cols in layers.items():
     for role,col in cols.items():col.hide_render=(prop!=name or role!=part)
    scene.render.filepath=str(private/f'{name}-{part}-{state}-raw.png');bpy.ops.render.render(write_still=True,scene=scene.name);image=read_rgba(Path(scene.render.filepath))
    if state=='night' and part!='hardware':
     halo=np.zeros_like(image);halo[:,:,:3]=PALETTES[state][name];halo[:,:,3:4]=np.minimum(.25,blur(image[:,:,3:4],1.1)*.35+blur(image[:,:,3:4],2.5)*.17);image=over(halo,image)
    arrays[name,part,state]=image;path=out/f'city-beacon-{name}-{part}-{state}-v2.png';save_rgba(name,image[y:y+h,x:x+w],path)
    assets.append({'name':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgba_decoded_bytes':w*h*4})
 # Editable source demonstrates staggered travelling-band opacity intent.
 for cols in layers.values():
  for col in cols.values():col.hide_render=False
 palette('night');scene.render.fps=24;scene.frame_start=1;scene.frame_end=97
 for name,cols in layers.items():
  for band in range(3):
   rig=bpy.data.objects.new(f'{name}_travelling_wave_{band+1}',None);cols[f'ring-{band+1}'].objects.link(rig)
   rig.location=(-8.1,-.19,7.25) if name=='bluetooth' else (3,.51,8.18)
   for obj in [o for o in cols[f'ring-{band+1}'].objects if o.type=='MESH']:
    world=obj.matrix_world.copy();obj.parent=rig;obj.matrix_world=world
   for frame,value in [(1,1),(9+band*8,1),(21+band*8,1.015),(33+band*8,1),(97,1)]:rig.scale=(value,1,value);rig.keyframe_insert(data_path='scale',frame=frame)
 scene.frame_set(1);scene['no_solid_bluetooth_background']=True;scene['state_contract']='Core and wave layers separately gated by real powered/connected/playing status. No fake PCM data. Daydarkcobalt/teal, nightcyan/sage.'
 bpy.ops.wm.save_as_mainfile(filepath=str(source/'open-service-beacons-v2.blend'),compress=True)
 sys.path.insert(0,str(args.audit_scripts.resolve()));import bx_audit
 gates=[{'name':o.name,**bx_audit.deliverable([o],profile='render')} for o in parts];assert all(g['pass'] for g in gates)
 (source/'mesh-audit.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
 for state in ['day','night']:
  basepath=out/f'gothic-city-{state}-v3.png';base=read_rgba(basepath);bg=np.zeros_like(base);bg[:,:,:3]=(.62,.70,.73) if state=='day' else (.055,.09,.12);bg[:,:,3]=1;base=over(bg,base)
  for fog in [False,True]:
   for connected in [False,True]:
    image=base.copy()
    if fog:
     veil=np.zeros_like(image);veil[:,:,:3]=(.68,.73,.74);veil[:,:,3]=np.linspace(.25,.66,570)[:,None];image=over(image,veil)
    for name in layers:
     image=over(image,arrays[name,'hardware',state])
     if connected:
      image=over(image,arrays[name,'core',state])
      for part in PARTS[2:]:
       wave=arrays[name,part,state].copy();wave[:,:,3]*=.75;image=over(image,wave)
    path=private/f'{state}-{"fog" if fog else "clear"}-{"connected" if connected else "idle"}-full.png';save_rgba('Review',image,path)
    im=bpy.data.images.load(str(path));im.scale(800,208);im.filepath_raw=str(path).replace('-full.png','-native.png');im.save();bpy.data.images.remove(im)
    if connected:
     combined=image.copy();levels=[.55,.60,.48,.62,.54,.57,.59,.52]
     for index,level in enumerate(levels):
      neonpath=out/f'radio-neon-{"day-" if state=="day" else ""}zone-{index+1:02d}.png'
      if neonpath.exists():
       small=read_rgba(neonpath);layer=np.zeros_like(combined);layer[136:417,909:1027]=small;layer[:,:,3]*=level;combined=over(combined,layer)
     combinedpath=private/f'{state}-{"fog" if fog else "clear"}-combined-full.png';save_rgba('Review_Combined',combined,combinedpath)
     im=bpy.data.images.load(str(combinedpath));im.scale(800,208);im.filepath_raw=str(combinedpath).replace('-full.png','-native.png');im.save();bpy.data.images.remove(im)
 report={'schema':2,'blender':bpy.app.version_string,'samples':scene.eevee.taa_render_samples,'preview':args.preview,'layouts':layouts,'parts':len(parts),'vertices':sum(len(o.data.vertices) for o in parts),'triangles':sum(len(f.vertices)-2 for o in parts for f in o.data.polygons),'assets':assets,'encoded_bytes':sum(e['bytes'] for e in assets),'rgba_decoded_bytes':sum(e['rgba_decoded_bytes'] for e in assets),'no_solid_bluetooth_background':True,'day_palette':PALETTES['day'],'night_palette':PALETTES['night'],'audit':{'pass':True,'scope':'closed props separately','errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates)},'source_city_sha256':source_hash,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':'Offline authored geometry; runtime travelling opacity/state/lifecycle and actual native performance remain separate acceptance.'}
 assert report['encoded_bytes']<=180000 and report['rgba_decoded_bytes']<=1300000;assert hashlib.sha256(oldpath.read_bytes()).hexdigest()==source_hash
 (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
