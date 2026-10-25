"""Render the installed Blender skill's review sheet and audit the baked scene.

blender -b --factory-startup --python-exit-code 1 -P this_file --
    --root REPO --skills-root PATH_TO_INSTALLED_SKILLS
Audit artifacts stay in .runtime; only summarized provenance belongs in Git.
"""
import argparse
import json
from pathlib import Path
import sys

import bpy


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--skills-root',type=Path,required=True)
    opts=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    root=opts.root.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/pysh-gothic-city-v1.blend'))
    for name in ['scenario-blender-expert','scenario-blender-lighting-rendering']:
        sys.path.append(str(opts.skills_root/name/'scripts'))
    import bx_review
    import bx_audit
    import bx_light
    scene=bpy.data.scenes['PySH_Gothic_City']
    bpy.context.window.scene=scene
    owned=[o for o in scene.objects if o.type=='MESH' and o.get('pysh_authored')]
    out=root/'.runtime/blender-city-review'
    out.mkdir(parents=True,exist_ok=True)
    sheet=bx_review.review(owned,str(out),views=('front','threequarter','right'),modes=('silhouette','matcap'),res=480)
    report={'blender':bpy.app.version_string,'review_sheet':str(sheet),'color_audit':bx_light.color_audit(scene),'meshes':{},'scope':'RGBA scene baking; architectural islands and intentional open window/arch planes are not game/print meshes'}
    for ob in owned:
        result=bx_audit.audit(ob)
        report['meshes'][ob.name]={key:value for key,value in result.items() if key in ['verts','faces','zero_area_faces','loose_verts','loose_edges','flipped_faces','duplicate_verts','non_manifold_edges']}
    # Closed weather props are individual portable render assets and can use the
    # complete render-profile gate, unlike the disconnected city architecture.
    report['weather_deliverables']={}
    for name in ['raindrop','ice']:
        sprite=bpy.data.scenes['PySH_'+name]
        bpy.context.window.scene=sprite
        meshes=[o for o in sprite.objects if o.type=='MESH']
        report['weather_deliverables'][name]=bx_audit.deliverable(meshes,profile='render')
    bpy.context.window.scene=scene
    (out/'review-report.json').write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
    print('RESULT '+json.dumps({'review_sheet':str(sheet),'color_audit':report['color_audit'],'weather_gates':{name:value['pass'] for name,value in report['weather_deliverables'].items()}}))


if __name__=='__main__':
    main()
