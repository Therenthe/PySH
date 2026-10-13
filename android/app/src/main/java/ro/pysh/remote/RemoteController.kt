package ro.pysh.remote

import android.content.Context
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
fun query(value: String) = URLEncoder.encode(value, "UTF-8")

class RemoteController(context: Context, private val scope: CoroutineScope) {
    private val store = ConnectionStore(context)
    private val uiStore = context.getSharedPreferences("interface", Context.MODE_PRIVATE)
    private val client = HubClient(context)
    private val writes = Mutex()
    private val reads = Mutex()
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
    val preferences get() = state.child("preferences")
    val enabled get() = online && busy == 0
    private var polling: Job? = null
    private var reading = false
    internal fun previewState(value: JSONObject, romanian: Boolean=true) {
        check(BuildConfig.DEBUG)
        state=value;ro=romanian;online=true
        connection=HubConnection("192.168.100.127","0".repeat(64),"preview","preview")
    }
    fun language(value: Boolean) { ro = value; uiStore.edit().putString("language", if (ro) "ro" else "en").apply() }
    fun theme(value: Boolean) { dark = value; uiStore.edit().putBoolean("dark", value).apply() }
    fun start() {
        if (polling?.isActive == true) return
        polling = scope.launch { while (isActive) { refresh(); delay(2000) } }
    }
    fun stop() { polling?.cancel(); polling = null }
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
                val result = client.request(current, "/api/state")
                if (connection == current) { state = result; online = true }
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { if (connection == current) { online = false; connectionIssue=code(e) } }
            finally { syncing = false; reading = false }
        }
    }
    fun reconnect() { scope.launch { refresh(true) } }
    fun pair(host: String, fingerprint: String, code: String) {
        if (busy > 0) return
        scope.launch {
            busy++; error = null
            try {
                val candidate = HubConnection(LanPolicy.host(host), LanPolicy.pin(fingerprint), "", "")
                val result = client.request(candidate, "/remote/pair", "POST", obj("code" to LanPolicy.pairingCode(code), "name" to "PySH Android"))
                val paired = candidate.copy(token = result.getString("token"), deviceId = result.getString("deviceId"))
                store.save(paired); connection = paired; state = JSONObject(); online = false
                refresh()
            } catch (e: CancellationException) { throw e }
            catch (e: Exception) { error = this@RemoteController.code(e) }
            finally { busy-- }
        }
    }
    fun forget() { store.clear(); connection = null; state = JSONObject(); online = false; error = null }
    fun revoke() { command("/remote/revoke-self",after={forget()}) }
    fun changeAddress(host: String) {
        try {
            val updated=connection?.copy(host=LanPolicy.host(host)) ?: return
            store.save(updated);connection=updated;online=false;reconnect()
        } catch(e: Exception) { error=code(e) }
    }
    fun command(path: String, body: JSONObject = JSONObject(), method: String = "POST", parallel: Boolean = false, after: ((JSONObject) -> Unit)? = null) {
        val current = connection ?: return
        scope.launch {
            suspend fun perform() {
                if(connection!=current) return
                busy++; error = null; notice = null
                try {
                    val result = client.request(current, path, method, body)
                    if (connection != current) return
                    notice = "saved"; after?.invoke(result)
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
        code == "invalid_lan_address" -> t("Introdu o adresă IP locală, de exemplu 192.168.100.127.", "Enter a local IP address, such as 192.168.100.127.")
        code == "invalid_fingerprint" -> t("Amprenta certificatului trebuie să conțină 64 de caractere hexazecimale.", "The certificate fingerprint must contain 64 hexadecimal characters.")
        code == "invalid_pairing_code" -> t("Codul de asociere are 8 cifre.", "The pairing code has 8 digits.")
        code == "certificate_changed" -> t("Certificatul hubului nu corespunde. Verifică amprenta pe PySH înainte de o nouă asociere.", "The hub certificate does not match. Verify its fingerprint on PySH before pairing again.")
        code.startsWith("pairing_") -> t("Codul nu este valid sau a expirat. Generează un cod nou pe PySH.", "The code is invalid or expired. Generate a new code on PySH.")
        code == "unauthorized" -> t("Accesul telefonului a fost revocat. Asociază-l din nou.", "This phone's access was revoked. Pair it again.")
        code == "hub_unavailable" || code == "upstream_unavailable" -> t("PySH nu răspunde. Verifică rețeaua și serviciul LAN. Comanda poate să fi ajuns; verifică starea înainte să o repeți.", "PySH is not responding. Check the network and LAN service. The command may have arrived; check its state before repeating it.")
        code == "no_audio_output" -> t("Selectează o ieșire audio disponibilă în Dispozitiv → Audio.", "Select an available audio output in Device → Audio.")
        code == "no_favorites" -> t("Adaugă posturi favorite pentru a folosi anterior/următor.", "Add favorite stations to use previous/next.")
        code == "media_in_use" -> t("Oprește redarea înainte de a șterge fișierul.", "Stop playback before deleting the file.")
        code == "rate_limited" -> t("Prea multe comenzi. Așteaptă puțin și reîncearcă.", "Too many commands. Wait a moment and try again.")
        code.contains("bluetooth") || code.contains("pair") -> t("Operația Bluetooth nu s-a încheiat. Verifică dispozitivul și încearcă din nou.", "The Bluetooth operation did not complete. Check the device and try again.")
        code.contains("network") -> t("Conexiunea nu a putut fi modificată. Verifică parola și rețeaua pe hub.", "The connection could not be changed. Check the password and network on the hub.")
        code.contains("media") -> t("Fișierul sau directorul nu este disponibil. Reîncarcă lista.", "The file or folder is unavailable. Reload the list.")
        else -> t("Operația nu s-a încheiat. Verifică starea hubului și reîncearcă.", "The operation did not complete. Check the hub's state and try again.")
    }
}
