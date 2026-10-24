"""Original varied city massing. Blender5.2 headless; legacy assets stay intact."""
import argparse,hashlib,json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
import build_ambient_city as B
import build_ambient_city_v2 as V
box,cone,poly=B.box,B.cone,B.poly
R=random.Random(241026)
LANDMARKS={3,10,12}

def line(mat,a,b,r=.025,sides=8):
 a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
 if u.length<.01:u=axis.cross(Vector((0,1,0)))
 u.normalize();v=axis.cross(u);pts=[]
 for center in (a,b):
  pts.extend(tuple(center+r*(u*math.cos(i*math.tau/sides)+v*math.sin(i*math.tau/sides))) for i in range(sides))
 faces=[tuple(reversed(range(sides))),tuple(range(sides,sides*2))]+[(i,(i+1)%sides,(i+1)%sides+sides,i+sides) for i in range(sides)]
 poly(mat,pts,faces)

def sphere(mat,x,y,z,rx,ry,rz):
 # Closed low-poly ellipsoid: deliberately broad dome, no tiny tessellation.
 n=24;rings=8;pts=[(x,y,z-rz)]
 for j in range(1,rings):
  phi=-math.pi/2+j*math.pi/rings
  pts.extend((x+rx*math.cos(phi)*math.cos(i*math.tau/n),y+ry*math.cos(phi)*math.sin(i*math.tau/n),z+rz*math.sin(phi)) for i in range(n))
 pts.append((x,y,z+rz));top=len(pts)-1
 faces=[(0,1+(i+1)%n,1+i) for i in range(n)]
 for j in range(rings-2):
  first=1+j*n;next_=first+n
  faces.extend((first+i,first+(i+1)%n,next_+(i+1)%n,next_+i) for i in range(n))
 faces.extend((top,1+(rings-2)*n+i,1+(rings-2)*n+(i+1)%n) for i in range(n))
 poly(mat,pts,faces)

def pane(x,y,z,w,h,on=False,pointed=False):
 V.pane(x,y,z,w,h,('window-amber' if on else 'window-dark'),pointed)

def windows(x,y,z,w,h,cols=3,rows=5,arched=False):
 for row in range(rows):
  occupied=R.random()<.47
  for col in range(cols):
   pane(x+(col-(cols-1)/2)*w/max(1,cols),y,z+row*h/max(1,rows),w/(cols*2),h/(rows*1.7),occupied and col%3!=2,arched)

def original_landmark(i):
 x,h,w=V.POSITIONS[i];y=.4+(i%3)*.24;st=['stone-blue','stone-charcoal','stone-slate'][i%3];face=y-.6
 box(st,x,y,0,w,1.15,h);box('stone-trim',x,y,h-.13,w+.08,1.23,.14);box(st,x,face-.025,.05,w+.06,.12,.3)
 cols=max(2,int(w/.3));rows=int((h-.45)/.53)
 for col in range(cols+1):box('stone-trim' if i%3==0 else st,x-w*.43+col/cols*w*.86,face-.075,.3,.055,.16,h-.38)
 for row in range(rows):
  floor_on=R.random()<(.57 if i in (3,7,10) else .36);group=R.randrange(max(1,cols-1))
  for col in range(cols):
   mat=('window-cool' if (i+row)%4==0 else 'window-amber' if (row+col)%3 else 'window-warm') if floor_on and abs(col-group)<2 else 'window-dark'
   V.pane(x-w*.35+col/(cols-1)*w*.7,face-.09,.32+row*.53,.12 if cols>3 else .16,.27 if i%3 else .32,mat,i in (3,7,10) and row>=rows-2)
  if i%3==1 and row%2==0:box(st,x,face-.04,.24+row*.53,w,.07,.085)
 for level in [.3,h*.48,h-.22]:box('stone-trim',x,face-.03,level,w+.035,.12,.055)
 if i in (3,7,10):
  for dx in [-w*.47,w*.47]:box(st,x+dx,face-.1,.15,.11,.24,h-.11)
 V.crown(i,x,y,h,w,st)

