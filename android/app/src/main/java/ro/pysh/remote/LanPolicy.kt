package ro.pysh.remote

/** Literal IPv4 only: no DNS, ambiguous octal, public addresses or forwarded hosts. */
object LanPolicy {
    fun host(value: String): String {
        val parts = value.trim().split('.')
        require(parts.size == 4) { "invalid_lan_address" }
        val bytes = parts.map {
            require(it.matches(Regex("0|[1-9][0-9]{0,2}"))) { "invalid_lan_address" }
            it.toInt().also { n -> require(n in 0..255) { "invalid_lan_address" } }
        }
        val (a, b, _, d) = bytes
        require(a == 10 || (a == 172 && b in 16..31) || (a == 192 && b == 168)) { "lan_required" }
        require(d != 0 && d != 255) { "invalid_lan_address" }
        return bytes.joinToString(".")
    }
    fun pin(value: String): String = value.replace(":", "").replace(" ", "").replace("\n", "").trim().lowercase().also {
        require(it.matches(Regex("[0-9a-f]{64}"))) { "invalid_fingerprint" }
    }
    fun pairingCode(value: String): String = value.trim().also {
        require(it.matches(Regex("[0-9]{8}"))) { "invalid_pairing_code" }
    }
    fun path(value: String): String = value.also {
        require((it.startsWith("/api/") && !it.startsWith("/api/session")) || it in setOf("/remote/pair", "/remote/health", "/remote/revoke-self", "/remote/heartbeat", "/remote/identity", "/remote/pair/request", "/remote/pair/status", "/remote/pair/cancel")) { "invalid_request" }
        require(!it.contains('#') && !it.contains('\r') && !it.contains('\n')) { "invalid_request" }
    }
}
