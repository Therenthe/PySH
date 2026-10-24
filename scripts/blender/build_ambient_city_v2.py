"""Original architectural refinement of the PySH city; offline Blender 5.2.

Baseline remains in build_ambient_city.py and pysh-gothic-city-v1.blend.
Run headless/factory with --root REPO [--preview]. Only city/metro v2 are written.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).parent))
import build_ambient_city as B

POSITIONS = [(-12,2.9,1.1),(-10.8,3.8,1.25),(-9.3,2.4,.95),(-8.1,5.1,1.6),(-6.6,3.2,1.0),(-5.4,4.2,1.25),(-3.9,2.5,1.25),(-2.3,6.1,1.85),(-.5,3.15,1.3),(1.1,4.0,1.5),(3.0,5.3,1.7),(4.7,3.1,1.3),(6.3,4.1,1.5),(8.0,3.0,1.2),(9.7,4.6,1.6),(11.5,3.1,1.15)]
R = random.Random(231026)
box, cone, poly = B.box, B.cone, B.poly


def pane(x,y,z,w,h,mat,pointed=False):
    # Dark shadow reveal, narrow dressed sill; panes sit in front of the solid
    # wall but behind the jambs. Distinct depths supply real occlusion.
    box('recess',x,y,z-.025,w+.06,.045,h+.06)
    if pointed:
        outline=[(x-w/2,y-.027,z),(x+w/2,y-.027,z),(x+w/2,y-.027,z+h*.74),(x,y-.027,z+h),(x-w/2,y-.027,z+h*.74)]
        poly(mat,outline,[(0,1,2,3,4)])
    else:
        box(mat,x,y-.031,z,w,.024,h)
    box('stone-trim',x,y-.05,z-.035,w+.09,.08,.035)
    if w>.15:
        box('metal',x,y-.05,z,.018,.025,h*.85)


def crown(i,x,y,h,w,stone):
    if i in (3,10):
        # Existing anchored radio/Bluetooth landmarks keep exact geometry.
        for tier in range(3):
            tw=w*(.78-tier*.19)
            box(stone,x,y,h+tier*.26,tw,.88-tier*.16,.27)
            box('stone-trim',x,y,h+tier*.26+.23,tw+.04,.9-tier*.16,.055)
        cone('roof-copper',x,y,h+.78,w*.15,.42)
        cone('metal',x,y,h+1.15,.018,.45)
        cone('metal',x,y-.35,h+.1,.025,.85)
        for j in range(3):
            box('metal',x,y-.35,h+.35+j*.18,.38-j*.075,.035,.026)
    elif i==7:
        # Slender civic lantern replaces the repeated wedding-cake crown.
        box(stone,x,y,h,w*.73,.88,.21)
        box('stone-trim',x,y,h+.19,w*.78,.94,.065)
        box('recess',x,y,h+.25,w*.45,.62,.55)
        for dx in [-.31,-.105,.105,.31]:
            box('stone-trim',x+dx,y-.35,h+.24,.065,.09,.59)
            if abs(dx)<.2:
                pane(x+dx,y-.355,h+.35,.095,.28,'window-amber')
        box('stone-trim',x,y,h+.8,w*.53,.72,.09)
        cone('roof-copper',x,y,h+.89,.39,.63,sides=8)
        cone('metal',x,y,h+1.5,.016,.1)
    elif i==14:
        # High mansard with a short square belvedere.
        cone('roof-copper',x,y,h,w*.53,.54,top=w*.32,sides=4)
        box(stone,x,y,h+.5,w*.45,.55,.34)
        for dx in [-.17,.17]:
            pane(x+dx,y-.31,h+.56,.11,.19,'window-dim')
        box('stone-trim',x,y,h+.82,w*.5,.64,.08)
        cone('roof-copper',x,y,h+.9,.3,.36,sides=4)
    elif i==5:
        # Clock remains subordinate, flanked by a simple flat parapet.
        box(stone,x,y,h,w*.81,.87,.27)
        box('stone-trim',x,y,h+.25,w*.94,.97,.065)
        for j in range(24):
            a=j*math.tau/24
            box('stone-trim',x+math.cos(a)*.27,y-.66,h-.55+math.sin(a)*.27,.025,.035,.025)
        box('window-amber',x,y-.69,h-.57,.025,.025,.21)
        box('window-amber',x+.06,y-.69,h-.57,.14,.025,.025)
    elif i==12:
        # Exact original pitched roof underneath separately rendered Wi-Fi prop.
        cone('roof-copper',x,y,h,w*.4,.48,sides=4)
    elif i in (1,6,9,15):
        # Asymmetric setbacks and solid parapets break the repeating skyline.
        box(stone,x-w*.12,y,h,w*.72,.9,.25)
        box('stone-trim',x-w*.12,y,h+.23,w*.77,.96,.06)
        box('metal',x+w*.3,y,h,.14,.25,.43)
    elif i in (0,4,11):
        cone('roof-copper',x,y,h,w*.51,.42,top=w*.32,sides=4)
        for dx in [-.22,.22]:
            box(stone,x+dx,y-.32,h+.04,.17,.18,.24)
            box('roof-copper',x+dx,y-.32,h+.28,.2,.2,.04)
    else:
        box('stone-trim',x,y,h,w+.05,1.21,.075)
        cone('roof-copper',x-w*.17,y,h+.08,.19,.33,top=.19,sides=16)
        cone('metal',x-w*.17,y,h+.41,.22,.08)
        box('metal',x+w*.31,y,h+.08,.12,.17,.29)


def city():
    # Distant clustered blocks use quieter silhouette and less trim contrast.
    for i in range(33):
        x=-13+i*.82
        h=R.uniform(1.4,3.7)
        w=R.uniform(.5,1)
        box('distant-stone',x,2.6,0,w,1,h)
        box('distant-trim',x-.06,2.6,h,w*.68,.85,.17)
        if i%6==0:
            cone('distant-trim',x,2.6,h+.17,.15,.4)
    for i,(x,h,w) in enumerate(POSITIONS):
        y=.4+(i%3)*.24
        st=['stone-blue','stone-charcoal','stone-slate'][i%3]
        box(st,x,y,0,w,1.15,h)
        face=y-.6
        # Tall continuous piers alternate with broad masonry bays. Lower
        # pedestals and inset lintels give buildings weight at street level.
        box('stone-trim',x,y,h-.13,w+.08,1.23,.14)
        box(st,x,face-.025,.05,w+.06,.12,.3)
        cols=max(2,int(w/.3))
        rows=int((h-.45)/.53)
        for col in range(cols+1):
            px=x-w*.43+col/cols*w*.86
            box('stone-trim' if i%3==0 else st,px,face-.075,.3,.055,.16,h-.38)
        for row in range(rows):
            # Adjacent apartments share occupancy; office floors have quieter
            # long dark runs. Bright isolated cells are used sparingly.
            floor_on=R.random()<(.57 if i in (3,7,10) else .36)
            group=R.randrange(max(1,cols-1))
            for col in range(cols):
                wx=x-w*.35+col/(cols-1)*w*.7
                wz=.32+row*.53
                on=floor_on and abs(col-group)<2
                mat=('window-cool' if (i+row)%4==0 else 'window-amber' if (row+col)%3 else 'window-warm') if on else 'window-dark'
                if on and R.random()<.13: mat='window-dim'
                pane(wx,face-.09,wz,.12 if cols>3 else .16,.27 if i%3 else .32,mat,i in (3,7,10) and row>=rows-2)
            if i%3==1 and row%2==0:
                box(st,x,face-.04,wz-.08,w,.07,.085)
        # Bold enough to survive the 800-wide composition; no microscopic grout.
        for level in [.3,h*.48,h-.22]:
            box('stone-trim',x,face-.03,level,w+.035,.12,.055)
        if i in (3,7,10):
            for dx in [-w*.47,w*.47]:
                box(st,x+dx,face-.1,.15,.11,.24,h-.11)
        crown(i,x,y,h,w,st)
    # Street terrace with mansards, shop awnings, chimney clusters and small
    # differing cornices, retaining the low architectural foreground footprint.
    for i in range(24):
        x=-13+i*1.13
        h=.87+(.12,.42,.23,.57,.32,.16)[i%6]
        st=['front-stone','stone-charcoal','stone-slate'][i%3]
        box(st,x,-1.15,.04,1.06,.7,h)
        box('stone-trim',x,-1.15,h+.03,1.12,.79,.065)
        if i%3==0:
            cone('roof-copper',x,-1.15,h+.095,.55,.22,top=.4,sides=4)
        else:
            box('roof-copper',x,-1.15,h+.095,1.03,.65,.07)
        for wx in [-.31,0,.31]:
            pane(x+wx,-1.535,h-.31,.125,.21,'window-amber' if (i+int(wx*10))%5==0 else 'window-dark')
        if i%4==0:
            pane(x-.25,-1.535,.17,.23,.57,'window-dim',True)
            pane(x+.22,-1.535,.17,.32,.46,'window-dark')
            for j in range(5):box('metal',x+.22,-1.61,.2+j*.08,.32,.025,.015)
        elif i%4==1:
            pane(x-.14,-1.535,.17,.5,.39,'shop-warm')
            pane(x+.33,-1.535,.17,.13,.5,'window-dark')
            box('awning',x,-1.62,.71,1.02,.3,.055)
            for wx in [-.36,.05]:box('metal',x+wx,-1.62,.17,.024,.04,.43)
        else:
            for wx in [-.25,.25]:pane(x+wx,-1.535,.17,.25,.43,'window-dim' if i%5==2 else 'window-dark',i%4==3)
        for wx in [-.46,.46]:box('stone-trim',x+wx,-1.54,.05,.055,.07,h-.02)
        if i%3==0:
            for dx,dz in [(0,.24),(.15,.18)]:box('metal',x+.22+dx,-1.1,h+.14,.09,.14,dz)
        if i%3==0:
            cone('metal',x-.45,-1.9,.05,.016,1.13)
            box('lamp-warm',x-.45,-1.9,1.18,.065,.065,.1)
            box('metal',x-.45,-1.9,1.28,.11,.11,.025)
    # Solid segmented barrel arches: genuinely thick masonry, with shadowed
    # soffits and individual voussoirs, rather than a single flat front strip.
    for i in range(24):
        x=-13+i*1.14
        box('viaduct',x,-2.35,0,.17,.47,.5)
        box('stone-trim',x,-2.35,.02,.23,.53,.07)
        for j in range(10):
            a=math.pi-j*math.pi/10
            b=math.pi-(j+1)*math.pi/10
            pts=[]
            for y in [-2.61,-2.11]:
                for rad,ang in [(.48,a),(.48,b),(.56,b),(.56,a)]:
                    pts.append((x+.57+math.cos(ang)*rad,y,.17+math.sin(ang)*rad*.54))
            poly('viaduct' if j%3 else 'viaduct-key',pts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)])
    box('viaduct',0,-2.35,.48,28,.55,.14)
    box('stone-trim',0,-2.64,.51,28,.055,.04)
    for y in [-2.65,-2.32]:box('metal',0,y,.64,28,.025,.035)
    for i in range(104):
        x=-14+i*.275
        box('metal',x,-2.65,.59,.018,.026,.16)
    box('metal',0,-2.65,.75,28,.025,.024)
    box('front-stone',0,-2.2,-.2,29,1.4,.19)


def metro():
    # Four coupled cars with narrow articulated ends, bogies, door recesses,
    # roof ventilation and restrained turquoise waist stripe.
    for i in range(4):
        x=(i-1.5)*1.1
        box('train-body',x,0,0,1.025,.4,.36)
        box('train-roof',x,0,.35,.99,.38,.07)
        box('train-accent',x,-.212,.07,1.01,.025,.045)
        box('metal',x,-.21,0,1.03,.03,.055)
        for wx in [-.36,-.18,.18,.36]:pane(x+wx,-.213,.17,.115,.125,'train-window')
        box('recess',x,-.217,.1,.12,.025,.24)
        for dx in [-.033,.033]:box('train-window',x+dx,-.235,.2,.045,.02,.1)
        box('train-body',x,-.245,.1,.01,.02,.24)
        for dx in [-.28,.28]:
            box('metal',x+dx,0,-.075,.19,.29,.09)
            cone('metal',x+dx,-.15,-.075,.052,.05,sides=12)
            box('metal',x+dx,0,.42,.17,.23,.026)
        if i<3:box('recess',x+.55,0,.05,.07,.32,.24)
    box('lamp-warm',2.17,-.19,.12,.025,.035,.055)
    box('train-tail',-2.17,-.19,.12,.025,.035,.055)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True); p.add_argument('--preview',action='store_true')
    o=p.parse_args(sys.argv[sys.argv.index('--')+1:]); root=o.root.resolve()
    out=root/'app/ui/public/ambient'; source=root/'assets/blender'; private=root/'.runtime/city-polish-20261023/blender'
    private.mkdir(parents=True,exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.context.preferences.filepaths.save_version=0
    s=bpy.context.scene; s.name='PySH_Gothic_City_v2'; B.settings(s,1600,570)
    s.render.image_settings.compression=100
    s.eevee.use_raytracing=True; s.eevee.taa_render_samples=96 if not o.preview else 32
    s.eevee.ray_tracing_options.resolution_scale='1'
    s.eevee.ray_tracing_options.denoise_temporal=False
    colors={'stone-blue':(.12,.16,.19),'stone-charcoal':(.085,.106,.12),'stone-slate':(.15,.175,.18),'stone-trim':(.23,.255,.25),'roof-copper':(.09,.15,.145),'metal':(.045,.065,.075),'distant-stone':(.14,.185,.22),'distant-trim':(.145,.195,.23),'front-stone':(.075,.09,.105),'viaduct':(.12,.14,.155),'viaduct-key':(.17,.185,.19),'window-dark':(.025,.045,.058),'recess':(.018,.025,.034),'window-warm':(.72,.43,.19),'window-amber':(.56,.35,.17),'window-dim':(.24,.24,.18),'window-cool':(.27,.4,.43),'shop-warm':(.54,.36,.2),'lamp-warm':(.78,.55,.28),'awning':(.1,.16,.15),'train-body':(.24,.3,.31),'train-roof':(.125,.16,.175),'train-accent':(.08,.25,.22),'train-window':(.56,.43,.25),'train-tail':(.45,.035,.018)}
    emit={'window-warm':1.5,'window-amber':1.0,'window-dim':.28,'window-cool':.65,'shop-warm':.9,'lamp-warm':2,'train-window':1.15,'train-tail':1.4}
    for name,col in colors.items():B.material(name,col,emit.get(name,0))
    city(); city_objects=B.flush('City_v2_')
    B.camera(s,(0,-42,14),(0,0,3.7),28.6)
    key=B.light(s,'Moon_Key','AREA',(-10,-8,15),(.59,.72,.95),1100,7)
    fill=B.light(s,'Ambient_Fill','AREA',(10,5,8),(.38,.53,.65),135,15)
    rim=B.light(s,'Roof_Rim','AREA',(5,1,12),(.48,.63,.66),330,8)
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.21
    s['pysh_brief']='Original mature gothic/art-deco city; preserved camera, full city footprint and separate sky. 1600x570 RGBA, native800 runtime208px.'
    from bpy_extras.object_utils import world_to_camera_view
    bpy.context.view_layer.update()
    def anchor(pt):
        v=world_to_camera_view(s,s.camera,Vector(pt)); return [round(v.x*100,3),round((1-v.y)*100,3)]
    s['radio_anchor_percent']=anchor((3,.64,6.9)); s['bluetooth_anchor_percent']=anchor((-8.1,.4,6.65))
    s['wifi_roof_world']=[6.3,.4,4.58]
    s['source_license']='Original PySH procedural geometry/materials, no external textures or models.'
    assert list(s['radio_anchor_percent']) == [60.49,18.001]
    assert list(s['bluetooth_anchor_percent']) == [21.678,20.945]
    assert sum(len(a.data.vertices) for a in city_objects)<200000
    assert sum(len(f.vertices)-2 for a in city_objects for f in a.data.polygons)<80000
    s['stage']='architecture and night values'
    bpy.ops.wm.save_as_mainfile(filepath=str(private/'stage-01-architecture.blend'),compress=True)
    s.render.resolution_percentage=50 if o.preview else 100
    suffix='preview' if o.preview else 'v2'
    B.render(s,(private if o.preview else out)/('gothic-city-night-'+suffix+'.png'))
    key.data.color=(1,.89,.74); key.data.energy=3400; fill.data.energy=1200; rim.data.energy=800
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
    for name in emit:
        sh=B.MATERIALS[name].node_tree.nodes['Principled BSDF']
        sh.inputs['Emission Strength'].default_value=.05
        if name.startswith('window'):
            sh.inputs['Base Color'].default_value=(.12,.17,.18,1)
    B.render(s,(private if o.preview else out)/('gothic-city-day-'+suffix+'.png'))
    for name,value in emit.items():
        sh=B.MATERIALS[name].node_tree.nodes['Principled BSDF']
        sh.inputs['Emission Strength'].default_value=value
        sh.inputs['Base Color'].default_value=(*colors[name],1)
    key.data.color=(.59,.72,.95); key.data.energy=1100; fill.data.energy=135; rim.data.energy=330
    s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.21
    prop=bpy.data.scenes.new('PySH_Metro_v2'); B.settings(prop,512,96); bpy.context.window.scene=prop
    prop.render.image_settings.compression=100
    metro(); objs=B.flush('Metro_v2_')
    rig=bpy.data.objects.new('Metro_Passage_Control',None); prop.collection.objects.link(rig)
    for ob in objs:ob.parent=rig
    for frame,x in [(1,-16),(83,-16),(94,-15),(506,16),(516,16),(1032,16)]:
        rig.location.x=x; rig.keyframe_insert(data_path='location',frame=frame)
    from bpy_extras.anim_utils import action_get_channelbag_for_slot
    for curve in action_get_channelbag_for_slot(rig.animation_data.action,rig.animation_data.action_slot).fcurves:
        for k in curve.keyframe_points:k.interpolation='LINEAR'
    prop.frame_set(293); rig.location.x=0
    B.camera(prop,(0,-12,2),(0,0,.15),5); B.light(prop,'Metro_key','AREA',(-2,-5,6),(.7,.85,1),450,5)
    B.render(prop,(private if o.preview else out)/('metro-'+suffix+'.png'))
    bpy.context.window.scene=s; s.render.resolution_percentage=100
    report={'version':2,'blender':bpy.app.version_string,'seed':231026,'city_objects':len(city_objects),'city_vertices':sum(len(a.data.vertices) for a in city_objects),'city_polygons':sum(len(a.data.polygons) for a in city_objects),'transparent':True,'resolution':[1600,570],'radio_anchor':list(s['radio_anchor_percent']),'bluetooth_anchor':list(s['bluetooth_anchor_percent']),'wifi_roof_world':list(s['wifi_roof_world']),'camera':{'position':[0,-42,14],'target':[0,0,3.7],'ortho_scale':28.6},'metro_resolution':[512,96],'metro_timing':{'fps':24,'frames':1032,'crossing_frames':[94,506]},'authoring':'Original procedural Blender geometry, procedural stone, no external textures/models. v1 baseline retained.','scope':'City and metro only. Separate sky/stars/Moon/weather/network hardware assets unchanged.','limits':'Offline raster scenery; architectural islands and open window planes are intentional. Not a watertight/printable/game export. Browser/native-device acceptance separate.'}
    if not o.preview:
        bpy.ops.wm.save_as_mainfile(filepath=str(source/'pysh-gothic-city-v2.blend'),compress=True)
        report['assets']=[{'name':n,'bytes':(out/n).stat().st_size,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in ['gothic-city-night-v2.png','gothic-city-day-v2.png','metro-v2.png']]
        report['builder_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report['helper_sha256']=hashlib.sha256(Path(B.__file__).read_bytes()).hexdigest()
        report['encoded_bytes']=sum(a['bytes'] for a in report['assets'])
        report['rgba_decoded_bytes']=1600*570*4*2+512*96*4
        report['city_base_triangles']=sum(len(f.vertices)-2 for a in city_objects for f in a.data.polygons)
        report['png_compression']='RGBA8, Blender PNG compression100, lossless; no palette quantization.'
        (source/'build-report-v2.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (private/('preview-report.json' if o.preview else 'build-report.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('RESULT '+json.dumps(report),flush=True)


if __name__=='__main__':main()
