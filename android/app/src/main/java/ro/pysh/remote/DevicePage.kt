package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import org.json.JSONObject

@Composable fun DevicePage(remote: RemoteController) {
    val audio=remote.state.child("audio")
    val bluetooth=remote.state.child("bluetooth")
    val network=remote.state.child("network")
    var nearby by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var wifi by remember { mutableStateOf<JSONObject?>(null) }
    var forgetting by remember { mutableStateOf<JSONObject?>(null) }
    var btForget by remember { mutableStateOf<JSONObject?>(null) }
    PageTitle(T(remote.ro,"Dispozitiv","Device"),T(remote.ro,"Fă hubul să se simtă acasă.","Make your hub feel at home."))
    Panel {
        SectionTitle("Audio",Icons.Outlined.Speaker)
        VolumeControl(remote)
        if(!audio.optBoolean("available")) Text(T(remote.ro,"Ieșirea audio a hubului este indisponibilă.","The hub's audio output is unavailable."))
        audio.objects("outputs").forEach { output ->
            OutlinedButton(onClick={remote.command("/api/audio",obj("output" to output.optString("id")))},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) {
                Icon(if(output.optString("id")==audio.optString("output")) Icons.Outlined.CheckCircle else Icons.Outlined.Speaker,null,Modifier.size(22.dp));Spacer(Modifier.width(10.dp));Text(output.optString("description",output.optString("name",output.optString("id"))),Modifier.weight(1f))
            }
        }
        if(!audio.optBoolean("ready")) Text(T(remote.ro,"Selectează explicit o ieșire pentru redare. Disponibilitatea ieșirii nu confirmă că există o boxă fizică.","Select an output explicitly for playback. An available output does not confirm a physical speaker is present."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
    Panel {
        SectionTitle("Bluetooth",Icons.Outlined.Bluetooth)
        ToggleRow(T(remote.ro,"Bluetooth pe hub","Hub Bluetooth"),bluetooth.optBoolean("powered"),remote.enabled && bluetooth.optBoolean("available")) { enabled -> remote.command("/api/bluetooth/power",obj("enabled" to enabled)) }
        Button(onClick={remote.command("/api/bluetooth/scan")},enabled=remote.enabled && bluetooth.optBoolean("powered"),modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Icon(Icons.Outlined.Search,null);Spacer(Modifier.width(8.dp));Text(T(remote.ro,"Caută dispozitive","Scan for devices")) }
        if(!bluetooth.optBoolean("available")) Text(T(remote.ro,"Adaptorul Bluetooth este indisponibil.","The Bluetooth adapter is unavailable."))
        if(bluetooth.optBoolean("discovering")) Text(T(remote.ro,"Se caută dispozitive în apropierea hubului…","Searching for devices near your hub…"))
        bluetooth.objects("devices").forEach { device ->
            Column(verticalArrangement=Arrangement.spacedBy(5.dp)) {
                Text(device.optString("name"),style=MaterialTheme.typography.titleMedium)
                Text(device.optString("address")+" · "+if(device.optBoolean("connected")) T(remote.ro,"Conectat","Connected") else if(device.optBoolean("paired")) T(remote.ro,"Asociat","Paired") else T(remote.ro,"Neasociat","Not paired"),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                    val action=if(device.optBoolean("connected")) "disconnect" else if(device.optBoolean("paired")) "connect" else "pair"
                    TextButton(onClick={remote.command("/api/bluetooth/action",obj("address" to device.optString("address"),"action" to action))},enabled=remote.enabled) { Text(when(action){"disconnect"->T(remote.ro,"Deconectează","Disconnect");"connect"->T(remote.ro,"Conectează","Connect");else->T(remote.ro,"Asociază","Pair")}) }
                    if(device.optBoolean("paired")) TextButton(onClick={btForget=device},enabled=remote.enabled) { Text(T(remote.ro,"Uită","Forget")) }
                }
                HorizontalDivider(color=MaterialTheme.colorScheme.outline.copy(alpha=.25f))
            }
        }
        if(bluetooth.objects("devices").isEmpty() && bluetooth.optBoolean("available")) Text(T(remote.ro,"Pornește scanarea și pune boxa în modul de asociere.","Start scanning and put your speaker in pairing mode."),style=MaterialTheme.typography.bodyMedium)
    }
    Panel {
        SectionTitle(T(remote.ro,"Rețeaua hubului","Hub network"),Icons.Outlined.Wifi)
        Text(if(network.optString("state")=="connected") T(remote.ro,"Conectat","Connected") else T(remote.ro,"Conexiune indisponibilă","Connection unavailable"),color=MaterialTheme.colorScheme.primary)
        network.objects("devices").forEach { device -> Text(listOf(device.optString("interface"),device.optString("ssid"),device.optString("state")).filter{it.isNotBlank() && it!="null"}.joinToString(" · "),style=MaterialTheme.typography.bodyMedium) }
        Button(onClick={remote.command("/api/network/scan",after={nearby=it.objects("networks")})},enabled=remote.enabled && network.optBoolean("available"),modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Text(T(remote.ro,"Caută rețele Wi-Fi","Scan Wi-Fi networks")) }
        (if(nearby.isEmpty()) network.objects("networks") else nearby).forEach { access ->
            OutlinedButton(onClick={wifi=access},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Text(access.optString("ssid"),Modifier.weight(1f));Text("${access.optInt("signal")}%",style=MaterialTheme.typography.bodyMedium) }
        }
        SectionTitle(T(remote.ro,"Conexiuni salvate","Saved connections"))
        network.objects("saved").forEach { profile ->
            Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) { Text(profile.optString("name"));Text(if(profile.optBoolean("active")) T(remote.ro,"Activă","Active") else T(remote.ro,"Salvată","Saved"),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant) }
                if(profile.optString("type")=="802-11-wireless" && profile.optString("ssid").isNotBlank()) IconButton(onClick={wifi=obj("ssid" to profile.optString("ssid"),"profile_id" to profile.optString("id"),"security" to profile.optString("security"))},enabled=remote.enabled) { Icon(Icons.Outlined.Edit,T(remote.ro,"Editează conexiunea","Edit connection")) }
                if(profile.optString("type")=="802-11-wireless") IconButton(onClick={forgetting=profile},enabled=remote.enabled) { Icon(Icons.Outlined.DeleteOutline,T(remote.ro,"Elimină conexiunea","Remove connection")) }
            }
        }
    }
    wifi?.let { access -> WifiDialog(remote,access){wifi=null} }
    forgetting?.let { profile -> ConfirmDialog(T(remote.ro,"Elimini conexiunea salvată?","Remove the saved connection?"),profile.optString("name")+"\n\n"+T(remote.ro,"Dacă este activă, telecomanda poate pierde legătura. Poți reconecta rețeaua de pe ecranul hubului.","If it is active, the remote may lose connection. You can reconnect from the hub's screen."),remote.ro,{remote.command("/api/network/forget",obj("id" to profile.optString("id")));forgetting=null}){forgetting=null} }
    btForget?.let { device -> ConfirmDialog(T(remote.ro,"Uiți dispozitivul?","Forget this device?"),device.optString("name"),remote.ro,{remote.command("/api/bluetooth/action",obj("address" to device.optString("address"),"action" to "forget"));btForget=null}){btForget=null} }
}

@Composable fun ToggleRow(label: String, checked: Boolean, enabled: Boolean, onChange:(Boolean)->Unit) {
    Row(Modifier.fillMaxWidth().heightIn(min=52.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) { Text(label,Modifier.weight(1f),style=MaterialTheme.typography.bodyLarge);Switch(checked=checked,onCheckedChange=onChange,enabled=enabled) }
}
@Composable fun ConfirmDialog(title: String, description: String, ro: Boolean, confirm:()->Unit, dismiss:()->Unit) {
    AlertDialog(onDismissRequest=dismiss,title={Text(title)},text={Text(description)},confirmButton={TextButton(onClick=confirm){Text(T(ro,"Confirmă","Confirm"))}},dismissButton={TextButton(onClick=dismiss){Text(T(ro,"Anulează","Cancel"))}})
}
@Composable fun WifiDialog(remote: RemoteController, access: JSONObject, dismiss:()->Unit) {
    var password by remember { mutableStateOf("") }
    AlertDialog(onDismissRequest=dismiss,title={Text(access.optString("ssid"))},text={Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
        Text(T(remote.ro,"Schimbarea rețelei hubului poate întrerupe telecomanda. Telefonul trebuie să fie apoi în aceeași rețea; la nevoie reconectează PySH de pe ecranul său.","Changing the hub's network may disconnect the remote. Your phone must then join the same network; if needed, reconnect PySH from its screen."),style=MaterialTheme.typography.bodyMedium)
        if(access.optString("security")!="open") Field(T(remote.ro,"Parolă Wi-Fi","Wi-Fi password"),password,{password=it},password=true)
    }},confirmButton={TextButton(onClick={val body=obj("ssid" to access.optString("ssid"),"password" to password);if(access.has("profile_id"))body.put("profile_id",access.optString("profile_id"));remote.command("/api/network/connect",body);password="";dismiss()},enabled=remote.enabled) { Text(T(remote.ro,"Conectează hubul","Connect hub")) }},dismissButton={TextButton(onClick={password="";dismiss()}){Text(T(remote.ro,"Anulează","Cancel"))}})
}

/** Pairing can await this reply, so it is intentionally independent of the mutation queue. */
@Composable fun BluetoothPrompts(remote: RemoteController) {
    val prompt=remote.state.child("bluetooth").objects("prompts").firstOrNull() ?: return
    var value by remember(prompt.optString("id")) { mutableStateOf("") }
    val kind=prompt.optString("kind")
    val input=kind in listOf("pin_code","passkey")
    AlertDialog(onDismissRequest={},icon={Icon(Icons.Outlined.Bluetooth,null)},title={Text(T(remote.ro,"Asociere Bluetooth","Bluetooth pairing"))},text={Column(verticalArrangement=Arrangement.spacedBy(12.dp)) {
        Text(prompt.optString("name"))
        Text(if(input) T(remote.ro,"Introdu codul boxei.","Enter the speaker's code.") else T(remote.ro,"Verifică același cod pe dispozitiv înainte de confirmare.","Check the same code on the device before confirming."))
        if(input) Field("PIN",value,{value=it.take(16)},keyboard=KeyboardType.NumberPassword,password=true)
        else Text(prompt.optString("value"),style=MaterialTheme.typography.headlineLarge)
    }},confirmButton={TextButton(onClick={remote.command("/api/bluetooth/reply",obj("id" to prompt.optString("id"),"accept" to true,"value" to if(input) value else null),parallel=true)},enabled=remote.online && (!input || value.isNotBlank())) { Text(T(remote.ro,"Acceptă","Accept")) }},dismissButton={TextButton(onClick={remote.command("/api/bluetooth/reply",obj("id" to prompt.optString("id"),"accept" to false),parallel=true)},enabled=remote.online) { Text(T(remote.ro,"Refuză","Reject")) }})
}
