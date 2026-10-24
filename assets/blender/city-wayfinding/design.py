"""R03T03: naturally narrower Barlow400, reduced physical rim at measured14.45px cap; champion positions and stems retained."""
import bpy,hashlib
from mathutils import Vector

def build(ctx):
 font_path=ctx.root/'assets/blender/city-wayfinding/fonts/BarlowSemiCondensed-Regular.ttf'
 assert hashlib.sha256(font_path.read_bytes()).hexdigest()=='e8c7242f612b13d026e18a94b63b0fd079e91a3faf009d1b6981dbb5f16d1153'
 font=bpy.data.fonts.load(str(font_path));font.pack()
 face=ctx.material('quiet-face',(.004,.012,.016),(.80,.85,.82),emit_night=.8,metallic=.08,roughness=.65)
 rim=ctx.material('quiet-keyline',(.82,.87,.84),(.002,.004,.006),emit_day=.08,roughness=.9)
 pointer=ctx.material('soft-pointer',(.10,.17,.18),(.36,.49,.47),emit_night=.05,roughness=.8)
 centers={'media':(105,342,-3),'audio':(174,253,3),'settings':(335,276,-3),'radio':(482,246,3),'network':(580,300,-3)}
 for id,(x,y,yaw) in centers.items():
  sign=ctx.sign(id,x,y,yaw=yaw)
  main=ctx.text(sign,face,weight='500',size=1.44,tracking=1.0,extrude=.012,bevel=.0013,location=(0,-.10,0))
  back=ctx.text(sign,rim,weight='500',size=1.44,tracking=1.0,extrude=.014,bevel=.0008,offset=.025,location=(0,-.075,0),copy=True)
  main.data.font=font;back.data.font=font
  metric_curve=main.data.copy();metric_curve.body='H';metric=bpy.data.objects.new('CandidateCapMetric',metric_curve);ctx.collection.objects.link(metric);bpy.context.view_layer.update();metric.matrix_world=main.matrix_world.copy();metric.hide_render=True;bpy.context.view_layer.update()
  ys=[v[1] for v in metric.bound_box];a=ctx.native(metric.matrix_world@Vector((0,min(ys),0)));b=ctx.native(metric.matrix_world@Vector((0,max(ys),0)));height=abs(a[1]-b[1]);assert height>0
  uniform_size=main.data.size*14.45/height;main.data.size=uniform_size;back.data.size=uniform_size
  bpy.data.objects.remove(metric,do_unlink=True);bpy.data.curves.remove(metric_curve);bpy.context.view_layer.update()
  direction=Vector((sign['portal_x']-sign['root'].location.x,0,2.3-sign['root'].location.z)).normalized()
  start=Vector((0,0,-.43));end=start+direction*.20
  ctx.rod(sign,'short-pointer',start,end,.022,pointer)
 ctx.options.update(float_y=.9,float_x=.15,intro_yaw=[10,6,3,1,-.2,0],intro_y=[1.4,.9,.45,.15,-.05,0])
