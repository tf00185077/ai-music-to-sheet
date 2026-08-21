# Stem 分離到 MIDI／音符轉錄的 Ground-truth 基準資料集

> 查核日：2026-08-21。只引用資料集作者／維護者的官方頁面、論文、儲存庫或授權紀錄。此處的「可商用」只描述資料集宣告，非法律意見；未明示授權者不可推定可重散布或商用。

## 結論

沒有一個公開資料集同時完美涵蓋「真實流行歌曲四 stem」與「所有 stem 的對齊 MIDI」。本專案現階段應採兩個互補、固定且有時限的小基準，而不是立即建立大規模研究：

1. **[Slakh2100-redux](https://zenodo.org/records/4599666) 8 個 30 秒片段**：從官方 test split 中，依 track ID 排序後取第一批同時含 drums、bass 與至少一種 pitched instrument 的 8 首；評估分離後 MIDI／`NoteEvents` 的端到端準確率。它是合成音訊，但逐 source MIDI 就是生成音訊所用的真值。
2. **[MUSDB18-HQ](https://sigsep.github.io/datasets/musdb.html) 8 個 30 秒片段**：從官方 test split 依 track ID 排序取前 8 首，評估真實流行音樂的 vocals、drums、bass、other 分離品質。它沒有 MIDI，因此只報音訊分離指標。

兩組各只評分 `00:05–00:35`，總評分音訊 8 分鐘；清單與規則必須在第一次跑分前固定。這能回答兩個不同問題：真實流行音樂的 stem 是否分得好，以及分離結果是否真的改善後續 MIDI。若把兩者強行合成一個分數，反而會掩蓋失敗發生在哪個階段。

**[URMP](https://labsites.rochester.edu/air/projects/URMP/URMP_doc.pdf)** 是很好的補充：它有真實演奏、混音、逐樂器乾淨參考音訊、MIDI 與逐音符標註，官方文件也說明混音是逐軌直接相加。不過其內容主要是弦、木管與銅管二至五重奏；只有在 API 與免費軟體都能輸出相同的古典樂器 stem taxonomy 時，才能拿來公平比較。若兩邊只提供 vocals／drums／bass／other，URMP 不應作首輪主基準。

若後續確定兩個供應者都支援弦／木管／銅管，再追加固定的 **8 個 URMP 30 秒評分片段（總計 4:00）**：從每個完整 URMP 檔輸入給兩條管線，但只評分 `00:05–00:35`，避開切段邊界。清單不可在跑分後更動：

| URMP ID | 編制 | 用意 |
|---|---:|---|
| `01_Jupiter_vn_vc`、`03_Dance_fl_cl` | 二重奏 | 弦／木管、低與高重疊 |
| `17_Nocturne_vn_fl_cl`、`19_Pavane_cl_vn_vc` | 三重奏 | 混合音色與不同音域 |
| `24_Pirates_vn_vn_va_vc`、`28_Fugue_fl_ob_cl_bn` | 四重奏 | 同族弦與同族木管的困難分離 |
| `38_Jerusalem_vn_vn_va_vc_db`、`42_Arioso_tpt_tpt_hn_tbn_tba` | 五重奏 | 弦與銅管的最高 source 數 |

URMP 子集是固定的補充回歸集，**不是**對真實流行歌曲泛化能力的宣稱。首次比較完成後，才以未調參的方式追加另一個已預先固定的 URMP 8 片段 hold-out；不要在此輪混入訓練資料或反覆挑選「好看的」案例。URMP 有 44 個二至五重奏、13 種樂器；其官方文件列出上述曲目、長度、逐軌 WAV、MIDI、frame-F0 與 note-level 標註。

## 資料集判讀

| 資料集 | 音訊／規模／樂器 | stems 與符號真值 | 取得與權利 | 能評估的階段 |
|---|---|---|---|---|
| **[Slakh2100-redux](https://zenodo.org/records/4599666)** | **合成**：以樣本式虛擬樂器渲染；2,100 首、145 h、187 patches／34 類，至少含鋼琴、吉他、鼓、貝斯；mono 44.1 kHz FLAC。 | 每首 mix、可變數量的逐 source 音訊與「實際用來合成」的逐 source MIDI；是完整的分離＋多樂器 AMT 真值。原始切分有 MIDI 重複，官方 redux 將其放進 `omitted`，AMT 不可使用。 | 105 GB；官方專案宣告 **CC BY 4.0**，可商用但必須署名。 | **分離、轉錄、端到端**；大而合成，適合後續擴展／回歸，不是本輪真實音訊 MVP。 |
| **[URMP](https://labsites.rochester.edu/air/projects/URMP/URMP_doc.pdf)** | **真實但受控**的古典二至五重奏；44 首、13 樂器；48 kHz／24-bit mono。 | mix 是個別演奏軌的直接相加；有各樂器 WAV、MIDI/PDF、逐 frame F0 與逐音符 onset/pitch/duration。 | 官方請下載者填登記表；文件**未載明內容授權**，商用、重散布前應取得書面確認。 | **分離、轉錄、端到端**；本專案首選。 |
| **[Bach10](https://labsites.rochester.edu/air/datasets/Bach10%20Dataset_v1.0.pdf)** | **真實但受控**：10 首四部 Bach chorale；固定為 violin／clarinet／saxophone／bassoon。 | ensemble 與四個 part WAV、MIDI、人工 audio–MIDI 對齊、frame pitch、note 真值；文件本身也列 BSS_EVAL 作分離評估。音高／音符由 isolated tracks 的 YIN 後再人工修正，非直接 MIDI capture。 | 免費下載／追蹤表；**未明示授權**，不得假定可商用或重散布。 | **分離、轉錄、端到端**；可作 URMP 前的 10 曲 smoke test，但編制太固定，不單獨作主基準。 |
| **[GuitarSet v1.1](https://zenodo.org/records/3371780)** | **真實** acoustic guitar；360 個近 30 秒片段，6 位演奏者、5 種風格。 | 麥克風、6 聲道 hex pickup、去干擾 hex；每弦 JAMS `midi_note`、pitch contour、string/fret、beat/tempo/chord。每弦訊號可作「弦」參考，但不是一般多樂器樂團 stems。 | 7.5 GB，現行紀錄為 **CC BY 4.0**（可商用、須署名）；勿誤用舊版 1.0.1 的 CC BY-NC 版本。 | **轉錄、端到端**；可有限度作六弦分離。很適合日後吉他／TAB 產品分支。 |
| **[MAESTRO v3](https://magenta.withgoogle.com/datasets/maestro)** | **真實** Disklavier 鋼琴；1,276 場、198.7 h、古典；44.1–48 kHz stereo。 | 高精度 MIDI capture 與 WAV 約 3 ms 對齊，含 velocity 與三種 pedal；v3 移除了含弦樂四重奏伴奏的 6 段，故為純鋼琴，**沒有 source stems**。 | 101 GB 壓縮檔；**CC BY-NC-SA 4.0**，不可商用。 | **轉錄**（及無分離需求的端到端 audio→MIDI）；不能比較 stem 分離。 |
| **[MusicNet](https://zenodo.org/records/5120004)** | **真實**古典錄音；330 段、約 34 h、11 種樂器。 | mix WAV、CSV note 時間／樂器／節拍位置與建標用 reference MIDI；**無 stems**。標籤由 score–recording DTW 產生、音樂家驗證，官方估計約 4% 標註錯誤，非演奏捕獲 MIDI。 | 11.1 GB；Zenodo 現行紀錄 **CC BY 4.0**，但逐錄音來源／權利仍須讀 metadata。 | **轉錄、端到端**；可做較廣的真實多樂器 AMT，但不衡量分離。 |
| **[MUSDB18-HQ](https://sigsep.github.io/datasets/musdb.html)** | **真實商業／錄音室音樂**；150 首約 10 h，stereo 44.1 kHz。 | 4 個聚合 stems：drums、bass、vocals、other；HQ 為無壓縮 WAV，和 MUSDB18 內容相同。**沒有 MIDI／逐音符標註**。 | 22.7 GB；須申請 Zenodo 存取、僅 academic use，且權利按歌曲混合，非單一可商用授權。 | **分離**；不能當 downstream MIDI ground truth。 |
| **[MedleyDB／2.0](https://medleydb.weebly.com/description.html)** | **真實**多軌錄音；122 + 74 = 196 tracks，流行、爵士、古典、世界音樂等。 | 44.1 kHz/16-bit mix、processed stems、raw tracks；有樂器 activity、stem ranking、主旋律／stem F0。108 個原始 tracks 有 melody annotation，但它是連續 F0，**不是全聲部 MIDI／note-event 真值**；部分 stems 可能 bleed。 | **CC BY-NC-SA**、音訊下載需快速許可；不可商用。 | **分離**；另可評估主旋律 F0，不可作完整轉錄的金標。 |

## 固定執行與指標

兩管線必須使用同一個 mix、相同切段／重採樣、相同 downstream transcriber、相同音符正規化（秒、MIDI pitch、onset、offset）與相同樂器對應；只替換「分離」實作。對每個具有 note truth 的 target track（首輪是 Slakh，選配是 URMP）依序輸出：預測 stem、由該 stem 轉出的 MIDI／`NoteEvents`，並保留模型及資料版號。

1. **分離（有參考 stem 才算）**：每個 target 音軌計算 **SI-SDR（dB）**與 **BSS Eval v4 SDR（dB）**，以 source × case 的 median 與 macro median 報告（不要把長片段或多音符 source 權重放大）。可用 MUSDB 官方列出的 [museval／BSSEval v4](https://github.com/sigsep/sigsep-mus-eval)；URMP 與 Bach10 可直接對各樂器 WAV，Slakh 可直接對各 source。另列出 silent／近靜音軌的排除規則與數量。
2. **轉錄（每個 target track）**：以 [mir_eval transcription 規格](https://mir-eval.readthedocs.io/latest/api/transcription.html) 統一匹配，先報 `onset` P/R/F1（相同 MIDI pitch、onset 誤差 ≤ **50 ms**），再報 `onset+offset` P/R/F1（再要求 offset 誤差 ≤ `max(50 ms, 20% × 參考音長)`）。以所有片段合併的 micro P/R/F1 為主數字，並列 case macro-F1、每種編制與每個樂器的結果；不要只報平均值。
3. **端到端歸因**：同時把同一轉錄器餵入「reference stem」與「pipeline stem」。前者是轉錄器上限，兩者 F1 的落差才可歸因於分離；再以 mix 直接轉錄作無分離 baseline。如此可回答「分離較好是否真的讓 MIDI 較好」。

### 重要限制

將兩個**預測** MIDI 檔互相比較（edit distance、重疊或 F1）只能量到兩模型的**一致／不一致**，不能量到正確性：兩者可能同錯，也可能其中一個較正確卻不一致。只有對上述 MIDI／note-event ground truth 的匹配，才可稱 precision、recall 或 F1 為準確率。

## 後續，而非本輪範圍

若首輪兩個 8 片段基準穩定，再新增各自獨立的驗證軌：

- **擴大 Slakh2100-redux 官方 test split、排除 `omitted`**：檢查大規模、多類樂器的合成上界與 regression；
- **URMP 固定 8 片段**：只在兩個供應者支援可對應的弦／木管／銅管 stem 時，檢查真實演奏的分離與 MIDI 端到端表現；
- **GuitarSet 或 MAESTRO 的官方 test split**：分別檢查吉他細粒度 note／TAB，或真實鋼琴轉錄。

MUSDB18-HQ、MedleyDB 則保留給純分離比較；不要把其輸出的預測 MIDI 互比後誤標為轉錄正確率。
