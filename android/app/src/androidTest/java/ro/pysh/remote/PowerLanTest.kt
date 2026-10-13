package ro.pysh.remote

import android.content.Intent
import android.graphics.Bitmap
import android.view.accessibility.AccessibilityNodeInfo
import androidx.test.platform.app.InstrumentationRegistry
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Assume.assumeTrue
import org.junit.Test
import java.io.File

/** Explicitly selected by the operator after deployment; never run as part of the APK build. */
@Suppress("DEPRECATION")
class PowerLanTest {
    private val instrumentation=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrumentation.targetContext
    private fun connection()=ConnectionStore(context).load() ?: throw AssertionError("Pair the phone first")

    @Test fun nativeIcoPixelsAndEmbeddedPng() {
        val client=HubClient(context)
        fun icon(frame:ByteArray)=java.nio.ByteBuffer.allocate(22+frame.size).order(java.nio.ByteOrder.LITTLE_ENDIAN).apply {
            putShort(0);putShort(1);putShort(1);put(1);put(1);put(0);put(0)
            putShort(1);putShort(32);putInt(frame.size);putInt(22);put(frame)
        }.array()
        val dib=java.nio.ByteBuffer.allocate(48).order(java.nio.ByteOrder.LITTLE_ENDIAN).apply {
            putInt(40);putInt(1);putInt(2);putShort(1);putShort(32);putInt(0);putInt(4)
            putInt(0);putInt(0);putInt(0);putInt(0);putInt(0xff336699.toInt());putInt(0)
        }.array()
        val decoded=client.decodeArtwork(icon(dib),"image/x-icon")
        assertEquals(0xff336699.toInt(),decoded.getPixel(0,0))
        val png=java.io.ByteArrayOutputStream().also { decoded.compress(Bitmap.CompressFormat.PNG,100,it) }.toByteArray()
        val embedded=client.decodeArtwork(icon(png),"image/vnd.microsoft.icon")
        assertEquals(1,embedded.width);assertEquals(1,embedded.height)
        assertEquals(decoded.getPixel(0,0),embedded.getPixel(0,0))
        decoded.recycle();embedded.recycle()
        try { client.decodeArtwork(icon(dib.copyOf(44)),"image/x-icon");fail("Truncated mask was accepted") }
        catch(e:HubFailure) { assertEquals("invalid_artwork",e.code) }
    }

    @Test fun timerAndErrorContract() {
        assertNull(remainingTimerMinutes(obj("remainingSeconds" to null)))
        assertNull(remainingTimerMinutes(obj("remainingSeconds" to 0)))
        assertNull(remainingTimerMinutes(obj("remainingSeconds" to -1)))
        assertEquals(1,remainingTimerMinutes(obj("remainingSeconds" to 1)))
        assertEquals(1,remainingTimerMinutes(obj("remainingSeconds" to 60)))
        assertEquals(2,remainingTimerMinutes(obj("remainingSeconds" to 61)))
        assertTrue(errorText("brightness_write_failed",true).contains("Luminozitatea"))
        assertTrue(errorText("brightness_write_failed",false).contains("Brightness"))
        assertTrue(errorText("power_failed",true).contains("Repausul"))
        assertTrue(errorText("power_failed",false).contains("Standby"))
    }

    @Test fun powerReadAndAuthenticatedArtwork()=runBlocking {
        val client=HubClient(context)
        val connection=connection()
        val state=client.request(connection,"/api/state")
        val power=client.request(connection,"/api/power")
        assertTrue(state.has("power"));assertTrue(power.has("standby"))
        assertTrue(power.child("daily").getString("time").matches(Regex("(?:[01][0-9]|2[0-3]):[0-5][0-9]")))
        val brightness=power.child("brightness")
        if(brightness.optBoolean("available") && !brightness.isNull("value")) assertTrue(brightness.getInt("value") in 0..100)
        val station=state.child("preferences").optJSONArray("favorites")?.optJSONObject(0)?.optString("uuid").orEmpty()
        if(station.isNotEmpty()) {
            try {
                val logo=client.artwork(connection,station)
                assertTrue(logo.width in 1..512);assertTrue(logo.height in 1..512)
                File(context.filesDir,"radio-logo.png").outputStream().use{logo.compress(Bitmap.CompressFormat.PNG,100,it)}
                logo.recycle()
            } catch(e:HubFailure) { throw AssertionError("Configured station artwork failed: ${e.code}",e) }
        }
    }

