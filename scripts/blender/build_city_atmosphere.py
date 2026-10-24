"""Blender-authored dusk windows, wet asphalt and forward-time return journeys.

The preserved city-destinations master is read-only. Run factory/headless with
--python-exit-code1; windows/ground keep the exact city-v4 orthographic camera.
"""
import argparse, hashlib, json, math, shutil, subprocess, sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import build_radio_entry as R
import build_radio_neon as N

DESTINATIONS=['media','audio','settings','radio','network']
KEYS=[1,16,31,46,60]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--mode',choices=['plates','exits','preview','audit'],required=True);p.add_argument('--ffmpeg',type=Path);p.add_argument('--destinations',default=','.join(DESTINATIONS));p.add_argument('--palettes',default='day,night');p.add_argument('--samples',type=int,default=24)
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=a.root.resolve();src=root/'assets/blender/city-atmosphere';src.mkdir(exist_ok=True,parents=True);private=root/'.runtime/city-atmosphere-authoring';private.mkdir(exist_ok=True,parents=True);out=root/'app/ui/public/ambient';original=root/'assets/blender/city-destinations/city-destinations.blend';old=sha(original)
 input_master=src/'city-atmosphere.blend' if a.mode in ['plates','audit'] and (src/'city-atmosphere.blend').is_file() else original
 bpy.ops.wm.open_mainfile(filepath=str(input_master));bpy.context.preferences.filepaths.save_version=0;s=bpy.context.scene;s.name='PySH_City_Atmosphere';s.render.film_transparent=True;s.render.fps=24;s.frame_start=1;s.frame_end=60;s.eevee.taa_render_samples=a.samples;s.eevee.ray_tracing_options.denoise_temporal=False;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.compression=65
 recipes=json.loads(s['journey_actions_json']);home=s.camera;report={'schema':1,'blender':bpy.app.version_string,'source_master_sha256':old,'builder_sha256':sha(Path(__file__)),'runtime_city_size':[800,208],'static_resolution':[1600,570],'fps':24,'frames':60,'duration_seconds':2.5,'audio':False,'assets':[]}
 materials={m.name:m for m in bpy.data.materials};shader={}
 for n,m in materials.items():
  sh=m.node_tree.nodes.get('Principled BSDF') if m.node_tree else None
  if sh:shader[n]={k:tuple(sh.inputs[k].default_value) if k in ['Base Color','Emission Color'] else float(sh.inputs[k].default_value) for k in ['Base Color','Emission Color','Emission Strength','Roughness','Metallic']}
 lights={o.name:(tuple(o.data.color),o.data.energy) for o in s.objects if o.type=='LIGHT'};world=s.world.node_tree.nodes['Background'].inputs['Strength'].default_value
 actors=[o for o in s.objects if o.name.startswith(('District_Car_','District_Metro','District_Walker_')) and o.type=='EMPTY'];original_visibility={o.name:o.hide_render for o in s.objects};return_actions={};return_positions={}
 def show_actors(show):
  for ob in actors:
   for o in [ob,*ob.children_recursive]:o.hide_render=not show
 def theme(day,active=None,unlit=False):
  for n,values in shader.items():
   sh=materials[n].node_tree.nodes['Principled BSDF']
   for k,v in values.items():sh.inputs[k].default_value=v
   if n.startswith('window'):
    if unlit:sh.inputs['Base Color'].default_value=(.055,.079,.088,1) if day else (.018,.031,.043,1);sh.inputs['Emission Strength'].default_value=0
    elif day:sh.inputs['Base Color'].default_value=(.12,.17,.18,1);sh.inputs['Emission Strength'].default_value=.05
   elif day and n in ['shop-warm','lamp-warm','civic-lamp']:sh.inputs['Emission Strength'].default_value=.05
   if n=='Entry_Street practical':sh.inputs['Emission Strength'].default_value=.12 if day else 1.5
   if n.startswith('Entry_') and n.endswith(' practical') and n.split('Entry_',1)[1].split(' practical')[0] in DESTINATIONS:sh.inputs['Emission Strength'].default_value=.12 if day else .9
   if n.startswith('Entry_Letter enamel '):
    name=n.split('Entry_Letter enamel ')[1];lit=not day and(active is None or name==active);c=(.72,.78,.74) if lit else (.36,.25,.12);sh.inputs['Base Color'].default_value=(*c,1);sh.inputs['Emission Color'].default_value=(*c,1);sh.inputs['Emission Strength'].default_value=.45 if lit else 0
  for o in s.objects:
   if o.type!='LIGHT':continue
   color,energy=lights[o.name];o.data.color=color;o.data.energy=energy
   if day:
    if o.name=='Moon_key':o.data.color=(1,.89,.74);o.data.energy=3400
    elif o.name=='Urban_fill':o.data.energy=1200
    elif o.name=='Roof_rim':o.data.energy=800
    elif o.name.startswith('Street_practical'):o.data.energy=0
  s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55 if day else world
 def render(path,w,h,frame=1):
  path.parent.mkdir(parents=True,exist_ok=True);s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100;s.frame_set(frame);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 def item(path,**kw):return {'name':path.name,'bytes':path.stat().st_size,'sha256':sha(path),**kw}
 def return_shot(name):
  original_cam=bpy.data.objects['JourneyCamera_'+name];positions=[]
  for f in range(60,0,-1):s.frame_set(f);bpy.context.view_layer.update();positions.append((original_cam.location.copy(),original_cam.rotation_euler.to_quaternion()))
  s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=285/208
  home_rotation=home.rotation_euler.to_quaternion();up=home_rotation@Vector((0,1,0));home_center=home.location+up*6.661875
  cam=original_cam.copy();cam.data=original_cam.data.copy();cam.animation_data_clear();cam.data.animation_data_clear();cam.name='ReturnCamera_'+name;s.collection.objects.link(cam);s.camera=cam;cam.data.type='PERSP';cam.data.clip_start=.008;cam.data.clip_end=8000;cam.data.sensor_width=36
  for f,(loc,rot) in enumerate(positions,1):
   t=min(1,max(0,(f-16)/44));blend=t*t*(3-2*t);rotation=rot.slerp(home_rotation,blend);center=loc.lerp(home_center,blend)
   q=min(1,max(0,(f-32)/28));back=3500*q*q*q;forward=rotation@Vector((0,0,-1))
   cam.location=center-forward*back;cam.rotation_euler=rotation.to_euler();cam.data.lens=54*(42.9+back)/42.9;cam.data.clip_start=max(.008,back-20);cam.data.clip_end=back+200
   cam.keyframe_insert(data_path='location',frame=f);cam.keyframe_insert(data_path='rotation_euler',frame=f);cam.data.keyframe_insert(data_path='lens',frame=f);cam.data.keyframe_insert(data_path='clip_start',frame=f);cam.data.keyframe_insert(data_path='clip_end',frame=f)
  R.frames_linear(cam);cam.animation_data.action.name='Return_'+name+'_Camera';cam.animation_data.action.use_fake_user=True
  R.frames_linear(cam.data);cam.data.animation_data.action.name='Return_'+name+'_Projection';cam.data.animation_data.action.use_fake_user=True
  return_actions[name]={'camera':cam.name,'camera_action':cam.animation_data.action.name,'projection_action':cam.data.animation_data.action.name,'doors':{}}
  return_positions[name]=[]
  for frame in range(1,61):s.frame_set(frame);return_positions[name].append(list(cam.location))
  for obname,actionname in recipes[name]['doors'].items():
   o=bpy.data.objects[obname];action=bpy.data.actions[actionname];o.animation_data_create();o.animation_data.action=action;o.animation_data.action_slot=action.slots[0];angles=[]
   for f in range(60,0,-1):s.frame_set(f);angles.append(o.rotation_euler.z)
   o.animation_data_clear()
   for f,angle in enumerate(angles,1):o.rotation_euler.z=angle;o.keyframe_insert(data_path='rotation_euler',frame=f)
   R.frames_linear(o);o.animation_data.action.name='Return_'+name+'_Door_'+obname;o.animation_data.action.use_fake_user=True;return_actions[name]['doors'][obname]=o.animation_data.action.name
  # Only the camera and hinges reverse. Cars, train and walk cycles advance.
  x=json.loads((root/'assets/blender/city-destinations/build-report.json').read_text(encoding='utf-8'))['anchors'][name]['world_x'];R.animate_travel(bpy.data.objects['District_Metro'],(x-6,-2.485,.67),(x-2,-2.485,.67))
  return cam
 if a.mode in ['exits','preview']:
  if a.mode=='exits':assert a.destinations.split(',')==DESTINATIONS and a.palettes.split(',')==['day','night'],'Final export requires all five destinations and both palettes'
  show_actors(True);clips=[];gates=[]
  for name in a.destinations.split(','):
   assert name in DESTINATIONS;cam=return_shot(name);previous=None;collisions=[]
   for f in range(1,61):
    s.frame_set(f);bpy.context.view_layer.update();pos=cam.matrix_world.translation.copy()
    if previous is not None:
     delta=pos-previous
     if delta.length>1e-7:
      hit,loc,normal,poly,ob,matrix=s.ray_cast(bpy.context.evaluated_depsgraph_get(),previous,delta.normalized(),distance=delta.length)
      if hit:collisions.append({'frame':f,'object':ob.name})
    previous=pos
   assert not collisions,(name,collisions);gates.append({'destination':name,'camera_segment_collisions':0,'frames':60,'actors_time_direction':'forward'})
   for palette in a.palettes.split(','):
    assert palette in ['day','night'];theme(palette=='day',active=name);folder=private/'returns'/name/palette
    for f in (KEYS if a.mode=='preview' else range(1,61)):
     path=folder/f'{f:04d}.png';render(path,400 if a.mode=='preview' else 800,240 if a.mode=='preview' else 480,f)
     rgba=N.read_rgba(path)
     if f==1:assert rgba[:,:,3].min()>.999,'Return starts inside opaque threshold'
     if f==60:assert rgba[:10,:,3].max()<.001,'Return ending sky must stay transparent'
     if f in KEYS:N.save_rgba(name+palette+str(f),rgba,private/f'return-{name}-{palette}-{f:02d}.png')
    if a.mode=='exits':
     assert a.ffmpeg and a.ffmpeg.is_file();file=out/f'city-exit-{name}-{palette}-v1.webm'
     r=subprocess.run([str(a.ffmpeg),'-nostdin','-hide_banner','-y','-framerate','24','-i',str(folder/'%04d.png'),'-vf','setsar=1','-c:v','libvpx','-pix_fmt','yuva420p','-auto-alt-ref','0','-lag-in-frames','0','-crf','12','-b:v','1800k','-deadline','good','-cpu-used','2','-an',str(file)],capture_output=True,text=True);(private/f'encode-{name}-{palette}.log').write_text(r.stderr,encoding='utf-8');r.check_returncode();clips.append(item(file))
     N.save_rgba(name+palette+'review',N.read_rgba(folder/'0031.png')[::2,::2],src/f'key-return-{name}-{palette}-31.png')
  report.update(clips=clips,camera_gates=gates,return_camera_positions=return_positions,return_projection={'pixel_aspect':[1,285/208],'display_sar':1,'home_center_offset_world':6.661875,'far_perspective_back_distance':3500,'near_clip':'max(.008,back-20)','far_clip':'back+200','no_late_vertical_warp':True},actors_time_direction='forward; camera and door hinges reversed')
  if a.mode=='exits':
   s.camera=home;show_actors(False);theme(False);s.frame_set(1);s.render.resolution_x=1600;s.render.resolution_y=570;s.render.filepath='//renders/';s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=1;s['return_actions_json']=json.dumps(return_actions);s['return_render_json']=json.dumps({'width':800,'height':480,'pixel_aspect':[1,285/208],'encoded_sar':1});
   if (src/'city-atmosphere.blend').is_file():
    overlay_source=private/'preserved-overlay-source.blend';shutil.copyfile(src/'city-atmosphere.blend',overlay_source)
    with bpy.data.libraries.load(str(overlay_source),link=False) as (existing,loaded):loaded.objects=[n for n in existing.objects if n.startswith('Atmosphere_')]
    for overlay in loaded.objects:
     if overlay:
      assert overlay.library is None and overlay.data.library is None
      assert all(m is None or m.library is None for m in overlay.data.materials)
      s.collection.objects.link(overlay)
    for library in list(bpy.data.libraries):
     assert not bpy.data.user_map().get(library,set()),'Appended overlay must be fully local/portable';bpy.data.libraries.remove(library)
   bpy.ops.wm.save_as_mainfile(filepath=str(src/'city-atmosphere.blend'),compress=True);(src/'return-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 elif a.mode=='plates':
  s.camera=home;home.animation_data_clear();home.data.animation_data_clear();show_actors(False);s.frame_set(1)
  if 'return_actions_json' not in s:
   s['return_actions_json']=json.dumps({name:{'camera':'ReturnCamera_'+name,'camera_action':bpy.data.objects['ReturnCamera_'+name].animation_data.action.name,'doors':{ob.name:next(ac.name for ac in bpy.data.actions if ac.name=='Return_'+name+'_Door_'+ob.name) for ob in s.objects if ob.name in recipes[name]['doors']}} for name in DESTINATIONS})
  # Rerender only this builder's overlay geometry; preserved city/return data remains untouched.
  for old_overlay in list(s.objects):
   if old_overlay.name.startswith('Atmosphere_'):bpy.data.objects.remove(old_overlay,do_unlink=True)
  static_objects=[o for o in s.objects if o.type in ['MESH','CURVE','FONT']]
  # Separate original connected window panes, retaining exact vertices/world pose.
  # Their deterministic occupancy/palette is inherited; dark windows stay dark.
  banks=[[] for _ in range(3)];bank_objects=[];pane_count=0
  for ob in static_objects:
   if ob.type!='MESH' or not any(m and m.name.startswith('window') and shader.get(m.name,{}).get('Emission Strength',0)>0 for m in ob.data.materials):continue
   mesh=ob.data;neighbors=[set() for _ in mesh.vertices]
   for edge in mesh.edges:
    x,y=edge.vertices;neighbors[x].add(y);neighbors[y].add(x)
   remaining=set(range(len(mesh.vertices)))
   while remaining:
    seed=next(iter(remaining));component={seed};todo=[seed];remaining.remove(seed)
    while todo:
     for n in neighbors[todo.pop()]:
      if n in remaining:remaining.remove(n);component.add(n);todo.append(n)
    polys=[poly for poly in mesh.polygons if poly.vertices[0] in component]
    if not polys:continue
    points=[ob.matrix_world@mesh.vertices[i].co for i in sorted(component)];center=sum(points,Vector())/len(points)
    bank=(round(center.x*19)+round(center.y*13)+round(center.z*23))%3;lookup={old:i for i,old in enumerate(sorted(component))};faces=[tuple(lookup[i] for i in poly.vertices) for poly in polys]
    material=ob.data.materials[polys[0].material_index]
    if not material or shader.get(material.name,{}).get('Emission Strength',0)<=0:continue
    banks[bank].append((points,faces,material));pane_count+=1
  bank_materials={}
  for bank,panes in enumerate(banks):
   vertices=[];faces=[];mat_ids=[];used=[]
   for points,polygons,material in panes:
    offset=len(vertices);vertices.extend(points);faces.extend(tuple(i+offset for i in face) for face in polygons)
    if material.name not in bank_materials:
     copy=material.copy();copy.name='Atmosphere_'+material.name;sh=copy.node_tree.nodes['Principled BSDF'];sh.inputs['Emission Strength'].default_value=max(1.0,shader[material.name]['Emission Strength']);bank_materials[material.name]=copy
    copy=bank_materials[material.name]
    if copy not in used:used.append(copy)
    mat_ids.extend([used.index(copy)]*len(polygons))
   mesh=bpy.data.meshes.new('Atmosphere_WindowBank_'+str(bank));mesh.from_pydata(vertices,[],faces);mesh.update();assert not mesh.validate();ob=bpy.data.objects.new(mesh.name,mesh);s.collection.objects.link(ob);ob['atmosphere_bank']=bank
   for material in used:mesh.materials.append(material)
   for poly,index in zip(mesh.polygons,mat_ids):poly.material_index=index
   ob.hide_render=True;bank_objects.append(ob)
  holdout=bpy.data.materials.new('Atmosphere_Occlusion');holdout.use_nodes=True;nodes=holdout.node_tree.nodes;nodes.clear();hold=nodes.new('ShaderNodeHoldout');holdout.node_tree.links.new(hold.outputs[0],nodes.new('ShaderNodeOutputMaterial').inputs[0])
  original_slots={o.name:list(o.data.materials) for o in static_objects};original_hides={o.name:o.hide_render for o in static_objects}
  def restore_slots():
   for o in static_objects:
    o.data.materials.clear()
    for m in original_slots[o.name]:o.data.materials.append(m)
    o.hide_render=original_hides[o.name]
  def occluders():
   for o in static_objects:
    if original_hides[o.name]:continue
    # Original panes must not self-occlude their exact duplicate emission surface.
    if any(m and m.name.startswith('window') for m in original_slots[o.name]):o.hide_render=True;continue
    o.data.materials.clear();o.data.materials.append(holdout)
  unlit=[]
  for palette in ['day','night']:
   theme(palette=='day',unlit=True);path=out/f'gothic-city-{palette}-unlit-v1.png';render(path,1600,570)
   rgba=N.read_rgba(path);assert rgba[-8:,:,3].min()>.999;unlit.append(item(path))
  theme(False);occluders();window_records=[]
  for bank,ob in enumerate(bank_objects):
   ob.hide_render=False;path=out/f'city-window-bank-{bank}-v1.png';render(path,1600,570);rgba=N.read_rgba(path);assert (rgba[:,:,3]>.1).sum()>100;assert rgba[-8:,:,3].max()==0;ob.hide_render=True;window_records.append(item(path,pane_components=len(banks[bank]),lit_pixels=int((rgba[:,:,3]>.1).sum())))
  restore_slots()
  # A physical asphalt/water surface inherits the existing deck footprint.
  # Its reflected city is rendered before a holdout-only visibility mask clips it.
  wet=R.mat('Atmosphere wet asphalt',(.025,.04,.044),metal=.76,rough=.075);sh=wet.node_tree.nodes['Principled BSDF'];sh.inputs['Coat Weight'].default_value=.65;sh.inputs['Coat Roughness'].default_value=.13
  nt=wet.node_tree;tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=15;tex.inputs['Detail'].default_value=2
  coords=nt.nodes.new('ShaderNodeTexCoord');stretch=nt.nodes.new('ShaderNodeVectorMath');stretch.operation='MULTIPLY';stretch.inputs[1].default_value=(.8,.08,1);nt.links.new(coords.outputs['Object'],stretch.inputs[0]);nt.links.new(stretch.outputs[0],tex.inputs['Vector'])
  bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.065;bump.inputs['Distance'].default_value=.022;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],sh.inputs['Normal'])
  floor=R.cube('Atmosphere_WetRoad',(0,-.8,-.036),(48,7.5,.006),wet);floor['atmosphere_wet_surface']=True
  # The transit wall stays camera-opaque; excluding it only from glossy rays
  # lets existing low-angle city practicals read on the narrow foreground road.
  glossy_occluders=[o for o in static_objects if o.name.startswith(('District_ExtendedRail','District_Retaining','District_Foundation','District_RailAbutment','City_v3_viaduct'))]
  original_glossy={o.name:o.visible_glossy for o in glossy_occluders}
  for o in glossy_occluders:o.visible_glossy=False
  wet_records=[]
  for palette in ['day','night']:
   theme(palette=='day');s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.max_bounces=4;s.cycles.diffuse_bounces=2;s.cycles.glossy_bounces=3
   if palette=='night':
    for name in ['window-warm','window-amber','window-cool','lamp-warm','civic-lamp']:
     if name in materials:materials[name].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value*=1.8
   beauty=private/f'wet-beauty-{palette}.png';render(beauty,1600,570)
   s.render.engine='BLENDER_EEVEE';occluders();mask=private/f'wet-mask-{palette}.png';render(mask,1600,570);restore_slots()
   rgb=N.read_rgba(beauty);alpha=N.read_rgba(mask)[:,:,3];layer=np.dstack((rgb[:,:,:3],alpha*.70));path=out/f'city-road-wet-{palette}-v1.png';N.save_rgba(palette,layer,path)
   assert (alpha>.5).sum()>1000;assert alpha[:350].max()==0,'Wet mask must remain on actual ground';wet_records.append(item(path,visible_ground_pixels=int((alpha>.5).sum()),max_alpha=178))
  for o in glossy_occluders:o.visible_glossy=original_glossy[o.name]
  floor.hide_render=True;theme(False);show_actors(False);s.camera=home;s.render.resolution_x=1600;s.render.resolution_y=570;s.render.filepath='//renders/';bpy.ops.wm.save_as_mainfile(filepath=str(src/'city-atmosphere.blend'),compress=True)
  report.update(unlit_baseplates=unlit,window_banks=window_records,window_pane_components=pane_count,wet_reflections=wet_records,window_occlusion='Original opaque city holdouts; no light through foreground buildings',wet_geometry='Existing deck footprint; Cycles reflection + actual opaque-city visibility mask; alpha0.70 for subtle compositing; camera-opaque transit objects excluded only from glossy rays, existing practical reflections favored1.8x at night')
  (src/'plates-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 elif a.mode=='audit':
  assert a.ffmpeg and a.ffmpeg.is_file();movies=[];camera_checks=[];actor_checks=[]
  poses=json.loads((src/'return-report.json').read_text(encoding='utf-8'))['return_camera_positions'];returns=json.loads(s['return_actions_json'])
  for name in DESTINATIONS:
   cam=bpy.data.objects[returns[name]['camera']];maximum=0.0
   for f in range(1,61):
    s.frame_set(f);bpy.context.view_layer.update();maximum=max(maximum,(cam.matrix_world.translation-Vector(poses[name][f-1])).length)
   assert maximum<1e-4,(name,maximum);camera_checks.append({'destination':name,'positions_checked':60,'max_camera_error':maximum,'camera_returns_to_matched_home_projection':True})
  from bpy_extras.object_utils import world_to_camera_view
  handoff=[]
  for name in DESTINATIONS:
   cam=bpy.data.objects[returns[name]['camera']]
   for frame in [59,60]:
    s.frame_set(frame);bpy.context.view_layer.update();points=[ob.matrix_world@v.co for ob in s.objects if ob.type=='MESH' and not ob.hide_render for v in ob.data.vertices];expected=[]
    s.camera=home;s.render.resolution_x=1600;s.render.resolution_y=570;s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=1
    for point in points:
     uv=world_to_camera_view(s,home,point)
     if 0<=uv.x<=1 and 0<=uv.y<=1:expected.append((point,Vector((uv.x*800,272+(1-uv.y)*208))))
    s.camera=cam;s.render.resolution_x=800;s.render.resolution_y=480;s.render.pixel_aspect_x=1;s.render.pixel_aspect_y=285/208;errors=[]
    for point,target in expected:
     uv=world_to_camera_view(s,cam,point);errors.append((Vector((uv.x*800,(1-uv.y)*480))-target).length)
    assert max(errors)<2,(name,frame,max(errors));handoff.append({'destination':name,'frame':frame,'points_checked':len(errors),'max_error_px':max(errors),'mean_error_px':sum(errors)/len(errors)})
  for name in ['District_Car_0','District_Car_1','District_Metro','District_Walker_0']:
   ob=bpy.data.objects[name];s.frame_set(1);bpy.context.view_layer.update();first=ob.matrix_world.translation.copy();s.frame_set(60);bpy.context.view_layer.update();last=ob.matrix_world.translation.copy();dx=float(last.x-first.x)
   expected={'District_Car_0':12,'District_Car_1':-9,'District_Metro':4,'District_Walker_0':1}[name];assert abs(dx-expected)<1e-5;actor_checks.append({'object':name,'forward_world_x_delta':round(dx,6),'matches_original_time_direction':True})
  for name in DESTINATIONS:
   for palette in ['day','night']:
    file=out/f'city-exit-{name}-{palette}-v1.webm';r=subprocess.run([str(a.ffmpeg),'-nostdin','-hide_banner','-loglevel','error','-c:v','libvpx','-i',str(file),'-progress','pipe:1','-nostats','-f','null','-'],capture_output=True,text=True);r.check_returncode();frames=[int(z.split('=')[1]) for z in r.stdout.splitlines() if z.startswith('frame=')];assert frames[-1]==60
    folder=private/'codec'/file.stem;folder.mkdir(parents=True,exist_ok=True)
    r=subprocess.run([str(a.ffmpeg),'-nostdin','-hide_banner','-loglevel','error','-y','-c:v','libvpx','-i',str(file),'-vf',r'select=lt(n\,7)+eq(n\,59)','-fps_mode','vfr',str(folder/'%02d.png')],capture_output=True,text=True);r.check_returncode()
    first=N.read_rgba(folder/'01.png');last=N.read_rgba(folder/'08.png');assert first.shape==last.shape==(480,800,4);assert first[:,:,3].min()>.999;assert last[:10,:,3].max()<.001;assert last[-8:,:,3].min()>.999
    black=0
    for k in range(1,8):
     frame=N.read_rgba(folder/f'{k:02d}.png');lum=frame[:,:,:3]@np.array([.2126,.7152,.0722]);fraction=float(((lum<10/255)&(frame[:,:,3]>250/255)).mean())
     if fraction>.95:black+=1
     else:break
    assert black<=5,(name,palette,black)
    metadata=subprocess.run([str(a.ffmpeg),'-nostdin','-hide_banner','-i',str(file)],capture_output=True,text=True).stderr
    assert 'Video: vp8' in metadata and '800x480' in metadata and '24 fps' in metadata and 'Audio:' not in metadata
    movies.append(item(file,frames_decoded=60,first_frame_opaque=True,ending_sky_transparent=True,ending_ground_opaque=True,leading_95pct_black_frames=black,leading_seconds=round(black/24,3)))
  statics=[]
  for palette in ['day','night']:
   file=out/f'gothic-city-{palette}-unlit-v1.png';rgba=N.read_rgba(file);assert rgba.shape==(570,1600,4) and rgba[-8:,:,3].min()>.999;statics.append(item(file,ground_opaque=True))
   file=out/f'city-road-wet-{palette}-v1.png';rgba=N.read_rgba(file);assert rgba.shape==(570,1600,4) and rgba[:350,:,3].max()==0 and rgba[:,:,3].max()<=179/255;statics.append(item(file,actual_ground_mask_only=True))
  masks=[]
  for bank in range(3):
   file=out/f'city-window-bank-{bank}-v1.png';rgba=N.read_rgba(file);assert rgba.shape==(570,1600,4) and rgba[-8:,:,3].max()==0 and (rgba[:,:,3]>.1).sum()>100;statics.append(item(file,existing_pane_geometry=True));masks.append(rgba[:,:,3]>.5)
  overlap=sum(int((masks[i]&masks[j]).sum()) for i,j in [(0,1),(1,2),(0,2)])
  sys.path.insert(0,str(Path.home()/'.codex/skills/scenario-blender-expert/scripts'));import bx_audit
  new_parts=[o for o in s.objects if o.name.startswith('Atmosphere_') and o.type=='MESH'];gates=[]
  for obj in new_parts:
   if 'atmosphere_bank' not in obj:gates.append(bx_audit.deliverable([obj],profile='render'));continue
   # An emission bank intentionally groups spatially separate original panes.
   # Gate each authored connected pane, not the atlas as one solid building.
   mesh=obj.data;neighbors=[set() for _ in mesh.vertices]
   for edge in mesh.edges:
    i,j=edge.vertices;neighbors[i].add(j);neighbors[j].add(i)
   remaining=set(range(len(mesh.vertices)))
   while remaining:
    seed=next(iter(remaining));component={seed};todo=[seed];remaining.remove(seed)
    while todo:
     for n in neighbors[todo.pop()]:
      if n in remaining:remaining.remove(n);component.add(n);todo.append(n)
    indices=sorted(component);lookup={old:i for i,old in enumerate(indices)};faces=[tuple(lookup[i] for i in poly.vertices) for poly in mesh.polygons if poly.vertices[0] in component]
    source_polys=[poly for poly in mesh.polygons if poly.vertices[0] in component]
    temporary=bpy.data.meshes.new('AtmosphereGatePane');temporary.from_pydata([mesh.vertices[i].co for i in indices],[],faces);temporary.update();probe=bpy.data.objects.new('AtmosphereGatePane',temporary);s.collection.objects.link(probe);probe.matrix_world=obj.matrix_world
    for material in mesh.materials:temporary.materials.append(material)
    for polygon,original_polygon in zip(temporary.polygons,source_polys):polygon.material_index=original_polygon.material_index
    gates.append(bx_audit.deliverable([probe],profile='render'));bpy.data.objects.remove(probe,do_unlink=True);bpy.data.meshes.remove(temporary)
  (private/'mesh-gates.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
  assert len(gates)==154 and all(g['pass'] for g in gates),gates
  gate={'pass':True,'errors':[e for g in gates for e in g['errors']],'warnings':[w for g in gates for w in g['warnings']]}
  report.update(pass_gate=True,clips=movies,encoded_clip_bytes=sum(z['bytes'] for z in movies),static_assets=statics,camera_checks=camera_checks,home_handoff_geometry=handoff,actor_checks=actor_checks,window_bank_overlap_pixels=overlap,new_render_parts=len(new_parts),gated_logical_components=len(gates),intentional_disconnected_window_panes=153,mesh_gate={'pass':gate['pass'],'errors':len(gate['errors']),'warnings':len(gate['warnings'])},editable_master_sha256=sha(src/'city-atmosphere.blend'),window_pane_components=153,limits='Offline source/geometry/codec gates. Runtime weather/solar logic, native composition, touch and decoder performance are separate acceptance.')
  assert report['encoded_clip_bytes']<10*1024*1024
  (src/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 assert sha(original)==old;print('RESULT '+json.dumps(report),flush=True)
if __name__=='__main__':main()
