package ro.pysh.remote

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.SystemBarStyle
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.platform.LocalContext
import kotlinx.coroutines.*
import java.time.ZonedDateTime
import java.time.ZoneId
import java.time.format.DateTimeFormatter
import java.util.Locale
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private lateinit var remote: RemoteController
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        remote = RemoteController(applicationContext, scope)
        setContent {
            val dark=remote.dark
            SideEffect {
                enableEdgeToEdge(
                    statusBarStyle=SystemBarStyle.auto(android.graphics.Color.TRANSPARENT,android.graphics.Color.TRANSPARENT){dark},
                    navigationBarStyle=SystemBarStyle.auto(android.graphics.Color.TRANSPARENT,android.graphics.Color.TRANSPARENT){dark}
                )
            }
            RemoteApp(remote)
        }
    }
    override fun onStart() { super.onStart(); remote.start() }
    override fun onStop() { remote.stop(); super.onStop() }
    override fun onDestroy() { scope.cancel(); super.onDestroy() }
}

val Mint = Color(0xFFA7F3CD)
val Lavender = Color(0xFFB9A6F5)
val LocalRomanian = staticCompositionLocalOf { true }
private val DarkPalette = darkColorScheme(primary = Mint, onPrimary = Color(0xFF103A29), primaryContainer = Color(0xFF244F3A), secondary = Lavender,
    background = Color(0xFF10141C), surface = Color(0xFF191F2A), surfaceVariant = Color(0xFF242C39), onSurface = Color(0xFFF0F3F7), onSurfaceVariant = Color(0xFFB9C4D4), outline = Color(0xFF7F8DA2))
private val LightPalette = lightColorScheme(primary = Color(0xFF176342), onPrimary = Color.White, primaryContainer = Color(0xFFD3F1DF), secondary = Color(0xFF67539C),
    background = Color(0xFFF6F5F0), surface = Color(0xFFFFFFFF), surfaceVariant = Color(0xFFE8ECE5), onSurface = Color(0xFF172720), onSurfaceVariant = Color(0xFF4A5E53), outline = Color(0xFF647568))

@Composable fun T(ro: Boolean, romanian: String, english: String) = if(ro) romanian else english
fun text(ro: Boolean, romanian: String, english: String) = if(ro) romanian else english
@Composable fun AppTheme(dark: Boolean, ro: Boolean=true, content: @Composable () -> Unit) {
    MaterialTheme(colorScheme = if(dark) DarkPalette else LightPalette, typography = Typography(
        headlineLarge = androidx.compose.ui.text.TextStyle(fontWeight = FontWeight.Bold, fontSize = 32.sp, letterSpacing = (-1).sp),
        headlineMedium = androidx.compose.ui.text.TextStyle(fontWeight = FontWeight.Bold, fontSize = 26.sp, letterSpacing = (-0.5).sp),
        titleLarge = androidx.compose.ui.text.TextStyle(fontWeight = FontWeight.SemiBold, fontSize = 21.sp),
        bodyLarge = androidx.compose.ui.text.TextStyle(fontSize = 16.sp, lineHeight = 24.sp),
        bodyMedium = androidx.compose.ui.text.TextStyle(fontSize = 14.sp, lineHeight = 21.sp)
    )) { CompositionLocalProvider(LocalRomanian provides ro,content=content) }
}

