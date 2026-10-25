package ro.pysh.remote

import java.util.UUID

data class DiscoveredHub(val host:String,val hubId:String,val name:String="PySH")
data class HubIdentity(val hubId:String,val name:String,val pin:String,val enabled:Boolean)

/** Discovery is an address hint, never permission to use an existing credential. */
object DiscoveryPolicy {
    const val SERVICE_TYPE="_pysh-control._tcp."
    fun hubId(value:String):String = value.also {
        require(it.matches(Regex("[a-fA-F0-9]{8}-(?:[a-fA-F0-9]{4}-){3}[a-fA-F0-9]{12}"))) { "invalid_response" }
        require(UUID.fromString(it).toString().equals(it,true)) { "invalid_response" }
    }.lowercase()
    fun discovered(host:String,port:Int,id:String,protocol:String,name:String):DiscoveredHub {
        require(port==8766 && protocol=="2") { "unsupported_hub" }
        return DiscoveredHub(LanPolicy.host(host),hubId(id),name.filterNot { it.isISOControl() }.take(48).ifBlank { "PySH" })
    }
    fun verifyPairing(discoveredId:String,identityId:String,identityPin:String,actualPin:String) {
        require(hubId(discoveredId)==hubId(identityId)) { "hub_identity_changed" }
        require(LanPolicy.pin(identityPin)==LanPolicy.pin(actualPin)) { "certificate_changed" }
    }
    fun verifyReconnect(savedId:String,savedPin:String,identityId:String,identityPin:String) {
        require(savedId.isBlank() || hubId(savedId)==hubId(identityId)) { "hub_identity_changed" }
        require(LanPolicy.pin(savedPin)==LanPolicy.pin(identityPin)) { "certificate_changed" }
    }
    fun bootstrapPath(path:String,method:String,hasToken:Boolean):String {
        require(path=="/remote/identity" && method=="GET" && !hasToken) { "invalid_request" }
        return path
    }
}
