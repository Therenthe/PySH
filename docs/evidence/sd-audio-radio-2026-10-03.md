# Bluetooth audio and owner radio on fresh SD

Candidatec8ac9c709acb/source3ca7e4e, following [first SD boot](sd-boot-2026-10-03.md). Owner reconfirmed ML-DAC-SPKBT-QC15 powered and available. The backend discovery result already reported that known speaker paired; this automated probe did **not** execute a new pair request, so it does not establish full first-pair UI acceptance.

The application API connected the known speaker and reported active Bluetooth output/audio ready. It generated an approved local PCM mono16kHz440Hz tone, played for15 seconds at20% and stopped, restoring prior volume/mute. Owner confirmed it was audible and reported listening to radio through the speaker afterwards. No unknown devices were paired or prompts accepted.

A subsequent read-only observation made six real API reads over40 seconds during the owner's radio playback. All six: player playing, kind radio, audio ready, Bluetooth sink active. Position advanced31.940593→72.004944 seconds. Whole-compositor live image showed the radio page in Romanian at800×480. Observation sent no player, volume, station, network or pairing mutations.

Independent ext4 inspection of the original image found `/var/lib/bluetooth` empty and no Pi Smart Hub preferences or Chromium user profile under the checked home paths. Existing pairing belongs to the post-installation device state, not embedded image configuration.

BT-01/02 and MEDIA-01/02/03 remain OPEN: owner hearing tone/radio does not prove all pair/forget/reconnect, source failures, formats, volume and route-recovery flows or EN/RO physical UI. Raw logs, paths and screenshots remain private.
