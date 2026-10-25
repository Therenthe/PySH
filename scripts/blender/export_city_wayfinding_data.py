"""Convert a verified final Blender contract into the small typed UI data module.
No rendering, copying assets, dependency installation or hidden destination.
"""
import argparse,hashlib,json,math,re,struct
from pathlib import Path
IDS={'media','audio','settings','radio','network'}
REQUIRED_GATES=('unicode','unstretched_native_cap_14_16','target48_nonoverlap','all_intro_bob_object_beacon_clearance','viewport58_480','original_inputs_unchanged','four_locale_palette_matrix','loop_pure_translation')
def finite(value):return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
def validate(c):
 if not isinstance(c.get('gates'),dict) or any(c['gates'].get(key) is not True for key in REQUIRED_GATES):raise ValueError('All eight structural/render gates must explicitly be true')
 if c.get('preview') is not False or set(c.get('signs',{}))!=IDS:raise ValueError('A completed final five-sign contract is required')
 for id,sign in c['signs'].items():
  if sign.get('frame_count')!=6:raise ValueError('Final export must contain six genuine rendered frames')
  for key in ['crop','final_face_rect']:
   rect=sign[key]
   if set(rect)!={'x','y','width','height'} or not all(finite(v) for v in rect.values()) or rect['width']<=0 or rect['height']<=0:raise ValueError('Invalid projected geometry')
  if set(sign['languages'])!={'en','ro'}:raise ValueError('Both languages are required')
  for mapping in sign['languages'].values():
   if set(mapping)!={'day','night'}:raise ValueError('Both palettes are required')
   for filename in mapping.values():
    if not isinstance(filename,str) or not re.fullmatch(r'city-wayfinding-[a-z0-9-]+\.png',filename) or filename not in c['assets']:raise ValueError('Unsafe or absent atlas filename')
    asset=c['assets'][filename]
    if asset['dimensions']!=[sign['crop']['width']*6,sign['crop']['height']]:raise ValueError('Atlas dimensions do not match contract')
 frames=c.get('float_keyframes',[])
 if len(frames)!=81 or frames[0]['offset']!=0 or frames[-1]['offset']!=1:raise ValueError('Expected81 complete projected float samples')
 for i,frame in enumerate(frames):
  if set(frame)!={'offset','x','y'} or not all(finite(v) for v in frame.values()) or (i and frame['offset']<=frames[i-1]['offset']):raise ValueError('Invalid float trajectory')
 if not finite(c.get('duration_ms')) or c['duration_ms']<=0 or not finite(c.get('float_duration_ms')) or c['float_duration_ms']<=0:raise ValueError('Invalid animation duration')
 return {'signs':{id:{key:sign[key] for key in ['crop','final_face_rect','frame_count','languages']} for id,sign in c['signs'].items()},'duration_ms':c['duration_ms'],'float_duration_ms':c['float_duration_ms'],'float_keyframes':frames}
def check_assets(c,directory):
 directory=Path(directory).resolve();assets=c.get('assets')
 if not isinstance(assets,dict) or not assets:raise ValueError('Allowlisted atlases are required')
 total=0
 for filename,entry in assets.items():
  if not isinstance(filename,str) or not re.fullmatch(r'city-wayfinding-[a-z0-9-]+\.png',filename):raise ValueError('Unsafe allowlisted atlas name')
  file=(directory/filename).resolve(strict=True)
  if file.parent!=directory or not file.is_file():raise ValueError('Atlas must be a regular file beside the contract')
  raw=file.read_bytes();expected_sha=entry.get('sha256')
  if type(entry.get('bytes')) is not int or entry['bytes']!=len(raw):raise ValueError('Atlas byte count mismatch: '+filename)
  if not isinstance(expected_sha,str) or not re.fullmatch(r'[0-9a-fA-F]{64}',expected_sha) or hashlib.sha256(raw).hexdigest()!=expected_sha.lower():raise ValueError('Atlas SHA256 mismatch: '+filename)
  if len(raw)<33 or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR':raise ValueError('Atlas is not a valid PNG header: '+filename)
  dimensions=list(struct.unpack('>II',raw[16:24]))
  if dimensions!=entry.get('dimensions') or raw[24]!=8 or raw[25]!=6:raise ValueError('Atlas dimensions/RGBA8 header mismatch: '+filename)
  if 'decoded_rgba_bytes' in entry and entry['decoded_rgba_bytes']!=dimensions[0]*dimensions[1]*4:raise ValueError('Decoded atlas byte count mismatch: '+filename)
  total+=len(raw)
 return {'atlas_files':len(assets),'verified_atlas_bytes':total}

def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--replace',action='store_true',help='Explicitly allow replacing an existing generated module.');a=p.parse_args();raw=a.contract.read_bytes();contract=json.loads(raw);data=validate(contract);asset_check=check_assets(contract,a.contract.resolve().parent);out=a.output.expanduser().resolve()
 if out.suffix!='.ts':raise ValueError('Output must be an explicit TypeScript file')
 if out.exists() and not a.replace:raise FileExistsError('Output already exists; use --replace explicitly')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text('/* Generated from a verified final Blender asset contract. */\nexport const cityWayfinding = '+json.dumps(data,ensure_ascii=True,separators=(',',':'))+' as const;\n',encoding='utf-8');print(json.dumps({'contract_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'signs':5,'frames_per_sign':6,'float_points':81,**asset_check,'full_mesh_audit':contract.get('gates',{}).get('full_mesh_audit','not_specified')}))
if __name__=='__main__':main()
