package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import org.json.JSONObject

@Composable fun RadioPage(remote: RemoteController) {
    var search by rememberSaveable { mutableStateOf("") }
    var country by rememberSaveable { mutableStateOf("") }
    var language by rememberSaveable { mutableStateOf("") }
    var results by remember { mutableStateOf<List<JSONObject>>(emptyList()) }
    var loading by remember { mutableStateOf(false) }
    var searched by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<String?>(null) }
    var stale by remember { mutableStateOf(false) }
    var custom by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    fun load() { scope.launch {
        loading=true;failure=null
        try {
            val response=remote.read("/api/radio?q=${query(search)}&country=${query(country)}&language=${query(language)}")
            results=response.objects("stations");stale=response.optBoolean("stale");searched=true
        } catch(e: CancellationException) { throw e } catch(e: Exception) { failure=(e as? HubFailure)?.code ?: "operation_failed" }
        finally { loading=false }
    } }
    PageTitle("Radio",T(remote.ro,"Un post pentru fiecare moment.","A station for every moment."))
    Panel {
        Field(T(remote.ro,"Caută un post","Search for a station"),search,{search=it})
        Row(horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            Box(Modifier.weight(1f)) { Field(T(remote.ro,"Țară","Country"),country,{country=it}) }
            Box(Modifier.weight(1f)) { Field(T(remote.ro,"Limbă","Language"),language,{language=it}) }
        }
        Button(onClick={load()},enabled=remote.online && !loading,modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Icon(Icons.Outlined.Search,null);Spacer(Modifier.width(8.dp));Text(if(loading) T(remote.ro,"Se caută…","Searching…") else T(remote.ro,"Găsește posturi","Find stations")) }
        failure?.let { MessageCard(errorText(it,remote.ro),true) }
        if(stale) Text(T(remote.ro,"Catalog salvat pe hub; sursa online nu este disponibilă.","Saved catalog on the hub; the online source is unavailable."),style=MaterialTheme.typography.bodyMedium)
    }
    val favorites=remote.preferences.objects("favorites")
    SectionTitle(T(remote.ro,"Favoritele tale","Your favorites"),Icons.Outlined.FavoriteBorder)
    if(favorites.isEmpty()) Panel { Text(T(remote.ro,"Găsește un post și atinge inima. Favoritele sunt salvate pe PySH.","Find a station and tap the heart. Favorites are saved on PySH."),color=MaterialTheme.colorScheme.onSurfaceVariant) }
    favorites.forEach { StationRow(it,true,remote) }
    OutlinedButton(onClick={custom=true},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Icon(Icons.Outlined.Add,null);Spacer(Modifier.width(8.dp));Text(T(remote.ro,"Adaugă un flux radio propriu","Add your own radio stream")) }
    if(custom) CustomStationDialog(remote){custom=false}
    if(searched) {
        SectionTitle(T(remote.ro,"Rezultate","Results"),Icons.Outlined.Radio)
        if(results.isEmpty()) Panel { Text(T(remote.ro,"Niciun post găsit. Încearcă alt nume sau schimbă filtrele.","No stations found. Try another name or change the filters.")) }
        results.forEach { station -> StationRow(station,favorites.any{it.optString("uuid")==station.optString("uuid")},remote) }
    }
}

