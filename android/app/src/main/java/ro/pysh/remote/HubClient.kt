package ro.pysh.remote

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.net.URL
import java.io.ByteArrayOutputStream
import java.security.KeyStore
import java.security.MessageDigest
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.X509TrustManager

data class HubConnection(val host: String, val pin: String, val token: String, val deviceId: String, val hubId:String="")
class HubFailure(val code: String) : Exception(code)

/** Credentials encrypted by a non-exportable Android Keystore key; backup is disabled. */
class ConnectionStore(context: Context) {
    private val prefs = context.getSharedPreferences("connection", Context.MODE_PRIVATE)
    private fun key(): SecretKey {
        val store = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        (store.getKey("pysh-connection", null) as? SecretKey)?.let { return it }
        return KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").apply {
            init(KeyGenParameterSpec.Builder("pysh-connection", KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE).build())
        }.generateKey()
    }
    fun load(): HubConnection? = runCatching {
        val raw = prefs.getString("value", null) ?: return null
        val bytes = Base64.decode(raw, Base64.NO_WRAP)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes.copyOfRange(0, 12))) }
        val json = JSONObject(String(cipher.doFinal(bytes.copyOfRange(12, bytes.size)), Charsets.UTF_8))
        HubConnection(LanPolicy.host(json.getString("host")), LanPolicy.pin(json.getString("pin")), json.getString("token"), json.getString("deviceId"),json.optString("hubId"))
    }.getOrNull()
    fun save(value: HubConnection) {
        val json = JSONObject().put("host", value.host).put("pin", value.pin).put("token", value.token).put("deviceId", value.deviceId).put("hubId",value.hubId)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding").apply { init(Cipher.ENCRYPT_MODE, key()) }
        check(prefs.edit().putString("value", Base64.encodeToString(cipher.iv + cipher.doFinal(json.toString().toByteArray()), Base64.NO_WRAP)).commit())
    }
    fun clear() { prefs.edit().clear().commit() }
}

