"""Audit authored sky meshes and render multi-view source reviews, offline only."""
import argparse
import json
from pathlib import Path
import sys

import bpy


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--skills-root',type=Path,required=True)
    options=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=options.root.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/sky3d/pysh-ambient-sky-v1.blend'))
    for skill in ['scenario-blender-expert','scenario-blender-lighting-rendering']:
        sys.path.append(str(options.skills_root/skill/'scripts'))
    import bx_audit
    import bx_review
    import bx_light
    out=root/'.runtime/blender-sky-review';out.mkdir(parents=True,exist_ok=True)
    report={'blender':bpy.app.version_string,'scope':'Independent render props; intentionally separate clouds/optical rays are not a single watertight game mesh.','scenes':{},'reviews':{}}
    for scene in bpy.data.scenes:
        meshes=[obj for obj in scene.objects if obj.type=='MESH' and obj.get('pysh_authored_sky')]
        if not meshes:continue
        bpy.context.window.scene=scene
        entries={}
        for obj in meshes:
            audit=bx_audit.audit(obj)
            entries[obj.name]={key:audit.get(key) for key in ['verts','faces','zero_area_faces','loose_verts','loose_edges','flipped_faces','duplicate_verts','non_manifold_edges']}
            entries[obj.name]['render_gate']=bx_audit.deliverable([obj],profile='render')
        report['scenes'][scene.name]={'color_audit':bx_light.color_audit(scene),'meshes':entries}
        if scene.name in ['PySH_3D_airliner','PySH_3D_glider']:
            report['reviews'][scene.name]=str(bx_review.review(meshes,str(out/scene.name),views=('top','front','threequarter'),modes=('silhouette','matcap'),res=320))
    (out/'review-report.json').write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
    failures=[(scene,obj,data['render_gate'].get('errors')) for scene,scoped in report['scenes'].items() for obj,data in scoped['meshes'].items() if not data['render_gate']['pass']]
    print('RESULT '+json.dumps({'report':str(out/'review-report.json'),'reviews':report['reviews'],'failed_render_props':failures},default=str))


if __name__=='__main__':main()
