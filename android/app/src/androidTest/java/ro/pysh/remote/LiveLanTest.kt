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
    @Test fun testScreensWithSavedPairing() = runBlocking {
        val context=instrumentation.targetContext
        val connection=ConnectionStore(context).load() ?: throw AssertionError("Pair first")
        assertTrue(HubClient(context).request(connection,"/api/state").has("preferences"))
        val local=obj("station_name" to null,"title" to "Local music")
        assertEquals("",local.label("station_name"))
        assertEquals("Local music",local.label("station_name").ifBlank{local.label("title")})
        val activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        Thread.sleep(2200);capture("home-ro-night")
        for(label in listOf("Radio","Media","Dispozitiv","Setări")) {
            clickText(label);Thread.sleep(900);capture(label.lowercase().replace("ă","a"))
        }
        activity.finish()
    }
    @Test fun testCommandsPersistenceAndPalettes() = runBlocking {
        val context=instrumentation.targetContext
        val connection=ConnectionStore(context).load() ?: throw AssertionError("Pair the phone first")
        val client=HubClient(context)
        val initial=client.request(connection,"/api/state")
        val originalTheme=initial.child("preferences").getString("theme")
        val volume=initial.child("audio").getInt("volume")
        val playing=initial.child("player").optString("state")=="playing"
        try {
            val changed=if(volume<100)volume+1 else volume-1
            client.request(connection,"/api/audio","POST",obj("volume" to changed))
            assertEquals(changed,client.request(connection,"/api/state").child("audio").getInt("volume"))
            client.request(connection,"/api/audio","POST",obj("volume" to volume))
            if(playing) {
                client.request(connection,"/api/player","POST",obj("action" to "pause"))
                assertEquals("paused",client.request(connection,"/api/state").child("player").getString("state"))
                client.request(connection,"/api/player","POST",obj("action" to "resume"))
            }
            val alternate=if(originalTheme=="night")"ink" else "night"
            client.request(connection,"/api/preferences","PATCH",obj("theme" to alternate))
            assertEquals(alternate,client.request(connection,"/api/state").child("preferences").getString("theme"))
            client.request(connection,"/api/preferences","PATCH",obj("theme" to originalTheme))
        } finally {
            client.request(connection,"/api/audio","POST",obj("volume" to volume))
            client.request(connection,"/api/preferences","PATCH",obj("theme" to originalTheme))
            if(playing)client.request(connection,"/api/player","POST",obj("action" to "resume"))
        }
        assertEquals(volume,client.request(connection,"/api/state").child("audio").getInt("volume"))
        val preferences=context.getSharedPreferences("interface",android.content.Context.MODE_PRIVATE)
        for(ro in listOf(true,false))for(dark in listOf(true,false)) {
            preferences.edit().putString("language",if(ro)"ro" else "en").putBoolean("dark",dark).commit()
            val activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
            Thread.sleep(2200)
            capture("home-${if(ro)"ro" else "en"}-${if(dark)"night" else "light"}")
            activity.finish();instrumentation.waitForIdleSync()
        }
        preferences.edit().putString("language","ro").putBoolean("dark",true).commit()
        assertNotNull(ConnectionStore(context).load())
        assertTrue(client.request(ConnectionStore(context).load()!!,"/api/state").has("preferences"))
    }
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
