package ro.pysh.remote

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import org.json.JSONObject
import kotlin.math.ceil

/** OFF is reversible standby; the hub remains powered and reachable on LAN. */
@Composable fun PowerButton(remote:RemoteController) {
    val asleep=remote.power.optBoolean("standby")
    FilledTonalButton(onClick={remote.standby(!asleep)},enabled=remote.enabled && remote.powerAvailable,
        modifier=Modifier.heightIn(min=48.dp),contentPadding=PaddingValues(horizontal=12.dp)) {
        Icon(Icons.Outlined.PowerSettingsNew,null,Modifier.size(20.dp))
        Spacer(Modifier.width(7.dp))
        Text(T(remote.ro,if(asleep) "Pornește" else "Repaus",if(asleep) "Wake" else "Standby"),maxLines=1)
    }
}

@Composable fun AsleepCard(remote:RemoteController) {
    Panel {
        Icon(Icons.Outlined.Bedtime,null,Modifier.size(36.dp),tint=MaterialTheme.colorScheme.secondary)
        Text(T(remote.ro,"PySH este în repaus","PySH is resting"),style=MaterialTheme.typography.headlineMedium)
        Text(T(remote.ro,"Ecranul și redarea sunt oprite. Hubul rămâne conectat și îl poți activa de aici.","The screen and playback are off. Your hub stays connected and you can wake it here."),color=MaterialTheme.colorScheme.onSurfaceVariant)
        Button(onClick={remote.standby(false)},enabled=remote.enabled && remote.powerAvailable,modifier=Modifier.fillMaxWidth().heightIn(min=54.dp)) {
            Icon(Icons.Outlined.PowerSettingsNew,null);Spacer(Modifier.width(8.dp));Text(T(remote.ro,"Pornește PySH","Wake PySH"))
        }
    }
}

fun remainingTimerMinutes(timer:JSONObject):Int? {
    if(timer.isNull("remainingSeconds")) return null
    return timer.optDouble("remainingSeconds").takeIf{it.isFinite() && it>0}?.let{ceil(it/60).toInt()}
}

@Composable fun TimerSummary(remote:RemoteController) {
    remainingTimerMinutes(remote.power.child("timer"))?.let { minutes ->
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
            Icon(Icons.Outlined.Timer,null,Modifier.size(20.dp),tint=MaterialTheme.colorScheme.secondary)
            Spacer(Modifier.width(10.dp))
            Text(T(remote.ro,"Repaus în $minutes min","Standby in $minutes min"),Modifier.weight(1f),style=MaterialTheme.typography.bodyMedium)
            TextButton(onClick={remote.sleepTimer(0)},enabled=remote.enabled,modifier=Modifier.heightIn(min=48.dp)) { Text(T(remote.ro,"Anulează","Cancel")) }
        }
    }
}

@Composable fun PowerSettings(remote:RemoteController) {
    var editTime by remember { mutableStateOf(false) }
    val power=remote.power
    val brightness=power.child("brightness")
    val asleep=power.optBoolean("standby")
    val available=brightness.optBoolean("available") && !brightness.isNull("value")
    val actual=brightness.optInt("value")
    val desired=brightness.optInt("desired",remote.preferences.optInt("screenBrightness",70)).coerceIn(1,100)
    val confirmed=if(asleep) desired else actual.coerceIn(1,100)
    var slider by remember { mutableFloatStateOf(confirmed.toFloat()) }
    var dragging by remember { mutableStateOf(false) }
    // Every readback, including a failed save, returns the slider to the actual reported state.
    LaunchedEffect(confirmed,remote.busy,remote.error) { if(!dragging && remote.busy==0) slider=confirmed.toFloat() }
    Panel {
        SectionTitle(T(remote.ro,"Ecran și repaus","Screen and standby"),Icons.Outlined.SettingsBrightness)
        if(!remote.powerAvailable) Text(T(remote.ro,"Conectează hubul pentru a vedea aceste controale.","Connect your hub to see these controls."),color=MaterialTheme.colorScheme.onSurfaceVariant)
        Row(Modifier.fillMaxWidth(),verticalAlignment=Alignment.CenterVertically) {
            Text(T(remote.ro,if(asleep) "Luminozitate la activare" else "Luminozitate",if(asleep) "Brightness when awake" else "Brightness"),Modifier.weight(1f),fontWeight=FontWeight.Medium)
            Text(if(available) "${slider.toInt()}%" else "—",color=MaterialTheme.colorScheme.primary)
        }
        Slider(slider,{dragging=true;slider=it},onValueChangeFinished={dragging=false;remote.patch("screenBrightness",slider.toInt())},
            enabled=remote.enabled && remote.powerAvailable && available,valueRange=1f..100f,modifier=Modifier.fillMaxWidth().heightIn(min=48.dp))
        if(!available && remote.powerAvailable) Text(T(remote.ro,"Luminozitatea nu este disponibilă pe acest ecran.","Brightness is unavailable on this display."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        if(asleep && available) Text(T(remote.ro,"Ecran stins · setarea se aplică la activare.","Screen off · this setting applies when the hub wakes."),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
        HorizontalDivider(color=MaterialTheme.colorScheme.outline.copy(alpha=.2f))
        Text(T(remote.ro,"Repaus după","Standby after"),style=MaterialTheme.typography.titleMedium)
        TimerSummary(remote)
        listOf(listOf(15,30,60),listOf(90,120)).forEach { row ->
            Row(Modifier.fillMaxWidth(),horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                row.forEach { minutes -> OutlinedButton(onClick={remote.sleepTimer(minutes)},enabled=remote.enabled && remote.powerAvailable && !asleep,
                    modifier=Modifier.weight(1f).heightIn(min=48.dp),contentPadding=PaddingValues(horizontal=6.dp)) { Text("$minutes min") } }
                if(row.size==2) Spacer(Modifier.weight(1f))
            }
        }
        HorizontalDivider(color=MaterialTheme.colorScheme.outline.copy(alpha=.2f))
        val daily=power.child("daily")
        ToggleRow(T(remote.ro,"Repaus zilnic","Daily standby"),daily.optBoolean("enabled",remote.preferences.optBoolean("dailyStandbyEnabled")),remote.enabled && remote.powerAvailable){remote.patch("dailyStandbyEnabled",it)}
        SettingButton(T(remote.ro,"La ora","At time"),daily.optString("time",remote.preferences.optString("dailyStandbyTime","23:00")),remote.enabled && remote.powerAvailable){editTime=true}
        Text(T(remote.ro,"Ora hubului · ${remote.preferences.optString("timezone","Europe/Bucharest")}","Hub time · ${remote.preferences.optString("timezone","Europe/Bucharest")}"),style=MaterialTheme.typography.bodyMedium,color=MaterialTheme.colorScheme.onSurfaceVariant)
    }
    if(editTime) PreferenceDialog(remote,"dailyStandbyTime"){editTime=false}
}
