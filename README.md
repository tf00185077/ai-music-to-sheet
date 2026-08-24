# AI Music to Sheet

輸入一首流行歌曲的混音音訊，輸出可閱讀、可編輯、可播放的吉他譜、鼓譜或鋼琴譜。

專案最終包含兩條彼此分離、共用底層能力的工作流水線：

1. **原曲忠實轉譜**：轉錄原曲中實際存在的目標樂器聲部，優先開發。
2. **重新編曲**：理解歌曲後，重新配置成指定樂器可演奏的版本，於忠實轉譜穩定後開發。

所有輸出必須明確標示為 `transcription` 或 `arrangement`。推測、補寫或重新配置的音符，不得被標示為原曲忠實轉錄。

## P0 到最終成果

| 階段 | 階段成果 |
| --- | --- |
| **P0 — 契約與驗證基線** | 定義所有流水線產物的資料契約、來源追蹤規則、測試資料集、評估指標與可重現的驗證方式。完成後，後續功能都有一致且可量化的完成標準。 |
| **P1 — 真實歌曲共用前端** | 可讀取常見音訊／影片格式，產生標準化音訊，分析 tempo、beat、downbeat、拍號與段落，並完成 drums、piano、guitar 等目標樂器的音源分離與存在偵測。 |
| **P2 — 鼓譜忠實轉錄** | 將完整流行曲混音轉成原曲鼓聲部的鼓組 MIDI、MusicXML 與 PDF，支援常見鼓件、同時擊打、力度與基本擊法。 |
| **P3 — 同步檢視與人工修正** | 同步顯示音訊、時間軸、小節與樂譜；可定位低信心事件，執行增刪、移動、分類、量化、undo／redo，並保存完整修正歷史。 |
| **P4 — 鋼琴譜忠實轉錄** | 將完整流行曲混音轉成鋼琴大譜表，包含多音音高、時值、力度、延音踏板、聲部與左右手配置，輸出 MIDI、MusicXML 與 PDF。 |
| **P5 — 吉他譜忠實轉錄** | 將完整流行曲混音轉成吉他標準譜與 TAB，包含調弦、capo、弦格配置、和弦、節奏及可辨識的常見奏法。 |
| **P6 — 產品化** | 提供非同步工作、進度、取消、重試、快取、錯誤恢復、資源限制與多格式下載，使完整歌曲能穩定處理與交付。 |
| **P7 — 重新編曲流水線** | 建立 SongIR，理解旋律、和聲、曲式與 groove，依指定樂器、難度及演奏限制，產生明確標示為重新編曲的樂譜。 |
| **最終成果** | 使用者輸入一首流行曲，選擇吉他、鼓或鋼琴，以及忠實轉譜或重新編曲模式，即可取得可追溯、可修正、可播放並可由主流樂譜軟體開啟的 MIDI、MusicXML、PDF 或 TAB。 |

開發順序固定為：

```text
P0 驗證基線
  → P1 共用前端
  → P2 鼓譜
  → P3 修正閉環
  → P4 鋼琴譜
  → P5 吉他譜
  → P6 產品化
  → P7 重新編曲
  → 最終成果
```

在 P0 通過前，不開始以功能展示取代正式驗證；P1 以後的詳細驗證內容，於進入該階段前再依 P0 建立的規則制定。

## P0 成果

P0 的目的不是產生樂譜，而是建立後續每個階段都必須遵守的「產物契約」與「驗證基線」。P0 完成時應交付以下內容。

### 1. Artifact 契約

至少定義下列 artifact：

| Artifact | 用途 | 必要資訊 |
| --- | --- | --- |
| `SourceMedia` | 原始使用者輸入 | 檔案格式、內容雜湊、大小、音軌資訊、來源識別 |
| `CanonicalAudio` | 統一格式的處理音訊 | sample rate、channel layout、sample format、duration、來源 artifact ID |
| `SongAnalysis` | 歌曲時間與結構資訊 | tempo map、beats、downbeats、meter、key、sections、各項信心值 |
| `StemSet` | 分離後的樂器音軌 | taxonomy、每個 stem 的檔案與雜湊、目標樂器存在狀態、信心值 |
| `TrackIR` | 忠實轉錄或編曲後的樂器事件 | 樂器類型、模式、事件、時間位置、信心值、來源證據 |
| `NotationIR` | 可輸出成樂譜的記譜結構 | measures、voices、staff、meter、tempo、ties、樂器專用記譜 |
| `EvaluationReport` | 流程測試與 benchmark 結果 | 資料集版本、指標、門檻、結果、程式／模型版本、產物位置 |