def warehouse(x=-12,y=.75):
 box('stone-brick',x,y,0,1.8,1.4,2.15)
 for z in [.18,1.05,2.1]:box('stone-trim',x,y-.74,z,1.88,.12,.09)
 for dx in [-.58,0,.58]:pane(x+dx,y-.76,.3,.34,.6,dx==0,True);pane(x+dx,y-.76,1.27,.35,.54,dx!=0,True)
 # Sawtooth production hall, physically thick asymmetric roof sections.
 for dx in [-.58,0,.58]:
  points=[(x+dx-.3,y-.75,2.2),(x+dx+.3,y-.75,2.2),(x+dx+.3,y-.75,2.66),(x+dx-.3,y+.75,2.2),(x+dx+.3,y+.75,2.2),(x+dx+.3,y+.75,2.66)]
  poly('roof-copper',points,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)])
 box('metal',x+.72,y+.3,2.5,.18,.18,.8)

def chamfered(mat,x,y,z,w,d,h,cut=.2):
 pts=[(-w/2+cut,-d/2),(w/2-cut,-d/2),(w/2,-d/2+cut),(w/2,d/2-cut),(w/2-cut,d/2),(-w/2+cut,d/2),(-w/2,d/2-cut),(-w/2,-d/2+cut)]
 points=[(x+px,y+py,z+zz) for zz in (0,h) for px,py in pts]
 poly(mat,points,[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)])

def cinema(x=-10.3,y=.85):
 # Dark Deco cinema: chamfered black mass, cantilever marquee and vertical fins.
 chamfered('stone-oxblood',x,y,0,1.9,1.55,3.6,.24)
 chamfered('roof-copper',x-.14,y,3.6,1.5,1.3,.32,.18)
 box('stone-trim',x,y-.85,2.95,2.1,.38,.13)
 box('stone-charcoal',x,y-.88,.12,1.6,.16,.7)
 for dx in [-.6,-.2,.2,.6]:pane(x+dx,y-.99,.25,.17,.43,dx<.3)
 for dx in [-.5,-.25,0,.25,.5]:
  box('metal',x+dx,y-.82,1.08,.13,.08,1.58)
  box('stone-trim',x+dx+.09,y-.87,1.05,.045,.09,1.68)
 box('stone-charcoal',x-.43,y-.85,3.2,.31,.14,.8)
 for z in [3.3,3.53,3.76]:box('window-dim',x-.43,y-.94,z,.15,.025,.07)

def buttress_office(x=-5.65,y=1.05):
 # Asymmetric monumental slab, stepped shoulders and a diagonal parapet cut.
 chamfered('stone-charcoal',x,y,0,2.65,1.9,3.5,.22)
 box('stone-oxblood',x-.76,y,0,.65,1.7,5.0)
 box('stone-oxblood',x+.88,y,0,.46,1.4,4.25)
 chamfered('stone-charcoal',x-.12,y,3.5,1.35,1.5,.66,.18)
 box('stone-trim',x-.76,y,4.9,.76,1.85,.13)
 box('metal',x+.88,y,4.2,.58,1.5,.12)
 for dx in [-.38,0,.38]:
  box('recess',x+dx,y-1.02,.3,.21,.08,3.57)
  for z in [.45,1.02,1.59,2.16,2.73,3.3]:pane(x+dx,y-1.07,z,.12,.29,(int(z*10)+int(dx*10))%3!=0)
 for dx in [-.76,.88]:
  for z in [1,2,3,3.7]:pane(x+dx,y-.89,z,.13,.36,z<2)
 # Offset entrance arcade remains architectural, not church tracery.
 box('stone-trim',x+.13,y-1.07,.12,.74,.32,.12)
 for dx in [-.22,.22]:box('stone-trim',x+.13+dx,y-1.07,.25,.08,.25,.76)
 box('window-dim',x+.13,y-1.02,.25,.31,.03,.62)

def civic(x=-2.3,y=.64):
 # Monumental flat-capped Deco lantern. No frozen clock or picturesque spire.
 chamfered('stone-limestone',x,y,0,1.8,1.5,5.3,.18)
 for dx in [-.66,-.3,.3,.66]:box('stone-charcoal',x+dx,y-.82,.3,.12,.12,4.8)
 windows(x,y-.84,.4,1.15,4.4,3,8)
 for z,w in [(0,1.98),(5.15,1.96),(6.15,1.5),(6.98,1.07)]:box('metal',x,y,z,w,1.58,.12)
 chamfered('stone-oxblood',x,y,5.3,1.44,1.24,.92,.16)
 for dx in [-.42,0,.42]:box('recess',x+dx,y-.66,5.48,.18,.04,.48)
 chamfered('stone-charcoal',x,y,6.3,1.0,1.0,.65,.11)
 for dx in [-.33,0,.33]:
  box('civic-lamp',x+dx,y-.52,6.41,.115,.025,.36)
 box('stone-trim',x,y,7.09,.73,.82,.13)
 box('metal',x-.14,y,7.22,.16,.22,.33)


