# SILVER Project

## Canonical direction

포켓몬스터 은 / Pokémon Silver의 **확인된 모든 retail release를 독립적으로 조사**하고, 그 차이를 보존하면서 Game Boy Advance / Generation III 계열 기반의 현대화 리메이크로 재구축한다.

일본판은 Master Reference이지만 유일한 입력이 아니다. 한국어/영어/독일어/프랑스어/이탈리아어/스페인어 릴리스도 각각 독립적인 ROM/SAV 입력과 provenance를 가진다.

## Audited original inputs

1. Japanese Rev.0 — `Pocket Monsters Gin (Japan).gbc/.sav`
2. Japanese Rev.A — `Pocket Monsters Gin (Japan) (Rev A).gbc/.sav`
3. Korean Rev.0 — `Pocket Monsters Eun (Korea).gbc/.sav`
4. English Rev.0 — `Pokemon - Silver Version (USA, Europe).gbc/.sav`
5. German Rev.0 — `Pokemon - Silberne Edition (Germany).gbc/.sav`
6. French Rev.0 — `Pokemon - Version Argent (France).gbc/.sav`
7. Italian Rev.0 — `Pokemon - Versione Argento (Italy).gbc/.sav`
8. Spanish Rev.0 — `Pokemon - Edicion Plata (Spain).gbc/.sav`

공통 save layout을 재사용할 수는 있어도 release identity를 `western` 같은 하나의 profile로 합치지 않는다.

## Runtime baseline

- Host: Game Boy Advance
- Engine family: Generation III-derived
- Modern core reference: `rh-hideout/pokeemerald-expansion@75b806a3ab57a81ff1eb6179288981f0b3cc3050`
- Coordination/reference workspace: `SakuraiTsubaki/EMERALD`

GB/GBC mapper/SRAM/address는 원본 분석·import 근거다. 최종 런타임 엔진은 GBA이며, 10세대 대비 확장 ABI는 모든 8개 원본 release를 구분한 채 GBA-native 데이터/세이브 모델로 변환한다.