@Composable fun StationRow(station: JSONObject, favorite: Boolean, remote: RemoteController) {
    Surface(shape=RoundedCornerShape(22.dp),color=MaterialTheme.colorScheme.surface) {
        Row(Modifier.fillMaxWidth().padding(14.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            Surface(shape=RoundedCornerShape(14.dp),color=MaterialTheme.colorScheme.primaryContainer,modifier=Modifier.size(48.dp)) { Box(contentAlignment=Alignment.Center) { Text(station.optString("name","R").take(2).uppercase(),color=MaterialTheme.colorScheme.onPrimaryContainer,fontWeight=FontWeight.Bold,fontSize=18.sp) } }
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(4.dp)) {
                Text(station.optString("name"),fontWeight=FontWeight.SemiBold,maxLines=2,overflow=TextOverflow.Ellipsis)
                Text(listOf(station.optString("country"),station.optString("codec"),station.optInt("bitrate").let{if(it>0) "$it kbps" else ""}).filter{it.isNotBlank()}.joinToString(" · "),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant,maxLines=2)
            }
            Column {
                IconButton(onClick={remote.playStation(station)},enabled=remote.enabled) { Icon(Icons.Outlined.PlayArrow,T(remote.ro,"Redă postul","Play station"),tint=MaterialTheme.colorScheme.primary) }
                IconButton(onClick={remote.command("/api/favorites",obj("station" to station,"remove" to favorite))},enabled=remote.enabled) { Icon(if(favorite) Icons.Outlined.Favorite else Icons.Outlined.FavoriteBorder,if(favorite) T(remote.ro,"Elimină din favorite","Remove favorite") else T(remote.ro,"Adaugă la favorite","Add favorite"),tint=MaterialTheme.colorScheme.secondary) }
            }
        }
    }
}