@Composable fun RemoteApp(remote: RemoteController) {
    AppTheme(remote.dark,remote.ro) {
        if(remote.connection!=null) BluetoothPrompts(remote)
        var tab by rememberSaveable { mutableIntStateOf(0) }
        val pageScroll=remember(tab,remote.connection?.deviceId) { ScrollState(0) }
        BackHandler(enabled = tab != 0) { tab = 0 }
        Scaffold(containerColor = MaterialTheme.colorScheme.background,
            bottomBar = {
                if(remote.connection != null) Column {
                    if(tab != 0 && remote.state.child("player").optString("state") !in listOf("", "idle", "ended")) MiniPlayer(remote)
                    NavigationBar(containerColor = MaterialTheme.colorScheme.surface, tonalElevation = 0.dp) {
                        val labels = listOf(text(remote.ro,"Acasă","Home"),"Radio",text(remote.ro,"Media","Media"),text(remote.ro,"Dispozitiv","Device"),text(remote.ro,"Setări","Settings"))
                        val icons = listOf(Icons.Outlined.Home, Icons.Outlined.Radio, Icons.Outlined.LibraryMusic, Icons.Outlined.Speaker, Icons.Outlined.Tune)
                        labels.forEachIndexed { index, label -> NavigationBarItem(selected = tab == index, onClick = { tab = index }, icon = { Icon(icons[index], label) }, label = { Text(label, maxLines=1, fontSize=11.sp) }, colors = NavigationBarItemDefaults.colors(indicatorColor = MaterialTheme.colorScheme.primaryContainer)) }
                    }
                }
            }
        ) { padding ->
            Box(Modifier.fillMaxSize().padding(padding).imePadding(), contentAlignment = Alignment.TopCenter) {
                Column(Modifier.widthIn(max = 680.dp).fillMaxWidth().verticalScroll(pageScroll).padding(horizontal=22.dp).padding(top=18.dp,bottom=28.dp), verticalArrangement=Arrangement.spacedBy(20.dp)) {
                    BrandHeader(remote)
                    remote.error?.let { code -> MessageCard(errorText(code, remote.ro), true) { remote.error = null } }
                    remote.notice?.let { notice -> MessageCard(text(remote.ro, if(notice=="sent_check") "Comandă trimisă. Reconectează-te pentru a verifica rezultatul." else "Comandă confirmată de hub.", if(notice=="sent_check") "Command sent. Reconnect to check the result." else "Command confirmed by the hub."), false) { remote.notice = null } }
                    if(remote.connection == null) PairPage(remote)
                    else {
                        if(!remote.online) OfflineBanner(remote)
                        if(remote.busy > 0) Row(verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(12.dp)) { CircularProgressIndicator(Modifier.size(18.dp), strokeWidth=2.dp); Text(T(remote.ro,"Se aplică pe PySH…","Applying on PySH…"), style=MaterialTheme.typography.bodyMedium) }
                        when(tab) {
                            0 -> HomePage(remote) { tab = it }
                            1 -> RadioPage(remote)
                            2 -> MediaPage(remote)
                            3 -> DevicePage(remote)
                            4 -> SettingsPage(remote)
                        }
                    }
                }
            }
        }
    }
}

@Composable fun BrandHeader(remote: RemoteController) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement=Arrangement.SpaceBetween, verticalAlignment=Alignment.CenterVertically) {
        Row(Modifier.weight(1f),verticalAlignment=Alignment.CenterVertically, horizontalArrangement=Arrangement.spacedBy(10.dp)) {
            Box(Modifier.size(38.dp).clip(RoundedCornerShape(13.dp)).background(MaterialTheme.colorScheme.primaryContainer), contentAlignment=Alignment.Center) { Icon(Icons.Outlined.GraphicEq,"PySH",tint=MaterialTheme.colorScheme.primary,modifier=Modifier.size(23.dp)) }
            Column(Modifier.weight(1f)) { Text("PySH",Modifier.fillMaxWidth(),fontSize=22.sp,fontWeight=FontWeight.Bold,maxLines=1); Text(T(remote.ro,"TELECOMANDĂ","REMOTE"),Modifier.fillMaxWidth(),fontSize=10.sp,letterSpacing=2.sp,color=MaterialTheme.colorScheme.onSurfaceVariant,maxLines=1) }
        }
        Surface(shape=CircleShape,color=MaterialTheme.colorScheme.surfaceVariant) {
            Row(Modifier.padding(horizontal=12.dp,vertical=9.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                Icon(if(remote.online) Icons.Outlined.Wifi else Icons.Outlined.WifiOff,null,Modifier.size(16.dp),tint=MaterialTheme.colorScheme.primary)
                Text(if(remote.online) "LAN" else T(remote.ro,"Local","Local"),fontSize=12.sp,fontWeight=FontWeight.SemiBold)
            }
        }
    }
}

