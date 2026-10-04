/** Local illustrative ephemeris: UTC instant, east-positive longitude, degrees.
 * Orbital elements/major lunar perturbations: Paul Schlyter,
 * https://stjarnhimlen.se/comp/ppcomp.html (sections 3–13).
 * Sea-level topocentric coordinates; no terrain, nutation, aberration or UT1/TT model.
 * Standard refraction: NOAA https://gml.noaa.gov/grad/solcalc/calcdetails.html.
 * The scene is a south-facing panorama: east on the right, west on the left.
 */
export type CelestialBody = {
 altitude:number; apparentAltitude:number; azimuth:number;
 x:number; y:number; visible:boolean;
};
export type CelestialScene = {sun:CelestialBody;moon:CelestialBody;night:boolean};
const rad=Math.PI/180,deg=180/Math.PI;
const sin=(angle:number)=>Math.sin(angle*rad),cos=(angle:number)=>Math.cos(angle*rad);
const atan2=(y:number,x:number)=>Math.atan2(y,x)*deg;
const wrap=(angle:number)=>((angle%360)+360)%360;
type Vector = {x:number;y:number;z:number};
function eccentricAnomaly(mean:number,e:number){
 const m=wrap(mean)*rad;
 let value=m+e*Math.sin(m)*(1+e*Math.cos(m));
 for(let iteration=0;iteration<5;iteration++){
  const change=(value-e*Math.sin(value)-m)/(1-e*Math.cos(value));
  value-=change;if(Math.abs(change)<1e-10)break;
 }
 return value*deg;
}
function eclipticVector(longitude:number,latitude:number,distance:number):Vector{
 return {x:distance*cos(longitude)*cos(latitude),y:distance*sin(longitude)*cos(latitude),z:distance*sin(latitude)};
}
function toEquatorial(v:Vector,obliquity:number):Vector{
 return {x:v.x,y:v.y*cos(obliquity)-v.z*sin(obliquity),z:v.y*sin(obliquity)+v.z*cos(obliquity)};
}
/** Standard atmosphere, degrees. Below -0.575° no extrapolated refraction:
 * bodies already below the horizon should not acquire false visibility.
 */
