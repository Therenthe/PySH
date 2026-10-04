/** Backend local-media sizes are bytes. Unknown data stays unavailable. */
export function formatMediaSize(raw:unknown,language:string):string {
 const bytes=typeof raw==='number'?raw:typeof raw==='string'&&/^\d+$/.test(raw)?Number(raw):NaN;
 if(!Number.isSafeInteger(bytes)||bytes<0)return '';
 const units=['B','KB','MB','GB'];let unit=0,value=bytes;
 while(value>=1000&&unit<units.length-1){value/=1000;unit++;}
 // Avoid rounded boundary labels such as 1,000 KB when MB is clearer.
 if(unit<units.length-1&&Math.round(value*10)/10>=1000){value/=1000;unit++;}
 return `${new Intl.NumberFormat(language==='ro'?'ro-RO':'en-GB',{maximumFractionDigits:unit?1:0}).format(value)} ${units[unit]}`;
}