@Composable fun Panel(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Surface(modifier.fillMaxWidth(),shape=RoundedCornerShape(26.dp),color=MaterialTheme.colorScheme.surface,tonalElevation=0.dp) {
        Column(Modifier.padding(20.dp),verticalArrangement=Arrangement.spacedBy(14.dp),content=content)
    }
}
@Composable fun PageTitle(title: String, description: String) { Column(Modifier.fillMaxWidth(),verticalArrangement=Arrangement.spacedBy(6.dp)) { Text(title,Modifier.fillMaxWidth(),style=MaterialTheme.typography.headlineLarge); Text(description,Modifier.fillMaxWidth(),style=MaterialTheme.typography.bodyLarge,color=MaterialTheme.colorScheme.onSurfaceVariant) } }
@Composable fun SectionTitle(title: String, icon: ImageVector? = null) { Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(10.dp)) { if(icon!=null) Icon(icon,null,tint=MaterialTheme.colorScheme.primary,modifier=Modifier.size(22.dp)); Text(title,Modifier.weight(1f),style=MaterialTheme.typography.titleLarge) } }
@Composable fun MessageCard(message: String, isError: Boolean, close: (() -> Unit)? = null) {
    Surface(shape=RoundedCornerShape(18.dp),color=if(isError) MaterialTheme.colorScheme.errorContainer else MaterialTheme.colorScheme.primaryContainer) {
        Row(Modifier.fillMaxWidth().padding(start=16.dp,top=12.dp,bottom=12.dp,end=4.dp),verticalAlignment=Alignment.CenterVertically) {
            Text(message,Modifier.weight(1f),color=if(isError) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onPrimaryContainer,style=MaterialTheme.typography.bodyMedium)
            if(close!=null) IconButton(onClick=close) { Icon(Icons.Outlined.Close,T(LocalRomanian.current,"Închide","Close"),tint=if(isError) MaterialTheme.colorScheme.onErrorContainer else MaterialTheme.colorScheme.onPrimaryContainer) }
        }
    }
}
@Composable fun OfflineBanner(remote: RemoteController) {
    Panel { SectionTitle(T(remote.ro,"Hub deconectat","Hub disconnected"),Icons.Outlined.WifiOff); Text(T(remote.ro,"Datele afișate sunt ultima stare primită.","The values shown are the last received state."),style=MaterialTheme.typography.bodyMedium);Text(errorText(remote.connectionIssue,remote.ro),style=MaterialTheme.typography.bodyMedium); Button(onClick={remote.reconnect()},modifier=Modifier.heightIn(min=48.dp),enabled=!remote.syncing) { Text(T(remote.ro,"Reconectează","Reconnect")) } }
}

