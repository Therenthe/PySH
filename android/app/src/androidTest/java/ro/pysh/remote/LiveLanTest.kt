package ro.pysh.remote

import android.content.Intent
import android.graphics.Bitmap
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Test
import org.junit.Assert.*
import kotlinx.coroutines.runBlocking
import java.io.File

/** Opt-in, real-hub smoke test. No fixture can make this pass without LAN + pin. */
@Suppress("DEPRECATION")
class LiveLanTest {
    private val instrumentation=InstrumentationRegistry.getInstrumentation()
    @Test
    fun testPairReadAudioAndScreens() = runBlocking {
        val arguments=InstrumentationRegistry.getArguments()
        val context=instrumentation.targetContext
        val host=arguments.getString("host") ?: throw AssertionError("Provide private LAN host")
        val fingerprint=arguments.getString("pin") ?: throw AssertionError("Provide verified certificate pin")
        val code=arguments.getString("code") ?: throw AssertionError("Provide one-time pairing code")
        val client=HubClient(context)
        val candidate=HubConnection(LanPolicy.host(host),LanPolicy.pin(fingerprint),"","")
        val pair=client.request(candidate,"/remote/pair","POST",obj("code" to LanPolicy.pairingCode(code),"name" to "Android USB verification"))
        val connection=candidate.copy(token=pair.getString("token"),deviceId=pair.getString("deviceId"))
        ConnectionStore(context).save(connection)
        val state=client.request(connection,"/api/state")
        assertTrue(state.has("preferences"))
        val audio=state.child("audio")
        if(audio.optBoolean("available") && !audio.isNull("volume")) {
            client.request(connection,"/api/audio","POST",obj("volume" to audio.getInt("volume")))
            val read=client.request(connection,"/api/state")
            assertEquals(audio.getInt("volume"),read.child("audio").getInt("volume"))
        }
        val activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        instrumentation.waitForIdleSync()
        Thread.sleep(3000)
        capture("home-ro-night")
        for(label in listOf("Radio","Media","Dispozitiv","Setări")) {
            clickText(label)
            Thread.sleep(1600)
            capture(label.lowercase().replace("ă","a"))
        }
        activity.finish()
        // Persisted on purpose for manual phone acceptance; revoke via Settings when done.
    }
    private fun clickText(label:String) {
        fun find(node:android.view.accessibility.AccessibilityNodeInfo?):android.view.accessibility.AccessibilityNodeInfo? {
            if(node==null)return null
            if(node.text?.toString()==label || node.contentDescription?.toString()==label) return node
            for(index in 0 until node.childCount)find(node.getChild(index))?.let{return it}
            return null
        }
        var node=find(instrumentation.uiAutomation.rootInActiveWindow) ?: throw AssertionError("Missing navigation: $label")
        while(!node.isClickable)node=node.parent ?: throw AssertionError("Not clickable: $label")
        assertTrue(node.performAction(android.view.accessibility.AccessibilityNodeInfo.ACTION_CLICK))
    }
    private fun capture(name:String) {
        val screenshot=instrumentation.uiAutomation.takeScreenshot() ?: throw AssertionError("Screenshot unavailable")
        File(instrumentation.targetContext.filesDir,"$name.png").outputStream().use { screenshot.compress(Bitmap.CompressFormat.PNG,100,it) }
        screenshot.recycle()
    }
}
