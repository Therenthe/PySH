# Flash PySH OS prin SSH, cu progres în consolă

Proba Linux pe loop-uri deținute a verificat scrierea, block flush, readback-ul și provisioning FAT, cu cleanup complet; [dovada](evidence/ssh-flasher-linux-2026-10-03.md). Aceasta nu înlocuiește SD-ul real și primul boot. `tests/linux/ssh_flasher_loop.py` poate repeta proba într-un workspace nou, privat, folosind doar backing files proprii; producția continuă să refuze loop-uri.

Acest tool scrie **un card SD inactiv** dintr-un Raspberry pornit de pe USB. Nu poate rescrie în siguranță sistemul SD din care rulează Raspberry; refuză root, boot, swap, partiții montate sau dispozitive cu holders. Nu permite ținte USB, aliasuri/symlinkuri, partiții individuale sau identificarea doar prin numele `/dev/mmcblk0`. CID-ul fizic și capacitatea exactă trebuie confirmate și repetate.

Tool-urile sunt `scripts/flash-pysh-ssh.py` pe PC și `scripts/flash-pysh-target.py` ca helper transmis în sesiunea SSH, executat cu `sudo -n python3`. Nu este necesară instalarea unui daemon. PC-ul necesită Python 3.12+ și OpenSSH; Raspberry necesită Linux, Python, sudo administrativ, lsblk, blockdev, udevadm, blkid, mount/umount și vfat. SSH folosește obligatoriu cheia explicită și fișierul known-hosts explicit, strict host checking și BatchMode; nu acceptă parole sau expunere publică. Comenzile exemplificate mai jos sunt pe o singură linie și funcționează din PowerShell sau shell Linux, adaptând căile.

Înainte de orice ștergere, păstrează USB-ul actual ca recuperare, confirmă că Raspberry rulează de pe USB, introdu SD-ul original fără reboot și inspectează-l. Dacă a fost montat automat, tool-ul îl refuză: verifică exact mount-urile și operația de demontare separat. Tool-ul nu demontează partițiile originale pentru a forța scrierea.

```text
python scripts/flash-pysh-ssh.py --host 192.168.100.127 --user pysh-admin --key <cheie-privată-locală> --known-hosts <known-hosts-verificat> --target /dev/mmcblk0
```

Acesta este modul implicit **inspect**, fără backup sau scriere. Ieșirea identifică target, CID, bytes și identitatea hostului; refuză o țintă în uz. Nu inventa CID-ul sau capacitatea din exemple. Verifică spațiul liber pe PC: backupul este întreaga capacitate fizică a SD-ului, nu doar partițiile folosite. Alege un director local privat pe NTFS/ext4 sau alt filesystem care acceptă fișiere mari și hardlinks; nu FAT32, folder public/sincronizat sau media de pe țintă.

```text
python scripts/flash-pysh-ssh.py backup --host 192.168.100.127 --user pysh-admin --key <cheie> --known-hosts <known-hosts> --target /dev/mmcblk0 --cid <CID-32-hex> --size <bytes-exacți> --backup <PC-private/sd-original.raw> --backup-record <PC-private/sd-original.json>
python scripts/flash-pysh-ssh.py verify-backup --backup <PC-private/sd-original.raw> --backup-record <PC-private/sd-original.json> --receipt <PC-private/sd-original.receipt.json>
```

Backupul trece prin SSH către PC, cu progres bytes/procent și hash remote comparat cu streamul local. Un transfer întrerupt rămâne `.partial`, fără receipt și fără a deveni backup valid. Fișierul este creat exclusiv, fără suprascriere. `verify-backup` recitește **independent** backupul complet pe PC, verifică lungimea și SHA-256 și emite receipt legat de CID, capacitate și host. Acesta este un document administrativ generat de operator, nu o atestare criptografică nefalsificabilă. Păstrează backupul și receipt-ul privat; backupul poate conține conturi și date personale.

