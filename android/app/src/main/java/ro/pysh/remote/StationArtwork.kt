package ro.pysh.remote

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive

/** No internet image loader: only the authenticated, pinned HubClient can supply pixels. */
@Composable fun StationArtwork(remote:RemoteController,station:String,name:String,modifier:Modifier=Modifier,identity:String=station) {
    var bitmap by remember(remote.connection,identity) { mutableStateOf<Bitmap?>(null) }
    LaunchedEffect(remote.connection,remote.online,identity) {
        if(remote.online && remote.connection?.token!="preview") {
            while(isActive && bitmap==null) {
                bitmap=remote.artwork(station,identity)
                if(bitmap==null) delay(60_000)
            }
        }
    }
    Surface(modifier=modifier,shape=RoundedCornerShape(18.dp),color=if(bitmap==null) MaterialTheme.colorScheme.primaryContainer else Color.White) {
        Box(contentAlignment=Alignment.Center) {
            bitmap?.let {
                Image(it.asImageBitmap(),T(remote.ro,"Sigla postului $name","$name station logo"),Modifier.fillMaxSize().padding(8.dp),contentScale=ContentScale.Fit)
            } ?: Text(name.trim().take(2).uppercase().ifBlank{"FM"},fontWeight=FontWeight.SemiBold,fontSize=22.sp,color=MaterialTheme.colorScheme.onPrimaryContainer)
        }
    }
}

@Composable fun CurrentArtwork(remote:RemoteController,modifier:Modifier=Modifier) {
    val player=remote.state.child("player")
    if(player.optString("kind")=="radio") {
        val saved=remote.preferences.child("lastStation")
        val id=player.label("station_uuid").ifBlank{saved.label("uuid")}
        val station=if(id.matches(Regex("[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}"))) id else "current"
        val name=player.label("station_name").ifBlank{player.label("title").ifBlank{"Radio"}}
        StationArtwork(remote,station,name,modifier,"$id|$name")
    } else RadioArtwork(modifier)
}
