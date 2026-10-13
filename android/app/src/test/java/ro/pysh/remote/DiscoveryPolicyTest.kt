package ro.pysh.remote

import org.junit.Assert.*
import org.junit.Test
import java.security.KeyFactory
import java.security.spec.X509EncodedKeySpec
import java.security.spec.MGF1ParameterSpec
import java.util.Base64
import javax.crypto.Cipher
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

class DiscoveryPolicyTest {
    private val id="079ab3e4-6dd7-486b-88b9-8a1a6900dc8b"
    private val other="bbf1c347-5a1e-43cb-b494-b0df2b52a801"
    private val pin="ab".repeat(32)
    @Test fun serviceHintsRequirePrivateAddressProtocolAndPort() {
        assertEquals(id,DiscoveryPolicy.discovered("192.168.1.6",8766,id,"2","PySH").hubId)
        listOf("8.8.8.8","127.0.0.1","pysh.local","192.168.1.6:443").forEach {
            assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.discovered(it,8766,id,"2","PySH") }
        }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.discovered("192.168.1.6",443,id,"2","PySH") }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.discovered("192.168.1.6",8766,id,"1","PySH") }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.hubId("not-a-hub") }
    }
    @Test fun changedIpDoesNotChangeTrustedHubOrCertificate() {
        DiscoveryPolicy.verifyReconnect(id,pin,id,pin)
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.verifyReconnect(id,pin,other,pin) }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.verifyReconnect(id,pin,id,"cd".repeat(32)) }
        DiscoveryPolicy.verifyReconnect("",pin,id,pin) // Legacy credentials migrate through the saved certificate.
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.verifyReconnect("",pin,id,"cd".repeat(32)) }
    }
    @Test fun approvalResultIsBoundToActualHandshakeAndDiscoveredHub() {
        DiscoveryPolicy.verifyPairing(id,id,pin,pin)
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.verifyPairing(id,other,pin,pin) }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.verifyPairing(id,id,"cd".repeat(32),pin) }
    }
    @Test fun bootstrapCannotSendTokensOrReplayAnyMutation() {
        assertEquals("/remote/identity",DiscoveryPolicy.bootstrapPath("/remote/identity","GET",false))
        listOf("/api/state","/api/player","/api/preferences","/remote/pair/request","/remote/pair/status","/remote/revoke-self").forEach {
            assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.bootstrapPath(it,"POST",false) }
            assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.bootstrapPath(it,"GET",true) }
        }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.bootstrapPath("/remote/identity","POST",false) }
        assertThrows(IllegalArgumentException::class.java) { DiscoveryPolicy.bootstrapPath("/remote/identity","GET",true) }
    }
    @Test fun approvalEnvelopeUsesCompatibleSha256OaepAndOwnPrivateKey() {
        val first=PairingCrypto();val second=PairingCrypto()
        val publicKey=KeyFactory.getInstance("RSA").generatePublic(X509EncodedKeySpec(Base64.getDecoder().decode(first.publicKey)))
        val cipher=Cipher.getInstance("RSA/ECB/OAEPPadding")
        cipher.init(Cipher.ENCRYPT_MODE,publicKey,OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT))
        val plain="{\"token\":\"${"a".repeat(43)}\",\"deviceId\":\"$other\",\"hubId\":\"$id\",\"certificateSha256\":\"$pin\"}"
        val encrypted=Base64.getEncoder().encodeToString(cipher.doFinal(plain.toByteArray()))
        assertEquals(plain,first.decrypt(encrypted))
        assertThrows(Exception::class.java) { second.decrypt(encrypted) }
        assertThrows(IllegalArgumentException::class.java) { first.decrypt("YWJj") }
    }
}
