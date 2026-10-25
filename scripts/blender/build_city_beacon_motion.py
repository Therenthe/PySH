"""Genuine Blender Bluetooth turn and router-free rooftop Wi-Fi waves.

The rune rotates as closed 3D geometry about its vertical axis. Static supports
do not turn. Four state/lighting atlases use the unchanged installed city camera.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from build_radio_neon import tube,read_rgba,save_rgba,blur,over
from build_city_wifi import arc

COUNT=32
DURATION=3.2
BT_CROP={'x':290,'y':45,'width':114,'height':105}
WIFI_CROP={'x':1116,'y':153,'width':73,'height':89}
PIVOT=(-8.1,-.165,7.25)
ANGLES=[math.tau*(.5-.5*math.cos(math.pi*i/(COUNT-1))) for i in range(COUNT)]
FRAMES=[1+round(i*77/(COUNT-1)) for i in range(COUNT)]


def collection(scene,name):
 col=bpy.data.collections.new(name);scene.collection.children.link(col);return col


def linked_copy(source,col,materials):
 obj=source.copy();obj.data=source.data.copy();obj.animation_data_clear();col.objects.link(obj)
 for i,material in enumerate(obj.data.materials):
  if material.name not in materials:materials[material.name]=material.copy()
  obj.data.materials[i]=materials[material.name]
 obj['pysh_original_mesh_source']=source.name
 return obj


def material(name,color,emission):
 mat=bpy.data.materials.new(name);node=mat.node_tree.nodes['Principled BSDF']
 node.inputs['Base Color'].default_value=(*color,1);node.inputs['Emission Color'].default_value=(*color,1)
 node.inputs['Emission Strength'].default_value=emission;node.inputs['Roughness'].default_value=.4
 return mat


def set_palette(state,materials,wifi_mat,key,world):
 color=(.007,.055,.25) if state=='day' else (.025,.42,.98)
 node=materials['Bluetooth illuminated cobalt cyan'].node_tree.nodes['Principled BSDF']
 node.inputs['Base Color'].default_value=(*color,1);node.inputs['Emission Color'].default_value=(*color,1)
 node.inputs['Emission Strength'].default_value=.08 if state=='day' else 2.2
 color=(.006,.105,.085) if state=='day' else (.20,.85,.57)
 node=wifi_mat.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=(*color,1);node.inputs['Emission Color'].default_value=(*color,1);node.inputs['Emission Strength'].default_value=.08 if state=='day' else 2.0
 key.data.energy=1250 if state=='day' else 900;key.data.color=(1,.94,.83) if state=='day' else (.65,.78,1)
 world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6 if state=='day' else .18


def finish(image,state,color):
 if state=='day':return image
 halo=np.zeros_like(image);halo[:,:,:3]=color
 halo[:,:,3:4]=np.minimum(.22,blur(image[:,:,3:4],1.05)*.30+blur(image[:,:,3:4],2.3)*.15)
 return over(halo,image)


def crop_render(scene,crop,path):
 x,y,w,h=(crop[k] for k in ['x','y','width','height'])
 scene.render.use_border=True;scene.render.use_crop_to_border=True
 scene.render.border_min_x=x/1600;scene.render.border_max_x=(x+w)/1600
 scene.render.border_min_y=(570-y-h)/570;scene.render.border_max_y=(570-y)/570
 scene.render.filepath=str(path);bpy.ops.render.render(write_still=True,scene=scene.name)
 image=read_rgba(path);assert image.shape==(h,w,4),(path,image.shape,crop)
 return image


def full_layer(crop,image):
 result=np.zeros((570,1600,4),dtype=np.float32);x,y,w,h=(crop[k] for k in ['x','y','width','height']);result[y:y+h,x:x+w]=image;return result


def native_review(root,private,state,glyphs,tile,support,wifi_images):
 # Controlled asset composition uses the actual original city/sky proportions.
 # It is an authored review, not an actual application screenshot.
 background=np.zeros((480,800,4),dtype=np.float32);background[:,:,3]=1
 top=np.array((.68,.77,.80) if state=='day' else (.035,.060,.095));bottom=np.array((.37,.49,.52) if state=='day' else (.065,.105,.125))
 for row in range(480):background[row,:,:3]=top+(bottom-top)*(row/479)
 city=read_rgba(root/f'app/ui/public/ambient/gothic-city-{state}-v3.png')
 base=city.copy()
 for fog in [False,True]:
  fogged=base.copy()
  if fog:
   veil=np.zeros_like(base);veil[:,:,:3]=(.68,.73,.74);veil[:,:,3]=np.linspace(.25,.66,570)[:,None];fogged=over(fogged,veil)
  for i in [0,7,10,15,23,31]:
   image=over(over(fogged,full_layer(BT_CROP,support)),full_layer(tile,glyphs[i]))
   for wave in wifi_images:image=over(image,full_layer(WIFI_CROP,wave))
   city_path=private/f'{state}-{"fog" if fog else "clear"}-pose-{i:02d}-city.png';save_rgba('Review_city',image,city_path)
   im=bpy.data.images.load(str(city_path));im.scale(800,208);im.filepath_raw=str(city_path).replace('-city.png','-city-native.png');im.save();bpy.data.images.remove(im)
   native_city=read_rgba(Path(str(city_path).replace('-city.png','-city-native.png')))
   native=background.copy();native[272:480]=over(native[272:480],native_city)
   save_rgba('Native_full_review',native,private/f'{state}-{"fog" if fog else "clear"}-pose-{i:02d}-800x480.png')


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',required=True,type=Path);parser.add_argument('--preview',action='store_true');parser.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve();source=root/'assets/blender/city-beacon-motion';source.mkdir(parents=True,exist_ok=True)
 out=root/'app/ui/public/ambient';private=root/'.runtime/city-beacon-motion-20261024';private.mkdir(parents=True,exist_ok=True)
 original=root/'assets/blender/city-beacons-v2/open-service-beacons-v2.blend';original_hash=hashlib.sha256(original.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(original));bpy.context.preferences.filepaths.save_version=0
 old=bpy.data.scenes['PySH_Open_Service_Beacons_v2'];scene=bpy.data.scenes.new('PySH_Bluetooth_Turn_WiFi_Waves');bpy.context.window.scene=scene
 scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24 if args.preview else 64
 scene.render.resolution_x=1600;scene.render.resolution_y=570;scene.render.resolution_percentage=100;scene.render.film_transparent=True
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=100;scene.view_settings.view_transform='AgX'
 scene.camera=old.camera.copy();scene.camera.data=old.camera.data.copy();scene.collection.objects.link(scene.camera)
 world=old.world.copy();scene.world=world
 ld=bpy.data.lights.new('Turn soft rooftop key','AREA');ld.shape='DISK';ld.size=8
 key=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(key);key.location=(0,-10,15);key.rotation_euler=(Vector((0,0,5))-key.location).to_track_quat('-Z','Y').to_euler()
 support_col=collection(scene,'BT_fixed_roof_support');rune_col=collection(scene,'BT_rotating_rune');wifi_cols=[collection(scene,f'WiFi_wave_{i+1}') for i in range(3)]
 materials={};supports=[];runes=[]
 for obj in old.objects:
  if obj.type!='MESH':continue
  if obj.name.startswith(('BT_mount_foot','BT_mount_post')):supports.append(linked_copy(obj,support_col,materials))
  elif obj.name.startswith(('BT_open_rune_back_bevel','BT_open_rune_neon_core')):runes.append(linked_copy(obj,rune_col,materials))
 assert len(supports)==3 and len(runes)==2
 # A second luminous tube behind the central sculpted stroke makes a designed
 # double-sided neon rune, rather than pretending a flat front remains visible.
 x,y,z=PIVOT;rear_points=[(x+dx,y+.025,z+dz) for dx,dz in [(-.28,-.33),(.28,.28),(0,.54),(0,-.54),(.28,-.28),(-.28,.33)]]
 rear=tube('BT_motion_rear_neon_core',rear_points,materials['Bluetooth illuminated cobalt cyan'],rune_col,.035);runes.append(rear)
 rig=bpy.data.objects.new('Bluetooth_genuine_vertical_turn',None);rune_col.objects.link(rig);rig.location=PIVOT;bpy.context.view_layer.update()
 for obj in runes:
  matrix=obj.matrix_world.copy();obj.parent=rig;obj.matrix_world=matrix
 scene.render.fps=24;scene.frame_start=1;scene.frame_end=78
 projected=[]
 for frame,angle in zip(FRAMES,ANGLES):
  rig.rotation_euler.z=angle;rig.keyframe_insert(data_path='rotation_euler',frame=frame);bpy.context.view_layer.update()
  for obj in runes:
   projected.extend(world_to_camera_view(scene,scene.camera,obj.matrix_world@v.co) for v in obj.data.vertices)
 # Trim only blank alpha around the rune; offset remains relative to old crop.
 pad=6;x0=math.floor(min(p.x for p in projected)*1600)-pad;x1=math.ceil(max(p.x for p in projected)*1600)+pad
 y0=math.floor(min(1-p.y for p in projected)*570)-pad;y1=math.ceil(max(1-p.y for p in projected)*570)+pad
 tile={'x':x0,'y':y0,'width':x1-x0,'height':y1-y0};assert tile['width']*COUNT<2048
 assert x0>=BT_CROP['x'] and y0>=BT_CROP['y'] and x1<=BT_CROP['x']+BT_CROP['width'] and y1<=BT_CROP['y']+BT_CROP['height']
 scene.frame_set(1)
 wifi_mat=material('Router_free_WiFi_wave',(.20,.85,.57),2)
 wifi=[]
 for i,radius in enumerate([.22,.43,.64]):
  obj=arc(f'WiFi_no_router_wave_{i+1}',radius,.068,(6.3,.295,5.24),wifi_mat)
  for col in list(obj.users_collection):col.objects.unlink(obj)
  wifi_cols[i].objects.link(obj);wifi.append(obj)
 bpy.context.view_layer.update()
 for obj in wifi:
  for vertex in obj.data.vertices:
   p=world_to_camera_view(scene,scene.camera,obj.matrix_world@vertex.co);px,py=p.x*1600,(1-p.y)*570
   assert WIFI_CROP['x']<=px<=WIFI_CROP['x']+WIFI_CROP['width'] and WIFI_CROP['y']<=py<=WIFI_CROP['y']+WIFI_CROP['height']
 layout={'schema':1,'resolution':[1600,570],'bluetooth':{'wrapper_crop':BT_CROP,'glyph_tile':tile,'tile_offset_in_wrapper':{'x':x0-BT_CROP['x'],'y':y0-BT_CROP['y']},'atlas':{'columns':COUNT,'rows':1,'width':COUNT*tile['width'],'height':tile['height'],'frame_count':COUNT,'duration_seconds':DURATION,'steps':COUNT-1,'first_last_front':True,'rotation_axis':'world Z','angles_radians':ANGLES},'files':{'atlas':'city-bluetooth-turn-{day|night}-{idle|connected}-v1.png','support':'city-bluetooth-support-{day|night}-motion-v1.png'}},'wifi':{'crop':WIFI_CROP,'roof_world':[6.3,.4,4.58],'wave_center_world':[6.3,.295,5.24],'hardware_visible':False,'lamp_visible':False,'files':'city-wifi-wave-{1|2|3}-{day|night}-motion-v1.png'}}
 (source/'layout.json').write_text(json.dumps(layout,indent=2)+'\n',encoding='utf-8');print('LAYOUT '+json.dumps(layout),flush=True)
 assets=[];review={}
 def export(name,image):
  path=out/name;save_rgba(name,image,path);assets.append({'name':name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'width':image.shape[1],'height':image.shape[0],'rgba_decoded_bytes':image.shape[0]*image.shape[1]*4})
 for state in ['day','night']:
  set_palette(state,materials,wifi_mat,key,world);rune_col.hide_render=True
  for col in wifi_cols:col.hide_render=True
  support_col.hide_render=False
  support=crop_render(scene,BT_CROP,private/f'support-{state}.png');export(f'city-bluetooth-support-{state}-motion-v1.png',support)
  support_col.hide_render=True;rune_col.hide_render=False;poses={}
  for connected in [False,True]:
   for obj in runes:obj.hide_render=('neon_core' in obj.name and not connected)
   atlas=np.zeros((tile['height'],tile['width']*COUNT,4),dtype=np.float32);frame_images=[]
   for i,frame in enumerate(FRAMES):
    scene.frame_set(frame);image=crop_render(scene,tile,private/f'{state}-{"connected" if connected else "idle"}-{i:02d}.png')
    if connected:image=finish(image,state,(.025,.42,.98))
    atlas[:,i*tile['width']:(i+1)*tile['width']]=image;frame_images.append(image)
   # Geometry at0/360 is exactly the same. Lock the duplicate endpoint to the
   # identical rendered first frame, avoiding temporal AA noise on the rest pose.
   atlas[:,-tile['width']:]=frame_images[0];frame_images[-1]=frame_images[0].copy()
   export(f'city-bluetooth-turn-{state}-{"connected" if connected else "idle"}-v1.png',atlas);poses[connected]=frame_images
  rune_col.hide_render=True
  wifi_images=[]
  for i,col in enumerate(wifi_cols):
   for other in wifi_cols:other.hide_render=(other!=col)
   image=crop_render(scene,WIFI_CROP,private/f'wifi-{state}-{i+1}.png');image=finish(image,state,(.20,.85,.57));wifi_images.append(image);export(f'city-wifi-wave-{i+1}-{state}-motion-v1.png',image)
  review[state]={'support':support,'poses':poses,'wifi':wifi_images}
  native_review(root,private,state,poses[True],tile,support,wifi_images)
 for obj in runes:obj.hide_render=False
 for col in [support_col,rune_col,*wifi_cols]:col.hide_render=False
 scene.frame_set(1);set_palette('night',materials,wifi_mat,key,world);scene.render.use_border=False;scene.render.use_crop_to_border=False
 scene['purpose']='Genuine vertical 3D Bluetooth turn with fixed posts, router-free WiFi wave bands. Runtime state/scheduling remain integration.'
 scene['motion_duration_seconds']=DURATION;scene['first_last_pose']='same exact front';scene['wifi_has_router_or_lamp']=False
 bpy.ops.wm.save_as_mainfile(filepath=str(source/'bluetooth-turn-wifi-waves.blend'),compress=True)
 sys.path.insert(0,str(args.audit_scripts.resolve()));import bx_audit
 owned=[*supports,*runes,*wifi];gates=[{'name':obj.name,**bx_audit.deliverable([obj],profile='render')} for obj in owned];assert all(g['pass'] for g in gates)
 (source/'mesh-audit.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
 report={'blender':bpy.app.version_string,'samples':scene.eevee.taa_render_samples,'layout':layout,'parts':len(owned),'vertices':sum(len(obj.data.vertices) for obj in owned),'triangles':sum(len(face.vertices)-2 for obj in owned for face in obj.data.polygons),'assets':assets,'encoded_bytes':sum(a['bytes'] for a in assets),'rgba_decoded_bytes':sum(a['rgba_decoded_bytes'] for a in assets),'first_last_pixels_identical':True,'post_transform_animated':False,'genuine_3d_axis':'Z','wifi_router_geometry':False,'wifi_lamp_geometry':False,'audit':{'pass':True,'errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates)},'source_beacons_sha256':original_hash,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':'Authored sprite animation, not realtime3D. State/lifecycle/schedule/reducedmotion and actual device performance require integration tests.'}
 assert report['rgba_decoded_bytes']<3300000 and report['encoded_bytes']<500000;assert hashlib.sha256(original.read_bytes()).hexdigest()==original_hash
 (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
