# MVP 分類音軌與 Post-MVP 拆分決策

**狀態：** 已接受
**日期：** 2026-08-21
**範圍：** 音軌分離的產品輸出 taxonomy；完整系統規格仍在討論中。

## MVP 決策

MVP 固定輸出六個使用者可見的「分類群組（Instrument Groups）」，不是還原錄音室原始 tracks：

| 分類群組 | 涵蓋內容 | 後續產物 |
|---|---|---|
| `vocals` | 主唱與合聲 | 音訊、主要單音旋律 MIDI、獨立樂譜 |
| `drums` | 鼓組與常見打擊樂器 | 音訊、General MIDI 鼓事件、獨立鼓譜 |
| `bass` | 電貝斯、木貝斯與 Synth Bass | 音訊、MIDI、獨立樂譜 |
| `guitar` | 電吉他與木吉他 | 音訊、MIDI、獨立樂譜 |
| `keyboard` | Piano、Electric Piano、Organ、Keyboard Synth、Clavinet | 音訊、MIDI、獨立雙譜表樂譜 |
| `unclassified` | 其他樂器、環境音、效果、殘響及無法可靠歸類的聲音 | 音訊；MVP 不產生 MIDI 或樂譜 |

原曲可以包含任意數量的聲音來源。多個同類來源在 MVP 合併到同一分類群組；六類以外的來源進入 `unclassified`。因此原曲即使包含十個以上樂器，產品仍輸出固定六個分類群組。

Provider Adapter 必須將供應者輸出映射或合併成上述 taxonomy。若 Provider 只能輸出 `vocals`、`drums`、`bass`、`other`，必須再將 `other` 分解為 `guitar`、`keyboard` 與 `unclassified`，否則不能宣稱符合 MVP interface。不能用假造的空音軌掩飾 Provider 缺少必要能力。

原曲確實沒有某類樂器時，該分類允許產生靜音或近靜音音軌；對應的 classified stem 可以產生合法空 MIDI 與休止樂譜。這和 Provider 無法提供該分類是不同情況。

## MVP 情境測試要求

實作前的情境測試必須包含：

- 原曲具有全部分類；
- 原曲缺少 vocals、guitar 或 keyboard；
- 原曲只有 drums；
- 原曲含十個以上來源，但正確聚合成六個分類群組；
- 多個同類樂器聚合到同一群組；
- 未知樂器進入 `unclassified`；
- Provider 回傳超過六類時正確映射；
- Provider 缺少必要分類能力時整個 Job 失敗，而不是產生假空音軌；
- 產物損壞或無法解析時整個 Job 失敗。

功能測試只驗證 interface、狀態、檔案與資料結構，不判斷分離內容的音樂正確性。音訊與 MIDI 正確性由獨立的 Quality Evaluation 使用 Reference Audio／Reference MIDI 量測。

## Post-MVP

### 動態樂器分類

辨識並新增第七種以上的樂器分類，例如 saxophone、strings 或 winds，而不是永久放在 `unclassified`。

### 同類來源實例分離

在一個分類群組內進一步拆分多個同類來源（Source Instances），例如：

```text
keyboard
└── piano
    ├── piano_1
    └── piano_2

guitar
└── electric_guitar
    ├── electric_guitar_1
    └── electric_guitar_2
```

每個拆出的來源實例應能獨立產生音訊、MIDI 與樂譜。這項能力可推廣到所有分類群組，實作優先順序暫定為 Guitar、Keyboard、Vocals，其後才是多組 Drums 或 Bass。

拆出來源實例後是否仍保留群組總軌，以及無法完全拆分的 group residual 如何呈現，留待 Post-MVP 階段正式設計時決定。
