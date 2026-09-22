# Generation 10 expansion foundation

SILVER의 10세대 대비 확장은 **8개 retail Silver release 전체**를 입력으로 한다. 일본판은 Master Reference지만 유일한 source profile이 아니다.

## Release-specific import boundary

`jp-rev0`, `jp-rev1`, `ko-rev0`, `en-rev0`, `de-rev0`, `fr-rev0`, `it-rev0`, `es-rev0`를 각각 독립 provenance로 유지한다.

JP는 9 boxes x 30, KO/국제판 계열은 14 x 20처럼 layout family를 공유할 수 있지만, layout 공유는 코드 재사용일 뿐 release identity 통합이 아니다.

## Runtime boundary

최종 runtime은 GBA이다. GBC의 MBC3/RTC/SRAM 자료는 원본 분석과 legacy import의 근거로 보존한다. 새 런타임 개체/세이브 구조는 legacy GBC bank address를 identity로 사용하지 않는다.

## ExpandedMonV1

Gen II box record의 species/item/4 moves는 1 byte이므로 16-bit로 승격한다. form/ability는 별도 16-bit 필드로 두되 Gen II에 없는 값을 추측하지 않는다. 원본 나머지 26 bytes는 그대로 보존한다.

64-byte record 안의 source profile code는 8개 release를 각각 구분한다. 이 provenance는 향후 언어별 문자열, 이벤트, save migration, 버전 고유 동작을 비교·재현하는 기준이 된다.

## Next engine work

다음 구현 경계는 8개 release별 SAV decoder를 실제 field 단위로 완성하고, party/box/battle/link/script 경로의 8-bit species/item/move 접근을 GBA runtime의 16-bit accessor로 교체하는 것이다.
