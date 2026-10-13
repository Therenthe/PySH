package ro.pysh.remote

import android.content.Context
import android.graphics.Bitmap
import android.os.Build
import android.util.LruCache
import androidx.compose.runtime.*
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import org.json.JSONArray
import org.json.JSONObject
import java.net.URLEncoder

fun obj(vararg entries: Pair<String, Any?>) = JSONObject().apply { entries.forEach { put(it.first, it.second ?: JSONObject.NULL) } }
fun JSONObject.objects(key: String): List<JSONObject> = optJSONArray(key)?.let { array -> (0 until array.length()).mapNotNull { array.optJSONObject(it) } } ?: emptyList()
fun JSONObject.child(key: String): JSONObject = optJSONObject(key) ?: JSONObject()
fun JSONObject.label(key: String): String = if(isNull(key)) "" else optString(key)
fun query(value: String) = URLEncoder.encode(value, "UTF-8")

class RemoteController(context: Context, private val scope: CoroutineScope) {
    private val store = ConnectionStore(context)
    private val uiStore = context.getSharedPreferences("interface", Context.MODE_PRIVATE)
    private val client = HubClient(context)
    private val discovery=HubDiscovery(context) { found,phase ->
        discoveredHubs=found;discoveryState=phase
        if(connection!=null && !online && foreground) recoverDiscoveredAddress()
    }
    private val writes = Mutex()
    private val reads = Mutex()
    private val presence = Mutex()
    private val artworkReads = Mutex()
    private val artworkCache = object : LruCache<String,Bitmap>(4*1024*1024) {
        override fun sizeOf(key:String,value:Bitmap)=value.allocationByteCount
    }
    private val artworkFailures = LinkedHashMap<String,Long>()
    @Volatile private var foreground=true
    var connection by mutableStateOf(store.load()); private set
    var state by mutableStateOf(JSONObject()); private set
    var online by mutableStateOf(false); private set
    var syncing by mutableStateOf(false); private set
    var connectionIssue by mutableStateOf("hub_unavailable"); private set
    var busy by mutableIntStateOf(0); private set
    var error by mutableStateOf<String?>(null)
    var notice by mutableStateOf<String?>(null)
    var ro by mutableStateOf(uiStore.getString("language", "ro") != "en"); private set
    var dark by mutableStateOf(uiStore.getBoolean("dark", true)); private set
    var discoveredHubs by mutableStateOf<List<DiscoveredHub>>(emptyList());private set
    var discoveryState by mutableStateOf("searching");private set
    var pairingState by mutableStateOf("idle");private set
    var pairingHub by mutableStateOf<String?>(null);private set
    val phoneName=listOf(Build.MANUFACTURER,Build.MODEL).distinct().joinToString(" ").filterNot{it.isISOControl()}.take(64).ifBlank{"Android"}
    private var pairingJob:Job?=null
    private var recoveryJob:Job?=null
    private val recoveryAttempts=mutableMapOf<String,Long>()
    private var nextSearchAt=0L
    val preferences get() = state.child("preferences")
    val power get() = state.child("power")
    val powerAvailable get() = online && power.has("standby")
    val enabled get() = online && busy == 0
    private var polling: Job? = null
    private var reading = false
    internal fun previewState(value: JSONObject, romanian: Boolean=true) {
        check(BuildConfig.DEBUG)
        state=value;ro=romanian;online=true
        connection=HubConnection("192.168.100.127","0".repeat(64),"preview","preview")
    }
    internal fun previewOnboarding(phase:String,romanian:Boolean,night:Boolean) {
        check(BuildConfig.DEBUG)
        connection=null;state=JSONObject();online=false;ro=romanian;dark=night
        discoveryState=if(phase in setOf("searching","wifi_required","not_found","discovery_unavailable"))phase else "found"
        discoveredHubs=if(discoveryState=="found")listOf(DiscoveredHub("192.168.1.88","079ab3e4-6dd7-486b-88b9-8a1a6900dc8b")) else emptyList()
        pairingState=if(phase in setOf("waiting","pairing_denied","pairing_expired"))phase else "idle"
        pairingHub=if(phase=="waiting")"PySH" else null
    }
    fun language(value: Boolean) { ro = value; uiStore.edit().putString("language", if (ro) "ro" else "en").apply() }
    fun theme(value: Boolean) { dark = value; uiStore.edit().putBoolean("dark", value).apply() }
    fun start() {
        foreground=true
        if (polling?.isActive == true) return
        discovery.start()
        polling = scope.launch { while (isActive) { refresh(); delay(2000) } }
    }
    fun stop() {
        foreground=false;polling?.cancel();polling = null
        discovery.stop();recoveryJob?.cancel();pairingJob?.cancel()
        val current=connection ?: return
        // This finite cleanup survives Activity destruction, but is ordered before a resumed GET.
        CoroutineScope(Dispatchers.IO).launch {
            presence.withLock {
                if(foreground || connection!=current) return@withLock
                try { client.request(current,"/remote/heartbeat","DELETE") }
                catch(e:CancellationException) { throw e } catch(_:Exception) { /* Server TTL also expires presence. */ }
            }
        }
    }
    private fun code(error: Throwable) = when(error) {
        is HubFailure -> error.code
        is IllegalArgumentException -> error.message ?: "invalid_request"
        else -> "operation_failed"
    }
    suspend fun refresh(force: Boolean=false) {
        val current = connection ?: return
        if (reading && !force) return
        reads.withLock {
            if(connection!=current) return
            reading = true
            syncing = true
            try {
                val result = presence.withLock stateRead@ {
                    if(!foreground) return@stateRead null
                    client.request(current, "/api/state")
                } ?: return
                if (connection == current) {
                    state = result; online = true
                    if(current.hubId.isBlank()) migrateIdentity(current)
                }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) {
                if (connection == current) {
                    online = false;connectionIssue=code(e);recoverDiscoveredAddress()
                    // Re-resolve even if an mDNS implementation retained an instance after its IP changed.
                    if(foreground && System.currentTimeMillis()>=nextSearchAt) { nextSearchAt=System.currentTimeMillis()+12_000;discovery.restart() }
                }
            }
            finally { syncing = false; reading = false }
        }
    }
    fun reconnect() { searchAgain();scope.launch { refresh(true) } }
    fun searchAgain() { recoveryAttempts.clear();discovery.restart();recoverDiscoveredAddress() }
    private suspend fun migrateIdentity(current:HubConnection) {
        try {
            val identity=client.request(current,"/remote/identity")
            DiscoveryPolicy.verifyReconnect(current.hubId,current.pin,identity.getString("hubId"),identity.getString("certificateSha256"))
            if(connection==current) { val updated=current.copy(hubId=DiscoveryPolicy.hubId(identity.getString("hubId")));store.save(updated);connection=updated }
        } catch(e:CancellationException) { throw e } catch(_:Exception) { /* Old gateways remain paired until their upgrade. */ }
    }
    /** Only GET identity/state are retried. A failed command is never replayed at a new address. */
    private fun recoverDiscoveredAddress() {
        val saved=connection ?: return
        if(!foreground || online || recoveryJob?.isActive==true)return
        val hints=discoveredHubs.filter { (saved.hubId.isBlank() || it.hubId==saved.hubId) && (recoveryAttempts[it.host] ?: 0)<System.currentTimeMillis() }
        if(hints.isEmpty())return
        recoveryJob=scope.launch {
            for(hint in hints) {
                if(connection!=saved || !foreground)return@launch
                recoveryAttempts[hint.host]=System.currentTimeMillis()+15_000
                try {
                    // The stored certificate is verified before any bearer token reaches this hint.
                    val atHint=saved.copy(host=hint.host,token="")
                    val identity=client.request(atHint,"/remote/identity")
                    DiscoveryPolicy.verifyPairing(hint.hubId,identity.getString("hubId"),identity.getString("certificateSha256"),saved.pin)
                    DiscoveryPolicy.verifyReconnect(saved.hubId,saved.pin,identity.getString("hubId"),identity.getString("certificateSha256"))
                    val updated=saved.copy(host=hint.host,hubId=hint.hubId)
                    if(connection!=saved)return@launch
                    if(busy>0)notice="sent_check"
                    store.save(updated);connection=updated;refresh(true);return@launch
                } catch(e:CancellationException) { throw e }
                catch(e:Exception) { if(connection==saved)connectionIssue=code(e) }
            }
        }
    }
    fun pair(hub:DiscoveredHub) {
        if(pairingJob?.isActive==true || connection!=null)return
        pairingJob=scope.launch {
            pairingState="requesting";pairingHub=hub.name;error=null
            var candidate:HubConnection?=null
            var pending:JSONObject?=null
            var completed=false
            try {
                val identity=client.discoverIdentity(hub)
                if(!identity.enabled)throw HubFailure("control_disabled")
                val crypto=withContext(Dispatchers.Default) { PairingCrypto() }
                candidate=HubConnection(hub.host,identity.pin,"","",hub.hubId)
                val request=client.request(candidate,"/remote/pair/request","POST",obj("name" to phoneName,"publicKey" to crypto.publicKey))
                val id=DiscoveryPolicy.hubId(request.getString("requestId"))
                val secret=request.getString("requestSecret")
                require(secret.matches(Regex("[A-Za-z0-9_-]{43}"))) { "invalid_response" }
                pending=obj("requestId" to id,"requestSecret" to secret)
                pairingState="waiting"
                withTimeout(request.getInt("expiresIn").coerceIn(1,120)*1000L) {
                    while(true) {
                        val response=client.request(candidate,"/remote/pair/status","POST",pending)
                        when(response.getString("status")) {
                            "pending" -> delay(1500)
                            "denied" -> throw HubFailure("pairing_denied")
                            "expired" -> throw HubFailure("pairing_expired")
                            "approved" -> {
                                val result=JSONObject(withContext(Dispatchers.Default) { crypto.decrypt(response.getString("encryptedResult")) })
                                DiscoveryPolicy.verifyPairing(hub.hubId,result.getString("hubId"),result.getString("certificateSha256"),identity.pin)
                                val token=result.getString("token")
                                require(token.matches(Regex("[A-Za-z0-9_-]{43}"))) { "invalid_response" }
                                val paired=candidate.copy(token=token,deviceId=DiscoveryPolicy.hubId(result.getString("deviceId")))
                                // Prove the pinned authenticated association before persisting it.
                                val initial=client.request(paired,"/api/state")
                                store.save(paired);connection=paired;state=initial;online=true;completed=true;pairingState="idle"
                                return@withTimeout
                            }
                            else -> throw HubFailure("invalid_response")
                        }
                    }
                }
            } catch(_:TimeoutCancellationException) { pairingState="pairing_expired" }
            catch(e:CancellationException) { pairingState="idle";throw e }
            catch(e:Exception) { pairingState=code(e) }
            finally {
                if(!completed && candidate!=null && pending!=null) withContext(NonCancellable) {
                    // Own pending request only; the endpoint also revokes an uncollected approved token.
                    runCatching { withTimeout(4000) { client.request(candidate,"/remote/pair/cancel","POST",pending) } }
                }
                pairingHub=null
            }
        }
    }
    fun cancelPairing() { pairingJob?.cancel() }
    fun forget() { store.clear(); connection = null; state = JSONObject(); online = false; error = null;pairingState="idle";searchAgain() }
    fun revoke() { command("/remote/revoke-self",after={forget()}) }
    fun command(path: String, body: JSONObject = JSONObject(), method: String = "POST", parallel: Boolean = false, after: ((JSONObject) -> Unit)? = null) {
        val current = connection ?: return
        scope.launch {
            suspend fun perform() {
                if(connection!=current) return
                busy++; error = null; notice = null
                try {
                    val result = client.request(current, path, method, body)
                    if (connection != current) return
                    after?.invoke(result)
                    refresh(true)
                    if (!online) notice = "sent_check"
                } catch (e: CancellationException) { throw e }
                catch (e: Exception) { if (connection == current) error = code(e) }
                finally { busy-- }
            }
            if (parallel) perform() else writes.withLock { perform() }
        }
    }
    fun patch(key: String, value: Any) { command("/api/preferences", obj(key to value), "PATCH") }
    fun standby(value:Boolean) { command("/api/power",obj("standby" to value)) }
    fun sleepTimer(minutes:Int) { require(minutes in 0..720);command("/api/power/timer",obj("minutes" to minutes)) }
    suspend fun artwork(station:String,identity:String=station):Bitmap? {
        val current=connection ?: return null
        if(!online || current.token=="preview") return null
        val key="${current.host}|${current.pin}|${current.deviceId}|$identity"
        return artworkReads.withLock {
            artworkCache.get(key)?.let{return@withLock it}
            if((artworkFailures[key] ?: 0)>System.currentTimeMillis()) return@withLock null
            try {
                val bitmap=client.artwork(current,station)
                if(connection!=current) return@withLock null
                artworkCache.put(key,bitmap);bitmap
            } catch(e:CancellationException) { throw e }
            catch(_:Exception) {
                artworkFailures[key]=System.currentTimeMillis()+60_000
                while(artworkFailures.size>32) artworkFailures.remove(artworkFailures.keys.first())
                null
            }
        }
    }
    suspend fun read(path: String): JSONObject {
        val current = connection ?: throw HubFailure("unauthorized")
        return client.request(current, path)
    }
    fun transport(action: String) {
        val player = state.child("player")
        if (player.optString("kind") == "radio" && action in listOf("next", "previous")) {
            val stations = preferences.objects("favorites")
            if (stations.isEmpty()) { error = "no_favorites"; return }
            val last = preferences.child("lastStation")
            val index = stations.indexOfFirst { it.optString("uuid") == last.optString("uuid") }
            val delta = if (action == "next") 1 else -1
            playStation(stations[(if (index < 0) 0 else (index + delta + stations.size) % stations.size)])
        } else command("/api/player", obj("action" to action))
    }
    fun playStation(station: JSONObject) {
        val data = obj("source" to "radio", "url" to station.optString("url_resolved").ifBlank { station.optString("url") }, "title" to station.optString("name"), "favicon" to station.optString("favicon"))
        if (station.optString("uuid").matches(Regex("[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}"))) data.put("station_uuid", station.optString("uuid"))
        command("/api/play", data)
    }
}

