import type {ReactNode} from 'react';
import './settings-navigation.css';

// A setting has one canonical destination; shortcuts open the same section.
export const settingsGroups = [
 {id:'home',icon:'home',en:'Home',ro:'Acasă',sections:['home','visualizer','ambient']},
 {id:'display',icon:'sun',en:'Display & rest',ro:'Ecran și repaus',sections:['appearance','rest','power']},
 {id:'sound',icon:'speaker',en:'Sound & speakers',ro:'Sunet și boxe',sections:['audio','bluetooth']},
 {id:'connections',icon:'wifi',en:'Internet & phone',ro:'Internet și telefon',sections:['network','androidControl']},
 {id:'regional',icon:'globe',en:'Language & location',ro:'Limbă și locație',sections:['general','weather']},
 {id:'system',icon:'settings',en:'System',ro:'Sistem',sections:['diagnostics']},
] as const;
const sectionNames:Record<string,[string,string]>={home:['Cards & navigation','Carduri și navigare'],visualizer:['Visualizer','Vizualizator'],ambient:['Ambient effects','Efecte ambientale'],appearance:['Theme','Temă'],rest:['Rest screen','Ecran de repaus'],power:['Brightness & standby','Luminozitate și standby'],audio:['Volume & output','Volum și ieșire'],bluetooth:['Bluetooth','Bluetooth'],network:['Wi-Fi & Ethernet','Wi-Fi și cablu'],androidControl:['Phone control','Control de pe telefon'],general:['Language & time','Limbă și oră'],weather:['Weather location','Locație meteo'],diagnostics:['System','Sistem']};
export const settingsGroupFor=(section:string)=>settingsGroups.find(group=>(group.sections as readonly string[]).includes(section))||settingsGroups[0];
export const settingsSectionTitle=(section:string,ro:boolean)=>sectionNames[section]?.[ro?1:0]||section;
export function SettingsNavigation({section,ro,onSelect,icon}:{section:string;ro:boolean;onSelect:(section:string)=>void;icon:(name:string)=>ReactNode}){
 const selected=settingsGroupFor(section);
 return <nav className="settings-tabs" aria-label={ro?'Categorii de setări':'Settings categories'}>{settingsGroups.map(group=><button key={group.id} data-settings-group={group.id} className={selected.id===group.id?'active':''} aria-current={selected.id===group.id?'page':undefined} onClick={()=>onSelect(group.sections[0])}>{icon(group.icon)}<span>{ro?group.ro:group.en}</span></button>)}</nav>;
}
export function SettingsSections({section,ro,onSelect}:{section:string;ro:boolean;onSelect:(section:string)=>void}){
 const group=settingsGroupFor(section);
 return group.sections.length>1?<nav className="settings-subtabs" aria-label={ro?'Secțiuni de setări':'Settings sections'}>{group.sections.map(id=><button key={id} data-settings-section={id} aria-current={id===section?'page':undefined} className={id===section?'active':''} onClick={()=>onSelect(id)}>{settingsSectionTitle(id,ro)}</button>)}</nav>:null;
}