@Composable fun PairPage(remote: RemoteController) {
    var host by rememberSaveable { mutableStateOf("192.168.100.127") }
    var pin by rememberSaveable { mutableStateOf("") }
    var code by rememberSaveable { mutableStateOf("") }
    Column(verticalArrangement=Arrangement.spacedBy(22.dp)) {
        Box(Modifier.fillMaxWidth().height(190.dp).clip(RoundedCornerShape(30.dp)).background(Brush.linearGradient(listOf(Color(0xFF263C42),Color(0xFF272B48)))),contentAlignment=Alignment.Center) {
            RadioArtwork(Modifier.size(170.dp))
            Surface(Modifier.align(Alignment.BottomEnd).padding(16.dp),shape=CircleShape,color=Mint) { Row(Modifier.padding(horizontal=12.dp,vertical=8.dp),verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(6.dp)) { Icon(Icons.Outlined.Lock,null,Modifier.size(14.dp),tint=Color(0xFF103A29)); Text("LAN ONLY",color=Color(0xFF103A29),fontSize=11.sp,fontWeight=FontWeight.Bold,letterSpacing=1.sp) } }
        }
        PageTitle(T(remote.ro,"Hubul tău.\nLa o atingere.","Your hub.\nOne touch away."),T(remote.ro,"Sunetul, atmosfera și toate comenzile PySH, direct din rețeaua ta.","Sound, atmosphere and every PySH control, right on your network."))
        Panel {
            SectionTitle(T(remote.ro,"Conectează PySH","Connect PySH"),Icons.Outlined.Link)
            Text(T(remote.ro,"1. Conectează telefonul la Wi-Fi-ul hubului.\n2. Activează serviciul LAN pe PySH.\n3. Copiază amprenta și codul afișate local.","1. Join the hub's Wi-Fi network.\n2. Enable the LAN service on PySH.\n3. Copy the fingerprint and code shown locally."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
            Field(T(remote.ro,"Adresa IP a hubului","Hub IP address"),host,{host=it},keyboard=KeyboardType.Decimal)
            Field(T(remote.ro,"Amprentă certificat SHA-256","SHA-256 certificate fingerprint"),pin,{pin=it},single=false)
            Field(T(remote.ro,"Cod de asociere · 8 cifre","Pairing code · 8 digits"),code,{code=it.take(8)},keyboard=KeyboardType.NumberPassword,password=true)
            Button(onClick={remote.pair(host,pin,code)},modifier=Modifier.fillMaxWidth().heightIn(min=54.dp),enabled=remote.busy==0) { Icon(Icons.Outlined.Link,null); Spacer(Modifier.width(10.dp)); Text(if(remote.busy>0) T(remote.ro,"Se asociază…","Pairing…") else T(remote.ro,"Asociază telefonul","Pair this phone")) }
        }
        Text(T(remote.ro,"Telefonul comunică doar cu adresa locală a hubului. Fără cont, cloud sau control prin internet.","Your phone communicates only with the hub's local address. No account, cloud or internet remote access."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) { TextButton(onClick={remote.language(!remote.ro)}) { Text(if(remote.ro) "English" else "Română") }; TextButton(onClick={remote.theme(!remote.dark)}) { Text(T(remote.ro,"Schimbă tema","Change theme")) } }
    }
}

@Composable fun Field(label: String, value: String, change: (String) -> Unit, single: Boolean=true, keyboard: KeyboardType=KeyboardType.Text, password: Boolean=false) {
    OutlinedTextField(value=value,onValueChange=change,label={Text(label)},modifier=Modifier.fillMaxWidth(),singleLine=single,maxLines=if(single) 1 else 4,shape=RoundedCornerShape(15.dp),keyboardOptions=KeyboardOptions(keyboardType=keyboard),visualTransformation=if(password) PasswordVisualTransformation() else androidx.compose.ui.text.input.VisualTransformation.None)
}
@Composable fun RadioArtwork(modifier: Modifier=Modifier) {
    Canvas(modifier) {
        val center = androidx.compose.ui.geometry.Offset(size.width/2,size.height/2)
        val radius = size.minDimension/2
        drawCircle(Brush.radialGradient(listOf(Color(0xFF748C88),Color(0xFF334B4C),Color(0xFF26343C)),center,radius),radius,center)
        for(i in 1..9) drawCircle(Color(0xFFBBCED0).copy(alpha=0.08f),radius*(0.22f+i*0.075f),center,style=androidx.compose.ui.graphics.drawscope.Stroke(1.dp.toPx()))
        drawCircle(Color(0xFFB9A6F5),radius*0.30f,center)
        drawCircle(Color(0xFF26343C),radius*0.055f,center)
        drawArc(Color.White.copy(alpha=0.20f),220f,55f,false,topLeft=androidx.compose.ui.geometry.Offset(size.width*.12f,size.height*.12f),size=androidx.compose.ui.geometry.Size(size.width*.76f,size.height*.76f),style=androidx.compose.ui.graphics.drawscope.Stroke(9.dp.toPx()))
    }
}

fun playerLabel(player: JSONObject, ro: Boolean) = when(player.optString("state")) {
    "playing" -> text(ro,"În redare","Playing")
    "paused" -> text(ro,"Pauză","Paused")
    "connecting", "buffering" -> text(ro,"Se încarcă…","Buffering…")
    "error" -> text(ro,"Redare indisponibilă","Playback unavailable")
    "ended" -> text(ro,"Redare încheiată","Playback ended")
    else -> text(ro,"Alege ce asculți","Choose what to play")
}
@Composable fun HomePage(remote: RemoteController, navigate: (Int)->Unit) {
    val player = remote.state.child("player")
    var now by remember { mutableStateOf(ZonedDateTime.now()) }
    LaunchedEffect(remote.preferences.optString("timezone")) { while(true) { now = ZonedDateTime.now(runCatching { ZoneId.of(remote.preferences.optString("timezone","Europe/Bucharest")) }.getOrDefault(ZoneId.systemDefault())); delay(1000) } }
    val locale = if(remote.ro) Locale.forLanguageTag("ro-RO") else Locale.UK
    Column(verticalArrangement=Arrangement.spacedBy(6.dp)) {
        Text(now.format(DateTimeFormatter.ofPattern("EEEE, d MMMM",locale)).replaceFirstChar{it.uppercase()},style=MaterialTheme.typography.bodyLarge,color=MaterialTheme.colorScheme.onSurfaceVariant)
        Text(now.format(DateTimeFormatter.ofPattern("HH:mm")),Modifier.fillMaxWidth(),fontSize=60.sp,fontWeight=FontWeight.Light,maxLines=1)
        Text(T(remote.ro,"Spațiul tău sonor.","Your space for sound."),Modifier.fillMaxWidth(),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
    Surface(shape=RoundedCornerShape(30.dp),color=MaterialTheme.colorScheme.surface) {
        Column(Modifier.padding(22.dp),verticalArrangement=Arrangement.spacedBy(18.dp)) {
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween,verticalAlignment=Alignment.CenterVertically) { Text(T(remote.ro,"ACUM PE PYSH","NOW ON PYSH"),fontSize=11.sp,letterSpacing=2.sp,color=MaterialTheme.colorScheme.onSurfaceVariant); Icon(Icons.Outlined.Speaker,null,tint=MaterialTheme.colorScheme.primary) }
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(18.dp)) {
                RadioArtwork(Modifier.size(106.dp))
                Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)) {
                    Text(player.label("station_name").ifBlank { player.label("title").ifBlank { T(remote.ro,"Liniște, deocamdată","A quiet moment") } },style=MaterialTheme.typography.headlineMedium,maxLines=2,overflow=TextOverflow.Ellipsis)
                    val title = player.label("title")
                    if(title.isNotBlank() && title!=player.label("station_name")) Text(title,style=MaterialTheme.typography.bodyMedium,maxLines=2,color=MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(playerLabel(player,remote.ro),color=MaterialTheme.colorScheme.primary,style=MaterialTheme.typography.bodyMedium)
                }
            }
            PlaybackControls(remote)
            VolumeControl(remote)
        }
    }
    Row(horizontalArrangement=Arrangement.spacedBy(12.dp),modifier=Modifier.fillMaxWidth()) {
        Shortcut(Modifier.weight(1f),Icons.Outlined.Radio,"Radio",T(remote.ro,"Posturile tale","Your stations")) { navigate(1) }
        Shortcut(Modifier.weight(1f),Icons.Outlined.LibraryMusic,"Media",T(remote.ro,"Fișiere pe hub","Files on your hub")) { navigate(2) }
    }
    val weather = remote.state.child("weather")
    val current = weather.child("current")
    Panel {
        Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceBetween) {
            Column(Modifier.weight(1f),verticalArrangement=Arrangement.spacedBy(6.dp)) { SectionTitle(weather.child("location").optString("name").ifBlank{T(remote.ro,"Vremea pe hub","Hub weather")},Icons.Outlined.Cloud); Text(if(weather.optBoolean("stale")) T(remote.ro,"Date meteo salvate","Saved weather") else T(remote.ro,"Locația aleasă pe PySH","Location selected on PySH"),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant) }
            Text(if(current.has("temperature_c") && !current.isNull("temperature_c")) "${current.optDouble("temperature_c").toInt()}°" else "—",fontSize=40.sp,fontWeight=FontWeight.Light)
        }
        if(current.has("humidity_pct")) Text("${T(remote.ro,"Umiditate","Humidity")} ${if(current.isNull("humidity_pct")) "—" else current.optInt("humidity_pct").toString()+"%"}  ·  ${T(remote.ro,"Vânt","Wind")} ${current.opt("wind_kmh") ?: "—"} km/h",style=MaterialTheme.typography.bodyMedium)
        TextButton(onClick={navigate(4)}) { Text(T(remote.ro,"Configurează atmosfera","Set the atmosphere")); Icon(Icons.Outlined.ArrowForward,null,modifier=Modifier.padding(start=6.dp).size(18.dp)) }
    }
    remote.connection?.let { Text("PySH · ${it.host} · ${T(remote.ro,"Conexiune locală criptată","Encrypted local connection")}",style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant) }
}
@Composable fun Shortcut(modifier: Modifier, icon: ImageVector, title: String, subtitle: String, action: ()->Unit) {
    Surface(onClick=action,modifier=modifier,shape=RoundedCornerShape(23.dp),color=MaterialTheme.colorScheme.surface) { Column(Modifier.padding(18.dp),verticalArrangement=Arrangement.spacedBy(10.dp)) { Icon(icon,null,tint=MaterialTheme.colorScheme.primary,modifier=Modifier.size(26.dp)); Text(title,fontWeight=FontWeight.SemiBold,fontSize=18.sp); Text(subtitle,fontSize=12.sp,color=MaterialTheme.colorScheme.onSurfaceVariant) } }
}
@Composable fun PlaybackControls(remote: RemoteController) {
    val player = remote.state.child("player")
    val active = player.optString("state") !in listOf("", "idle", "ended", "error")
    val radio = player.optString("kind") == "radio"
    Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.SpaceEvenly,verticalAlignment=Alignment.CenterVertically) {
        IconButton(onClick={remote.transport("previous")},enabled=remote.enabled && (if(radio) remote.preferences.objects("favorites").isNotEmpty() else player.optBoolean("canPrevious")),modifier=Modifier.size(50.dp)) { Icon(Icons.Outlined.SkipPrevious,T(remote.ro,"Anterior","Previous"),modifier=Modifier.size(30.dp)) }
        FilledIconButton(onClick={remote.transport("toggle")},enabled=remote.enabled && active,modifier=Modifier.size(66.dp)) { Icon(if(player.optString("state")=="paused") Icons.Outlined.PlayArrow else Icons.Outlined.Pause,T(remote.ro,"Redare sau pauză","Play or pause"),modifier=Modifier.size(32.dp)) }
        IconButton(onClick={remote.transport("next")},enabled=remote.enabled && (if(radio) remote.preferences.objects("favorites").isNotEmpty() else player.optBoolean("canNext")),modifier=Modifier.size(50.dp)) { Icon(Icons.Outlined.SkipNext,T(remote.ro,"Următor","Next"),modifier=Modifier.size(30.dp)) }
        IconButton(onClick={remote.transport("stop")},enabled=remote.enabled && active,modifier=Modifier.size(48.dp)) { Icon(Icons.Outlined.Stop,T(remote.ro,"Oprește","Stop")) }
    }
    val duration = player.optDouble("duration",0.0)
    if(duration>0 && player.optString("kind")!="radio") {
        var position by remember { mutableFloatStateOf(0f) }
        var dragging by remember { mutableStateOf(false) }
        LaunchedEffect(player.toString()) { if(!dragging) position=player.optDouble("position",0.0).toFloat().coerceIn(0f,duration.toFloat()) }
        Slider(value=position,onValueChange={dragging=true;position=it},onValueChangeFinished={dragging=false;remote.command("/api/player",obj("action" to "seek","value" to position))},valueRange=0f..duration.toFloat(),enabled=remote.enabled)
        Text("${(position/60).toInt()}:${(position%60).toInt().toString().padStart(2,'0')} / ${(duration/60).toInt()}:${(duration%60).toInt().toString().padStart(2,'0')}",style=MaterialTheme.typography.bodyMedium)
    }
}
@Composable fun VolumeControl(remote: RemoteController) {
    val audio = remote.state.child("audio")
    var volume by remember { mutableFloatStateOf(audio.optInt("volume",remote.preferences.optInt("volume",40)).toFloat().coerceIn(0f,100f)) }
    var dragging by remember { mutableStateOf(false) }
    LaunchedEffect(audio.toString()) { if(!dragging) volume=audio.optInt("volume",remote.preferences.optInt("volume",40)).toFloat().coerceIn(0f,100f) }
    Row(verticalAlignment=Alignment.CenterVertically) {
        IconButton(onClick={remote.command("/api/audio",obj("mute" to !audio.optBoolean("mute")))},enabled=remote.enabled && audio.optBoolean("available")) { Icon(if(audio.optBoolean("mute")) Icons.Outlined.VolumeOff else Icons.Outlined.VolumeUp,T(remote.ro,"Activează sau dezactivează sunetul","Mute or unmute")) }
        Slider(value=volume,onValueChange={dragging=true;volume=it},onValueChangeFinished={dragging=false;remote.command("/api/audio",obj("volume" to volume.toInt()))},modifier=Modifier.weight(1f),enabled=remote.enabled && audio.optBoolean("available"),valueRange=0f..100f)
        Text(if(audio.optBoolean("available") && !audio.isNull("volume")) "${volume.toInt()}%" else "—",modifier=Modifier.width(44.dp),fontSize=13.sp)
    }
}
@Composable fun MiniPlayer(remote: RemoteController) {
    val player = remote.state.child("player")
    Surface(color=MaterialTheme.colorScheme.surfaceVariant) { Row(Modifier.fillMaxWidth().padding(start=22.dp,end=12.dp,top=6.dp,bottom=6.dp),verticalAlignment=Alignment.CenterVertically) {
        Icon(Icons.Outlined.GraphicEq,null,tint=MaterialTheme.colorScheme.primary,modifier=Modifier.size(24.dp)); Spacer(Modifier.width(12.dp))
        Column(Modifier.weight(1f)) { Text(player.label("station_name").ifBlank{player.label("title")},maxLines=1,overflow=TextOverflow.Ellipsis,fontSize=14.sp,fontWeight=FontWeight.SemiBold); Text(playerLabel(player,remote.ro),fontSize=11.sp,color=MaterialTheme.colorScheme.onSurfaceVariant) }
        IconButton(onClick={remote.transport("toggle")},enabled=remote.enabled) { Icon(if(player.optString("state")=="paused") Icons.Outlined.PlayArrow else Icons.Outlined.Pause,T(remote.ro,"Redare sau pauză","Play or pause")) }
    } }
}

@Preview(showBackground=true,widthDp=412,heightDp=915)
@Composable fun PairingPreview() { val context=LocalContext.current; val scope=rememberCoroutineScope(); RemoteApp(remember { RemoteController(context,scope) }) }
