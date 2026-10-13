package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import org.json.JSONArray
import org.json.JSONObject

@Composable fun SettingsPage(remote: RemoteController) {
    val prefs=remote.preferences
    var edit by remember { mutableStateOf<String?>(null) }
    var layout by remember { mutableStateOf<String?>(null) }
    var exit by remember { mutableStateOf(false) }
    var forget by remember { mutableStateOf(false) }
    var address by remember { mutableStateOf(false) }
    var diagnostic by remember { mutableStateOf<JSONObject?>(null) }
    var diagnosticLoading by remember { mutableStateOf(false) }
    val scope=rememberCoroutineScope()
    PageTitle(T(remote.ro,"Setări","Settings"),T(remote.ro,"Atmosfera, exact cum îți place.","The atmosphere, just as you like it."))
    Panel {
        SectionTitle(T(remote.ro,"Pe acest telefon","On this phone"),Icons.Outlined.PhoneAndroid)
        Choice(T(remote.ro,"Limba aplicației","App language"),if(remote.ro) "ro" else "en",listOf("ro" to "Română","en" to "English"),true) { remote.language(it=="ro") }
        ToggleRow(T(remote.ro,"Temă întunecată","Dark theme"),remote.dark,true){remote.theme(it)}
    }
    Panel {
        SectionTitle(T(remote.ro,"Aspectul hubului","Hub appearance"),Icons.Outlined.Palette)
        Choice(T(remote.ro,"Limba PySH","PySH language"),prefs.optString("language","ro"),listOf("ro" to "Română","en" to "English"),remote.enabled){remote.patch("language",it)}
        Choice(T(remote.ro,"Tema PySH","PySH theme"),prefs.optString("theme","ink"),listOf("ink" to "E-Ink","night" to T(remote.ro,"Noapte","Night")),remote.enabled){remote.patch("theme",it)}
        Choice(T(remote.ro,"Accent","Accent"),prefs.optString("accent","sage"),listOf("sage" to T(remote.ro,"Salvie","Sage"),"amber" to T(remote.ro,"Chihlimbar","Amber"),"blue" to T(remote.ro,"Albastru","Blue")),remote.enabled){remote.patch("accent",it)}
        ToggleRow(T(remote.ro,"Noapte automată","Automatic night mode"),prefs.optBoolean("nightEnabled"),remote.enabled){remote.patch("nightEnabled",it)}
        Choice(T(remote.ro,"Program nocturn","Night schedule"),prefs.optString("nightMode","solar"),listOf("solar" to T(remote.ro,"Apus și răsărit","Sunset and sunrise"),"schedule" to T(remote.ro,"Ore alese","Custom hours")),remote.enabled){remote.patch("nightMode",it)}
        SettingButton(T(remote.ro,"Început noapte","Night starts"),prefs.optString("nightStart","22:00"),remote.enabled){edit="nightStart"}
        SettingButton(T(remote.ro,"Sfârșit noapte","Night ends"),prefs.optString("nightEnd","07:00"),remote.enabled){edit="nightEnd"}
        SettingButton(T(remote.ro,"Fus orar","Time zone"),prefs.optString("timezone","Europe/Bucharest"),remote.enabled){edit="timezone"}
    }
    Panel {
        SectionTitle(T(remote.ro,"Ceas și vizualizare","Clock and visualization"),Icons.Outlined.GraphicEq)
        SettingButton(T(remote.ro,"Screensaver după","Screensaver after"),"${prefs.optInt("screensaverMinutes",5)} ${T(remote.ro,"minute · 0 = oprit","minutes · 0 = off")}",remote.enabled){edit="screensaverMinutes"}
        Choice(T(remote.ro,"Aspect screensaver","Screensaver layout"),prefs.optString("screensaverLayout","clock"),listOf("clock" to T(remote.ro,"Ceas și redare","Clock and playback"),"visualizer" to T(remote.ro,"Vizualizator","Visualizer")),remote.enabled){remote.patch("screensaverLayout",it)}
        Choice(T(remote.ro,"Vizualizator audio","Audio visualizer"),prefs.optString("visualizerStyle","off"),listOf("off" to T(remote.ro,"Oprit","Off"),"wave" to T(remote.ro,"Undă","Wave"),"bars" to T(remote.ro,"Bare","Bars"),"orbit" to T(remote.ro,"Orbită","Orbit"),"ribbon" to T(remote.ro,"Panglică","Ribbon"),"mirror" to T(remote.ro,"Oglindă","Mirror"),"rings" to T(remote.ro,"Inele","Rings")),remote.enabled){remote.patch("visualizerStyle",it)}
        Choice(T(remote.ro,"Dimensiune vizualizator","Visualizer size"),prefs.optString("visualizerSize","compact"),listOf("compact" to T(remote.ro,"Compact","Compact"),"balanced" to T(remote.ro,"Echilibrat","Balanced"),"large" to T(remote.ro,"Mare","Large")),remote.enabled){remote.patch("visualizerSize",it)}
    }
    Panel {
        SectionTitle(T(remote.ro,"Acasă pe PySH","PySH Home"),Icons.Outlined.Home)
        MultiChoice(T(remote.ro,"Carduri vizibile","Visible cards"),"homeCards",listOf("weather" to T(remote.ro,"Vreme","Weather"),"forecast" to T(remote.ro,"Prognoză","Forecast"),"playback" to T(remote.ro,"Redare","Playback")),remote)
        MultiChoice(T(remote.ro,"Scurtături","Shortcuts"),"shortcuts",listOf("radio" to "Radio","media" to "Media","bluetooth" to "Bluetooth","weather" to T(remote.ro,"Vreme","Weather")),remote)
        ToggleRow(T(remote.ro,"Avioane decorative","Decorative aircraft"),prefs.optBoolean("decorativeAircraft",true),remote.enabled){remote.patch("decorativeAircraft",it)}
        ToggleRow(T(remote.ro,"Praf lunar decorativ","Decorative lunar dust"),prefs.optBoolean("decorativeLunarDust"),remote.enabled){remote.patch("decorativeLunarDust",it)}
        ToggleRow(T(remote.ro,"Navigare restrânsă","Collapsed navigation"),prefs.optBoolean("navigationCollapsed"),remote.enabled){remote.patch("navigationCollapsed",it)}
        ToggleRow(T(remote.ro,"Retrage meniul automat","Auto-hide navigation"),prefs.optBoolean("navigationAutoHide"),remote.enabled){remote.patch("navigationAutoHide",it)}
        Text(T(remote.ro,"Poziția cardurilor pe ecranul hubului","Card positions on the hub's screen"),style=MaterialTheme.typography.titleMedium)
        listOf("weather" to T(remote.ro,"Vreme","Weather"),"forecast" to T(remote.ro,"Prognoză","Forecast"),"playback" to T(remote.ro,"Redare","Playback"),"visualizer" to T(remote.ro,"Vizualizator","Visualizer")).forEach { (key,label) -> SettingButton(label,T(remote.ro,"Aranjează","Arrange"),remote.enabled){layout=key} }
        OutlinedButton(onClick={remote.patch("homePositions",JSONObject())},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(T(remote.ro,"Resetează pozițiile cardurilor","Reset card positions"))}
    }
    LocationPanel(remote)
    Panel {
        SectionTitle(T(remote.ro,"Service și diagnostic","Service and diagnostics"),Icons.Outlined.Build)
        Text("PySH ${remote.state.optString("version","—")} · ${remote.connection?.host}",style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        SettingButton(T(remote.ro,"Adresa LAN a hubului","Hub LAN address"),remote.connection?.host ?: "—",true){address=true}
        OutlinedButton(onClick={scope.launch { diagnosticLoading=true;try{diagnostic=remote.read("/api/diagnostics")}catch(e:CancellationException){throw e}catch(e:Exception){remote.error=(e as? HubFailure)?.code ?: "operation_failed"}finally{diagnosticLoading=false} }},enabled=remote.online && !diagnosticLoading,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(T(remote.ro,"Vezi diagnosticul","View diagnostics"))}
        if(remote.state.optBoolean("serviceMode")) Button(onClick={remote.command("/api/service/return")},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(T(remote.ro,"Revino în hub","Return to hub"))}
        else OutlinedButton(onClick={exit=true},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(if(remote.state.optBoolean("appliance")) T(remote.ro,"Intră în modul de service","Enter service mode") else T(remote.ro,"Ieși la desktop","Exit to desktop"))}
        OutlinedButton(onClick={remote.patch("setupComplete",false)},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(T(remote.ro,"Reia configurarea pe hub","Restart setup on hub"))}
        TextButton(onClick={forget=true},modifier=Modifier.heightIn(min=48.dp)){Text(T(remote.ro,"Elimină asocierea acestui telefon","Remove this phone's pairing"))}
    }
    edit?.let { key -> PreferenceDialog(remote,key){edit=null} }
    layout?.let { key -> LayoutDialog(remote,key){layout=null} }
    if(exit) ConfirmDialog(T(remote.ro,"Schimbi modul hubului?","Change the hub's mode?"),T(remote.ro,"Redarea se oprește. Pentru a reveni, folosește comanda de revenire sau ecranul PySH.","Playback stops. To return, use the return control or the PySH screen."),remote.ro,{remote.command("/api/exit");exit=false}){exit=false}
    if(forget) ConfirmDialog(T(remote.ro,"Elimini asocierea telefonului?","Remove this phone's pairing?"),if(remote.online) T(remote.ro,"Accesul se revocă pe PySH și datele de asociere se șterg din telefon.","Access is revoked on PySH and pairing credentials are removed from this phone.") else T(remote.ro,"Hubul este deconectat: se elimină numai datele din telefon. Revocă separat telefonul în serviciul LAN al PySH.","The hub is disconnected: only credentials on this phone are removed. Revoke the phone separately in PySH's LAN service."),remote.ro,{if(remote.online)remote.revoke() else remote.forget();forget=false}){forget=false}
    if(address) AddressDialog(remote){address=false}
    diagnostic?.let { data -> AlertDialog(onDismissRequest={diagnostic=null},title={Text(T(remote.ro,"Diagnostic PySH","PySH diagnostics"))},text={Column(Modifier.heightIn(max=360.dp).verticalScrollCompat()) { Text(data.toString(2),style=MaterialTheme.typography.bodyMedium) }},confirmButton={TextButton(onClick={diagnostic=null}){Text(T(remote.ro,"Închide","Close"))}}) }
}

@Composable fun AddressDialog(remote: RemoteController,dismiss:()->Unit) {
    var host by remember{mutableStateOf(remote.connection?.host ?: "")}
    var invalid by remember{mutableStateOf(false)}
    AlertDialog(onDismissRequest=dismiss,title={Text(T(remote.ro,"Adresa hubului","Hub address"))},text={Column(verticalArrangement=Arrangement.spacedBy(10.dp)){Field("IP LAN",host,{host=it});Text(T(remote.ro,"Certificatul salvat rămâne verificat. Folosește această opțiune dacă adresa hubului s-a schimbat.","The saved certificate remains verified. Use this option if your hub's address changed."),style=MaterialTheme.typography.bodyMedium);if(invalid)Text(errorText("invalid_lan_address",remote.ro),color=MaterialTheme.colorScheme.error)}},confirmButton={TextButton(onClick={if(runCatching{LanPolicy.host(host)}.isSuccess){remote.changeAddress(host);dismiss()}else invalid=true}){Text(T(remote.ro,"Salvează","Save"))}},dismissButton={TextButton(onClick=dismiss){Text(T(remote.ro,"Anulează","Cancel"))}})
}

@Composable fun Modifier.verticalScrollCompat(): Modifier = verticalScroll(rememberScrollState())

@Composable fun SettingButton(label: String, value: String, enabled: Boolean, action:()->Unit) {
    OutlinedButton(onClick=action,enabled=enabled,modifier=Modifier.fillMaxWidth().heightIn(min=52.dp),contentPadding=PaddingValues(horizontal=14.dp,vertical=12.dp)) { Column(Modifier.weight(1f)) { Text(label);Text(value,style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant) };Icon(Icons.Outlined.ChevronRight,null) }
}
@Composable fun Choice(label: String, selected: String, items: List<Pair<String,String>>, enabled: Boolean, change:(String)->Unit) {
    var opened by remember { mutableStateOf(false) }
    Box {
        SettingButton(label,items.firstOrNull{it.first==selected}?.second ?: "—",enabled){opened=true}
        DropdownMenu(expanded=opened,onDismissRequest={opened=false}) { items.forEach { (key,value) -> DropdownMenuItem(text={Text(value)},onClick={opened=false;change(key)},leadingIcon={if(selected==key)Icon(Icons.Outlined.Check,null)}) } }
    }
}
@Composable fun MultiChoice(title: String, key: String, options: List<Pair<String,String>>, remote: RemoteController) {
    val array=remote.preferences.optJSONArray(key) ?: JSONArray()
    val selected=(0 until array.length()).map{array.optString(it)}
    Text(title,style=MaterialTheme.typography.titleMedium)
    options.forEach { (value,label) -> ToggleRow(label,value in selected,remote.enabled && (value in selected || selected.size<3)) { checked -> remote.patch(key,JSONArray(if(checked) selected+value else selected-value)) } }
}
@Composable fun PreferenceDialog(remote: RemoteController, key: String, dismiss:()->Unit) {
    var value by remember { mutableStateOf(remote.preferences.opt(key)?.toString() ?: "") }
    var failure by remember { mutableStateOf(false) }
    val title=when(key){"nightStart"->T(remote.ro,"Început noapte · HH:mm","Night starts · HH:mm");"nightEnd"->T(remote.ro,"Sfârșit noapte · HH:mm","Night ends · HH:mm");"timezone"->T(remote.ro,"Fus orar","Time zone");else->T(remote.ro,"Minute până la screensaver","Minutes before screensaver")}
    AlertDialog(onDismissRequest=dismiss,title={Text(title)},text={Column(verticalArrangement=Arrangement.spacedBy(10.dp)) { Field(title,value,{value=it});if(failure)Text(T(remote.ro,"Verifică valoarea: ora HH:mm, fus orar valid sau 0–120 minute.","Check the value: HH:mm time, a valid time zone or 0–120 minutes."),color=MaterialTheme.colorScheme.error) }},confirmButton={TextButton(onClick={
        val valid=when(key){"screensaverMinutes"->value.toIntOrNull()?.let{it in 0..120} ?: false;"timezone"->runCatching{java.time.ZoneId.of(value);true}.getOrDefault(false);else->value.matches(Regex("(?:[01][0-9]|2[0-3]):[0-5][0-9]"))}
        if(valid){remote.patch(key,if(key=="screensaverMinutes")value.toInt() else value);dismiss()}else failure=true
    },enabled=remote.enabled){Text(T(remote.ro,"Salvează","Save"))}},dismissButton={TextButton(onClick=dismiss){Text(T(remote.ro,"Anulează","Cancel"))}})
}
@Composable fun LayoutDialog(remote: RemoteController, key: String, dismiss:()->Unit) {
    val existing=remote.preferences.child("homePositions").child(key)
    var x by remember { mutableFloatStateOf(existing.optDouble("x",0.0).toFloat()) }
    var y by remember { mutableFloatStateOf(existing.optDouble("y",0.0).toFloat()) }
    var z by remember { mutableStateOf(existing.optInt("z",1).toString()) }
    var anchorX by remember { mutableStateOf(existing.optString("anchorX","left")) }
    var anchorY by remember { mutableStateOf(existing.optString("anchorY","top")) }
    AlertDialog(onDismissRequest=dismiss,title={Text(T(remote.ro,"Poziție pe ecranul PySH","Position on the PySH screen"))},text={Column(Modifier.heightIn(max=440.dp).verticalScrollCompat(),verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text(T(remote.ro,"Distanțe relative față de marginea aleasă. Hubul limitează poziția la spațiul vizibil.","Relative distances from the selected edge. The hub limits the position to its visible space."),style=MaterialTheme.typography.bodyMedium)
        Text("X · ${(x*100).toInt()}%");Slider(x,{x=it},valueRange=0f..1f)
        Text("Y · ${(y*100).toInt()}%");Slider(y,{y=it},valueRange=0f..1f)
        Choice(T(remote.ro,"Margine orizontală","Horizontal edge"),anchorX,listOf("left" to T(remote.ro,"Stânga","Left"),"right" to T(remote.ro,"Dreapta","Right")),true){anchorX=it}
        Choice(T(remote.ro,"Margine verticală","Vertical edge"),anchorY,listOf("top" to T(remote.ro,"Sus","Top"),"bottom" to T(remote.ro,"Jos","Bottom")),true){anchorY=it}
        Choice(T(remote.ro,"Strat","Layer"),z,(1..4).map{it.toString() to it.toString()},true){z=it}
    }},confirmButton={TextButton(onClick={val all=JSONObject(remote.preferences.child("homePositions").toString());all.put(key,obj("x" to x,"y" to y,"z" to z.toInt(),"anchorX" to anchorX,"anchorY" to anchorY));remote.patch("homePositions",all);dismiss()},enabled=remote.enabled){Text(T(remote.ro,"Salvează","Save"))}},dismissButton={TextButton(onClick=dismiss){Text(T(remote.ro,"Anulează","Cancel"))}})
}

@Composable fun LocationPanel(remote: RemoteController) {
    var search by rememberSaveable { mutableStateOf("") }
    var results by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var searched by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<String?>(null) }
    val scope=rememberCoroutineScope()
    Panel {
        SectionTitle(T(remote.ro,"Vreme și locație","Weather and location"),Icons.Outlined.Cloud)
        Text(remote.preferences.child("location").optString("name").ifBlank{T(remote.ro,"Nicio locație aleasă","No location selected")},style=MaterialTheme.typography.bodyLarge)
        Field(T(remote.ro,"Caută orașul","Search for a city"),search,{search=it})
        Button(onClick={scope.launch { loading=true;failure=null;try{results=remote.read("/api/geocode?q=${query(search)}").objects("results");searched=true}catch(e:CancellationException){throw e}catch(e:Exception){failure=(e as? HubFailure)?.code ?: "operation_failed"}finally{loading=false} }},enabled=remote.online && !loading && search.isNotBlank(),modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(if(loading) T(remote.ro,"Se caută…","Searching…") else T(remote.ro,"Caută locația","Find location"))}
        failure?.let{MessageCard(errorText(it,remote.ro),true)}
        if(searched && results.isEmpty())Text(T(remote.ro,"Nicio locație găsită.","No location found."))
        results.forEach { location -> OutlinedButton(onClick={remote.patch("location",location);results=emptyList();searched=false},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp)){Text(listOf(location.optString("name"),location.optString("admin1"),location.optString("country")).filter{it.isNotBlank()}.joinToString(", "))} }
        Text(T(remote.ro,"Vremea se actualizează automat pe hub. Furnizor: Open-Meteo, CC BY 4.0.","Weather updates automatically on the hub. Provider: Open-Meteo, CC BY 4.0."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
