# SILVER ROM/SAV all-release baseline

확장 기준은 일본판 하나가 아니라 **실제로 제공된 8개 Silver ROM + 8개 SAV 전체**다.

## 독립 release profiles

| profile | language/region | ROM | save layout family |
| --- | --- | ---: | --- |
| jp-rev0 | Japanese / Japan | 1 MiB | jp |
| jp-rev1 | Japanese / Japan Rev.A | 1 MiB | jp |
| ko-rev0 | Korean / Korea | 2 MiB | ko |
| en-rev0 | English / USA-Europe | 2 MiB | western |
| de-rev0 | German / Germany | 2 MiB | western |
| fr-rev0 | French / France | 2 MiB | western |
| it-rev0 | Italian / Italy | 2 MiB | western |
| es-rev0 | Spanish / Spain | 2 MiB | western |

`layout_family`은 decoder 구현을 공유하기 위한 정보일 뿐이다. provenance와 호환성 판단에서는 8개 profile을 절대 합치지 않는다.

## Binary audit facts

8개 ROM 모두 실제 header checksum과 global checksum을 다시 계산해 일치함을 확인했다. 모두 cartridge type `0x10` (MBC3 + TIMER + RAM + BATTERY), RAM size code `0x03` (32 KiB SRAM)이다.

8개 제공 SAV는 각각 32,812 bytes이며, 앞 32,768 bytes를 4개의 8 KiB SRAM bank로 독립 해시했다. 뒤 44 bytes는 관찰된 host-side trailing data로 별도 기록한다.

정확한 ROM/SAV SHA-256과 SRAM bank별 SHA-256은 `analysis/rom-save-baseline.json`에 저장한다.

## Expansion rule

- Japanese Rev.0과 Rev.A도 서로 다른 profile이다.
- Korean은 독립 profile이다.
- English/German/French/Italian/Spanish도 각각 독립 profile이다.
- 공통 구조를 가진다고 해서 `western` 하나로 provenance를 축약하지 않는다.
- legacy SAV import는 read-only이며, release profile을 먼저 결정한 후 공통 GBA runtime model로 변환한다.
- supplied SAV SHA는 조사 당시 상태의 fingerprint이지, 그 언어판의 모든 SAV가 동일해야 한다는 뜻이 아니다.
