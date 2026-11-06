/** One scalar write in flight; retain only the latest unsent absolute value. */
export class LiveLevel {
 private next:{value:number;persist:boolean;resolve:(result:unknown)=>void}|null=null;
 private running=false;
 private timer:ReturnType<typeof setTimeout>|undefined;
 private sentAt=-Infinity;
 constructor(private write:(value:number,persist:boolean)=>Promise<unknown>){}
 set(value:number,persist=true):Promise<unknown>{
  return new Promise(resolve=>{
   this.next?.resolve(undefined);
   this.next={value,persist,resolve};
   this.schedule();
  });
 }
 private schedule(){
  if(this.running||!this.next)return;
  clearTimeout(this.timer);
  this.timer=setTimeout(()=>void this.flush(),this.next.persist?0:Math.max(0,120-(performance.now()-this.sentAt)));
 }
 private async flush(){
  const next=this.next;if(!next||this.running)return;this.next=null;this.running=true;this.sentAt=performance.now();
  let result:unknown=null;
  try{result=await this.write(next.value,next.persist);}catch{/* The owner exposes recovery; never replay an uncertain mutation. */}
  next.resolve(result);this.running=false;
  if(result===null||result===false){this.discard();return;}
  this.schedule();
 }
 private discard(){this.next?.resolve(null);this.next=null;}
}