每個 artifact 都必須包含：

- `artifact_id` 與內容雜湊。
- `schema_version`。
- 上游 `source_artifact_ids`。
- 產生器、模型、參數與程式版本。
- 建立時間及執行環境。
- 成功、低信心、失敗或需人工確認的狀態。

### 2. 模式與樂器邊界

- `TrackIR.mode` 只能明確為 `transcription` 或 `arrangement`。
- 忠實轉譜事件必須包含可追溯到音訊或 stem 時間區段的來源證據。
- 編曲新增或改寫的事件必須標示為編曲決策，不能偽造音訊證據。
- 鼓、鋼琴與吉他使用各自的 TrackIR 語意：
  - 鼓：鼓件、擊打時間、力度與擊法。
  - 鋼琴：音高、onset／offset、voice、hand、pedal。
  - 吉他：音高、string、fret、tuning、capo、technique。
- 未知資訊必須表示為 `unknown` 或低信心，不能以未揭露的預設值冒充偵測結果。

### 3. 版本化驗證資料

P0 必須建立一份可重現的 fixture manifest，至少包含：

- 人工產生且答案精確已知的合成音訊。
- 由 MIDI 或事件標註渲染的音訊及原始 ground truth。
- 有隔離軌真值的 drums、piano、guitar 多軌片段。
- 有 beat、downbeat、meter、段落及樂器存在標註的混音片段。
- 目標樂器缺席、低音量、局部出現與被其他樂器遮蔽的負向／邊界案例。
- 合法授權資訊、資料切段、checksum、標註版本與用途限制。

資料集必須固定版本。新增或修正資料時建立新版本，不得直接改動已發布 benchmark 的內容。

### 4. 評估器與流程測試報告

每次流程測試必須輸出機器可讀的 `ProcessTestReport`，至少包含：

- `test_case_id`、輸入 checksum、fixture／dataset 版本。
- 執行的 stage、程式、模型、參數及 artifact schema 版本。
- 開始時間、結束時間、執行環境與產物路徑。
- 指標名稱、實際值、通過門檻及通過／失敗狀態。
- 失敗原因與是否需要人工確認。
- 是否包含人工修正；自動 benchmark 結果不得混入人工修正。

## P0 要驗證的內容

### A. Schema 契約驗證

每一種 artifact 都必須執行：

1. 建立有效 artifact。
2. serialize 成標準交換格式。
3. 使用 schema 驗證。
4. deserialize。
5. 比較前後語意是否一致。

必備失敗案例：

- 缺少必要欄位。
- 欄位型別錯誤。
- 非法 enum 或狀態轉換。
- 時間、sample rate、音高或信心值超出合法範圍。
- 不支援的重大 `schema_version`。
- 上游 artifact ID 不存在或 artifact 型別不相容。
- 內容已改變但 checksum 未更新。

**通過條件**：有效案例 100% round-trip 成功；無效案例 100% 被拒絕且回傳結構化錯誤。

### B. Schema 版本相容性驗證

- 同一 major version 的新增選填欄位，不得破壞既有 reader。
- 不支援的新 major version 必須明確拒絕，不能靜默忽略。
- migration 必須保留原始 artifact，產生新 artifact ID 並記錄遷移來源。
- migration 前後的音樂語意必須相同；允許差異需明列在 migration 規格中。

**通過條件**：支援的版本組合 100% 通過；不支援版本 100% 明確失敗；migration 來源鏈完整率 100%。

### C. 來源追蹤驗證

建立最小完整鏈：

```text
SourceMedia
  → CanonicalAudio
  → SongAnalysis / StemSet
  → TrackIR
  → NotationIR
  → 最終輸出與 EvaluationReport
```

驗證內容：

- 可由任一最終 artifact 反查所有直接與間接上游。
- 每個 ID 對應的內容 checksum 正確。
- 任一上游內容、模型或參數改變時，下游不得誤用舊快取。
- 刪除、替換或偽造一個上游 ID 時，完整性檢查必須失敗。
- `transcription` 事件有真實音訊證據；`arrangement` 事件有編曲決策紀錄。

**通過條件**：合法來源鏈完整率 100%；被破壞的來源鏈 100% 被偵測；跨模式誤標 0 件。

### D. Fixture 完整性與可重現性驗證

