package ro.pysh.remote

import androidx.test.platform.app.InstrumentationRegistry
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import android.content.Intent
import android.graphics.Bitmap
import android.view.accessibility.AccessibilityNodeInfo
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.runBlocking
import org.junit.Assert.*
import org.junit.Test
import org.junit.Assume.assumeTrue
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicReference
import java.io.File

/** Read-only, explicitly selected after the matching discovery gateway is deployed. */
class OnboardingLanTest {
    private val instrumentation=InstrumentationRegistry.getInstrumentation()
    private val context get()=instrumentation.targetContext
    @Test fun savedCertificateAuthenticatesStableHubIdentity()=runBlocking {
        val saved=ConnectionStore(context).load() ?: throw AssertionError("Existing association required")
        val identity=HubClient(context).request(saved,"/remote/identity")
        assertEquals(2,identity.getInt("protocol"))
        DiscoveryPolicy.verifyReconnect(saved.hubId,saved.pin,identity.getString("hubId"),identity.getString("certificateSha256"))
        assertTrue(identity.getBoolean("enabled"))
        assertTrue(HubClient(context).request(saved,"/api/state").has("power"))
    }
    @Test fun multicastFindsPairedHubWithoutTypingAddress()=runBlocking {
        val saved=ConnectionStore(context).load() ?: throw AssertionError("Existing association required")
        val identity=HubClient(context).request(saved,"/remote/identity")
        val expected=identity.getString("hubId")
        val latch=CountDownLatch(1)
        val found=AtomicReference<DiscoveredHub>()
        lateinit var discovery:HubDiscovery
        instrumentation.runOnMainSync {
            discovery=HubDiscovery(context) { hubs,_ -> hubs.firstOrNull { it.hubId==expected }?.let { found.set(it);latch.countDown() } }
            discovery.start()
        }
        try {
            assertTrue("mDNS did not find the paired hub within 35 seconds",latch.await(35,TimeUnit.SECONDS))
            val hint=found.get()
            val result=HubClient(context).discoverIdentity(hint)
            DiscoveryPolicy.verifyReconnect(expected,saved.pin,result.hubId,result.pin)
            assertEquals(saved.pin,result.pin)
        } finally { instrumentation.runOnMainSync { discovery.stop() } }
    }
    /** Simulates a stale saved address; neither hub networking nor credentials change. */
    @Test fun staleAddressAutomaticallyFindsPairedHub()=runBlocking {
        val store=ConnectionStore(context)
        val original=store.load() ?: throw AssertionError("Existing association required")
        val client=HubClient(context)
        val identity=client.request(original,"/remote/identity")
        val hubId=DiscoveryPolicy.hubId(identity.getString("hubId"))
        DiscoveryPolicy.verifyReconnect(original.hubId,original.pin,hubId,identity.getString("certificateSha256"))
        val stale=original.copy(host=if(original.host=="10.255.255.254")"10.255.255.253" else "10.255.255.254",hubId=hubId)
        var activity:MainActivity?=null
        try {
            store.save(stale)
            activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)) as MainActivity
            instrumentation.runOnMainSync { activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
            val deadline=android.os.SystemClock.elapsedRealtime()+55_000
            var recovered:HubConnection?=null
            while(android.os.SystemClock.elapsedRealtime()<deadline) {
                val candidate=store.load()
                if(candidate!=null && candidate.host!=stale.host) { recovered=candidate;break }
                Thread.sleep(200)
            }
            val current=recovered ?: throw AssertionError("Controller did not recover the stale address within 55 seconds")
            assertTrue("Stored certificate changed",original.pin==current.pin)
            assertTrue("Stored credential changed",original.token==current.token)
            assertTrue("Stored device identity changed",original.deviceId==current.deviceId)
            assertTrue("Stored hub identity changed",hubId==current.hubId)
            assertEquals(current.host,LanPolicy.host(current.host))
            assertTrue(client.request(current,"/api/state").has("power"))
            val uiDeadline=android.os.SystemClock.elapsedRealtime()+8000
            while(find("LAN")==null && android.os.SystemClock.elapsedRealtime()<uiDeadline)Thread.sleep(200)
            assertNotNull(find("LAN"));capture("onboarding-address-recovered")
        } finally {
            activity?.let { instrumentation.runOnMainSync { it.finish() } };instrumentation.waitForIdleSync()
            store.save(original)
        }
    }
    /** Native rendering fixtures, deliberately separate from real discovery/pairing evidence. */
    @Test fun onboardingLayoutStatesNeverAskForManualSecrets() {
        val activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)) as MainActivity
        val scope=CoroutineScope(SupervisorJob()+Dispatchers.Main.immediate)
        try {
            instrumentation.runOnMainSync { activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
            for(ro in listOf(true,false))for(night in listOf(true,false))for(phase in listOf("searching","found","waiting","pairing_denied","pairing_expired","wifi_required","not_found")) {
                instrumentation.runOnMainSync {
                    val remote=RemoteController(context,scope).apply { previewOnboarding(phase,ro,night) }
                    activity.setContent {
                        AppTheme(night,ro) { Surface {
                            Column(Modifier.fillMaxSize().systemBarsPadding().verticalScroll(rememberScrollState()).padding(22.dp),verticalArrangement=Arrangement.spacedBy(20.dp)) {
                                BrandHeader(remote);PairPage(remote);Text("Preview fixture · $phase")
                            }
                        } }
                    }
                }
                instrumentation.waitForIdleSync()
                var labels=emptyList<String>()
                var hasEditable=false
                val rendered=awaitUi(12_000) {
                    val nodes=walkNodes(instrumentation.uiAutomation.rootInActiveWindow)
                    val titles=nodes.map { it.text?.toString().orEmpty() }
                    val phaseReady=when(phase) {
                        "found" -> nodes.any { it.text?.toString()==text(ro,"Conectează PySH","Connect PySH") && clickableAncestor(it)!=null }
                        "waiting" -> titles.contains(text(ro,"Anulează conectarea","Cancel connection"))
                        "searching" -> titles.contains(text(ro,"Căutăm PySH în apropiere…","Looking for PySH nearby…"))
                        "pairing_denied","pairing_expired" -> titles.contains(errorText(phase,ro))
                        "wifi_required" -> titles.contains(text(ro,"Conectează telefonul la Wi-Fi-ul de acasă pentru a găsi PySH.","Join your home Wi-Fi to find PySH."))
                        "not_found" -> titles.any { it.startsWith(text(ro,"PySH nu este încă vizibil.","PySH is not visible yet.")) }
                        else -> false
                    }
                    val ready=phaseReady && titles.any { it.contains(if(ro) "Hubul tău." else "Your hub.") }
                    if(ready) { labels=titles;hasEditable=nodes.any { it.isEditable } }
                    ready
                }
                capture("onboarding-$phase-${if(ro)"ro" else "en"}-${if(night)"night" else "light"}")
                if(!rendered)dumpAccessibility("onboarding-$phase-${if(ro)"ro" else "en"}-${if(night)"night" else "light"}")
                assertTrue("Onboarding phase did not render: $phase / ${if(ro)"ro" else "en"} / ${if(night)"night" else "light"}",rendered)
                assertFalse("Onboarding must not request manual credentials",hasEditable)
                assertTrue(labels.any { it.contains(if(ro) "Hubul tău." else "Your hub.") })
                assertTrue(labels.none { it.contains("SHA-256")||it.contains("Adresa IP")||it.contains("Pairing code") })
                if(phase in setOf("searching","found"))assertTrue(labels.any { it.contains("Android App Control") })
                if(phase=="waiting")assertTrue(labels.any { it.contains(if(ro) "Anulează conectarea" else "Cancel connection") })
            }
        } finally { scope.cancel();activity.finish();instrumentation.waitForIdleSync() }
    }
    /** Requires an operator watching PySH; restores the original association even on failure. */
    @Test fun freshPairingUiApprovedOnHubRestoresOriginalAssociation()=runBlocking {
        assumeTrue("Opt in with -e fresh_pairing true",InstrumentationRegistry.getArguments().getString("fresh_pairing")=="true")
        val store=ConnectionStore(context)
        val original=store.load() ?: throw AssertionError("Original association required for safe restoration")
        val client=HubClient(context)
        val identity=client.request(original,"/remote/identity")
        val expectedHubId=identity.getString("hubId")
        DiscoveryPolicy.verifyReconnect(original.hubId,original.pin,expectedHubId,identity.getString("certificateSha256"))
        val interfacePrefs=context.getSharedPreferences("interface",android.content.Context.MODE_PRIVATE)
        val language=interfacePrefs.getString("language","ro")
        var activity:MainActivity?=null
        var owned:HubConnection?=null
        try {
            interfacePrefs.edit().putString("language","ro").commit()
            store.clear()
            activity=instrumentation.startActivitySync(Intent(context,MainActivity::class.java).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK)) as MainActivity
            instrumentation.runOnMainSync { activity.window.addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON) }
            val onboardingReady=awaitUi(12_000) { walkNodes(instrumentation.uiAutomation.rootInActiveWindow).any { it.text?.toString()?.contains("Hubul tău.")==true } }
            capture("onboarding-live-search")
            assertTrue("Live onboarding did not render before discovery",onboardingReady)
            val discoveryDeadline=android.os.SystemClock.elapsedRealtime()+40_000
            while(connectButton()==null && android.os.SystemClock.elapsedRealtime()<discoveryDeadline)Thread.sleep(200)
            val button=connectButton() ?: throw AssertionError("Discovered PySH connect button not found")
            assertTrue(button.performAction(AccessibilityNodeInfo.ACTION_CLICK))
            val requestDeadline=android.os.SystemClock.elapsedRealtime()+20_000
            fun approvalInstruction()=walkNodes(instrumentation.uiAutomation.rootInActiveWindow).any { it.text?.toString()?.contains("atinge „Da”")==true }
            while(!approvalInstruction() && android.os.SystemClock.elapsedRealtime()<requestDeadline)Thread.sleep(200)
            assertTrue(approvalInstruction());Thread.sleep(300);capture("onboarding-live-waiting")
            instrumentation.sendStatus(0,android.os.Bundle().apply { putString("stream","\nFresh pairing UI awaits approval on the PySH screen.\n") })
            val approvalDeadline=android.os.SystemClock.elapsedRealtime()+110_000
            while(android.os.SystemClock.elapsedRealtime()<approvalDeadline) {
                val saved=store.load()
                if(saved!=null && saved.deviceId!=original.deviceId) { owned=saved;break }
                Thread.sleep(250)
            }
            val paired=owned ?: throw AssertionError("Fresh UI pairing was not approved within the bounded wait")
            assertEquals(expectedHubId,paired.hubId);assertEquals(original.pin,paired.pin)
            assertNotEquals(original.deviceId,paired.deviceId)
            assertTrue(client.request(paired,"/api/state").has("power"))
            val homeDeadline=android.os.SystemClock.elapsedRealtime()+8000
            while(find("Spațiul tău sonor.")==null && android.os.SystemClock.elapsedRealtime()<homeDeadline)Thread.sleep(200)
            assertNotNull(find("Spațiul tău sonor."));assertNotNull(find("LAN"));capture("onboarding-live-connected")
        } finally {
            // Finish first: withdrawing this UI cannot revive the audit identity after restoration.
            activity?.let { instrumentation.runOnMainSync { it.finish() } };instrumentation.waitForIdleSync()
            val saved=store.load()
            if(owned==null && saved!=null && saved.deviceId!=original.deviceId)owned=saved
            var cleanupFailure:Exception?=null
            try { owned?.let { client.request(it,"/remote/revoke-self","POST",obj()) } }
            catch(e:Exception) { cleanupFailure=e }
            finally { store.save(original);interfacePrefs.edit().putString("language",language).commit() }
            if(cleanupFailure!=null)throw AssertionError("Audit identity revocation failed; original association has been restored",cleanupFailure)
        }
    }
    private fun walkNodes(node:AccessibilityNodeInfo?):List<AccessibilityNodeInfo> {
        if(node==null || !node.refresh())return emptyList()
        return listOf(node)+(0 until node.childCount).flatMap { walkNodes(node.getChild(it)) }
    }
    private fun find(label:String)=walkNodes(instrumentation.uiAutomation.rootInActiveWindow).firstOrNull { it.text?.toString()==label || it.contentDescription?.toString()==label }
    private fun connectButton(label:String="Conectează PySH"):AccessibilityNodeInfo? {
        for(node in walkNodes(instrumentation.uiAutomation.rootInActiveWindow).filter { it.text?.toString()==label }) {
            clickableAncestor(node)?.let { return it }
        }
        return null
    }
    private fun clickableAncestor(node:AccessibilityNodeInfo):AccessibilityNodeInfo? {
        var parent:AccessibilityNodeInfo?=node
        while(parent!=null) {
            if(parent.refresh() && parent.isClickable)return parent
            parent=parent.parent
        }
        return null
    }
    private fun awaitUi(timeout:Long,predicate:()->Boolean):Boolean {
        val deadline=android.os.SystemClock.elapsedRealtime()+timeout
        while(android.os.SystemClock.elapsedRealtime()<deadline) {
            if(predicate()) { Thread.sleep(200);return true }
            Thread.sleep(150)
        }
        return predicate()
    }
    private fun dumpAccessibility(name:String) {
        val lines=walkNodes(instrumentation.uiAutomation.rootInActiveWindow).map { node ->
            val bounds=android.graphics.Rect().also { node.getBoundsInScreen(it) }
            "class=${node.className} clickable=${node.isClickable} enabled=${node.isEnabled} visible=${node.isVisibleToUser} bounds=$bounds actions=${node.actionList.map { it.id }} text=${node.text} description=${node.contentDescription}"
        }
        // Fixture diagnostics remain private in app storage, never printed or checked into Git.
        File(context.filesDir,"$name-accessibility.txt").writeText(lines.joinToString("\n"))
    }
    private fun capture(name:String) {
        val image=instrumentation.uiAutomation.takeScreenshot() ?: throw AssertionError("No onboarding capture")
        File(context.filesDir,"$name.png").outputStream().use { image.compress(Bitmap.CompressFormat.PNG,100,it) };image.recycle()
    }
}
