# GitHub Actions runner admission — 2026-10-04

## Authoritative state

Installed application remains `24b26865a2d5`, source `152f7567ff95c2b043a9c813a70552474314e9f5`. Local tests and native evidence are in [idle-handle-radio-catalog](idle-handle-radio-catalog-2026-10-04.md); they do not substitute for a completed CI run or an OS image build.

REST workflow run/job reads report terminal failure for source152 application runs37162802336/37162799947 and image run37162799932. Documentation commitfc4 application runs37163036507/37163033295 also failed. Source152 PR job records have no executed steps and no assigned runner; backend3.12 was cancelled after backend3.13 failed admission.

The authenticated GitHub run summary explicitly attributes frontend/backend3.13 admission failure to account payment or spending-limit settings. The image summary reports the same admission error for root-expansion; its dependent image job was skipped and no artifacts exist. This is a runner-admission failure, not an executed test assertion failure. No settings, payments, workflow permissions or spending limits were changed. The account owner was asked to inspect Billing & plans; independent local/native work continues.

Authoritative summaries: [application run37162802336](https://github.com/Therenthe/PySH/actions/runs/37162802336), [image run37162799932](https://github.com/Therenthe/PySH/actions/runs/37162799932). Job log retrieval returns missing-blob404 because no log was produced. Do not rerun repeatedly while admission remains unavailable, or mark CI/image PASS from the older source.

The preceding sourcecd1ff application runs37160982489/37160979711 and image37160979739 are completed success. Their image is explicitly superseded and does not certify source152 or its successors.

## Remaining gate

After runner admission is available, run the normal verification and experimental image workflow for the final source. Inspect all executed jobs, download and independently verify the resulting image, then perform the required physical boot/recovery acceptance. This external issue does not block unrelated implementation and local/native verification.