- manifest 中每個檔案的 checksum 必須吻合。
- 每個 fixture 必須有唯一 ID、版本、授權資訊、用途及 ground truth。
- 相同 fixture、程式版本、參數與 seed 重跑，必須產生語意相同的 artifact。
- ground truth 時間單位、座標原點、音高標準及樂器 taxonomy 必須明確。
- fixture 缺檔、checksum 不符、標註版本不相容時，benchmark 必須停止，不能跳過後宣告成功。

**通過條件**：fixture 完整性 100%；相同條件重跑的語意一致率 100%；任何資料缺損都會使該次 benchmark 明確失敗。

### E. 評估器正確性驗證

每個評估器至少使用以下控制答案測試：

| 控制答案 | 預期結果 |
| --- | --- |
| 與 ground truth 完全相同 | 取得該指標的滿分或理論最佳值 |
| 所有事件固定偏移且超出容差 | onset／時間相關分數顯著下降 |
| 刪除部分事件 | recall 下降，precision 不應被錯誤處罰 |
| 加入多餘事件 | precision 下降，recall 不應被錯誤提高 |
| 將音高或鼓件分類替換 | 對應類別與音高指標下降 |
| 空答案對空 ground truth | 依指標規格回傳明確定義值，不得 NaN 或 crash |
| 空答案對非空 ground truth | recall 為 0，報告仍可完整產生 |

另外必須驗證：

- 邊界時間剛好等於容差時的包含規則。
- 一對多、多對一事件 matching 不會重複計分。
- micro、macro 與 per-class 指標使用相同且有文件記錄的定義。
- 評估器版本與容差會寫入 `EvaluationReport`。

**通過條件**：所有控制答案均得到預期結果；數值誤差落在 fixture 指定容差內；不得出現未處理的 NaN、Infinity 或除以零。

### F. ProcessTestReport 驗證

- 成功與失敗的流程都能產生報告。
- 報告引用的 input、artifact 與 log 必須存在且 checksum 正確。
- 實際值低於門檻時，狀態必須是失敗。
- 缺少指標、門檻、版本或失敗原因時，報告本身驗證失敗。
- 自動 benchmark 若使用人工修正 artifact，必須拒絕或明確隔離成不同評估類別。

**通過條件**：報告 schema 測試 100% 通過；刻意製造的低分案例 100% 被判定失敗；人工與自動結果混用 0 件。

### G. P0 最小端到端驗證

P0 不要求模型已具備正式轉譜能力，但必須以 deterministic stub 跑通 artifact 流程：

1. 載入一個版本化 fixture。
2. 建立 `SourceMedia` 與 `CanonicalAudio`。
3. 建立 stub `SongAnalysis` 與 `StemSet`。
4. 分別建立一個 `transcription` TrackIR 與一個 `arrangement` TrackIR。
5. 轉成 `NotationIR`。
6. 產生 `EvaluationReport`。
7. 由最終 artifact 反查完整來源鏈。

必備負向流程：

- 目標樂器不存在時，忠實轉譜不得產生正式 TrackIR。
- 上游狀態為失敗或低信心待確認時，下游不得被誤標為成功。
- 將 arrangement TrackIR 傳入只接受 transcription 的流程時必須被拒絕。
- 修改任一上游內容後，舊下游 artifact 必須失效。

**通過條件**：兩種模式的合法 stub 流程皆成功；所有負向流程皆在正確邊界停止；來源追蹤、版本與報告欄位完整率 100%。

## P0 完成門檻

只有同時符合以下條件，P0 才能宣告完成並進入 P1：

- 所有 artifact schema 已版本化並有文件。
- schema 正向、負向與 round-trip 測試全部通過。
- 模式與樂器專用資料邊界已被契約測試固定。
- fixture manifest、checksum、授權與 ground truth 完整。
- 評估器已通過完美、偏移、漏報、誤報、錯類及空輸入控制測試。
- `ProcessTestReport` 可重現每次驗證的輸入、版本、指標、門檻與結果。
- deterministic stub 的最小端到端流程與全部負向流程通過。
- 自動驗證可由單一命令在乾淨環境執行，失敗時回傳非零 exit code。
- CI 保存測試報告與關鍵 artifact，且無測試被靜默跳過。

P0 的驗收證據必須是可執行測試、版本化 fixture、機器可讀報告與可追溯 artifact；只有文件或展示畫面不足以宣告完成。
