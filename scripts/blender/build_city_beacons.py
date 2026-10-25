"""Original Blender radio mast and Bluetooth rooftop signal hardware.

Fixed city-v2 camera; cropped raster output avoids runtime WebGL. Runtime owns
state-dependent emission/pulse; keyed lights in source show animation intent.
"""
import argparse,hashlib,json,math,sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
sys.path.insert(0,str(Path(__file__).parent))
from build_radio_neon import tube,read_rgba,save_rgba,blur,over


def mat(name,color,emission=0,metal=.2):
 m=bpy.data.materials.new(name);s=m.node_tree.nodes['Principled BSDF']
 s.inputs['Base Color'].default_value=(*color,1);s.inputs['Metallic'].default_value=metal;s.inputs['Roughness'].default_value=.38
 s.inputs['Emission Color'].default_value=(*color,1);s.inputs['Emission Strength'].default_value=emission
 return m


def block(name,center,scale,material,col,bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=center);o=bpy.context.object;o.name=name;o.dimensions=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for c in list(o.users_collection):c.objects.unlink(o)
 col.objects.link(o);o.data.materials.append(material)
 if bevel:
  mod=o.modifiers.new('Machined edge','BEVEL');mod.width=bevel;mod.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
 o.select_set(False);return o


def build(scene):
 hardware={};emission={};all_parts=[]
 steel=mat('Brushed graphite',(.055,.085,.105),.02,.65)
 edge=mat('Alloy edge catches',(.20,.29,.32),.05,.65)
 glass=mat('Deep blue sign glass',(.012,.035,.065),.015,.3)
 engrave=mat('Unpowered Bluetooth glyph',(.20,.38,.48),.08,.3)
 cyan=mat('Bluetooth illuminated cobalt cyan',(.025,.43,1),4.2,.15)
 radio=mat('Radio transmission sage',(.20,.91,.59),3.6,.15)
 beacon=mat('Radio obstruction lamp',(.95,.19,.075),2.6,.15)
 for key in ['bluetooth','radio']:
  c=bpy.data.collections.new(key+'_hardware');scene.collection.children.link(c);hardware[key]=c
  c=bpy.data.collections.new(key+'_emission');scene.collection.children.link(c);emission[key]=c
 # Physical bracket and beveled housing rise from the existing Bluetooth roof.
 x=-8.1;y=-.02;z=7.25;c=hardware['bluetooth']
 all_parts.append(block('BT_mount_foot',(x,.4,6.40),(.66,.48,.12),steel,c))
 for dx in [-.29,.29]:
  all_parts.append(tube('BT_mount_post',[(x+dx,.4,6.4),(x+dx,.18,6.88)],edge,c,.035))
 all_parts.append(block('BT_sign_outer_housing',(x,y,z),(1.02,.16,1.35),edge,c,.08))
 all_parts.append(block('BT_sign_dark_face',(x,y-.096,z),(.90,.055,1.23),glass,c,.065))
 # Bluetooth bind-rune built from closed, extruded round rods rather than SVG.
 glyph=[(-.28,-.33),(.28,.28),(0,.54),(0,-.54),(.28,-.28),(-.28,.33)]
 points=[(x+dx,y-.145,z+dz) for dx,dz in glyph]
 all_parts.append(tube('BT_engraved_glyph',points,engrave,c,.041))
 c=emission['bluetooth'];all_parts.append(tube('BT_lit_glyph',[(px,py-.012,pz) for px,py,pz in points],cyan,c,.034))
 for side in [-1,1]:
  for band in range(2):
   rr=.59+band*.19;pts=[]
   for j in range(15):
    a=(-.60+1.2*j/14);pts.append((x+side*(rr*math.cos(a)+.03),y-.135,z+rr*.74*math.sin(a)))
   all_parts.append(tube(f'BT_signal_arc_{side}_{band}',pts,cyan,c,.024 if band==0 else .019))
 all_parts.append(block('BT_connected_practical',(x,y-.145,z-.49),(.12,.035,.055),cyan,c,.018))
 # A narrow tapered, cross-braced steel transmitter attached to radio crown.
 x=3.;y=.64;bottom=6.09;top=8.28;c=hardware['radio']
 for dx in [-.22,.22]:
  for dy in [-.16,.16]:
   all_parts.append(tube('Radio_mast_leg',[(x+dx,y+dy,bottom),(x+dx*.29,y+dy*.29,top)],edge,c,.023))
 for i in range(5):
  za=bottom+i*(top-bottom)/5;zb=bottom+(i+1)*(top-bottom)/5
  wa=.22*(1-i*.71/5);wb=.22*(1-(i+1)*.71/5)
  for sign in [-1,1]:
   yy=y+sign*.17
   all_parts.append(tube('Radio_X_brace_A',[(x-wa,yy,za),(x+wb,yy,zb)],steel,c,.016))
   all_parts.append(tube('Radio_X_brace_B',[(x+wa,yy,za),(x-wb,yy,zb)],edge,c,.016))
  all_parts.append(tube('Radio_crossmember',[(x-wa,y-.17,za),(x+wa,y-.17,za)],edge,c,.020))
 for zz,width in [(7.28,.78),(7.78,.61)]:
  all_parts.append(tube('Radio_dipole_crossarm',[(x-width/2,y-.04,zz),(x+width/2,y-.04,zz)],edge,c,.028))
  for sign in [-1,1]:
   xx=x+sign*width/2
   all_parts.append(tube('Radio_dipole_element',[(xx,y-.04,zz-.16),(xx,y-.04,zz+.16)],edge,c,.023))
 all_parts.append(block('Radio_tip_beacon_housing',(x,y,top+.025),(.14,.14,.13),steel,c,.025))
 c=emission['radio']
 all_parts.append(block('Radio_tip_lit_beacon',(x,y-.07,top+.045),(.095,.07,.085),beacon,c,.022))
 for side in [-1,1]:
  for band in range(3):
   rr=.31+band*.23;pts=[]
   for j in range(19):
    a=-.62+1.24*j/18
    pts.append((x+side*(.09+rr*math.cos(a)),y-.13,top-.10+rr*.62*math.sin(a)))
   all_parts.append(tube(f'Radio_transmission_arc_{side}_{band}',pts,radio,c,.023 if band==0 else .018))
 return hardware,emission,all_parts


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True,type=Path);p.add_argument('--preview',action='store_true');p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.root.resolve();source=root/'assets/blender/city-beacons';source.mkdir(parents=True,exist_ok=True)
 out=root/'app/ui/public/ambient';private=root/'.runtime/city-beacons-20261024';private.mkdir(parents=True,exist_ok=True)
 existing=root/'assets/blender/pysh-gothic-city-v2.blend';before=hashlib.sha256(existing.read_bytes()).hexdigest()
 bpy.ops.wm.open_mainfile(filepath=str(existing));bpy.context.preferences.filepaths.save_version=0
 old=bpy.data.scenes['PySH_Gothic_City_v2'];scene=bpy.data.scenes.new('PySH_City_Service_Beacons');bpy.context.window.scene=scene
 scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=32 if a.preview else 64
 scene.render.resolution_x=1600;scene.render.resolution_y=570;scene.render.resolution_percentage=100;scene.render.film_transparent=True
 scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=100
 scene.world=bpy.data.worlds.new('Beacon_world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
 scene.view_settings.view_transform='AgX';scene.camera=old.camera.copy();scene.camera.data=old.camera.data.copy();scene.collection.objects.link(scene.camera)
 ld=bpy.data.lights.new('Motivated cool sky','AREA');ld.energy=1000;ld.color=(.65,.78,1);ld.shape='DISK';ld.size=8
 key=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(key);key.location=(0,-10,15);key.rotation_euler=(Vector((0,0,5))-key.location).to_track_quat('-Z','Y').to_euler()
 practical=bpy.data.lights.new('Radio rooftop inspection practical','POINT');practical.color=(.36,.59,.69);practical.energy=24;practical.shadow_soft_size=.30
 practical_obj=bpy.data.objects.new(practical.name,practical);scene.collection.objects.link(practical_obj);practical_obj.location=(3,-.25,7.15)
 hardware,emission,parts=build(scene);scene.render.fps=24;scene.frame_start=1;scene.frame_end=97
 for name in ['Bluetooth illuminated cobalt cyan','Radio transmission sage']:
  sh=bpy.data.materials[name].node_tree.nodes['Principled BSDF']
  for f,v in [(1,3.6),(25,4.5),(49,3.6),(73,4.5),(97,3.6)]:sh.inputs['Emission Strength'].default_value=v;sh.inputs['Emission Strength'].keyframe_insert(data_path='default_value',frame=f)
 scene.frame_set(25);bpy.context.view_layer.update();layouts={}
 for name in hardware:
  points=[o.matrix_world@v.co for o in parts if o.name in {ob.name for c in [hardware[name],emission[name]] for ob in c.objects} for v in o.data.vertices]
  projected=[world_to_camera_view(scene,scene.camera,v) for v in points];pad=10
  x0=max(0,math.floor(min(v.x for v in projected)*1600)-pad);x1=min(1600,math.ceil(max(v.x for v in projected)*1600)+pad)
  y0=max(0,math.floor(min(1-v.y for v in projected)*570)-pad);y1=min(570,math.ceil(max(1-v.y for v in projected)*570)+pad)
  layouts[name]={'crop_px':{'x':x0,'y':y0,'width':x1-x0,'height':y1-y0},'crop_percent':{'left':x0/16,'top':y0/5.7,'width':(x1-x0)/16,'height':(y1-y0)/5.7},'asset_prefix':f'city-beacon-{name}'}
 (source/'layout.json').write_text(json.dumps({'schema':1,'resolution':[1600,570],'props':layouts},indent=2)+'\n',encoding='utf-8');print('LAYOUT '+json.dumps(layouts),flush=True)
 arrays={};assets=[]
 for name in hardware:
  crop=layouts[name]['crop_px'];x0,y0=crop['x'],crop['y'];x1,y1=x0+crop['width'],y0+crop['height']
  for state in ['night','day','emission']:
   for keyname in hardware:
    hardware[keyname].hide_render=keyname!=name or state=='emission';emission[keyname].hide_render=keyname!=name or state!='emission'
   ld.energy=1250 if state=='day' else 900;ld.color=(1,.94,.83) if state=='day' else (.65,.78,1)
   practical.energy=0 if state=='day' else 24
   scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.6 if state=='day' else .18
   scene.render.filepath=str(private/f'{name}-{state}-raw.png');bpy.ops.render.render(write_still=True,scene=scene.name);arr=read_rgba(Path(scene.render.filepath))
   if state=='emission':
    halo=np.zeros_like(arr);halo[:,:,:3]=(.035,.43,1) if name=='bluetooth' else (.19,.82,.51)
    halo[:,:,3:4]=np.minimum(.32,blur(arr[:,:,3:4],1.2)*.45+blur(arr[:,:,3:4],3)*.23);arr=over(halo,arr)
   arrays[name,state]=arr;path=out/f'city-beacon-{name}-{state}-v1.png';save_rgba(name,arr[y0:y1,x0:x1],path)
   assets.append({'name':path.name,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rgba_decoded_bytes':crop['width']*crop['height']*4})
 for c in list(hardware.values())+list(emission.values()):c.hide_render=False
 ld.energy=900;ld.color=(.65,.78,1);practical.energy=24;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.18
 scene['authoring']='Original mounted Bluetooth lightbox and cross-braced radio transmitter. No downloaded meshes or fonts.'
 scene['runtime']='State-gated emission layers. Source keys are animation intent, CSS pulse is integration responsibility. No fake audio waveform.'
 scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(source/'city-service-beacons.blend'),compress=True)
 sys.path.insert(0,str(a.audit_scripts.resolve()));import bx_audit
 gates=[{'name':o.name,**bx_audit.deliverable([o],profile='render')} for o in parts]
 assert all(g['pass'] for g in gates),json.dumps([g for g in gates if not g['pass']])
 (source/'mesh-audit.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
 for day in [False,True]:
  state='day' if day else 'night';base=read_rgba(out/f'gothic-city-{state}-v2.png');bg=np.zeros_like(base);bg[:,:,:3]=(.62,.70,.73) if day else (.055,.09,.12);bg[:,:,3]=1
  base=over(bg,base)
  for fog in [False,True]:
   image=base.copy()
   if fog:
    veil=np.zeros_like(image);veil[:,:,:3]=(.68,.73,.74);veil[:,:,3]=np.linspace(.25,.66,570)[:,None];image=over(image,veil)
   for name in hardware:image=over(over(image,arrays[name,state]),arrays[name,'emission'])
   path=private/f'{state}-{"fog" if fog else "clear"}-full.png';save_rgba('Review',image,path)
   im=bpy.data.images.load(str(path));im.scale(800,208);im.filepath_raw=str(private/f'{state}-{"fog" if fog else "clear"}-native.png');im.save();bpy.data.images.remove(im)
 report={'blender':bpy.app.version_string,'samples':scene.eevee.taa_render_samples,'preview':a.preview,'layouts':layouts,'parts':len(parts),'vertices':sum(len(o.data.vertices) for o in parts),'triangles':sum(len(f.vertices)-2 for o in parts for f in o.data.polygons),'assets':assets,'encoded_bytes':sum(e['bytes'] for e in assets),'rgba_decoded_bytes':sum(e['rgba_decoded_bytes'] for e in assets),'audit':{'pass':True,'scope':'closed hardware/sign/rod parts individually','errors':sum(len(g['errors']) for g in gates),'warnings':sum(len(g['warnings']) for g in gates)},'city_source_sha256':before,'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'limits':'Offline orthographic hardware and emission sprites. Runtime state/lifecycle/pulse and native readability/performance remain integration acceptance.'}
 assert hashlib.sha256(existing.read_bytes()).hexdigest()==before;assert report['encoded_bytes']<150000;assert report['rgba_decoded_bytes']<1500000
 (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
