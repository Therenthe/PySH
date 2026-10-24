import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {test} from 'node:test';
import vm from 'node:vm';

const rules=[];
const source=readFileSync(new URL('../os/polkit/50-pysh-networkmanager.rules',import.meta.url),'utf8');
vm.runInNewContext(source,{polkit:{addRule(rule){rules.push(rule);},Result:{YES:'yes'}}});
assert.equal(rules.length,1);
const decide=(id,user='pysh',extra={})=>rules[0]({id},{user,...extra});

const required=[
 'network-control','wifi.scan','enable-disable-wifi',
 'settings.modify.own','settings.modify.system','checkpoint-rollback',
];
for(const action of required){
 test(`dedicated appliance account can ${action} without an interactive session`,()=>{
  assert.equal(decide(`org.freedesktop.NetworkManager.${action}`,'pysh',{active:false,local:false,groups:[]}),'yes');
 });
 for(const user of ['root','pysh-admin','another-user','Pysh']){
  test(`${user} receives no PySH grant for ${action}`,()=>{
   assert.equal(decide(`org.freedesktop.NetworkManager.${action}`,user,{active:true,local:true,groups:['sudo','netdev']}),undefined);
  });
 }
}
for(const action of [
 'settings.modify.hostname','settings.modify.global-dns','enable-disable-network',
 'reload','sleep-wake','enable-disable-statistics','enable-disable-connectivity-check',
 'network-control.extra','settings.modify.system.extra','',
]){
 test(`no grant for unneeded NetworkManager action ${action||'(empty)'}`,()=>{
  assert.equal(decide(`org.freedesktop.NetworkManager.${action}`),undefined);
 });
}
test('unrelated services and prefix tricks receive no grant',()=>{
 for(const id of ['org.freedesktop.policykit.exec','org.freedesktop.accounts.user-administration',
  'evil.org.freedesktop.NetworkManager.network-control','org.freedesktop.NetworkManager']){
  assert.equal(decide(id),undefined);
 }
});
