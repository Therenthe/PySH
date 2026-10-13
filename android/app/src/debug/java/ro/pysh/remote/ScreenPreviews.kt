package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import org.json.JSONObject

private val fixture="""{"version":"Preview only","appliance":true,"preferences":{"language":"ro","theme":"ink","accent":"sage","volume":40,"timezone":"Europe/Bucharest","favorites":[],"homeCards":["weather","forecast","playback"],"shortcuts":["radio","media"],"location":{"name":"București"}},"audio":{"available":true,"ready":true,"volume":40,"mute":false,"output":"speaker","outputs":[{"id":"speaker","description":"Boxă Bluetooth","bluetooth":true}]},"bluetooth":{"available":true,"powered":true,"devices":[{"name":"Living Room Speaker","address":"AA:BB:CC:DD:EE:FF","paired":true,"connected":true}],"prompts":[]},"network":{"available":true,"state":"connected","saved":[],"devices":[]},"player":{"state":"playing","kind":"radio","station_name":"Radio Studio","title":"Muzică pentru dimineți calme"},"weather":{"location":{"name":"București"},"current":{"temperature_c":21,"humidity_pct":48,"wind_kmh":8},"stale":false}}"""

@Composable private fun Sample(dark:Boolean=true,ro:Boolean=true,page:@Composable (RemoteController)->Unit) {
    val context=LocalContext.current
    val scope=rememberCoroutineScope()
    val remote=remember { RemoteController(context,scope).apply { previewState(JSONObject(fixture),ro) } }
    AppTheme(dark,ro) { Surface(color=MaterialTheme.colorScheme.background) { Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(22.dp),verticalArrangement=Arrangement.spacedBy(20.dp)) { BrandHeader(remote);page(remote);Text(text(ro,"Previzualizare · date de exemplu","Preview · sample data"),style=MaterialTheme.typography.bodyMedium) } } }
}
@Preview(widthDp=412,heightDp=915,showBackground=true)
@Composable fun HomePreview() { Sample { HomePage(it){} } }
@Preview(widthDp=412,heightDp=915,showBackground=true)
@Composable fun HomeLightEnglishPreview() { Sample(false,false) { HomePage(it){} } }
@Preview(widthDp=412,heightDp=915,showBackground=true)
@Composable fun DevicePreview() { Sample { DevicePage(it) } }
@Preview(widthDp=412,heightDp=915,showBackground=true)
@Composable fun SettingsPreview() { Sample { SettingsPage(it) } }
