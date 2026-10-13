package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.unit.dp

fun externalLabel(state:String,ro:Boolean)=when(state){
    "ready","opened"->text(ro,"Deschis pe PySH","Opened on PySH")
    "failed","error"->text(ro,"Pregătire nereușită","Preparation failed")
    "cancelled","idle"->text(ro,"Inactiv","Inactive")
    else->text(ro,"Se pregătește…","Preparing…")
}

@Composable fun CustomStationDialog(remote: RemoteController,dismiss:()->Unit) {
    var name by remember{mutableStateOf("")}
    var url by remember{mutableStateOf("")}
    var invalid by remember{mutableStateOf(false)}
    AlertDialog(onDismissRequest=dismiss,title={Text(T(remote.ro,"Post radio propriu","Custom radio station"))},text={Column(verticalArrangement=Arrangement.spacedBy(12.dp)){
        Field(T(remote.ro,"Nume post","Station name"),name,{name=it.take(160)})
        Field(T(remote.ro,"Adresa fluxului HTTP(S)","HTTP(S) stream address"),url,{url=it})
        if(invalid)Text(T(remote.ro,"Introdu un nume și o adresă HTTP(S) validă, fără credențiale în adresă.","Enter a name and valid HTTP(S) address with no credentials in the address."),color=MaterialTheme.colorScheme.error)
    }},confirmButton={TextButton(onClick={val valid=runCatching{val uri=java.net.URI(url);uri.scheme in listOf("http","https") && !uri.host.isNullOrEmpty() && uri.userInfo==null && url.length<=2048}.getOrDefault(false)
        if(name.isNotBlank() && valid){remote.command("/api/favorites",obj("station" to obj("uuid" to "custom-${java.util.UUID.randomUUID()}","name" to name,"url" to url)));dismiss()}else invalid=true
    },enabled=remote.enabled){Text(T(remote.ro,"Adaugă","Add"))}},dismissButton={TextButton(onClick=dismiss){Text(T(remote.ro,"Anulează","Cancel"))}})
}
