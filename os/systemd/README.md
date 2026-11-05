# systemd

`pysh-recorder.service` este unitatea **user** pentru înregistrările IPTV,
separată de unitatea Hub `pysh.service`. Rulează ca `pysh` din
`/opt/pysh/current`, cu Python-ul existent în `/opt/pysh/venv`. Nu are
`PartOf=`, `Requires=` sau `BindsTo=` către Hub; închiderea UI/restartul Hub nu
oprește copiii FFmpeg ai recorderului. Relay-ul temporar HLS ascultă numai pe
loopback. `After/Wants=network-online.target` ordonează pornirea; nu garantează
accesul ulterior la internet.

După activarea unui release versionat verificat și instalarea dependenței OS
`ffmpeg`, invocarea explicită este:

```sh
sudo python3 /opt/pysh/current/scripts/install-recorder.py
```

Installerul verifică markerul existent `/opt/pysh/runtime-source.json` și hash-ul
unității din release. Creează `/etc/systemd/user/pysh-recorder.service` dacă
lipsește; acceptă o copie identică și refuză una diferită sau un symlink.
Refuză operația dacă există joburi active. Apoi activează unitatea în managerul
user `pysh`, fără restartul Hub. Nu îl rula înainte de activarea runtime-ului
și nu crea manual un marker pentru a trece verificarea.

Verificare read-only în sesiunea appliance existentă (UID-ul provisionat este
1000; reconfirmă-l dacă imaginea diferă):

```sh
sudo -u pysh env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user is-active pysh-recorder.service
sudo -u pysh env XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus systemctl --user status pysh-recorder.service --no-pager
```

`Restart=on-failure` și `KillMode=control-group` se aplică numai recorderului.
Un restart al său întrerupe înregistrările; la revenire daemonul păstrează
joburile/fișierele parțiale și raportează întreruperea. Nu promite continuarea
fără pierderi, trezire din suspendare sau recuperarea emisiunilor ratate.
Nu modifica/reporni serviciul cu joburi active. Pentru update/rollback,
coordonarea cu `current` și backupul SQLite/MKV sunt în
[OPERATIONS](../../docs/OPERATIONS.md#tv-înregistrări-și-date-private).

Unitatea și installerul sunt implementate; activarea lor, pornirea la reboot
și fluxul complet HLS/MKV pe panou trebuie probate pe candidatul instalat.
Dependența adăugată în definiția OS nu reprezintă o imagine construită/flashed.
Acceptarea completă a produsului rămâne OPEN; consultă [STATUS](../../STATUS.md).
