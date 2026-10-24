"""Scoped offline city v2 mesh/part/color audit and orbit review.

Headless/factory: --root REPO --skills-root PATH_TO_INSTALLED_SKILLS
Independent architectural islands are audited as individual render components.
Whole-city watertightness, intersection-free export or physical UI are not claimed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import bpy
import bmesh


def main():
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,required=True); p.add_argument('--skills-root',type=Path,required=True)
    o=p.parse_args(sys.argv[sys.argv.index('--')+1:]); root=o.root.resolve()
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/pysh-gothic-city-v2.blend'))
    for name in ['scenario-blender-expert','scenario-blender-lighting-rendering']:
        sys.path.append(str(o.skills_root/name/'scripts'))
    import bx_review, bx_audit, bx_light
    out=root/'.runtime/city-polish-20261023/blender'; out.mkdir(parents=True,exist_ok=True)
    scene=bpy.data.scenes['PySH_Gothic_City_v2']; bpy.context.window.scene=scene
    city=[ob for ob in scene.objects if ob.type=='MESH']
    sheet=bx_review.review(city,str(out/'orbit'),views=('front','threequarter','right'),modes=('silhouette','matcap','wire'),res=400)
    report={'blender':bpy.app.version_string,'review_sheet':str(sheet),'color_audit':bx_light.color_audit(scene),'meshes':{},'closed_component_gates':[],'open_components':0,'closed_components':0,'inside_out_components':0,'scope':'Base offline architectural scene components. Solid components gated independently; intentional overlap/embedding joins facade panels/cornices/roof hardware. Open glazing faces are intentional. Whole city is neither a watertight print nor game-export asset.'}
    seen=set()
    for target in [scene,bpy.data.scenes['PySH_Metro_v2']]:
        bpy.context.window.scene=target
        for ob in [a for a in target.objects if a.type=='MESH']:
            r=bx_audit.audit(ob)
            report['meshes'][ob.name]={k:r[k] for k in ['verts','faces','tris_equivalent','zero_area_faces','loose_verts','loose_edges','flipped_faces','duplicate_verts','non_manifold_edges','self_intersections']}
            bm=bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
            pending=set(bm.verts)
            while pending:
                v=pending.pop(); verts={v}; stack=[v]
                while stack:
                    for e in stack.pop().link_edges:
                        for n in e.verts:
                            if n in pending:pending.remove(n); verts.add(n); stack.append(n)
                faces={f for v in verts for f in v.link_faces}
                closed=all(e.is_manifold for v in verts for e in v.link_edges)
                if not closed:report['open_components']+=1; continue
                report['closed_components']+=1
                ordered=list(verts); ids={v:i for i,v in enumerate(ordered)}
                mesh=bpy.data.meshes.new('Audit_component'); mesh.from_pydata([tuple(v.co) for v in ordered],[],[[ids[v] for v in f.verts] for f in faces]); mesh.update()
                single=bmesh.new(); single.from_mesh(mesh)
                volume=single.calc_volume(signed=True); single.free()
                if volume < -1e-12:report['inside_out_components']+=1
                # Gate each distinct topology archetype, while every component's
                # volume, boundary, zero/loose/winding metrics are measured above.
                signature=(ob.name,len(ordered),tuple(sorted(len(f.verts) for f in faces)),round(volume<0))
                if signature not in seen:
                    seen.add(signature)
                    for mat in ob.data.materials:mesh.materials.append(mat)
                    temp=bpy.data.objects.new('Audit_component',mesh); target.collection.objects.link(temp)
                    gate=bx_audit.deliverable([temp],profile='render',evaluated=False)
                    report['closed_component_gates'].append({'source':ob.name,'vertices':len(ordered),'faces':len(faces),'pass':gate['pass'],'errors':gate['errors'],'warnings':gate['warnings']})
                    bpy.data.objects.remove(temp,do_unlink=True)
                bpy.data.meshes.remove(mesh)
            bm.free()
    bpy.context.window.scene=scene
    scene.render.resolution_percentage=50
    master=bx_light.render(str(out/'night-master'),scene=scene)
    report['lighting_analysis']=bx_light.analyse(master['png'],mask=bx_light.load_rgba(master['exr'])[...,3],exr=master['exr'])
    bx_light.value_study(master['png'],str(out/'night-value-study.png'),width=800)
    scene.render.engine='CYCLES'; scene.cycles.samples=32; scene.cycles.use_denoising=True
    scene.cycles.max_bounces=3; scene.cycles.diffuse_bounces=3; scene.cycles.glossy_bounces=3
    scene.cycles.seed=231026
    reference=bx_light.render(str(out/'cycles-night-reference'),scene=scene,exr=False)
    report['cycles_reference']={'png':reference['png'],'samples':32,'scope':'800x285 diagnostic comparison only; final runtime is EEVEE with baked AgX.'}
    report['pass']=not report['color_audit'] and not report['inside_out_components'] and all(v['pass'] for v in report['closed_component_gates']) and all(not m[k] for m in report['meshes'].values() for k in ['zero_area_faces','loose_verts','loose_edges','flipped_faces'])
    (out/'review-report-v2.json').write_text(json.dumps(report,indent=2,default=str)+'\n',encoding='utf8')
    public_path=root/'assets/blender/build-report-v2.json'
    public=json.loads(public_path.read_text(encoding='utf8'))
    public['editable_source_sha256']=hashlib.sha256((root/'assets/blender/pysh-gothic-city-v2.blend').read_bytes()).hexdigest()
    public['reviewer_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    public['offline_review']={'pass':report['pass'],'color_audit':report['color_audit'],'closed_components':report['closed_components'],'inside_out_components':report['inside_out_components'],'intentional_open_glazing_components':report['open_components'],'render_profile_archetypes':len(report['closed_component_gates']),'archetype_errors':sum(len(v['errors']) for v in report['closed_component_gates']),'archetype_warnings':sum(len(v['warnings']) for v in report['closed_component_gates']),'zero_area_faces':sum(v['zero_area_faces'] for v in report['meshes'].values()),'loose_vertices':sum(v['loose_verts'] for v in report['meshes'].values()),'loose_edges':sum(v['loose_edges'] for v in report['meshes'].values()),'flipped_faces':sum(v['flipped_faces'] for v in report['meshes'].values()),'night_subject_internal_ratio':report['lighting_analysis']['subject']['internal_ratio'],'night_subject_edge_merge_percent':report['lighting_analysis']['subject']['edge_merge_pct'],'night_linear_max':report['lighting_analysis']['linear_max'],'night_clip_percent':report['lighting_analysis']['clip_pct'],'cycles_reference_samples':32,'limits':'Open facades and deliberate overlapping stone assemblies are expected in this offline raster scene. Whole-frame black percentage includes transparent sky and is not a display contrast measurement. Native Pi/animation performance and browser integration remain separate.'}
    public_path.write_text(json.dumps(public,indent=2)+'\n',encoding='utf8')
    print('RESULT '+json.dumps({k:report[k] for k in ['pass','color_audit','review_sheet','open_components','closed_components','inside_out_components']}),flush=True)
    assert report['pass'], 'See private review-report-v2.json for actual failures'


if __name__=='__main__':main()
