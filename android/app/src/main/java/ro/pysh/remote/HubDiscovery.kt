package ro.pysh.remote

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.net.nsd.NsdManager
import android.net.nsd.NsdServiceInfo
import android.net.wifi.WifiManager
import android.os.Handler
import android.os.Looper
import java.util.ArrayDeque

/** Foreground-only mDNS, serial resolution, no subnet scan and no internet fallback. */
@Suppress("DEPRECATION")
class HubDiscovery(context:Context,private val changed:(List<DiscoveredHub>,String)->Unit) {
    private val nsd=context.getSystemService(NsdManager::class.java)
    private val connectivity=context.getSystemService(ConnectivityManager::class.java)
    private val wifi=context.applicationContext.getSystemService(WifiManager::class.java)
    private val main=Handler(Looper.getMainLooper())
    private var running=false
    private var listener:NsdManager.DiscoveryListener?=null
    private var callback:ConnectivityManager.NetworkCallback?=null
    private var multicast:WifiManager.MulticastLock?=null
    private val hubs=linkedMapOf<String,DiscoveredHub>()
    private val queue=ArrayDeque<NsdServiceInfo>()
    private var resolving=false
    private var resolveTicket=0
    private var generation=0
    private var state="searching"
    fun hasLan()=connectivity.allNetworks.any {
        val c=connectivity.getNetworkCapabilities(it)
        c!=null && !c.hasTransport(NetworkCapabilities.TRANSPORT_VPN) && (c.hasTransport(NetworkCapabilities.TRANSPORT_WIFI)||c.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET))
    }
    private fun emit(value:String) { state=value;changed(hubs.values.toList(),value) }
    fun start() {
        if(running)return
        running=true
        val cb=object:ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network:Network) { main.post { restart() } }
            override fun onLost(network:Network) { main.post { restart() } }
            override fun onCapabilitiesChanged(network:Network,c:NetworkCapabilities) { main.post { if(running && listener==null && hasLan()) browse() } }
        }
        callback=cb
        try { connectivity.registerNetworkCallback(NetworkRequest.Builder().addCapability(NetworkCapabilities.NET_CAPABILITY_NOT_VPN).build(),cb) }
        catch(_:Exception) { callback=null;emit("discovery_unavailable") }
        browse()
    }
    fun restart() { if(!running)return;stopBrowse();hubs.clear();browse() }
    private fun browse() {
        if(!running || listener!=null)return
        if(!hasLan()) { emit("wifi_required");return }
        val epoch=++generation
        emit("searching")
        try { multicast=wifi.createMulticastLock("pysh-discovery").apply { setReferenceCounted(false);acquire() } }
        catch(_:Exception) { emit("discovery_unavailable");retry();return }
        val current=object:NsdManager.DiscoveryListener {
            override fun onDiscoveryStarted(type:String) {}
            override fun onDiscoveryStopped(type:String) {}
            override fun onStartDiscoveryFailed(type:String,code:Int) { main.post { if(epoch==generation) { stopBrowse();emit("discovery_unavailable");retry() } } }
            override fun onStopDiscoveryFailed(type:String,code:Int) {}
            override fun onServiceFound(info:NsdServiceInfo) { main.post { if(epoch==generation && queue.size<24) { queue.add(info);resolveNext(epoch) } } }
            override fun onServiceLost(info:NsdServiceInfo) { main.post { if(epoch==generation) { hubs.remove(info.serviceName);emit(if(hubs.isEmpty()) "searching" else "found") } } }
        }
        listener=current
        try { nsd.discoverServices(DiscoveryPolicy.SERVICE_TYPE,NsdManager.PROTOCOL_DNS_SD,current) }
        catch(_:Exception) { stopBrowse();emit("discovery_unavailable");retry() }
        main.postDelayed({ if(running && epoch==generation && hubs.isEmpty()) emit("not_found") },12_000)
    }
    private fun retry() { val epoch=generation;main.postDelayed({ if(running && epoch==generation) browse() },15_000) }
    private fun resolveNext(epoch:Int) {
        if(epoch!=generation || resolving || queue.isEmpty())return
        resolving=true
        val ticket=++resolveTicket
        val info=queue.removeFirst()
        val resolver=object:NsdManager.ResolveListener {
            override fun onResolveFailed(service:NsdServiceInfo,code:Int) { main.post { if(epoch==generation) { resolving=false;resolveNext(epoch) } } }
            override fun onServiceResolved(service:NsdServiceInfo) { main.post {
                if(epoch!=generation)return@post
                resolving=false
                runCatching {
                    val attributes=service.attributes
                    fun attr(key:String)=attributes[key]?.toString(Charsets.UTF_8).orEmpty()
                    DiscoveryPolicy.discovered(service.host?.hostAddress.orEmpty(),service.port,attr("hubId"),attr("protocol"),attr("name"))
                }.getOrNull()?.let { hubs[service.serviceName]=it;emit("found") }
                resolveNext(epoch)
            } }
        }
        try { nsd.resolveService(info,resolver) } catch(_:Exception) { resolving=false;resolveNext(epoch) }
        // A platform resolver that never calls back cannot hold the search indefinitely.
        main.postDelayed({ if(epoch==generation && ticket==resolveTicket && resolving) { stopBrowse();browse() } },10_000)
    }
    private fun stopBrowse() {
        generation++
        listener?.let { runCatching { nsd.stopServiceDiscovery(it) } };listener=null
        multicast?.let { if(it.isHeld)it.release() };multicast=null
        queue.clear();resolving=false
    }
    fun stop() {
        running=false;stopBrowse()
        callback?.let { runCatching { connectivity.unregisterNetworkCallback(it) } };callback=null
        main.removeCallbacksAndMessages(null)
    }
}
