import test from 'node:test';
import assert from 'node:assert/strict';
import { weatherCondition, weatherIsNight } from '../app/ui/src/weatherCondition.ts';

test('maps all supported WMO conditions into distinct icon families',()=>{
 const families={clear:[0],'mainly-clear':[1],'partly-cloudy':[2],overcast:[3],fog:[45,48],
  drizzle:[51,53,55],'freezing-drizzle':[56,57],rain:[61,63,65],'freezing-rain':[66,67],
  snow:[71,73,75,77],'rain-showers':[80,81,82],'snow-showers':[85,86],thunder:[95,97],'thunder-hail':[96,99]};
 for(const [family,codes] of Object.entries(families)) for(const code of codes) assert.equal(weatherCondition(code),family,`WMO${code}`);
});

test('missing and unrecognized values never masquerade as clear weather',()=>{
 for(const missing of [undefined,null]) assert.equal(weatherCondition(missing),'missing');
 for(const unknown of ['0','',false,true,NaN,Infinity,-1,4,50,98,100,1.5,{},[]]) assert.equal(weatherCondition(unknown),'unknown');
});

test('night variants use actual provider daylight and never infer from theme or clock',()=>{
 for(const night of [false,0]) assert.equal(weatherIsNight(night),true);
 for(const daytimeOrUnavailable of [true,1,undefined,null,2,NaN]) assert.equal(weatherIsNight(daytimeOrUnavailable),false);
});
