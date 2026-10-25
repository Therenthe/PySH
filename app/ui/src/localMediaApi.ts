export type LocalMediaMetadata={title?:string;artist?:string;album?:string;duration_s?:number};
export type MediaReference={path:string;media_identity:string};
export type ContinueItem=MediaReference&{name:string;position_s:number;duration_s:number;updated_at:number;metadata?:LocalMediaMetadata;artwork_available?:boolean};
export type VideoObservation={position_s:number;duration_s:number;ended:boolean};
export type MediaRequest=(path:string,init?:RequestInit)=>Promise<any>;
export type VideoSession={session_id:string;media_identity:string;resume_position_s:number;stream_url:string;duration_s?:number};
const finite=(value:unknown):value is number=>typeof value==='number'&&Number.isFinite(value);
export const mediaIdentity=(value:unknown):value is string=>typeof value==='string'&&/^m1_[a-f0-9]{64}$/.test(value);
export const mediaArtwork=(item:MediaReference)=>`/api/media/artwork?path=${encodeURIComponent(item.path)}&media_identity=${encodeURIComponent(item.media_identity)}`;
export function readVideoObservation(video:Pick<HTMLVideoElement,'currentTime'|'duration'|'ended'>):VideoObservation|null{
 if(!finite(video.duration)||video.duration<=0||!finite(video.currentTime)||video.currentTime<0)return null;
 return {position_s:Math.min(video.currentTime,video.duration),duration_s:video.duration,ended:video.ended};
}
export function validateVideoSession(reply:VideoSession,identity:string):VideoSession{
 if(!reply||typeof reply.session_id!=='string'||!/^[-_A-Za-z0-9]{32}$/.test(reply.session_id)||reply.media_identity!==identity||!finite(reply.resume_position_s)||reply.resume_position_s<0||reply.stream_url!==`/api/media/file?session_id=${reply.session_id}`)throw new Error('invalid_video_session');
 return reply;
}
export function continueItems(reply:unknown):ContinueItem[]{
 if(!reply||!Array.isArray((reply as {items?:unknown}).items))throw new Error('media_unavailable');
 return (reply as {items:ContinueItem[]}).items.filter(item=>item&&typeof item.path==='string'&&typeof item.name==='string'&&mediaIdentity(item.media_identity)&&finite(item.position_s)&&item.position_s>=0&&finite(item.duration_s)&&item.duration_s>0).slice(0,12);
}

/** One browser-owned descriptor; observations come only from its mounted video element. */
export class LocalVideoSession{
 readonly session:VideoSession;
 private sequence=0;
 private queue:Promise<unknown>=Promise.resolve();
 private closing=false;
 private closed=false;
 private closePending:Promise<void>|null=null;
 private finishKind:'save'|'discard'|null=null;
 private final:VideoObservation|null|undefined;
 private finalSequence=0;
 private observe:(()=>VideoObservation|null)|null=null;
 private pause:(()=>void)|null=null;
 constructor(session:VideoSession,private request:MediaRequest){this.session=session;}
 get unavailable(){return this.closing||this.closed;}
 bind(observe:()=>VideoObservation|null,pause:()=>void){this.observe=observe;this.pause=pause;return()=>{this.observe=null;this.pause=null;};}
 update(heartbeat=false):Promise<void>{
  if(this.closing||this.closed)return Promise.resolve();
  const observation=this.observe?.()??null;
  if(!heartbeat&&!observation)return Promise.resolve();
  const operation=this.queue.then(async()=>{
   if(this.closing||this.closed)return;
   await this.request(`/api/media/video-session/${this.session.session_id}`,{method:'PATCH',body:JSON.stringify({sequence:++this.sequence,...(heartbeat?{heartbeat:true}:observation)})});
  });
  this.queue=operation.catch(()=>{});return operation;
 }
 close(keepalive=false):Promise<void>{
  if(this.closed)return Promise.resolve();
  if(this.closePending)return this.closePending;
  this.finishKind='save';
  this.closing=true;this.pause?.();
  if(this.final===undefined)this.final=this.observe?.()??null;
  const operation=this.queue.then(async()=>{
   if(this.closed)return;
   if(!this.finalSequence)this.finalSequence=++this.sequence;
   try{await this.request(`/api/media/video-session/${this.session.session_id}`,{method:'DELETE',keepalive,...(this.final?{body:JSON.stringify({sequence:this.finalSequence,...this.final})}:{})});}
   catch(error){if((error as Error).message!=='stale_video_session')throw error;}
   this.closed=true;
  });
  this.queue=operation.catch(()=>{});
  this.closePending=operation.finally(()=>{this.closePending=null;this.finishKind=null;});return this.closePending;
 }
 discard():Promise<void>{
  if(this.closed)return Promise.resolve();
  if(this.closePending)return this.finishKind==='discard'?this.closePending:this.closePending.then(()=>{},()=>this.discard());
  this.finishKind='discard';
  this.closing=true;this.pause?.();
  const operation=this.queue.then(async()=>{
   if(this.closed)return;
   // Explicit discard drops the saved snapshot; a later Save retry reads the paused element again.
   this.final=undefined;this.finalSequence=0;
   await this.request(`/api/media/video-session/${this.session.session_id}`,{method:'DELETE'});
   this.closed=true;
  });
  this.queue=operation.catch(()=>{});
  this.closePending=operation.finally(()=>{this.closePending=null;this.finishKind=null;});return this.closePending;
 }
 abandon(){
  // Only after explicit local-leave confirmation; backend expiry owns unreachable descriptor cleanup.
  this.closing=true;this.closed=true;this.pause?.();this.final=undefined;this.observe=null;this.pause=null;
 }
}