function refraction(altitude:number){
 if(altitude>85||altitude<-.575)return 0;
 if(altitude>5){const t=Math.tan(altitude*rad);return (58.1/t-.07/t**3+.000086/t**5)/3600;}
 return (1735+altitude*(-518.2+altitude*(103.4+altitude*(-12.79+altitude*.711))))/3600;
}
function horizontal(v:Vector,latitude:number,lst:number,semidiameter:number):CelestialBody{
 // Subtract the observer in Earth radii, including approximate flattening.
 const geocentricLatitude=latitude-.1924*sin(2*latitude);
 const radius=.99833+.00167*cos(2*latitude);
 const top={x:v.x-radius*cos(geocentricLatitude)*cos(lst),y:v.y-radius*cos(geocentricLatitude)*sin(lst),z:v.z-radius*sin(geocentricLatitude)};
 const rightAscension=atan2(top.y,top.x);
 const declination=atan2(top.z,Math.hypot(top.x,top.y));
 const hourAngle=lst-rightAscension;
 const west=sin(hourAngle)*cos(declination);
 const south=cos(hourAngle)*cos(declination)*sin(latitude)-sin(declination)*cos(latitude);
 const up=cos(hourAngle)*cos(declination)*cos(latitude)+sin(declination)*sin(latitude);
 const altitude=atan2(up,Math.hypot(south,west));
 const azimuth=wrap(atan2(west,south)+180);
 const apparentAltitude=altitude+refraction(altitude);
 // A 360° panorama, not an AR camera projection. North wraps at the edges.
 return {altitude,apparentAltitude,azimuth,x:100-azimuth/3.6,y:84-70*Math.max(0,Math.min(90,apparentAltitude))/90,visible:apparentAltitude+semidiameter>=0};
}
export function getCelestialScene(now:Date,latitude:unknown,longitude:unknown):CelestialScene|null{
 if(!(now instanceof Date)||!Number.isFinite(now.getTime())||now.getUTCFullYear()<1900||now.getUTCFullYear()>2100||typeof latitude!=='number'||typeof longitude!=='number'||!Number.isFinite(latitude)||!Number.isFinite(longitude)||Math.abs(latitude)>90||Math.abs(longitude)>180)return null;
 const d=(now.getTime()-Date.UTC(1999,11,31))/86400000;
 const obliquity=23.4393-3.563e-7*d;
 const solarPerihelion=282.9404+4.70935e-5*d;
 const solarEccentricity=.016709-1.151e-9*d;
 const solarMean=wrap(356.047+.9856002585*d);
 const solarE=eccentricAnomaly(solarMean,solarEccentricity);
 const sx=cos(solarE)-solarEccentricity,sy=Math.sqrt(1-solarEccentricity**2)*sin(solarE);
 const solarDistance=Math.hypot(sx,sy),solarLongitude=atan2(sy,sx)+solarPerihelion;
 const solarMeanLongitude=solarMean+solarPerihelion;
 const utcHours=now.getUTCHours()+now.getUTCMinutes()/60+now.getUTCSeconds()/3600+now.getUTCMilliseconds()/3600000;
 const lst=wrap(solarMeanLongitude+180+utcHours*15+longitude);
 const node=125.1228-.0529538083*d,inclination=5.1454,perihelion=318.0634+.1643573223*d;
 const moonMean=wrap(115.3654+13.0649929509*d),moonE=eccentricAnomaly(moonMean,.0549);
 const mx=60.2666*(cos(moonE)-.0549),my=60.2666*Math.sqrt(1-.0549**2)*sin(moonE);
 const anomaly=atan2(my,mx),distance=Math.hypot(mx,my);
 const orbitalLongitude=anomaly+perihelion;
 const vx=distance*(cos(node)*cos(orbitalLongitude)-sin(node)*sin(orbitalLongitude)*cos(inclination));
 const vy=distance*(sin(node)*cos(orbitalLongitude)+cos(node)*sin(orbitalLongitude)*cos(inclination));
 const vz=distance*sin(orbitalLongitude)*sin(inclination);
 let moonLongitude=atan2(vy,vx),moonLatitude=atan2(vz,Math.hypot(vx,vy)),moonDistance=distance;
 const meanLongitude=moonMean+perihelion+node,elongation=meanLongitude-solarMeanLongitude,argumentLatitude=meanLongitude-node;
 moonLongitude+=-1.274*sin(moonMean-2*elongation)+.658*sin(2*elongation)-.186*sin(solarMean)-.059*sin(2*moonMean-2*elongation)-.057*sin(moonMean-2*elongation+solarMean)+.053*sin(moonMean+2*elongation)+.046*sin(2*elongation-solarMean)+.041*sin(moonMean-solarMean)-.035*sin(elongation)-.031*sin(moonMean+solarMean)-.015*sin(2*argumentLatitude-2*elongation)+.011*sin(moonMean-4*elongation);
 moonLatitude+=-.173*sin(argumentLatitude-2*elongation)-.055*sin(moonMean-argumentLatitude-2*elongation)-.046*sin(moonMean+argumentLatitude-2*elongation)+.033*sin(argumentLatitude+2*elongation)+.017*sin(2*moonMean+argumentLatitude);
 moonDistance+=-.58*cos(moonMean-2*elongation)-.46*cos(2*elongation);
 const sun=horizontal(toEquatorial(eclipticVector(solarLongitude,0,solarDistance*23454.8),obliquity),latitude,lst,.2666/solarDistance);
 const moon=horizontal(toEquatorial(eclipticVector(moonLongitude,moonLatitude,moonDistance),obliquity),latitude,lst,.2725*60/moonDistance);
 return {sun,moon,night:!sun.visible};
}
