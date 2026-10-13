package ro.pysh.remote

import org.junit.Assert.*
import org.junit.Test

class LanPolicyTest {
    @Test fun acceptsOnlyExplicitPrivateAddresses() {
        listOf("192.168.1.10", "10.0.0.3", "172.16.2.1", "172.31.1.2").forEach { assertEquals(it, LanPolicy.host(it)) }
        listOf("8.8.8.8", "127.0.0.1", "0.0.0.0", "100.64.0.1", "172.32.1.2", "169.254.1.2", "pysh.local", "192.168.1.10.evil.com", "192.168.001.1", "192.168.1.255", "https://192.168.1.10", "192.168.1.10:8766", "192.168.1.256", "192.168.1.-1").forEach { value ->
            assertThrows(value, IllegalArgumentException::class.java) { LanPolicy.host(value) }
        }
    }
    @Test fun validatesPinAndPairingCode() {
        assertEquals("ab".repeat(32), LanPolicy.pin("AB:".repeat(31) + "AB"))
        assertThrows(IllegalArgumentException::class.java) { LanPolicy.pin("AB".repeat(31)) }
        assertThrows(IllegalArgumentException::class.java) { LanPolicy.pin("zz".repeat(32)) }
        assertEquals("01234567", LanPolicy.pairingCode("01234567"))
        listOf("1234", "123456789", "abcdefgh").forEach { assertThrows(IllegalArgumentException::class.java) { LanPolicy.pairingCode(it) } }
    }
    @Test fun rejectsSessionAndForeignRoutes() {
        listOf("https://8.8.8.8", "//8.8.8.8", "/api/session", "/api/state\r\nHost: public", "/api/state#fragment").forEach { assertThrows(IllegalArgumentException::class.java) { LanPolicy.path(it) } }
        assertEquals("/api/media?path=%2Fhome", LanPolicy.path("/api/media?path=%2Fhome"))
    }
}
