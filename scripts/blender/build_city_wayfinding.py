"""Reproducible selected floating wayfinding assets, Blender5.2.2/OPTIX.
Derived from evaluated rendererV2. Geometry, projection and clearance math retained.
Use explicit fresh output; optional external mesh audit never has a personal default.
"""
import argparse,hashlib,importlib.util,json,math,struct,sys,unicodedata
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
_root_parser=argparse.ArgumentParser(add_help=False);_root_parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);_root_args,_=_root_parser.parse_known_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []);ROOT=_root_args.root.expanduser().resolve()
sys.path.insert(0,str(ROOT/'scripts/blender'))
import build_radio_entry as R
import build_radio_neon as N
IDS=('media','audio','settings','radio','network')
TEXT={'media':{'en':'Media','ro':'Media'},'audio':{'en':'Sound','ro':'Sunet'},'settings':{'en':'Settings','ro':'Set\u0103ri'},'radio':{'en':'Radio','ro':'Radio'},'network':{'en':'Internet','ro':'Internet'}}
PORTALS={'media':-10.3,'audio':-8.1,'settings':-2.3,'radio':3.,'network':6.3}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2),encoding='utf-8')
def merge(rs,pad=0):return [min(r[0] for r in rs)-pad,min(r[1] for r in rs)-pad,max(r[2] for r in rs)+pad,max(r[3] for r in rs)+pad]
def intersects(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
class Context:
 def __init__(self,scene):
  self.root=ROOT;self.scene=scene;self.camera=scene.camera;self.signs={};self.materials=[];self.fonts={};self.options={'float_y':1.1,'float_x':.25,'intro_yaw':[12,8,4,1,-.3,0],'intro_y':[1.8,1.2,.6,.2,-.05,0]};self.collection=bpy.data.collections.new('AutoresearchCandidate');scene.collection.children.link(self.collection)
 def native(self,p):
  v=world_to_camera_view(self.scene,self.camera,Vector(p));return [v.x*800,272+((1-v.y)*1024-227)*208/570]
 def register(self,sign,obj,face=True):
  for col in list(obj.users_collection):col.objects.unlink(obj)
  self.collection.objects.link(obj);obj.hide_render=False;sign['objects'].append(obj)
  if face:sign['face'].append(obj)
  return obj
 def material(self,name,day,night,emit_day=0,emit_night=0,metallic=0,roughness=.65):
  m=R.mat('Experiment_'+name,day,metal=metallic,rough=roughness);m.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=.08;self.materials.append((m,tuple(day),tuple(night),emit_day,emit_night));return m
 def palette(self,palette):
  day=palette=='day'
  for mat,a,b,ea,eb in self.materials:
   sh=mat.node_tree.nodes['Principled BSDF'];col=a if day else b;sh.inputs['Base Color'].default_value=(*col,1);sh.inputs['Emission Color'].default_value=(*col,1);sh.inputs['Emission Strength'].default_value=ea if day else eb
  self.scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55 if day else .12
  for obj in self.scene.objects:
   if obj.type!='LIGHT':continue
   if obj.name=='Moon_key':obj.data.color=(1,.89,.74) if day else (.54,.67,.82);obj.data.energy=3400 if day else 1100
   elif obj.name=='Urban_fill':obj.data.energy=1200 if day else 135
   elif obj.name=='Roof_rim':obj.data.energy=800 if day else 330
   elif obj.name.startswith('Street_practical'):obj.data.energy=0
 def sign(self,id,x,y,yaw=0):
  assert id in IDS and id not in self.signs
  xx=(x/800-.5)*28.6;base=self.native((xx,-2.85,0))[1];slope=self.native((xx,-2.85,1))[1]-base;rig=R.empty('Experiment_'+id,(xx,-2.85,(y-base)/slope));rig.rotation_euler.z=math.radians(yaw);obj={'id':id,'root':rig,'objects':[],'face':[],'texts':[],'portal_x':PORTALS[id]};self.signs[id]=obj;return obj
 def text(self,sign,material,weight='500',size=1.44,tracking=1.0,extrude=.018,bevel=.0015,offset=0,location=(0,-.10,0),copy=False):
  index={'400':6,'500':7,'600':8}[str(weight)];path=ROOT/f'app/ui/public/fonts/hub-font-{index}.ttf'
  if str(path) not in self.fonts:self.fonts[str(path)]=bpy.data.fonts.load(str(path));self.fonts[str(path)].pack()
  curve=bpy.data.curves.new('Experiment_'+sign['id']+'_Type','FONT');curve.font=self.fonts[str(path)];curve.body=TEXT[sign['id']]['en'];curve.align_x='CENTER';curve.align_y='CENTER';curve.size=size;curve.space_character=tracking;curve.extrude=extrude;curve.bevel_depth=bevel;curve.offset=offset;curve.bevel_resolution=1;curve.resolution_u=4;curve.materials.append(material);obj=bpy.data.objects.new(curve.name,curve);self.scene.collection.objects.link(obj);obj.parent=sign['root'];obj.location=location;obj.rotation_euler=(math.pi/2,0,0);self.register(sign,obj);sign['texts'].append({'object':obj,'copy':copy});return obj
 def box(self,sign,name,location,size,material,bevel=0,face=True):return self.register(sign,R.cube('Experiment_'+sign['id']+'_'+name,location,size,material,sign['root'],bevel),face)
 def rod(self,sign,name,a,b,width,material,face=False):
  a,b=Vector(a),Vector(b);obj=self.box(sign,name,(a+b)/2,(width,width,(b-a).length),material,face=face);obj.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();return obj
 def language(self,lang):
  for id,sign in self.signs.items():
   for item in sign['texts']:item['object'].data.body=TEXT[id][lang]
 def rect(self,objects,pad=0):
  points=[world_to_camera_view(self.scene,self.camera,o.matrix_world@Vector(v)) for o in objects for v in o.bound_box];return [math.floor(min(v.x for v in points)*1600)-pad,math.floor(min(1-v.y for v in points)*1024)-pad,math.ceil(max(v.x for v in points)*1600)+pad,math.ceil(max(1-v.y for v in points)*1024)+pad]
 def native_rect(self,r):return [r[0]/2,272+(r[1]-227)*208/570,r[2]/2,272+(r[3]-227)*208/570]

# Exact fixed opaque-service rectangles include the agreed3px margins.
PROTECTED_RECTS={'radio_hardware_emission':[451,272.284,516.5,333.39],
 'bluetooth':[142,285.421,205,329.737],'wifi':[555,324.832,597.5,363.308],
 'radio_pcm_neon':[451.5,318.63,516.5,427.18]}
def object_clearance(ctx,id,sign,phase):
 for obj in sign['objects']:
  r=ctx.native_rect(ctx.rect([obj]))
  assert r[0]>=0 and r[2]<=800 and r[1]>=58 and r[3]<=480,('object viewport',id,obj.name,phase,r)
  for protected,rect in PROTECTED_RECTS.items():
   assert not intersects(r,rect),('object beacon occlusion',id,obj.name,phase,protected,r,rect)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=ROOT);ap.add_argument('--mesh-audit',type=Path,help='Optional explicit bx_audit.py path; omit to record full mesh audit NOT_RUN.');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--candidate',type=Path,default=ROOT/'assets/blender/city-wayfinding/design.py');mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--preview',action='store_true');mode.add_argument('--final',action='store_true');args=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);out=args.out.expanduser().resolve();assert out.is_absolute() and out!=ROOT and out not in ROOT.parents;assert '.git' not in out.parts;assert not any(out==ROOT/name or ROOT/name in out.parents for name in ['app','assets','scripts']), 'Render to a fresh build directory, never over source/public inputs';assert not out.exists(),'Output must be a NEW directory; no existing evidence is overwritten';out.mkdir(parents=True,exist_ok=False)
 original=ROOT/'assets/blender/city-destinations/city-destinations.blend';inputs={str(p.relative_to(ROOT)):sha(p) for p in [original,*[ROOT/f'app/ui/public/fonts/hub-font-{i}.ttf' for i in [6,7,8]]]};bpy.ops.wm.open_mainfile(filepath=str(original));bpy.context.preferences.filepaths.save_version=0;s=bpy.context.scene;c=s.camera;c.animation_data_clear();c.data.animation_data_clear();s.frame_set(1);s.render.resolution_x=1600;s.render.resolution_y=570;s.render.resolution_percentage=100;check_points=[Vector((0,-2.19,.98)),Vector((3,-2.85,5.2))];old=[world_to_camera_view(s,c,p) for p in check_points];s.render.resolution_y=1024;new=[world_to_camera_view(s,c,p) for p in check_points];projection=[[b.x*1600-a.x*1600,(1-b.y)*1024-(1-a.y)*570-227] for a,b in zip(old,new)];assert max(abs(v) for row in projection for v in row)<.001
 for obj in s.objects:
  if obj.type not in ['CAMERA','LIGHT']:obj.hide_render=True
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices();devices=[]
 for d in prefs.devices:d.use=d.type=='OPTIX';devices.append({'name':d.name,'type':d.type,'use':d.use})
 assert any(d['use'] for d in devices),'OPTIX required by frozen renderer';s.render.engine='CYCLES';s.cycles.device='GPU';s.cycles.samples=24 if args.preview else 32;s.cycles.use_denoising=True;s.cycles.max_bounces=3;s.render.threads_mode='FIXED';s.render.threads=8;s.render.film_transparent=True;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.fps=20;s.frame_start=1;s.frame_end=81
 camera_before=(tuple(c.location),tuple(c.rotation_euler),c.data.type,c.data.ortho_scale,c.data.shift_x,c.data.shift_y,s.render.resolution_x,s.render.resolution_y);candidate=args.candidate.resolve();spec=importlib.util.spec_from_file_location('trial_candidate',candidate);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);ctx=Context(s);module.build(ctx);assert camera_before==(tuple(c.location),tuple(c.rotation_euler),c.data.type,c.data.ortho_scale,c.data.shift_x,c.data.shift_y,s.render.resolution_x,s.render.resolution_y),'Candidate changed frozen camera';assert set(ctx.signs)==set(IDS);assert 0<=ctx.options['float_y']<=3 and 0<=ctx.options['float_x']<=2;assert ctx.options['intro_yaw'][-1]==0 and ctx.options['intro_y'][-1]==0;assert len(ctx.options['intro_yaw'])==len(ctx.options['intro_y']) and len(ctx.options['intro_yaw']) in [1,6]
 bpy.context.view_layer.update();base={id:(sign['root'].location.copy(),sign['root'].rotation_euler.copy()) for id,sign in ctx.signs.items()};bounds={id:[] for id in IDS};faces={id:[] for id in IDS};base_rects={id:[] for id in IDS};fonts={};motion=[];text_audit={};count=len(ctx.options['intro_yaw'])
 def pose(id,index):
  rig=ctx.signs[id]['root'];location,rotation=base[id];rig.location=location.copy();rig.rotation_euler=rotation.copy();rig.rotation_euler.z+=math.radians(ctx.options['intro_yaw'][index]);slope=ctx.native(location+Vector((0,0,1)))[1]-ctx.native(location)[1];rig.location.z+=ctx.options['intro_y'][index]/slope
 # Actual Blender location keys; rotation remains fixed during the81-point loop.
 for id,sign in ctx.signs.items():
  rig=sign['root'];location,rotation=base[id];slope=ctx.native(location+Vector((0,0,1)))[1]-ctx.native(location)[1]
  for frame in range(1,82):
   t=(frame-1)/80;rig.location=location+Vector((ctx.options['float_x']*(math.cos(t*math.tau)-1)/(1600/28.6*.5),0,ctx.options['float_y']*math.sin(t*math.tau)/slope));rig.keyframe_insert('location',frame=frame)
  R.frames_linear(rig);rig.animation_data.action.name='Float_'+id;rig.animation_data.action.use_fake_user=True
 actions={id:sign['root'].animation_data.action for id,sign in ctx.signs.items()}
 for lang in ['en','ro']:
  ctx.language(lang);text_audit[lang]={}
  for id,sign in ctx.signs.items():
   main=[item['object'] for item in sign['texts'] if not item['copy']];assert len(main)==1;obj=main[0];value=obj.data.body;assert unicodedata.normalize('NFC',value).casefold()==TEXT[id][lang].casefold();assert not any(ord(ch)<32 or 127<=ord(ch)<=159 or ch in '\ufffd\u201a' for ch in value);text_audit[lang][id]={'text':value,'codepoints':[ord(ch) for ch in value]};assert tuple(obj.scale)==(1.,1.,1.),'No stretched type'
  for id,sign in ctx.signs.items():sign['root'].animation_data.action=actions[id]
  for frame in range(1,82):
   s.frame_set(frame);bpy.context.view_layer.update()
   for id,sign in ctx.signs.items():bounds[id].append(ctx.rect(sign['objects']));assert tuple(sign['root'].rotation_euler)==tuple(base[id][1]);object_clearance(ctx,id,sign,('float',lang,frame))
   if lang=='en':
    p=ctx.native(ctx.signs['radio']['root'].matrix_world.translation)
    if frame==1:origin=p
    motion.append({'offset':(frame-1)/80,'x':round(p[0]-origin[0],6),'y':round(p[1]-origin[1],6)})
  for id,sign in ctx.signs.items():sign['root'].animation_data.action=None
  for index in range(count):
   for id in IDS:pose(id,index)
   bpy.context.view_layer.update()
   for id,sign in ctx.signs.items():bounds[id].append(ctx.rect(sign['objects']));object_clearance(ctx,id,sign,('intro',lang,index))
  for id,sign in ctx.signs.items():
   sign['root'].location=base[id][0].copy();sign['root'].rotation_euler=base[id][1].copy();bpy.context.view_layer.update();faces[id].append(ctx.rect(sign['face']));base_rects[id].append(ctx.rect(sign['objects'],6))
   if lang=='en':
    font=[v['object'] for v in sign['texts'] if not v['copy']][0];curve=font.data.copy();curve.body='H';tmp=bpy.data.objects.new('CapMetric',curve);ctx.collection.objects.link(tmp);tmp.matrix_world=font.matrix_world.copy();tmp.hide_render=True;bpy.context.view_layer.update();ys=[v[1] for v in tmp.bound_box];a=ctx.native(tmp.matrix_world@Vector((0,min(ys),0)));b=ctx.native(tmp.matrix_world@Vector((0,max(ys),0)));height=abs(a[1]-b[1]);fonts[id]=height;bpy.data.objects.remove(tmp,do_unlink=True);bpy.data.curves.remove(curve);assert 14<=height<=16,(id,'native cap height',height)
 geometry={};hits={}
 for id in IDS:
  r=merge(bounds[id],6);nf=ctx.native_rect(merge(faces[id]));nr=ctx.native_rect(merge(bounds[id]));assert r[0]>=0 and r[1]>=0 and r[2]<=1600 and r[3]<=1024,(id,'overscan',r);cx=(nf[0]+nf[2])/2;cy=(nf[1]+nf[3])/2;hw=max(48,nf[2]-nf[0])/2;hh=max(48,nf[3]-nf[1])/2;hits[id]=[cx-hw-ctx.options['float_x']*2,cy-hh-ctx.options['float_y'],cx+hw+ctx.options['float_x']*2,cy+hh+ctx.options['float_y']];assert hits[id][0]>=0 and hits[id][2]<=800 and hits[id][1]>=58 and hits[id][3]<=480,('hit viewport',id,hits[id])
  crop=merge(base_rects[id]) if args.preview else r;face=merge(faces[id]);geometry[id]={'crop':{'x':crop[0],'y':crop[1]-227,'width':crop[2]-crop[0],'height':crop[3]-crop[1]},'final_face_rect':{'x':face[0],'y':face[1]-227,'width':face[2]-face[0],'height':face[3]-face[1]},'frame_count':1 if args.preview else count,'languages':{},'native_envelope':nr,'hit_envelope':hits[id],'native_cap_height':fonts[id],'portal_world_x':PORTALS[id]}
 for i,id in enumerate(IDS):
  for other in IDS[i+1:]:assert not intersects(hits[id],hits[other]),('hit overlap',id,other)
 audits=[];mesh_count=sum(obj.type=='MESH' for sign in ctx.signs.values() for obj in sign['objects']);mesh_audit_status='NOT_RUN'
 if args.mesh_audit:
  audit_path=args.mesh_audit.expanduser().resolve();assert audit_path.is_file();audit_spec=importlib.util.spec_from_file_location('explicit_mesh_audit',audit_path);bx_audit=importlib.util.module_from_spec(audit_spec);audit_spec.loader.exec_module(bx_audit);audits=[{'name':obj.name,**bx_audit.deliverable([obj],profile='render')} for sign in ctx.signs.values() for obj in sign['objects'] if obj.type=='MESH'];assert all(item['pass'] for item in audits),[v for v in audits if not v['pass']];mesh_audit_status='PASS'

 def render(path,r):
  x0,y0,x1,y1=r;s.render.use_border=True;s.render.use_crop_to_border=True;s.render.border_min_x=(x0+.01)/1600;s.render.border_max_x=(x1+.01)/1600;s.render.border_min_y=(1024-y1+.01)/1024;s.render.border_max_y=(1024-y0+.01)/1024;s.render.filepath=str(path);bpy.ops.render.render(write_still=True);pixels=N.read_rgba(path);assert pixels.shape[:2]==(y1-y0,x1-x0);return pixels
 if args.preview:
  combined=merge([merge(base_rects[id]) for id in IDS]);assert all(not intersects(merge(base_rects[id]),merge(base_rects[other])) for i,id in enumerate(IDS) for other in IDS[i+1:]),'Preview crop overlap'
  for palette in ['day','night']:
   ctx.palette(palette)
   for lang in ['en','ro']:
    ctx.language(lang)
    for id,sign in ctx.signs.items():sign['root'].location=base[id][0].copy();sign['root'].rotation_euler=base[id][1].copy()
    bpy.context.view_layer.update();pixels=render(out/f'combined-{palette}-{lang}.png',combined)
    for id,entry in geometry.items():
     r=entry['crop'];x=r['x']-combined[0];y=r['y']+227-combined[1];name=f'city-wayfinding-{id}-{palette}-{lang}.png';N.save_rgba(name,pixels[y:y+r['height'],x:x+r['width']],out/name);entry['languages'].setdefault(lang,{})[palette]=name
 else:
  for id,entry in geometry.items():
   for palette in ['day','night']:
    ctx.palette(palette)
    for lang in ['en','ro']:
     if lang=='ro' and TEXT[id]['en']==TEXT[id]['ro']:entry['languages'].setdefault(lang,{})[palette]=entry['languages']['en'][palette];continue
     ctx.language(lang)
     for other,sign in ctx.signs.items():
      for obj in sign['objects']:obj.hide_render=other!=id
     r=entry['crop'];rect=[r['x'],r['y']+227,r['x']+r['width'],r['y']+227+r['height']];frames=[]
     for index in range(count):pose(id,index);bpy.context.view_layer.update();frames.append(render(out/f'raw-{id}-{palette}-{lang}-{index}.png',rect))
     name=f'city-wayfinding-{id}-{palette}-{lang}.png';N.save_rgba(name,np.concatenate(frames,axis=1),out/name);entry['languages'].setdefault(lang,{})[palette]=name
 for id,sign in ctx.signs.items():
  for obj in sign['objects']:obj.hide_render=False
  sign['root'].animation_data.action=actions[id]
 s.frame_set(1);s.render.use_border=False;s.render.use_crop_to_border=False;ctx.language('ro');ctx.palette('night')
 # Packed bytes remain unchanged; remove workstation-specific source path hints.
 for font in bpy.data.fonts:
  if font.packed_file:font.filepath='//fonts/'+Path(font.filepath.replace('\\','/')).name
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'source.blend'),compress=True,relative_remap=False)
 assert all(sha(ROOT/path)==value for path,value in inputs.items()),'Original source/font changed'
 assets={p.name:{'bytes':p.stat().st_size,'sha256':sha(p),'dimensions':list(struct.unpack('>II',p.read_bytes()[16:24])),'decoded_rgba_bytes':math.prod(struct.unpack('>II',p.read_bytes()[16:24]))*4} for p in sorted(out.glob('city-wayfinding-*.png'))};assert all(assets[file]['dimensions']==[entry['crop']['width']*entry['frame_count'],entry['crop']['height']] for entry in geometry.values() for maps in entry['languages'].values() for file in maps.values());contract={'schema':1,'preview':args.preview,'signs':geometry,'duration_ms':0 if args.preview else count*50,'float_duration_ms':4000,'float_keyframes':motion,'candidate_sha256':sha(candidate),'renderer_sha256':sha(Path(__file__)),'original_inputs':inputs,'projection_errors_px':projection,'devices':devices,'assets':assets,'source_sha256':sha(out/'source.blend'),'research_provenance':{'renderer_v2_sha256':'d226347af6b37f1604ee02c8759647fb09c4399e523297b54d6dc7e4cf099aaf','winning_candidate_sha256':'548eaea784fbe20bf8283a9e409a8bda894c1b052707243914108c42dbbbadb3','retained_private_mesh_audit_required_for_research_claim':True},'text_audit':text_audit,'gates':{'unicode':True,'unstretched_native_cap_14_16':True,'target48_nonoverlap':True,'all_intro_bob_object_beacon_clearance':True,'viewport58_480':True,'mesh_parts':mesh_count,'full_mesh_audit':mesh_audit_status,'mesh_errors':0 if mesh_audit_status=='PASS' else None,'original_inputs_unchanged':True,'four_locale_palette_matrix':True,'loop_pure_translation':True}};write(out/'contract.json',contract);write(out/'audit.json',{'geometry':geometry,'mesh':audits});print(json.dumps({'out':str(out),'mode':'preview' if args.preview else 'final','gates':contract['gates'],'assets':len(assets)}),flush=True)
if __name__=='__main__':main()