def deco(x=1.1,y=.7):
 for z,w,h,dx in [(0,1.42,2.5,-.04),(2.5,1.05,1.25,.1),(3.75,.7,.8,.2)]:
  box('stone-oxblood',x+dx,y,z,w,1.25,h);box('stone-trim',x+dx,y,z+h-.09,w+.08,1.3,.1)
  windows(x+dx,y-.68,z+.25,w*.8,h-.3,3,round(h/.5))
 for dx in [-.56,.56]:box('metal',x+dx,y-.7,.15,.06,.09,2.2)
 cone('roof-copper',x+.2,y,4.55,.35,.52,sides=4)

def industrial(x=8,y=.95):
 box('stone-brick',x,y,0,1.45,1.8,2.8)
 windows(x,y-.95,.35,1.2,2.1,3,4)
 box('stone-trim',x,y-.97,2.73,1.6,.15,.14)
 # Twin brick stacks and a cylindrical water tank break the roof rhythm.
 for dx,h in [(-.42,1.9),(.13,1.2)]:
  cone('stone-brick',x+dx,y+.3,2.8,.14,h,top=.105,sides=12)
  cone('stone-trim',x+dx,y+.3,2.8+h,.15,.08,top=.15,sides=12)
 for dx in [-.3,.3]:line('metal',(x+.42+dx,y-.15,2.8),(x+.42+dx,y-.15,3.3),.025)
 cone('metal',x+.42,y-.15,3.3,.36,.55,top=.36,sides=16);cone('roof-copper',x+.42,y-.15,3.85,.39,.16,sides=16)

def exchange(x=10.1,y=1.1):
 # Chamfered financial exchange with separated shoulders and a narrow crown.
 chamfered('stone-charcoal',x,y,0,1.9,1.65,3.0,.28)
 chamfered('stone-limestone',x-.14,y,3.0,1.38,1.4,.82,.2)
 chamfered('stone-oxblood',x-.14,y,3.82,.87,1.05,.65,.16)
 box('metal',x-.14,y,4.47,1.0,1.15,.13)
 for dx in [-.62,0,.62]:
  box('metal',x+dx,y-.87,.25,.09,.12,2.6)
  for z in [.5,1.2,1.9]:pane(x+dx+.15,y-.91,z,.16,.33,dx<.2)
 for dx in [-.36,.08]:pane(x+dx,y-.77,3.15,.12,.43,True)
 box('recess',x,y-.88,.1,.44,.04,.72)


