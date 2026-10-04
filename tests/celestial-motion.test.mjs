import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {getCelestialScene} from '../app/ui/src/CelestialMotion.ts';
const fixtures=JSON.parse(readFileSync(new URL('./celestial-usno-fixtures.json',import.meta.url),'utf8'));
for(const fixture of fixtures)for(const expected of fixture.bodies){
 test(`USNO independent ${expected.body} ${fixture.utc} ${fixture.latitude},${fixture.longitude}`,()=>{
  const actual=getCelestialScene(new Date(fixture.utc),fixture.latitude,fixture.longitude)[expected.body];
  const targetAltitude=expected.geocentricAltitude-(typeof expected.parallax==='number'?expected.parallax:0);
  // Algorithm/geocentric-vs-topocentric azimuth differences: 0.2° is <1 pixel here.
  const azimuthError=Math.abs(((actual.azimuth-expected.azimuth+540)%360)-180);
  assert.ok(Math.abs(actual.altitude-targetAltitude)<.2,`alt ${actual.altitude} vs independent ${targetAltitude}`);
  assert.ok(azimuthError<.2,`az ${actual.azimuth} vs independent ${expected.azimuth}`);
  assert.ok(actual.x>=0&&actual.x<=100&&actual.y>=14&&actual.y<=84);
 });
}
test('Bucharest Sun traverses east/right to west/left and ascends then descends',()=>{
 const morning=getCelestialScene(new Date('2026-10-04T06:00Z'),44.4,26.1).sun;
 const noon=getCelestialScene(new Date('2026-10-04T10:00Z'),44.4,26.1).sun;
 const evening=getCelestialScene(new Date('2026-10-04T15:00Z'),44.4,26.1).sun;
 assert.ok(morning.x>noon.x&&noon.x>evening.x);assert.ok(morning.y>noon.y&&evening.y>noon.y);
});
test('Moon tracks its orbit independently, including visible daytime and absent early evening',()=>{
 const day=getCelestialScene(new Date('2026-10-04T06:00Z'),44.4,26.1);
 const evening=getCelestialScene(new Date('2026-10-04T18:00Z'),44.4,26.1);
 const late=getCelestialScene(new Date('2026-10-04T23:00Z'),44.4,26.1);
 assert.equal(day.night,false);assert.equal(day.moon.visible,true);
 assert.equal(evening.night,true);assert.equal(evening.moon.visible,false);
 assert.equal(late.moon.visible,true);assert.ok(late.moon.x>70);
});
test('Moon near actual rise crosses horizon with bounded minute movement',()=>{
 const before=getCelestialScene(new Date('2026-10-04T21:50Z'),44.4,26.1).moon;
 const after=getCelestialScene(new Date('2026-10-04T22:10Z'),44.4,26.1).moon;
 assert.equal(before.visible,false);assert.equal(after.visible,true);assert.ok(after.altitude>before.altitude);
 const later=getCelestialScene(new Date('2026-10-04T22:11Z'),44.4,26.1).moon;
 assert.ok(Math.abs(later.x-after.x)<.1&&Math.abs(later.y-after.y)<.3);
});
test('UTC date rollover/DST labels cannot reset orbital motion',()=>{
 const previous=getCelestialScene(new Date('2026-10-04T23:59:00Z'),44.4,26.1);
 const next=getCelestialScene(new Date('2026-10-05T00:00:00Z'),44.4,26.1);
 assert.ok(Math.abs(previous.moon.x-next.moon.x)<.1&&Math.abs(previous.moon.y-next.moon.y)<.3);
 assert.deepEqual(getCelestialScene(new Date('2026-10-25T04:00:00+03:00'),44.4,26.1),getCelestialScene(new Date('2026-10-25T03:00:00+02:00'),44.4,26.1));
});
test('Polar day/night and exact poles remain finite; no sunrise interpolation divide by zero',()=>{
 assert.equal(getCelestialScene(new Date('2026-06-21T00:00Z'),69.65,18.96).night,false);
 assert.equal(getCelestialScene(new Date('2026-12-21T12:00Z'),69.65,18.96).night,true);
 for(const latitude of [-90,90])for(const date of ['2026-06-21T12:00Z','2026-12-21T12:00Z']){
  const scene=getCelestialScene(new Date(date),latitude,0);
  for(const body of [scene.sun,scene.moon])for(const key of ['altitude','apparentAltitude','azimuth','x','y'])assert.ok(Number.isFinite(body[key]));
 }
});
test('Missing/invalid location/date has no invented fallback celestial position',()=>{
 for(const pair of [[undefined,26.1],[44.4,null],['44.4',26.1],[91,0],[0,181],[NaN,0],[0,Infinity]])assert.equal(getCelestialScene(new Date('2026-10-04T00:00Z'),...pair),null);
 assert.equal(getCelestialScene(new Date(NaN),44.4,26.1),null);
 assert.equal(getCelestialScene(new Date('2200-01-01T00:00Z'),44.4,26.1),null);
 assert.ok(getCelestialScene(new Date('2026-10-04T00:00Z'),0,0));
});