class HubClient(context: Context) {
    private val connectivity = context.getSystemService(ConnectivityManager::class.java)
    /** One public identity read only; no credential is ever sent using bootstrap trust. */
    suspend fun discoverIdentity(hub:DiscoveredHub):HubIdentity=withContext(Dispatchers.IO) {
        val response=exchange(HubConnection(hub.host,"","",""),"/remote/identity","GET",null,"application/json",8192,bootstrap=true)
        if(response.status !in 200..299)throw HubFailure("hub_unavailable")
        val identity=JSONObject(response.bytes.toString(Charsets.UTF_8))
        if(identity.optInt("protocol")!=2)throw HubFailure("unsupported_hub")
        DiscoveryPolicy.verifyPairing(hub.hubId,identity.getString("hubId"),identity.getString("certificateSha256"),response.pin)
        HubIdentity(hub.hubId,identity.optString("name","PySH"),response.pin,identity.optBoolean("enabled"))
    }
    suspend fun request(connection: HubConnection, path: String, method: String = "GET", body: JSONObject? = null): JSONObject = withContext(Dispatchers.IO) {
        val response=exchange(connection,path,method,body,"application/json",2*1024*1024)
        val result = runCatching { JSONObject(String(response.bytes, Charsets.UTF_8)) }.getOrElse { throw HubFailure("invalid_response") }
        if (response.status !in 200..299 || (method!="GET" && result.has("error") && !result.isNull("error"))) throw HubFailure(result.optString("error", "operation_failed"))
        result
    }
    /** Art is fetched through the exact same LAN transport, certificate pin and bearer token. */
    suspend fun artwork(connection: HubConnection, station: String): Bitmap = withContext(Dispatchers.IO) {
        require(station=="current" || station.matches(Regex("[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}"))) { "invalid_request" }
        val response=exchange(connection,"/api/radio/artwork?station=${query(station)}","GET",null,"image/png,image/jpeg,image/webp,image/gif,image/x-icon,image/vnd.microsoft.icon",256*1024)
        if(response.status !in 200..299) throw HubFailure("artwork_unavailable")
        decodeArtwork(response.bytes,response.type)
    }
    internal fun decodeArtwork(bytes:ByteArray,type:String):Bitmap {
        if(bytes.isEmpty() || bytes.size>256*1024) throw HubFailure("invalid_artwork")
        val pixels = if(type in setOf("image/x-icon","image/vnd.microsoft.icon")) {
            when(val frame=try { IcoArtwork.decode(bytes) } catch(_:IllegalArgumentException) { throw HubFailure("invalid_artwork") }) {
                is IcoArtwork.Frame.Pixels -> return Bitmap.createBitmap(frame.argb,frame.width,frame.height,Bitmap.Config.ARGB_8888)
                is IcoArtwork.Frame.Png -> frame.bytes
            }
        } else {
            if(type !in setOf("image/png","image/jpeg","image/webp","image/gif")) throw HubFailure("invalid_artwork")
            bytes
        }
        val bounds=BitmapFactory.Options().apply { inJustDecodeBounds=true }
        BitmapFactory.decodeByteArray(pixels,0,pixels.size,bounds)
        if(bounds.outWidth !in 1..4096 || bounds.outHeight !in 1..4096 || bounds.outWidth.toLong()*bounds.outHeight>16_000_000) throw HubFailure("invalid_artwork")
        val options=BitmapFactory.Options()
        while(bounds.outWidth/options.inSampleSize.coerceAtLeast(1)>512 || bounds.outHeight/options.inSampleSize.coerceAtLeast(1)>512) options.inSampleSize=options.inSampleSize.coerceAtLeast(1)*2
        return BitmapFactory.decodeByteArray(pixels,0,pixels.size,options) ?: throw HubFailure("invalid_artwork")
    }
    private data class Response(val status:Int,val type:String,val bytes:ByteArray,val pin:String)
    private fun exchange(connection: HubConnection,path:String,method:String,body:JSONObject?,accept:String,maxBytes:Int,bootstrap:Boolean=false):Response {
        val host = LanPolicy.host(connection.host)
        if(bootstrap) DiscoveryPolicy.bootstrapPath(path,method,connection.token.isNotEmpty())
        val fingerprint = if(bootstrap) "" else LanPolicy.pin(connection.pin)
        var observedPin=""
        val network = connectivity.allNetworks.firstOrNull { network ->
            val capabilities = connectivity.getNetworkCapabilities(network)
            capabilities != null && !capabilities.hasTransport(NetworkCapabilities.TRANSPORT_VPN) &&
                (capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) || capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))
        } ?: throw HubFailure("wifi_required")
        val trust = object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()
            override fun checkClientTrusted(chain: Array<X509Certificate>, authType: String) { throw CertificateException("server_only") }
            override fun checkServerTrusted(chain: Array<X509Certificate>, authType: String) {
                if (chain.isEmpty()) throw CertificateException("certificate_changed")
                chain[0].checkValidity()
                val actual = MessageDigest.getInstance("SHA-256").digest(chain[0].encoded)
                observedPin=actual.joinToString("") { "%02x".format(it.toInt() and 255) }
                if(!bootstrap) {
                    val expected = fingerprint.chunked(2).map { it.toInt(16).toByte() }.toByteArray()
                    if (!MessageDigest.isEqual(actual, expected)) throw CertificateException("certificate_changed")
                }
            }
        }
        val tls = SSLContext.getInstance("TLS").apply { init(null, arrayOf(trust), null) }
        val http = network.openConnection(URL("https://$host:8766${LanPolicy.path(path)}")) as HttpsURLConnection
        try {
            http.sslSocketFactory = tls.socketFactory
            // Numeric host identity is authenticated by the out-of-band exact certificate pin.
            http.hostnameVerifier = javax.net.ssl.HostnameVerifier { hostname, session ->
                hostname == host && runCatching { trust.checkServerTrusted(session.peerCertificates.map { it as X509Certificate }.toTypedArray(), "RSA"); true }.getOrDefault(false)
            }
            http.instanceFollowRedirects = false
            http.connectTimeout = if(path in setOf("/remote/heartbeat","/remote/pair/cancel")) 2000 else 6000
            http.readTimeout = if(path in setOf("/remote/heartbeat","/remote/pair/cancel")) 2000 else if(path.startsWith("/remote/pair/")||path=="/remote/identity") 6000 else if(accept.startsWith("image/")) 8000 else 35000
            http.requestMethod = method
            http.setRequestProperty("Accept", accept)
            if (connection.token.isNotEmpty()) http.setRequestProperty("Authorization", "Bearer ${connection.token}")
            if (body != null) {
                http.doOutput = true
                http.setRequestProperty("Content-Type", "application/json")
                http.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
            }
            val status = http.responseCode
            if (status in 300..399) throw HubFailure("redirect_refused")
            if(http.contentLengthLong>maxBytes) throw HubFailure("invalid_response")
            val input = (if (status in 200..299) http.inputStream else http.errorStream) ?: throw HubFailure("hub_unavailable")
            val bytes = input.use { stream ->
                val output=ByteArrayOutputStream()
                val buffer=ByteArray(8192)
                while(true) {
                    val count=stream.read(buffer)
                    if(count<0) break
                    if(output.size()+count>maxBytes) throw HubFailure("invalid_response")
                    output.write(buffer,0,count)
                }
                output.toByteArray()
            }
            return Response(status,http.contentType?.substringBefore(';')?.lowercase() ?: "",bytes,observedPin)
        } catch (error: javax.net.ssl.SSLException) {
            throw HubFailure("certificate_changed")
        } catch (error: java.io.IOException) {
            throw HubFailure("hub_unavailable")
        } finally { http.disconnect() }
    }
}