fun errorText(code: String, ro: Boolean): String {
    fun t(a: String, b: String) = if (ro) a else b
    return when {
        code == "wifi_required" || code == "lan_required" -> t("Conectează telefonul la aceeași rețea Wi-Fi sau Ethernet ca PySH.", "Connect your phone to the same Wi-Fi or Ethernet network as PySH.")
        code == "certificate_changed" || code == "hub_identity_changed" -> t("Identitatea PySH s-a schimbat. Conectarea s-a oprit pentru a proteja accesul. Verifică hubul și reia asocierea dacă l-ai reinstalat.", "PySH's identity changed. Connection stopped to protect access. Check the hub and pair again if you reinstalled it.")
        code == "pairing_denied" -> t("Cererea a fost refuzată pe PySH. Poți solicita din nou conectarea.","The request was declined on PySH. You can request a connection again.")
        code == "pairing_expired" -> t("Cererea a expirat. Alege din nou hubul și acceptă pe ecranul lui.","The request expired. Choose the hub again and accept on its screen.")
        code == "control_disabled" -> t("Activează Android App Control în Setări pe PySH, apoi caută din nou.","Enable Android App Control in PySH Settings, then search again.")
        code == "unsupported_hub" -> t("Actualizează Android App Control pe PySH pentru conectare automată.","Update Android App Control on PySH for automatic connection.")
        code.startsWith("pairing_") -> t("Conectarea nu s-a încheiat. Verifică ecranul PySH și solicită din nou conectarea.","Connection did not complete. Check PySH's screen and request a connection again.")
        code == "unauthorized" -> t("Accesul telefonului a fost revocat. Asociază-l din nou.", "This phone's access was revoked. Pair it again.")
        code == "hub_unavailable" || code == "upstream_unavailable" -> t("Regăsim automat PySH. Verifică rețeaua și Android App Control în Setări pe hub. Dacă ai trimis o comandă, verifică rezultatul după reconectare înainte să o repeți.", "Automatically finding PySH again. Check the network and Android App Control in hub Settings. If you sent a command, check the result after reconnecting before repeating it.")
        code == "no_audio_output" -> t("Selectează o ieșire audio disponibilă în Dispozitiv → Audio.", "Select an available audio output in Device → Audio.")
        code == "no_favorites" -> t("Adaugă posturi favorite pentru a folosi anterior/următor.", "Add favorite stations to use previous/next.")
        code.contains("brightness") -> t("Luminozitatea nu a putut fi aplicată. Verifică ecranul și permisiunile PySH.", "Brightness could not be applied. Check the display and PySH permissions.")
        code.contains("power") || code.contains("standby") -> t("Repausul nu a putut fi aplicat. Verifică starea hubului și reîncearcă.", "Standby could not be applied. Check the hub state and try again.")
        code == "media_in_use" -> t("Oprește redarea înainte de a șterge fișierul.", "Stop playback before deleting the file.")
        code == "rate_limited" -> t("Prea multe comenzi. Așteaptă puțin și reîncearcă.", "Too many commands. Wait a moment and try again.")
        code.contains("bluetooth") || code.contains("pair") -> t("Operația Bluetooth nu s-a încheiat. Verifică dispozitivul și încearcă din nou.", "The Bluetooth operation did not complete. Check the device and try again.")
        code.contains("network") -> t("Conexiunea nu a putut fi modificată. Verifică parola și rețeaua pe hub.", "The connection could not be changed. Check the password and network on the hub.")
        code.contains("media") -> t("Fișierul sau directorul nu este disponibil. Reîncarcă lista.", "The file or folder is unavailable. Reload the list.")
        else -> t("Operația nu s-a încheiat. Verifică starea hubului și reîncearcă.", "The operation did not complete. Check the hub's state and try again.")
    }
}
