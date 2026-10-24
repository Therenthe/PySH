package ro.pysh.remote

import java.security.KeyPairGenerator
import java.security.spec.MGF1ParameterSpec
import java.util.Base64
import javax.crypto.Cipher
import javax.crypto.spec.OAEPParameterSpec
import javax.crypto.spec.PSource

/** Ephemeral key only: a pending approval never stores an unapproved bearer token. */
class PairingCrypto {
    private val keys=KeyPairGenerator.getInstance("RSA").apply { initialize(3072) }.generateKeyPair()
    val publicKey:String get()=Base64.getEncoder().encodeToString(keys.public.encoded)
    fun decrypt(value:String):String {
        require(value.length in 1..1024) { "invalid_response" }
        val bytes=Base64.getDecoder().decode(value)
        require(bytes.size==384) { "invalid_response" }
        val cipher=Cipher.getInstance("RSA/ECB/OAEPPadding")
        cipher.init(Cipher.DECRYPT_MODE,keys.private,OAEPParameterSpec("SHA-256","MGF1",MGF1ParameterSpec.SHA256,PSource.PSpecified.DEFAULT))
        return cipher.doFinal(bytes).toString(Charsets.UTF_8)
    }
}
