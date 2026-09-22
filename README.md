# SILVER

**Pokémon Silver / ポケットモンスター 銀** 전체 retail release를 근거로 하는 GBA 현대화 리메이크 프로젝트입니다.

## 원본 범위

일본판만이 아닙니다. 현재 감사(audit)된 입력은 **8개 ROM + 8개 SAV**입니다.

- Japanese Rev.0
- Japanese Rev.A
- Korean Rev.0
- English Rev.0
- German Rev.0
- French Rev.0
- Italian Rev.0
- Spanish Rev.0

일본판은 Master Reference이지만, 나머지 릴리스를 `western` 하나로 합치지 않습니다. 각 release는 독립 SHA-256, ROM header, SAV fingerprint, import profile, provenance code를 가집니다.

## 10세대 대비 확장

- species / form / move / item / ability: 16-bit identity
- Gen II 32-byte box record -> 64-byte ExpandedMonV1 migration
- 원본 bytes 6..31 보존
- 8개 release-specific source profile 코드
- legacy form/ability는 추측하지 않고 NONE
- legacy SAV는 read-only import
- 최종 runtime/save는 GBA-native이며 GBC MBC3/SRAM 구조는 원본 분석·변환 근거로만 사용

근거:
- `analysis/rom-save-baseline.json`
- `config/legacy_save_profiles.json`
- `config/expanded_mon_v1.json`
- `config/expansion.json`

ROM/SAV 바이너리는 GitHub에 커밋하지 않습니다.
