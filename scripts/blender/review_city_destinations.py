"""Reopen the editable city master; gate paths, closed props and decoded alpha.

Run headless/factory after build_city_destinations.py, with the same root and
an existing full FFmpeg. Raw probes and per-part records remain private.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).parent))
import build_radio_neon as N
import build_radio_entry as R


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--ffmpeg',type=Path,required=True)
 p.add_argument('--audit-scripts',type=Path,default=Path.home()/'.codex/skills/scenario-blender-expert/scripts')
 args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);root=args.root.resolve();assert args.ffmpeg.is_file()
 source=root/'assets/blender/city-destinations';private=root/'.runtime/city-destinations-authoring/review';private.mkdir(parents=True,exist_ok=True)
 report=json.loads((source/'build-report.json').read_text(encoding='utf-8'))
 assert sha(root/'assets/blender/city-v3/pysh-city-v3.blend')==report['source_original_sha256']
 assert sha(root/'scripts/blender/build_city_destinations.py')==report['builder_sha256']
 bpy.ops.wm.open_mainfile(filepath=str(source/'city-destinations.blend'))
 scene=bpy.context.scene;recipes=json.loads(scene['journey_actions_json']);old_camera=scene.camera
 scene.render.resolution_x=800;scene.render.resolution_y=480
 path_checks=[]
 for name,recipe in recipes.items():
  cam=bpy.data.objects['JourneyCamera_'+name];scene.camera=cam
  for ob_name,action_name in recipe['doors'].items():
   ob=bpy.data.objects[ob_name];action=bpy.data.actions[action_name];ob.animation_data_create();ob.animation_data.action=action;ob.animation_data.action_slot=action.slots[0]
  # Reapply the recorded builder's per-shot transit offset. The master retains
  # one actor staging setup; each movie builder positions its metro locally.
  x=report['anchors'][name]['world_x'];metro=bpy.data.objects['District_Metro'];metro.animation_data_clear()
  R.animate_travel(metro,(x-6,-2.485,.67),(x-2,-2.485,.67))
  previous=None;collisions=[];late=[];max_error=0
  for f in range(1,61):
   scene.frame_set(f);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();pos=cam.matrix_world.translation.copy()
   max_error=max(max_error,(pos-Vector(report['camera_positions'][name][f-1])).length)
   if previous is not None:
    delta=pos-previous
    if delta.length>1e-7:
     hit,loc,normal,poly,ob,matrix=scene.ray_cast(dg,previous,delta.normalized(),distance=delta.length)
     if hit:collisions.append({'frame':f,'object':ob.name})
   previous=pos
   if f>=54:
    frame=cam.data.view_frame(scene=scene)
    for u,v in [(.5,.5),(.5,.05)]:
     direction=(cam.matrix_world.to_3x3()@frame[2].lerp(frame[1],u).lerp(frame[3].lerp(frame[0],u),v)).normalized()
     hit,loc,normal,poly,ob,matrix=scene.ray_cast(dg,pos,direction)
     late.append({'frame':f,'uv':[u,v],'object':ob.name if hit else None})
  assert max_error<1e-4,(name,max_error)
  assert not collisions,(name,collisions)
  assert all(item['object'] and item['object'].startswith('District_'+name+'_') for item in late),(name,late)
  path_checks.append({'destination':name,'frames':60,'camera_max_error':max_error,'camera_segment_collisions':0,'late_rays':len(late),'matching_portal_only':True})
 scene.camera=old_camera
 sys.path.insert(0,str(args.audit_scripts));import bx_audit
 parts=[o for o in scene.objects if o.type=='MESH' and o.name.startswith('District_')]
 gates=[{'name':o.name,**bx_audit.deliverable([o],profile='render')} for o in parts]
 assert len(gates)==report['mesh']['parts'] and all(g['pass'] for g in gates)
 (private/'mesh-audit-parts.json').write_text(json.dumps(gates,indent=2)+'\n',encoding='utf-8')
 movies=[]
 for item in report['clips']:
  file=root/'app/ui/public/ambient'/item['name'];assert sha(file)==item['sha256']
  result=subprocess.run([str(args.ffmpeg),'-nostdin','-hide_banner','-loglevel','error','-c:v','libvpx','-i',str(file),'-progress','pipe:1','-nostats','-f','null','-'],capture_output=True,text=True);result.check_returncode()
  frames=[int(s.split('=',1)[1]) for s in result.stdout.splitlines() if s.startswith('frame=')];assert frames[-1]==60
  folder=private/file.stem;folder.mkdir(exist_ok=True)
  extract=subprocess.run([str(args.ffmpeg),'-nostdin','-hide_banner','-loglevel','error','-y','-c:v','libvpx','-i',str(file),'-vf',r'select=eq(n\,0)+eq(n\,59)','-fps_mode','vfr',str(folder/'%02d.png')],capture_output=True,text=True);extract.check_returncode()
  first=N.read_rgba(folder/'01.png');last=N.read_rgba(folder/'02.png');assert first.shape==(480,800,4) and last.shape==first.shape
  assert np.max(first[:20,:,3])<.001 and np.min(first[-8:,:,3])>.999 and np.min(last[:,:,3])>.999,item['name']
  movies.append({'name':file.name,'frames_decoded':frames[-1],'resolution':[800,480],'sky_alpha':0,'opening_ground_alpha':255,'threshold_alpha':255,'pass':True})
 for item in report['static_assets']:
  file=root/'app/ui/public/ambient'/item['name'];assert sha(file)==item['sha256']
  if 'rail-front' not in file.name:assert np.min(N.read_rgba(file)[-8:,:,3])>.999
 original=N.read_rgba(root/'app/ui/public/ambient/metro-v2.png');trim=N.read_rgba(root/'app/ui/public/ambient/metro-v4.png')
 left,top,right,bottom=report['metro']['lossless_alpha_bounds'];cropped=original[top:bottom,left:right]
 assert np.array_equal(cropped[:,:,3],trim[:,:,3]);mask=cropped[:,:,3]>0
 assert np.array_equal(cropped[mask],trim[mask])
 result={'pass':True,'blender':bpy.app.version_string,'source_original_unchanged':True,'editable_master_sha256':sha(source/'city-destinations.blend'),'camera_paths':path_checks,'mesh_parts':len(gates),'mesh_errors':sum(len(g['errors']) for g in gates),'mesh_warnings':sum(len(g['warnings']) for g in gates),'movies':movies,'metro_visible_rgba_and_alpha_identical':True,'metro':report['metro'],'reviewer_sha256':sha(Path(__file__)),'limits':'Offline authoring/codec/source gates; native UI/touch/decode and aesthetics require independent application/device review.'}
 (source/'review-report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('RESULT '+json.dumps(result),flush=True)


if __name__=='__main__':main()