@Composable fun MediaPage(remote: RemoteController) {
    var folder by rememberSaveable { mutableStateOf("") }
    var listing by remember { mutableStateOf(JSONObject()) }
    var filter by rememberSaveable { mutableStateOf("") }
    var loading by remember { mutableStateOf(false) }
    var failure by remember { mutableStateOf<String?>(null) }
    var deleting by remember { mutableStateOf<JSONObject?>(null) }
    var revision by remember { mutableIntStateOf(0) }
    var externalJob by rememberSaveable { mutableStateOf("") }
    var externalStatus by remember { mutableStateOf(JSONObject()) }
    val scope=rememberCoroutineScope()
    LaunchedEffect(folder,revision,remote.online) {
        if(!remote.online) return@LaunchedEffect
        loading=true;failure=null
        try { listing=remote.read("/api/media?path=${query(folder)}") }
        catch(e: CancellationException) { throw e } catch(e: Exception) { failure=(e as? HubFailure)?.code ?: "media_unavailable" }
        finally { loading=false }
    }
    LaunchedEffect(externalJob,remote.online) {
        if(externalJob.isBlank() || !remote.online) return@LaunchedEffect
        while(true) {
            try { externalStatus=remote.read("/api/external/preparation?job=${query(externalJob)}") }
            catch(e: CancellationException) { throw e } catch(e: Exception) { failure=(e as? HubFailure)?.code ?: "operation_failed";break }
            kotlinx.coroutines.delay(2000)
        }
    }
    PageTitle("Media",T(remote.ro,"Biblioteca hubului, în mâna ta.","Your hub's library, in your hand."))
    Panel {
        SectionTitle(T(remote.ro,"Servicii pe ecranul PySH","Services on the PySH screen"),Icons.Outlined.Tv)
        Text(T(remote.ro,"Deschide serviciul oficial pe hub. Autentificarea și comenzile din site se folosesc pe ecranul PySH; compatibilitatea redării depinde de browser și serviciu.","Open the official service on your hub. Use the PySH screen for sign-in and website controls; playback compatibility depends on the browser and service."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        listOf("youtube" to "YouTube","netflix" to "Netflix","spotify" to "Spotify").forEach { (service,label) ->
            OutlinedButton(onClick={remote.command("/api/external",obj("service" to service),after={ result -> externalJob=result.optString("jobId");externalStatus=result })},enabled=remote.enabled,modifier=Modifier.fillMaxWidth().heightIn(min=50.dp)) { Text(label,Modifier.weight(1f));Icon(Icons.Outlined.OpenInNew,null,Modifier.size(18.dp)) }
        }
        if(externalJob.isNotEmpty()) {
            Text(T(remote.ro,"Pregătire serviciu","Service preparation")+": "+externalLabel(externalStatus.optString("state"),remote.ro),style=MaterialTheme.typography.bodyMedium)
            Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                TextButton(onClick={remote.command("/api/external/retry",obj("job" to externalJob))},enabled=remote.enabled) { Text(T(remote.ro,"Reîncearcă","Retry")) }
                TextButton(onClick={remote.command("/api/external/cancel",obj("job" to externalJob),after={externalJob=""})},enabled=remote.enabled) { Text(T(remote.ro,"Anulează","Cancel")) }
            }
        }
    }
    SectionTitle(T(remote.ro,"Fișiere pe hub","Files on the hub"),Icons.Outlined.FolderOpen)
    Panel {
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
            Text(folder.ifBlank{T(remote.ro,"Directoare media aprobate","Approved media folders")},Modifier.weight(1f),style=MaterialTheme.typography.bodyMedium,maxLines=3,overflow=TextOverflow.Ellipsis)
            IconButton(onClick={revision++},enabled=remote.online && !loading) { Icon(Icons.Outlined.Refresh,T(remote.ro,"Reîncarcă lista","Reload list")) }
        }
        if(folder.isNotBlank()) TextButton(onClick={folder=listing.optString("parent").takeIf{!listing.isNull("parent")} ?: ""},enabled=!loading) { Icon(Icons.Outlined.ArrowBack,null,Modifier.size(18.dp));Spacer(Modifier.width(8.dp));Text(T(remote.ro,"Director părinte","Parent folder")) }
        Field(T(remote.ro,"Filtrează fișierele","Filter files"),filter,{filter=it})
        if(loading) LinearProgressIndicator(Modifier.fillMaxWidth())
        failure?.let { MessageCard(errorText(it,remote.ro),true) }
        if(listing.optBoolean("partial")) Text(T(remote.ro,"Unele directoare nu pot fi citite. Lista este parțială.","Some folders cannot be read. This list is partial."),style=MaterialTheme.typography.bodyMedium)
    }
    val files=listing.objects("items").filter{it.optString("name").contains(filter,true)}
    if(files.isEmpty() && !loading && failure==null) Panel { Text(T(remote.ro,"Niciun fișier aici. Adaugă fișiere în directoarele media ale PySH sau conectează un suport USB.","No files here. Add files to PySH's media folders or connect a USB drive."),color=MaterialTheme.colorScheme.onSurfaceVariant) }
    files.forEach { item ->
        val directory=item.optBoolean("is_dir")
        Surface(shape=RoundedCornerShape(20.dp),color=MaterialTheme.colorScheme.surface) {
            Row(Modifier.padding(14.dp).fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                Icon(if(directory) Icons.Outlined.Folder else if(item.optString("kind")=="video") Icons.Outlined.Movie else Icons.Outlined.MusicNote,null,tint=MaterialTheme.colorScheme.primary)
                Column(Modifier.weight(1f)) { Text(item.optString("name"),fontWeight=FontWeight.SemiBold,maxLines=3,overflow=TextOverflow.Ellipsis);if(!directory) Text("${item.optLong("size")/1024} KB",style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant) }
                IconButton(onClick={if(directory) folder=item.optString("path") else remote.command("/api/play",obj("source" to "local","path" to item.optString("path"),"title" to item.optString("name")))},enabled=if(directory) !loading else remote.enabled) { Icon(if(directory) Icons.Outlined.ChevronRight else Icons.Outlined.PlayArrow,if(directory) T(remote.ro,"Deschide directorul","Open folder") else T(remote.ro,"Redă pe hub","Play on hub")) }
                if(item.optBoolean("deletable")) IconButton(onClick={deleting=item},enabled=remote.enabled) { Icon(Icons.Outlined.DeleteOutline,T(remote.ro,"Șterge fișierul","Delete file")) }
            }
        }
    }
    deleting?.let { file -> AlertDialog(onDismissRequest={deleting=null},icon={Icon(Icons.Outlined.DeleteOutline,null)},title={Text(T(remote.ro,"Ștergi fișierul de pe PySH?","Delete this file from PySH?"))},text={Text(file.optString("name")+"\n\n"+T(remote.ro,"Ștergerea este permanentă.","Deletion is permanent."))},confirmButton={TextButton(onClick={remote.command("/api/media",obj("path" to file.optString("path"),"token" to file.optString("delete_token")),"DELETE",after={revision++});deleting=null},enabled=remote.enabled) { Text(T(remote.ro,"Șterge","Delete"),color=MaterialTheme.colorScheme.error) }},dismissButton={TextButton(onClick={deleting=null}){Text(T(remote.ro,"Anulează","Cancel"))}}) }
}