def streets():
 # Broad three/four-storey blocks alternate with arcades and planted gaps.
 shops=[(-12,.85,.95),(-10.6,1.28,1.3),(-8.8,.9,1.4),(-6.75,1.52,1.5),(-4.5,1.0,1.45),(-1.15,1.5,1.45),(1.1,1.1,1.15),(4.2,1.42,1.5),(7.0,1.03,1.1),(9.2,1.3,1.2),(12,1.05,1.6)]
 for i,(x,h,w) in enumerate(shops):
  st=['stone-brick','front-stone','stone-oxblood','stone-limestone'][i%4];box(st,x,-1.1,.04,w,.74,h)
  box('stone-trim',x,-1.1,h,w+.08,.84,.09)
  windows(x,-1.52,h*.6,w*.85,h*.31,3,1)
  if i%3==0:
   box('roof-copper',x-w*.1,-1.1,h+.1,w*.76,.74,.24)
  elif i%3==1:
   for dx in [-w*.33,w*.33]:box(st,x+dx,-1.1,h+.05,.14,.65,.25)
  else:box('roof-copper',x,-1.1,h+.08,w,.7,.1)
  for dx in [-w*.26,w*.26]:pane(x+dx,-1.53,.17,w*.3,.44,True,False)
  if i%3==1:box('awning',x,-1.7,.7,w+.08,.35,.08)
 # Planted plaza gaps and low warm bollards, rather than a repeated picket row.
 for x in [-3.9,2.45,5.7]:
  box('stone-trim',x,-1.35,.02,.85,.7,.16)
  for dx in [-.28,.28]:
   line('metal',(x+dx,-1.35,.18),(x+dx,-1.35,.72),.035)
   sphere('foliage',x+dx,-1.35,.9,.23,.2,.32)
 for x in [-11.1,-7.9,-3.6,.2,5.2,8.45,11.1]:
  line('metal',(x,-1.95,.1),(x,-1.95,1.22),.022)
  box('lamp-warm',x,-1.95,1.2,.12,.1,.1);box('metal',x,-1.95,1.31,.18,.15,.03)
 # Established viaduct rhythm belongs to one continuous engineered structure.
 for i in range(24):
  x=-13+i*1.14;box('viaduct',x,-2.35,0,.17,.47,.5)
  for j in range(10):
   a=math.pi-j*math.pi/10;b=math.pi-(j+1)*math.pi/10;pts=[]
   for y in [-2.61,-2.11]:
    pts.extend((x+.57+math.cos(angle)*radius,y,.17+math.sin(angle)*radius*.54) for radius,angle in [(.48,a),(.48,b),(.56,b),(.56,a)])
   poly('viaduct' if j%3 else 'viaduct-key',pts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
 box('viaduct',0,-2.35,.48,28,.55,.14)
 for y in [-2.65,-2.32]:box('metal',0,y,.64,28,.025,.035)
 for i in range(104):box('metal',-14+i*.275,-2.65,.59,.018,.026,.16)
 box('metal',0,-2.65,.75,28,.025,.024);box('front-stone',0,-2.2,-.2,29,1.4,.19)

def city():
 for i in range(22):
  x=-13+i*1.22;h=R.uniform(1.2,3.5);w=R.uniform(.55,1.1)
  box('distant-stone',x,3.15,0,w,1.1,h)
  if i%3==0:box('distant-trim',x-.1,3.15,h,w*.5,.8,.38)
 for i in sorted(LANDMARKS):original_landmark(i)
 # Telecom landmark keeps its exact mounted roof, but becomes a broad,
 # asymmetric compound rather than a twin of the slender radio tower.
 for x,w,h in [(-9.0,.7,3.4),(-7.12,.45,2.7)]:
  box('stone-blue',x,.9,0,w,1.3,h);box('stone-trim',x,.9,h-.1,w+.1,1.4,.11)
  windows(x,.21,.35,w*.8,h-.6,2,max(1,round(h/.56)))
 warehouse();cinema();buttress_office();civic();deco();industrial();exchange()
 # Low colonnaded exchange and brick apartment are secondary volumes.
 box('stone-limestone',-.35,1.1,0,1.5,1.4,2.35)
 for dx in [-.55,-.18,.18,.55]:box('stone-trim',-.35+dx,.31,.2,.09,.2,2.12)
 box('stone-trim',-.35,.3,2.25,1.66,.3,.18)
 for dx in [-.36,0,.36]:pane(-.35+dx,.28,.4,.18,1.35,True,False)
 box('stone-brick',4.7,1.15,0,1.28,1.5,2.5);windows(4.7,.34,.3,1.0,1.9,3,4)
 box('stone-trim',4.7,.32,2.42,1.45,.17,.14)
 for k in range(3):box('roof-copper',4.3+k*.4,1.15,2.53,.25,.8,.21)
 box('stone-oxblood',12.3,1.1,0,1.55,1.6,3.1);windows(12.3,.25,.3,1.3,2.6,3,5)
 box('stone-trim',12.3,.23,3,1.72,.18,.15)
 streets()

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--preview',action='store_true');p.add_argument('--audit-scripts',type=Path)
 args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve();source=root/'assets/blender/city-v3';private=root/'.runtime/city-v3-20261024/blender';out=root/'app/ui/public/ambient'
 source.mkdir(parents=True,exist_ok=True);private.mkdir(parents=True,exist_ok=True)
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.context.preferences.filepaths.save_version=0
 scene=bpy.context.scene;scene.name='PySH_City_v3';B.settings(scene,1600,570);scene.render.image_settings.compression=100
 scene.eevee.use_raytracing=True;scene.eevee.taa_render_samples=32 if args.preview else 96;scene.eevee.ray_tracing_options.resolution_scale='1';scene.eevee.ray_tracing_options.denoise_temporal=False
 colors={'stone-blue':(.12,.16,.19),'stone-charcoal':(.085,.106,.12),'stone-slate':(.15,.175,.18),'stone-trim':(.18,.2,.21),'stone-brick':(.14,.06,.055),'stone-oxblood':(.11,.035,.045),'stone-limestone':(.12,.135,.14),'roof-copper':(.06,.10,.11),'metal':(.045,.065,.075),'distant-stone':(.10,.14,.17),'distant-trim':(.12,.165,.18),'front-stone':(.035,.045,.06),'viaduct':(.12,.14,.155),'viaduct-key':(.17,.185,.19),'window-dark':(.018,.031,.043),'recess':(.018,.025,.034),'window-warm':(.72,.43,.19),'window-amber':(.56,.35,.17),'window-dim':(.24,.24,.18),'window-cool':(.27,.4,.43),'shop-warm':(.54,.36,.2),'lamp-warm':(.78,.55,.28),'civic-lamp':(.58,.35,.16),'awning':(.1,.16,.15),'foliage':(.055,.09,.07)}
 emit={'window-warm':1.5,'window-amber':1,'window-dim':.28,'window-cool':.65,'shop-warm':.9,'lamp-warm':2,'civic-lamp':.45}
 for name,color in colors.items():B.material(name,color,emit.get(name,0))
 solid_parts=[];open_planes=[];original_poly=B.poly
 def recorded_poly(mat,points,faces):
  if len(faces)>1:
   # Every solid primitive here is convex. Orient its authored faces outward;
   # this also repairs winding of custom sawtooth/gable wedge end caps.
   center=sum((Vector(p) for p in points),Vector())/len(points);oriented=[]
   for face in faces:
    normal=(Vector(points[face[1]])-Vector(points[face[0]])).cross(Vector(points[face[2]])-Vector(points[face[0]]))
    middle=sum((Vector(points[i]) for i in face),Vector())/len(face)
    oriented.append(tuple(reversed(face)) if normal.dot(middle-center)<0 else face)
   faces=oriented
  original_poly(mat,points,faces)
  (solid_parts if len(faces)>1 else open_planes).append((mat,points,faces))
 B.poly=recorded_poly;V.poly=recorded_poly
 globals()['poly']=recorded_poly
 city();B.poly=original_poly;V.poly=original_poly;globals()['poly']=original_poly
 objects=B.flush('City_v3_');B.camera(scene,(0,-42,14),(0,0,3.7),28.6)
 key=B.light(scene,'Moon_key','AREA',(-10,-8,15),(.59,.72,.95),1100,7);fill=B.light(scene,'Urban_fill','AREA',(10,5,8),(.38,.53,.65),135,15);rim=B.light(scene,'Roof_rim','AREA',(5,1,12),(.48,.63,.66),330,8);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.21
 practicals=[]
 for index,x in enumerate([-11.1,-7.9,-3.6,.2,5.2,8.45,11.1]):
  light=B.light(scene,f'Street_practical_{index}','POINT',(x,-1.92,1.17),(1,.58,.28),5,.15);light.data.shadow_soft_size=.18;practicals.append(light)
 bpy.context.view_layer.update()
 from bpy_extras.object_utils import world_to_camera_view
 def anchor(pt):
  v=world_to_camera_view(scene,scene.camera,Vector(pt));return[round(v.x*100,3),round((1-v.y)*100,3)]
 radio=anchor((3,.64,6.9));bt=anchor((-8.1,.4,6.65));assert radio==[60.49,18.001] and bt==[21.678,20.945]
 vertices=sum(len(o.data.vertices) for o in objects);triangles=sum(len(f.vertices)-2 for o in objects for f in o.data.polygons);assert vertices<200000 and triangles<80000
 scene['radio_anchor_percent']=radio;scene['bluetooth_anchor_percent']=bt;scene['wifi_roof_world']=[6.3,.4,4.58];scene['source_license']='Original procedural PySH geometry/materials; no downloaded models/textures.'
 scene['brief']='Original Dark Deco1930s noir silhouettes, fixed service landmarks and native800x208 target.'
 bpy.ops.wm.save_as_mainfile(filepath=str(private/'stage-01-massing.blend'),compress=True)
 scene.render.resolution_percentage=50 if args.preview else 100;destination=private if args.preview else out;suffix='preview' if args.preview else 'v3'
 B.render(scene,destination/f'gothic-city-night-{suffix}.png')
 key.data.color=(1,.89,.74);key.data.energy=3400;fill.data.energy=1200;rim.data.energy=800;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
 for light in practicals:light.data.energy=0
 for name in emit:
  shader=B.MATERIALS[name].node_tree.nodes['Principled BSDF'];shader.inputs['Emission Strength'].default_value=.05
  if name.startswith('window'):shader.inputs['Base Color'].default_value=(.12,.17,.18,1)
 B.render(scene,destination/f'gothic-city-day-{suffix}.png')
 for name,value in emit.items():
  shader=B.MATERIALS[name].node_tree.nodes['Principled BSDF'];shader.inputs['Emission Strength'].default_value=value;shader.inputs['Base Color'].default_value=(*colors[name],1)
 key.data.color=(.59,.72,.95);key.data.energy=1100;fill.data.energy=135;rim.data.energy=330;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.21
 for light in practicals:light.data.energy=5
 report={'version':3,'blender':bpy.app.version_string,'resolution':[1600,570],'vertices':vertices,'triangles':triangles,'objects':len(objects),'radio_anchor':radio,'bluetooth_anchor':bt,'wifi_roof_world':[6.3,.4,4.58],'camera':{'position':[0,-42,14],'target':[0,0,3.7],'ortho_scale':28.6},'seed':241026,'architecture':['sawtooth-brick-factory','chamfered-cinema-palace','asymmetric-buttressed-office','monumental-deco-lantern','stepped-oxblood-deco','industrial-chimney-water-tank','chamfered-financial-exchange','colonnaded-exchange','pitched-industrial-apartment','deco-street-shops'],'preserved_landmark_indices':sorted(LANDMARKS),'limits':'Offline transparent raster architecture; intentional separate architectural parts and open decorative window panes; not watertight/game export. Actual browser/fog/native acceptance separate.'}
 if not args.preview:
  audit_path=args.audit_scripts or Path.home()/'.codex/skills/scenario-blender-expert/scripts'
  if not (audit_path/'bx_audit.py').is_file():raise RuntimeError('Provide --audit-scripts for the installed Blender expert audit helper')
  sys.path.insert(0,str(audit_path));import bx_audit
  audits=[]
  for index,(material,points,faces) in enumerate(solid_parts):
   mesh=bpy.data.meshes.new(f'GatePart{index:04d}');mesh.from_pydata(points,[],faces);mesh.update();ob=bpy.data.objects.new(mesh.name,mesh);ob.data.materials.append(B.MATERIALS[material]);scene.collection.objects.link(ob)
   result=bx_audit.deliverable([ob],profile='render',evaluated=False)
   audits.append({'index':index,'material':material,'pass':result['pass'],'errors':result['errors'],'warnings':result['warnings']})
   bpy.data.objects.remove(ob,do_unlink=True);bpy.data.meshes.remove(mesh)
  assert all(a['pass'] for a in audits),'Closed primitive delivery gate failed'
  material_counts={name:sum(a['material']==name for a in audits) for name in sorted({a['material'] for a in audits})}
  (private/'mesh-audit-parts.json').write_text(json.dumps(audits,indent=2)+'\n',encoding='utf-8')
  (source/'mesh-audit.json').write_text(json.dumps({'profile':'render','scope':'Each actually authored closed architectural primitive gated independently; open ornamental/window planes and intentional city-part spacing are not a watertight assembly. Full per-part gate results retained in private builder evidence.','closed_parts':len(audits),'intentional_open_planes':len(open_planes),'errors':sum(len(a['errors']) for a in audits),'warnings':sum(len(a['warnings']) for a in audits),'by_material':material_counts,'issues':[a for a in audits if a['errors'] or a['warnings']]},indent=2)+'\n',encoding='utf-8')
  report['closed_parts_audited']=len(audits);report['intentional_open_planes']=len(open_planes);report['delivery_errors']=sum(len(a['errors']) for a in audits);report['delivery_warnings']=sum(len(a['warnings']) for a in audits)
  scene.render.resolution_percentage=100;bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-city-v3.blend'),compress=True)
  report['assets']=[{'name':name,'bytes':(out/name).stat().st_size,'sha256':hashlib.sha256((out/name).read_bytes()).hexdigest()} for name in ['gothic-city-night-v3.png','gothic-city-day-v3.png']]
  report['encoded_bytes']=sum(a['bytes'] for a in report['assets']);report['rgba_decoded_bytes']=1600*570*4*2;report['builder_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();report['source_sha256']=hashlib.sha256((source/'pysh-city-v3.blend').read_bytes()).hexdigest()
  (source/'build-report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 (private/('preview-report.json' if args.preview else 'build-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('RESULT '+json.dumps(report),flush=True)

if __name__=='__main__':main()
