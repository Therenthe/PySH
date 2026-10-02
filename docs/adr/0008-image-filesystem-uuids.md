# ADR-0008 — Identificarea partițiilor imaginii prin UUID

Stare: acceptată pentru construcția candidatului; boot fizic SD/USB rămâne OPEN.

În rpi-image-gen 2.8, commit `262d4df5a9f9d4133370465399a7958a7c22cdc7`, scriptul `layer/rpi/device/storage-binder/bin/rpi-bootdev-tag` recunoaște doar modurile de boot 1 (SD) și 6 (NVMe). Layoutul upstream `image/mbr/simple_dual/setup.sh` folosește `/dev/disk/by-slot/system` și `/dev/disk/by-slot/boot`. Aceste căi nu sunt garantate pentru boot USB; nu declarăm suport USB pe baza lor.

Păstrăm layoutul MBR și cele două sisteme de fișiere upstream. Builderul copiază layoutul din commitul fixat într-un director generat, ignorat de Git, și înlocuiește exclusiv hookul `setup.sh` cu `os/image/assets/image-setup.sh`. Configurația indică acel director înaintea validării builderului. Checkoutul vendor rămâne nemodificat.

Hookul citește `img_uuids`, generat de `bdebstrap/customize10-pmap`, aceleași valori folosite de `pre-image.sh` pentru `mke2fs -U` și `mkdosfs -i`. Scrie `UUID=<ROOT_UUID>` în fstab și cmdline, respectiv `UUID=<BOOT_UUID>` pentru `/boot/firmware`. Un layout sau cmdline neașteptat oprește buildul. Inspectorul citește UUID-urile efective prin `blkid -p` din fișierele ext4/vfat și verifică identitatea exactă a referințelor. Proveniența layoutului și hashurile tuturor asseturilor copiate intră în `image-layout.json` și raportul de inspecție.

Rezultatul înlătură dependența de numele Linux al discului sau de binder pentru montarea acestor partiții. Nu dovedește suportul EEPROM pentru boot USB, compatibilitatea adaptorului, montarea pe Pi sau recuperarea SSH: acestea cer probe fizice pe candidatul identificat. Nu se modifică firmware-ul sau cardul activ pentru această decizie. La prima probă se păstrează cardul existent intact și se scrie doar destinația de test explicit aleasă de utilizator.

UUID-urile sunt unice per build, nu per copie: două clone identice conectate simultan pot produce ambiguitate. Procedura de boot cere conectarea unei singure copii a candidatului. Nu promitem imagini byte-identice deoarece upstream generează UUID-uri aleatorii.