Modul `hash` recitește întregul SD inactiv fără să transfere conținutul și fără scriere. Cere același CID/capacitate, claim exclusiv și verifică din nou identitatea și mount-urile după citire. Poate compara o copie completă rămasă după o eroare de finalizare cu sursa originală încă neschimbată; un `.partial` nu devine valid doar pentru că are lungimea corectă. Publicarea copiei și emiterea receipt-ului se fac numai după egalitatea hash-urilor și recitirea independentă pe PC.

```text
python scripts/flash-pysh-ssh.py hash --host 192.168.100.127 --user pysh-admin --key <cheie> --known-hosts <known-hosts> --target /dev/mmcblk0 --cid <CID> --size <bytes-exacți>
```

Pe Windows, dacă directorul privat este protejat prin ACL pentru proprietar, consola trebuie să ruleze sub acel cont cu acces la director. Un proces pornit anterior cu token restricționat poate pierde accesul după întărirea ACL; verificați codul de ieșire și receipt-ul, nu doar progresul 100%.

Folosește imaginea **raw `.img` decomprimată**, SHA-256 confirmat separat față de artefactul GitHub verificat și exact o cheie **publică Ed25519**. Cheia privată SSH nu este cheia publică de provisioning și nu se transmite. Tool-ul verifică și MBR-ul PySH: FAT la sector16384, 524288 sectoare, urmată de Linux fără suprapunere și în limitele imaginii.

```text
python scripts/flash-pysh-ssh.py flash --host 192.168.100.127 --user pysh-admin --key <cheie-privată-SSH> --known-hosts <known-hosts> --target /dev/mmcblk0 --cid <CID> --size <bytes-SD> --backup <PC-private/sd-original.raw> --backup-record <PC-private/sd-original.json> --receipt <PC-private/sd-original.receipt.json> --image <pysh-candidate.img> --image-sha256 <SHA-256-imagine> --public-key <recovery-ed25519.pub>
```

Fără `--write`, comanda `flash` este **dry-run**: verifică imaginea, backupul/receipt-ul și ținta live, apoi afișează planul; nu scrie. După autorizarea exactă a SD-ului, repetă comanda cu **`--write`**. Consolele arată fazele local-image-verify, backup-recheck, write, readback și public-key-verified, cu bytes/procent periodic. Nicio fază de 100% write nu reprezintă succes înainte de readback/provisioning.

Helper-ul recitește CID/capacitate/mount-uri înainte de primul write, verifică MBR înainte să deschidă writable target, folosește block-device claim exclusiv, tratează short writes și refuză streamuri incomplete/supradimensionate sau hash-uri diferite. După fsync invalidează cache-ul blocului și verifică separat SHA-256 pentru **prefixul exact de bytes al imaginii**. Restul capacității cardului nu este certificat drept egal imaginii.

Numai după readback corect, identifică p1 după offset/capacitate și FAT real, verifică boot files, o montează temporar cu nosuid/nodev/noexec și creează exclusiv `/pysh-recovery.pub`. Apoi flush/unmount/sync, remount read-only și verifică hash-ul cheii; demontează din nou. Provisioning-ul modifică legitim bytes din FAT: rezultatul raportează **hash-ul imaginii înainte de provisioning** și **hash-ul separat al cheii publice**. Nu pretinde că imaginea raw finală este neschimbată.

Nu există reboot automat, modificări EEPROM, modificări rețea, runtime sau sesiune, cleanup general ori scrieri pe USB-ul de operare. La întrerupere/eroare nu se declară succes. Nu boota SD-ul parțial; USB-ul și backupul original rămân căile de recuperare. Dacă alimentarea/kill forțat întrerupe provisioning-ul, inspectează eventualul mount temporar înainte de alte operații; un SIGKILL sau o pană nu poate executa cleanup.

După rezultatul verificat, oprirea controlată și schimbarea fizică pentru boot SD sunt pași separați cu proprietarul. Verifică model, identitatea noii imagini, SSH, boot, panou/touch, LAN, audio și aplicație. Readback-ul nu dovedește aceste rezultate și nu trece Definition of Done. Testele unitare și o probă Linux cu loop device nu înlocuiesc proba de flash/boot pe SD-ul real.