    @Test fun powerTimerAndDailyRestoreIdleHub()=runBlocking {
        assumeTrue("Opt in with power_mutations=true",InstrumentationRegistry.getArguments().getString("power_mutations")=="true")
        val client=HubClient(context);val connection=connection()
        val state=client.request(connection,"/api/state")
        assumeTrue("Use an idle hub so standby cannot stop user playback",state.child("player").optString("state") in listOf("","idle","ended"))
        val power=client.request(connection,"/api/power")
        assumeTrue("Preserve any pre-existing countdown",remainingTimerMinutes(power.child("timer"))==null)
        val asleep=power.getBoolean("standby")
        val prefs=state.child("preferences")
        val dailyEnabled=prefs.optBoolean("dailyStandbyEnabled")
        val dailyTime=prefs.optString("dailyStandbyTime","23:00")
        try {
            client.request(connection,"/api/power","POST",obj("standby" to !asleep))
            assertEquals(!asleep,client.request(connection,"/api/power").getBoolean("standby"))
            client.request(connection,"/api/power","POST",obj("standby" to asleep))
            client.request(connection,"/api/power/timer","POST",obj("minutes" to 15))
            assertTrue(client.request(connection,"/api/power").child("timer").getDouble("remainingSeconds") in 840.0..900.0)
            client.request(connection,"/api/power/timer","POST",obj("minutes" to 0))
            assertNull(remainingTimerMinutes(client.request(connection,"/api/power").child("timer")))
            val alternative=if(dailyTime=="23:15") "23:45" else "23:15"
            client.request(connection,"/api/preferences","PATCH",obj("dailyStandbyEnabled" to false,"dailyStandbyTime" to alternative))
            val changed=client.request(connection,"/api/power").child("daily")
            assertFalse(changed.getBoolean("enabled"));assertEquals(alternative,changed.getString("time"))
            val brightness=power.child("brightness")
            if(brightness.optBoolean("available")) {
                val desired=brightness.optInt("desired",prefs.optInt("screenBrightness",70))
                client.request(connection,"/api/preferences","PATCH",obj("screenBrightness" to desired))
                assertEquals(desired,client.request(connection,"/api/state").child("preferences").getInt("screenBrightness"))
            }
        } finally {
            val restore=listOf(
                Triple("/api/power/timer","POST",obj("minutes" to 0)),
                Triple("/api/preferences","PATCH",obj("dailyStandbyEnabled" to dailyEnabled,"dailyStandbyTime" to dailyTime)),
                Triple("/api/power","POST",obj("standby" to asleep)))
            val failures=mutableListOf<Exception>()
            for((path,method,body) in restore) try { client.request(connection,path,method,body) } catch(e:Exception) { failures.add(e) }
            if(failures.isNotEmpty()) throw AssertionError("Hub restoration failed; inspect standby/daily/timer before continuing",failures.first())
        }
    }

    @Test fun powerHeaderAndSettingsRemainReachable()=runBlocking {
        val state=HubClient(context).request(connection(),"/api/state")
        assertTrue(state.has("power"))
        val settings=context.getSharedPreferences("interface",android.content.Context.MODE_PRIVATE)
        val language=settings.getString("language","ro")
        val dark=settings.getBoolean("dark",true)
        try {
            for(ro in listOf(true,false)) for(night in listOf(true,false)) {
                settings.edit().putString("language",if(ro) "ro" else "en").putBoolean("dark",night).commit()
                val activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
                try {
                    instrumentation.runOnMainSync { activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
                    val action=if(state.child("power").optBoolean("standby")) text(ro,"Pornește","Wake") else text(ro,"Repaus","Standby")
                    val readyDeadline=android.os.SystemClock.elapsedRealtime()+15000
                    while(find(action)==null && android.os.SystemClock.elapsedRealtime()<readyDeadline) Thread.sleep(200)
                    assertNotNull(find(action));assertNull(find("TELECOMANDĂ"));assertNull(find("REMOTE"))
                    assertNull(find("Comandă confirmată de hub."));assertNull(find("Command confirmed by the hub."))
                    assertNull(find("Locația aleasă pe PySH"));assertNull(find("Location selected on PySH"))
                    click(text(ro,"Setări","Settings"))
                    val settingsLabel=text(ro,"Ecran și repaus","Screen and standby")
                    val settingsDeadline=android.os.SystemClock.elapsedRealtime()+8000
                    while(find(settingsLabel)==null && android.os.SystemClock.elapsedRealtime()<settingsDeadline) Thread.sleep(200)
                    assertNotNull(find(settingsLabel))
                    assertNotNull(find("15 min"));assertNotNull(find("30 min"));assertNotNull(find("60 min"))
                    val controls=instrumentation.uiAutomation.takeScreenshot() ?: throw AssertionError("No power screenshot")
                    File(context.filesDir,"power-controls-${if(ro)"ro" else "en"}-${if(night)"night" else "light"}.png").outputStream().use{controls.compress(Bitmap.CompressFormat.PNG,100,it)}
                    controls.recycle()
                    scroll();Thread.sleep(300)
                    assertNotNull(find(action)) // Fixed header stays available after content scrolling.
                    val image=instrumentation.uiAutomation.takeScreenshot() ?: throw AssertionError("No screenshot")
                    File(context.filesDir,"power-settings-${if(ro)"ro" else "en"}-${if(night)"night" else "light"}.png").outputStream().use{image.compress(Bitmap.CompressFormat.PNG,100,it)}
                    image.recycle()
                } finally { activity.finish();instrumentation.waitForIdleSync() }
            }
        } finally { settings.edit().putString("language",language).putBoolean("dark",dark).commit() }
    }
    private fun walk(node:AccessibilityNodeInfo?,match:(AccessibilityNodeInfo)->Boolean):AccessibilityNodeInfo? {
        if(node==null) return null
        if(match(node)) return node
        for(i in 0 until node.childCount) walk(node.getChild(i),match)?.let{return it}
        return null
    }
    private fun find(label:String)=walk(instrumentation.uiAutomation.rootInActiveWindow){it.text?.toString()==label || it.contentDescription?.toString()==label}
    private fun click(label:String) {
        var node=find(label) ?: throw AssertionError("Missing: $label")
        while(!node.isClickable) node=node.parent ?: throw AssertionError("Not clickable: $label")
        assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_CLICK))
    }
    private fun scroll() {
        val node=walk(instrumentation.uiAutomation.rootInActiveWindow){it.isScrollable} ?: throw AssertionError("No scroll container")
        assertTrue(node.performAction(AccessibilityNodeInfo.ACTION_SCROLL_FORWARD))
    }
}
