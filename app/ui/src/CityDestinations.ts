export type CityDestination='radio'|'media'|'audio'|'network'|'settings';
export const cityDestinations:{id:CityDestination;en:string;ro:string;left:number;width:number;height:number}[]=[
 {id:'media',en:'Media',ro:'Media',left:10.9091,width:6.1538,height:128},
 {id:'audio',en:'Sound and speakers',ro:'Sunet și boxe',left:18.6014,width:6.1538,height:183},
 {id:'settings',en:'Settings',ro:'Setări',left:38.8811,width:6.1538,height:166},
 {id:'radio',en:'Radio',ro:'Radio',left:56.75,width:7.4375,height:183},
 {id:'network',en:'Internet and phone',ro:'Internet și telefon',left:68.9511,width:6.1538,height:142},
];
export const cityDestinationName=(id:CityDestination,language:'en'|'ro')=>cityDestinations.find(destination=>destination.id===id)![language];
