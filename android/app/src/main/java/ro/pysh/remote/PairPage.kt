package ro.pysh.remote

import android.database.ContentObserver
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable private fun motionEnabled():Boolean {
    val resolver=LocalContext.current.contentResolver
    fun enabled()=Settings.Global.getFloat(resolver,Settings.Global.ANIMATOR_DURATION_SCALE,1f)>0f
    var motion by remember { mutableStateOf(enabled()) }
    DisposableEffect(resolver) {
        val observer=object:ContentObserver(Handler(Looper.getMainLooper())) { override fun onChange(selfChange:Boolean) { motion=enabled() } }
        resolver.registerContentObserver(Settings.Global.getUriFor(Settings.Global.ANIMATOR_DURATION_SCALE),false,observer)
        onDispose { resolver.unregisterContentObserver(observer) }
    }
    return motion
}

/** The pulse explains discovery/waiting. It stops with Android's animation scale set to zero. */
@Composable private fun ConnectionIllustration(searching:Boolean,waiting:Boolean) {
    val motion=motionEnabled()
    val primary=MaterialTheme.colorScheme.primary
    var phase by remember { mutableFloatStateOf(0.45f) }
    LaunchedEffect(searching,waiting,motion) {
        if(motion && (searching||waiting)) {
            val progress=Animatable(0f)
            progress.animateTo(1f,infiniteRepeatable(tween(if(waiting) 2000 else 2600, easing=LinearEasing),RepeatMode.Restart)) { phase=value }
        } else phase=0.45f
    }
    Box(Modifier.fillMaxWidth().height(156.dp).clip(RoundedCornerShape(30.dp)).background(Brush.linearGradient(listOf(MaterialTheme.colorScheme.primaryContainer,MaterialTheme.colorScheme.surfaceVariant))),contentAlignment=Alignment.Center) {
        Canvas(Modifier.size(150.dp)) {
            val radius=size.minDimension/2
            for(i in 0..2) {
                val step=(phase+i/3f)%1f
                drawCircle(primary.copy(alpha=(1-step)*0.22f),radius*(0.28f+step*0.65f),style=Stroke(2.dp.toPx()))
            }
        }
        Surface(shape=CircleShape,color=MaterialTheme.colorScheme.surface) {
            Icon(if(waiting) Icons.Outlined.PhoneAndroid else Icons.Outlined.Speaker,null,Modifier.padding(22.dp).size(36.dp),tint=primary)
        }
        Surface(Modifier.align(Alignment.BottomEnd).padding(14.dp),shape=CircleShape,color=MaterialTheme.colorScheme.surface) {
            Row(Modifier.padding(horizontal=12.dp,vertical=8.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                Icon(Icons.Outlined.Lock,null,Modifier.size(14.dp),tint=primary)
                Text(T(LocalRomanian.current,"Doar acasă","At home only"),fontSize=11.sp,fontWeight=FontWeight.SemiBold)
            }
        }
    }
}

@Composable fun PairPage(remote:RemoteController) {
    val waiting=remote.pairingState in setOf("requesting","waiting")
    val searching=remote.discoveryState=="searching" && remote.discoveredHubs.isEmpty()
    Column(verticalArrangement=Arrangement.spacedBy(22.dp)) {
        ConnectionIllustration(searching,waiting)
        PageTitle(T(remote.ro,"Hubul tău.\nLa o atingere.","Your hub.\nOne touch away."),T(remote.ro,"Telefonul găsește PySH în rețeaua ta. Tu aprobi conectarea pe ecranul hubului.","Your phone finds PySH on your network. You approve the connection on the hub's screen."))
        Panel(Modifier.animateContentSize(tween(180))) {
            SectionTitle(T(remote.ro,if(waiting) "Aprobă pe PySH" else "Conectează PySH",if(waiting) "Approve on PySH" else "Connect PySH"),if(waiting) Icons.Outlined.TouchApp else Icons.Outlined.Link)
            if(waiting) {
                Text(T(remote.ro,if(remote.pairingState=="requesting") "Pregătim conectarea…" else "Pe ecranul ${remote.pairingHub ?: "PySH"}, atinge „Da” pentru ${remote.phoneName}.",if(remote.pairingState=="requesting") "Preparing the connection…" else "On ${remote.pairingHub ?: "PySH"}, tap “Yes” for ${remote.phoneName}."),Modifier.semantics { liveRegion=LiveRegionMode.Polite },style=MaterialTheme.typography.bodyLarge)
                LinearProgressIndicator(Modifier.fillMaxWidth())
                Text(T(remote.ro,"Cererea este valabilă două minute. Nu trebuie să introduci nimic.","The request is valid for two minutes. There is nothing to type."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                OutlinedButton(onClick={remote.cancelPairing()},modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)) { Text(T(remote.ro,"Anulează conectarea","Cancel connection")) }
            } else {
                Text(T(remote.ro,"1. Conectează telefonul și PySH la aceeași rețea.\n2. Pe PySH: Setări → Android App Control → Activat.\n3. Alege hubul și acceptă cererea pe ecranul lui.","1. Connect your phone and PySH to the same network.\n2. On PySH: Settings → Android App Control → Enabled.\n3. Choose your hub and accept on its screen."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
                if(remote.pairingState !in setOf("idle","requesting","waiting")) {
                    Text(errorText(remote.pairingState,remote.ro),Modifier.semantics { liveRegion=LiveRegionMode.Polite },color=MaterialTheme.colorScheme.error,style=MaterialTheme.typography.bodyMedium)
                }
                if(remote.discoveredHubs.isNotEmpty()) {
                    remote.discoveredHubs.forEachIndexed { index,hub ->
                        Button(onClick={remote.pair(hub)},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) {
                            Icon(Icons.Outlined.Link,null);Spacer(Modifier.width(10.dp))
                            Text(T(remote.ro,"Conectează","Connect")+" ${hub.name}"+if(remote.discoveredHubs.size>1) " · ${index+1}" else "")
                        }
                    }
                    if(remote.discoveredHubs.size>1)Text(T(remote.ro,"Dacă ai mai multe huburi, verifică pe care apare cererea înainte să o accepți.","With multiple hubs, check which screen shows the request before accepting."),style=MaterialTheme.typography.bodyMedium)
                } else {
                    val message=when(remote.discoveryState) {
                        "wifi_required" -> T(remote.ro,"Conectează telefonul la Wi-Fi-ul de acasă pentru a găsi PySH.","Join your home Wi-Fi to find PySH.")
                        "not_found" -> T(remote.ro,"PySH nu este încă vizibil. Verifică Android App Control pe hub și folosește aceeași rețea; rețelele pentru oaspeți pot izola dispozitivele.","PySH is not visible yet. Check Android App Control on the hub and use the same network; guest networks may isolate devices.")
                        "discovery_unavailable" -> T(remote.ro,"Căutarea locală nu este disponibilă momentan. Reîncearcă după conectarea la Wi-Fi.","Local discovery is unavailable for now. Try again after joining Wi-Fi.")
                        else -> T(remote.ro,"Căutăm PySH în apropiere…","Looking for PySH nearby…")
                    }
                    Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                        if(searching)CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp)
                        Text(message,Modifier.weight(1f).semantics { liveRegion=LiveRegionMode.Polite },style=MaterialTheme.typography.bodyMedium)
                    }
                    OutlinedButton(onClick={remote.searchAgain()},modifier=Modifier.fillMaxWidth().heightIn(min=52.dp)) { Icon(Icons.Outlined.Refresh,null);Spacer(Modifier.width(8.dp));Text(T(remote.ro,"Caută din nou","Search again")) }
                }
            }
        }
        Text(T(remote.ro,"După asociere, aplicația regăsește automat hubul când adresa lui se schimbă. Controlul rămâne în rețeaua ta locală.","After pairing, the app automatically finds your hub when its address changes. Control stays on your local network."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            TextButton(onClick={remote.language(!remote.ro)},modifier=Modifier.heightIn(min=48.dp)) { Text(if(remote.ro) "English" else "Română") }
            TextButton(onClick={remote.theme(!remote.dark)},modifier=Modifier.heightIn(min=48.dp)) { Text(T(remote.ro,"Schimbă tema","Change theme")) }
        }
    }
}
