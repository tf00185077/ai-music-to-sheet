# 成熟商用音訊 Stem Separation 產品研究（2026-08-21）

## 結論

本文件只收錄可實際取得、**非開源**且有第一方產品頁、手冊或 API 文件佐證的方案；資料核對日為 2026-08-21。先把三類產品清楚拆開：

1. **可嵌入服務的 API/SDK**：可成為本專案的「上傳音檔 → 非同步分離 → 取得 stem」後端。首選短名單是 **Music AI、AudioShake、LALAL.AI、Fadr**；其中 Fadr 額外直接給和弦／MIDI，最貼近「audio-to-sheet」，Music AI 則能把 stems、和弦、beats、轉錄串成同一 workflow。
2. **終端使用者 App／Web**：Moises、BandLab Splitter 等很適合人工驗收、競品比較或讓使用者自行處理；其訂閱不等於可把分離能力轉售或嵌入本專案。
3. **DAW／DJ 功能**：設計目的是本機編曲、修復或現場混音，通常把結果留在 project／資料庫，而非輸出供本專案呼叫的 API。可作品質基準與人工處理路徑，不能取代產品後端。

「本機／離線」指推論在使用者裝置完成；「雲端」指檔案或可讀 URL 必須送往供應商。未有第一方明說離線的桌面軟體，本文不把「有桌面 App」誤標為離線。

## 對本專案的建議

| 優先序 | 建議 | 原因與限制 |
|---|---|---|
| 1 | **Music AI API** 做可程式化 MVP／production adapter | API、Python/Node SDK、jobs、暫存簽名上傳與結果 URL 都已公開；同平台也有 chords、beats 與轉錄模組，減少多家串接。雲端與每分鐘計費，必須在後端保管 API key、刪除 jobs，並做資料保留／DPA 審查。|
| 2 | **Fadr API** 做「快速原型／音樂轉譜特色」候選 | 一次主分離即回 vocals/drums/bass/melodies/instrumental，並產生旋律／人聲／bass MIDI、和弦 TXT/MIDI、key 與 tempo；這是本題目最直接的 sheet music 輸入。公開文件仍以 2023 API 為主，正式採用前應以測試帳戶重新驗證配額、SLA、商業再散布權與輸出品質。|
| 3 | **AudioShake**（需要 sales/onboarding） | 有 batch API、on-device real-time SDK、Widget，且官方持續遷移至較能一 task 多模型的 Tasks API；適合權利人、目錄批次與日後行動端。價格不公開，採購／資料條款是前置條件。|
| 4 | **LALAL.AI API** | 明示能嵌入 SaaS／內部 pipeline，包含 OpenAPI；對「只要高品質音訊 stem」的整合很直接。公開 consumer 方案與 API／enterprise 採購需分開看；不可把其 Desktop/VST 的離線 Lyra 當作可嵌入 SDK。|

所有選項都只會得到**估計 stem**，不是原始 multitrack，也不保證可直接轉成正確樂譜。產品介面應將分離與音高／節奏／和弦辨識拆成可重試的 stages，保存 `provider/model/version/stem_type`，讓使用者下載音訊及校正 MIDI／樂譜。另應要求上傳者確認有處理錄音與作品的權利；這是產品與著作權風險提醒，不是法律意見。

## 1. 消費者 Web／Mobile／Desktop App（不可當作 API 授權）

| 產品 | 平台／部署 | 使用流程、stem 與輸出 | 整合與計費模式 | 成熟度與本專案適配 |
|---|---|---|---|---|
| **Moises** | Web、iOS/Android、桌面 App；第一方 DAW integrations 明示要網路連線，故分離屬雲端服務。 | 上傳裝置檔或 public URL → 選擇分離 → 處理 → 音量／solo／mute → 匯出。免費有 2（vocals/instrumental）或 4（vocals/drums/bass/other）軌；Premium／Pro 可選 vocals、lead/backing vocal、guitar 類、piano/keys、strings/wind，Pro 可做 drum-kit 及 dialogue/soundtrack/effects；Web/Desktop 可匯出 MP3、M4A、付費 WAV，分離軌可打 ZIP。官方亦有 chord、key、tempo 工作流。參見 [分離選項](https://help.moises.ai/hc/en-us/articles/360010972019-Which-instruments-can-be-separated-on-Moises)、[輸出說明](https://help.moises.ai/hc/en-us/articles/360013691720-How-do-I-export-my-file) 與 [custom upload](https://help.moises.ai/hc/en-us/articles/19247459645724-How-do-I-separate-my-tracks-using-the-Custom-Upload-on-the-Mobile-App)。 | 免費限額 + Premium／Pro 訂閱；產品頁明示免費每月有有限 uploads。另有公開的 [Developer Platform stem endpoint](https://developer-legacy-stage.moises.ai/docs/media/stems-separation)，可 POST `inputUrl`、輪詢 `/api/media/:id`；但網域名為 `developer-legacy-stage`，不要在未取得 Moises 正式合約／SLA 前當作穩定 self-service API。 | 官方主站宣稱逾 7,000 萬音樂人使用，且 2025 help 仍更新；是很成熟的手動品質基準。對本專案：可用於人工測試；若 Moises 書面確認 API，才加成 vendor adapter。|
| **LALAL.AI** | Web、Windows/macOS/Linux desktop、iOS/Android、VST；雲端 Andromeda 與 Desktop/VST 的 **Lyra**（官方稱本機、無上傳、可離線）並存。 | Web upload audio/video → preview → full split → download；雲端 Stem Splitter 可逐類取得 vocals、instrumental、drums、bass、piano、acoustic/electric guitar、synth、strings、wind（最多 10 類）；輸出可保持原格式或 MP3/WAV/FLAC/OGG/AAC/AIFF。Lyra 支援 7 stems（vocals/instrumental/drums/bass/piano/兩種 guitar）。見 [Stem Splitter 說明](https://www.lalal.ai/stem-splitter/) 和 [2026 Media Kit](https://www.lalal.ai/media-kit/)。 | Starter（試用）、訂閱及 top-up 分鐘；官方頁公開 consumer 方案。**同時有正式 API**，但它屬下一節的雲端服務，不是本機 Lyra SDK。 | 官方 changelog 在 2026 持續發布、並在 2025 更新 Andromeda、2026 加入 Lyra/Lynx，訊號強。若用 API，很適合作為純音訊分離供應商；若用離線桌面版，只適合個人工作流程。|
| **BandLab Splitter** | BandLab Web、mobile、Studio 內功能；雲端型使用者服務。 | 匯入歌曲後分離、在 Studio 使用，下載 stems 或 MIDI。官方已說明 4-stem 基本組、另有 guitar/piano/strings/backing-vocal 等較多 stem，並把匯出進度／MIDI export 放在更新中；詳見 [Splitter 功能更新](https://blog.bandlab.com/splitter-updated-features/) 與 [Membership 說明](https://blog.bandlab.com/bandlab-membership/)。 | 基本免費、Membership 訂閱解鎖更多 stems、速度、Studio 功能；官方沒有公開的第三方 stem-separation API／SDK。 | 成熟的免費手動替代方案，強項是 MIDI 與 Studio 協作；不適合作為本專案伺服器依賴。|
| **Fadr** | Web app（雲端）；另有 VST3/AU Stems Plugin，會錄取 DAW 音訊並上傳 Fadr 後再回傳結果，**不是本機推論**。 | Web upload → stems／MIDI／remix；免費 Basic 為 vocals/melodies/drums/bass，Plus 有 lead/background vocals、piano/guitars/strings/wind、kick/snare 等合計 18 類及 WAV。官方 [Plus 頁](https://fadr.com/plus) 列有每類與一小時 upload；Plugin 文件明述它把錄得音訊上傳伺服器再取得四 stem。 | Basic 免費；Plus 公開為月／年訂閱（價格可能變動，請以 [官方 Plus 頁](https://fadr.com/plus) 為準）。**公開 REST API 存在**，詳見下一節。 | 對「音檔轉樂譜」特別有價值：其 API 主 stem task 能回 MIDI、chord progression、key/tempo。2025 文件入口及 Plus 頁仍在運作；仍需以帳戶實測 2023 endpoint 的當前可用性。|

## 2. 桌面專業 DAW／修復工具（僅本機工作流程）

這些是已授權軟體功能，不是雲端 API，也沒有第一方公開文件允許把內建 separator 以第三方 SaaS 身份呼叫。音檔應由操作人匯入 project、完成分離、再由正常 DAW export／bounce 輸出。

| 工具 | 平台／本機性與輸入流程 | stem、輸出與計費 | 現況／適用性 |
|---|---|---|---|
| **Apple Logic Pro Stem Splitter** | macOS，僅 M1+ Apple silicon（非 Intel/Rosetta）。在 audio region 上選 `Processing > Stem Splitter`，選 preset／個別 stem 或 submix，套用後建立 summing stack 與可編輯 audio regions；見 [Apple 使用手冊](https://support.apple.com/guide/logicpro/extract-vocal-instrumental-stems-stem-lgcp61bae908/mac)。文件描述在 Mac／project 內處理，未要求網路。 | vocals、drums、bass、guitar、piano、other；可用正常 Logic audio export/bounce 產出檔案。隨付費 Logic Pro 授權／Apple Creator Studio 取得，非按分鐘 API。 | 最新線上手冊已列 Logic Pro 12.3，屬成熟本機 DAW 功能。適合 macOS 操作員人工修整與驗收；**不提供本專案後端 API**。|
| **Ableton Live Suite 12.3+** | macOS/Windows；官方明說模型為 local use，無網路與外部工具也可分離。從 Browser 或 Session/Arrangement clip 選 `Separate Stems to New Audio Tracks`，選 High Speed／High Quality；12.4 起可只分離 clip 的選定片段。 | 固定 vocals/drums/bass/others；產出的 stem 一律 44.1 kHz／16-bit WAV，成為普通 clips 後可 edit/export。僅 Live **Suite** 12.3 起含有，非 Standard/Intro/Lite；為 Suite 授權／升級，無 API。官方亦明示其演算法來自 Music AI，見 [FAQ](https://help.ableton.com/hc/en-us/articles/23730994755996-Stem-Separation-in-Ableton-Live-FAQ) 與 [手冊](https://www.ableton.com/en/live-manual/12/stem-separation/)。 | 2026 手冊／FAQ仍更新，且可用於低延遲本機工作。不等於可直接取得 Music AI 的商業授權；產品端應直接談 Music AI。|
| **FL Studio** | Windows/macOS DAW；將混音音檔在 FL 中分離，所需 Stem Separation 是可下載的 optional feature，官方另提供下載後用於離線電腦的說明，故可視為本機 engine（初次安裝／更新仍需取得該套件）。 | vocals、drums、bass、instrument/music，進入可編輯 channel／mixer tracks 再渲染。Producer Edition 以上包含；官方 pricing 也標示為此級別功能，採 DAW 授權與 lifetime updates，沒有 server API。見 [產品功能頁](https://www.image-line.com/fl-studio/features)、[版本比較](https://www.image-line.com/fl-studio/pricing?t=3) 與 [2026 changelog](https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/WhatsNew.htm)。 | 21.2 在 2023 導入；2026-03 changelog 仍含 stem extraction 改進，為活躍成熟功能。可當 Windows DAW 人工處理選項，非 app integration。|
| **Steinberg SpectraLayers Pro 13** | Windows/macOS 的頻譜修復／編輯器，對選取 layer 施行 `Unmix Song`，直接生成可在 layer 中檢查／修復的非破壞性結果；是本機專業編輯流程。 | Pro 的 Unmix Song 可分 vocals/drums/bass/guitar/piano/sax & brass/other，並有 Fast/Balanced/High；結果以 layer 編輯，使用一般 export 輸出。付費 Pro 授權；Elements 的功能較少，沒有 API。見 [Unmix Song 文件](https://download.steinberg.net/downloads_software/SpectraLayers_12/help/Pro/_unmix_song.html) 與 [SpectraLayers 13 公告／功能頁](https://www.steinberg.net/spectralayers/)。 | 12 已在 2025 提升 Unmix Song、drums、instrument；13 為當前世代，適合要人工修復 bleed／噪聲的高價值音檔，不適合無人值守批次 SaaS。|
| **RipX DAW / RipX DAW PRO** | Windows/macOS 本機 AI DAW；匯入後「rip」成可逐音符／layer 編輯的內容，支援 MIDI/export 與外部 sample editor 整合。首次線上授權，官方也提供 PRO offline activation；推論在本機，GPU 可加速。見 [下載與系統需求](https://sales.hitnmix.com/downloads)。 | 宣傳為 6+ stem separation，可將 audio/MIDI 作為 DAW 工作成果 export；採付費授權／版本，不是 API。2025 v8 的 release notes 明載 separation、note recognition、MIDI export、CUDA/Apple Silicon 改進：[變更紀錄](https://hitnmix.com/changes/)。 | 對「先分離、再人工修正音符而出譜」是所有桌面項中最接近的工具；但桌面 license 不能取代嵌入式 SDK。|
| **iZotope RX 12 Music Rebalance** | Windows/macOS 的 RX standalone 與部分 DAW plugin/Audiosuite，離線或 real-time 都可用。把混音載入 RX → Music Rebalance → `Stem Split`；新 Stems View 可在各 stem 上套 RX 修復工具。 | vocals、bass、percussion、others，能在 Stems View 匯出 individual stems 或混合檔；RX Standard/Advanced 授權，非 API。官方明述 RX 12 重訓 neural nets、offline processing，以及 Music Rebalance 在 standalone／plugin 的位置：[功能頁](https://www.izotope.com/products/rx-standard)、[實作教學](https://www.izotope.com/en/learn/stem-separation-music-rebalance)。 | RX 12 於 2026-04 發行（[release notes](https://www.izotope.com/pages/release-notes/rx-standard)），最適合後製／修復已分離但有 artifacts 的高價案件，而非主動做開放上傳服務。|

## 3. DJ Stem 工具（即時操控，通常不交付獨立 master stems）

| 工具 | 平台／模式 | stem 與輸出／整合限制 | 本專案適配 |
|---|---|---|---|
| **Serato Stems（DJ Pro/Lite／Studio／Sample）** | 本機 real-time separation；觸發後會為檔案建立 `.serato-stems` 快取。官方 3.0.4 更新仍改善即時分離與分析速度：[更新說明](https://support.serato.com/hc/en-us/articles/6374404478223-Updating-Stems-in-Serato-DJ-Pro-Lite)。 | acapella/melody/bass/drums（產品情境另稱 instrument）；主目標是 mute/solo、DJ／sampling。Studio 可 export **project deck** stems，但不要把這和「原曲分離後的獨立 WAV API」混為一談；沒有公開 service API。見 [Studio Stems 手冊](https://support.serato.com/hc/en-us/articles/6214861307663-Misc-Stems)。 | 適合 DJ 即時表演與人工取樣，不適合作為上傳音檔轉樂譜的後端。|
| **rekordbox Track Separation** | rekordbox performance mode 的本機即時功能，受電腦 RAM／buffer／multithread 影響，並可映射至相容 DJ hardware。 | VOCAL、DRUMS、INST 三部分，可 mute/solo、PART ISO 音量、PART FX；需支援 plan 或 Hardware Unlock，且 streaming tracks 有限制。第一方 FAQ 定義與需求見 [Track Separation FAQ](https://rekordbox.com/en/support/faq/trackseperation-6/)。 | 現場分部控制，非檔案 export API。適合作為 DJ 競品參考，排除於本專案產品架構。|
| **VirtualDJ Stems 2.0** | Windows/macOS 本機；現代 GPU/Apple Silicon 可高品質即時，較弱硬體建議在非演出時先 prepare 並存 saved stem 檔，檔案約為原始的 4 倍。 | 可控制 vocals、instruments、bass、drums（並含 kick／hi-hat 等 DJ 控制），提供 performance pads、EQ、stems FX；用途是即時 remix。官方 [Stems 2.0 手冊](https://virtualdj.com/manuals/virtualdj/interface/stems2.html) 清楚說明預先運算、fallback 與本機硬體；VirtualDJ 2026 下載仍列該功能。 | 可能是 DJ 本機離線模式最成熟的一種，但快取不是面向使用者的交付／API；不納入 SaaS 後端。|
| **Algoriddim djay Neural Mix** | macOS/iOS/Windows/Android DJ app 的 real-time separation，能在支援 controller 上直接操作。 | 可選 2 stems（instrumental/acapella 或 percussive/tonal）、3 stems，或 4 stems（drums/bass/harmonic/vocals），各可 mute/solo/level；只作 mixing，未見官方提供下載分離檔或第三方 API。見 [Neural Mix tracks](https://help.algoriddim.com/user-manual/djay-ios/neural-mix/tracks)、[硬體支援](https://help.algoriddim.com/topic/hardware/using-neural-mix-on-supported-controllers) 和 [djay Pro 功能頁](https://www.algoriddim.com/djay-pro-mac)。 | 即時 DJ UX 很成熟，但不輸出可供樂譜 pipeline 消費的 stem assets。|

## 4. 可嵌入的開發者／企業 API、SDK

| 供應商 | 部署與輸入流程 | 可用 stem／輸出與整合 | 官方公開計費與成熟訊號 | 對本專案的實際判斷 |
|---|---|---|---|---|
| **Music AI API** | **雲端非同步 jobs**。以 public `inputUrl`，或 `GET /upload` 取得暫時簽名 URL → PUT 檔案 → `POST /job` 指定 workflow → 查 job status／取得 result URLs → `DELETE /job`。第一方 [Quick Start](https://music.ai/docs/getting-started/quick-start/) 與 [API reference](https://music.ai/docs/api/reference/) 均有完整流程。 | 可選 musical stems（vocals/bass/drums/guitars/strings/piano/keys/wind/other），也有 drum、guitar parts、lead/back vocals、instrumental、cinematic dialogue/music/effects；可把 stems 與 beats、chords、lyrics/transcription 合成 workflow。官方有 Python、Node.js SDK 與 CLI/desktop client，**不是 on-device SDK**；參見 [API 產品頁](https://music.ai/platform/api/) 與 [Musical Stems module](https://music.ai/modules/stem-separation/musical-stems/)。 | 公開 pay-as-you-go／Professional／volume pricing；2026 官方 [價格頁](https://music.ai/pricing/) 逐分鐘列出各 stem module（勿把網站當成長期固定報價）。API 文檔最近仍更新，且 Ableton Live 12.3 使用 Music AI 演算法，是強採用訊號。 | **最平衡的首選**。抽象為 `upload/submit/status/download/delete`，將 chords、beats、transcription 也納入同一 job 或後續 job；避免在前端暴露 key 或直接把私人檔案 URL 設為永久公開。|
| **AudioShake** | Batch **cloud API** 可 upload asset → 建 task（指定 targets/models/format）→ webhook 或 poll → 下載 output assets。舊 Jobs API 文件仍可讀，但官方正遷移至 Tasks API，一個 task 能產生多模型 outputs；見 [Tasks migration](https://developer.audioshake.ai/migrating-from-jobs) 與 [開發者首頁](https://www.audioshake.ai/developer-home)。另有 **on-device real-time SDK**。 | 音樂 instrument stems（vocals/instrumental/drums/bass/other，以及更細的 instruments）、dialogue/music/effects、lyrics transcription/alignment；SDK 官方列 iOS/macOS、Windows、Android、Linux，亦有可嵌入 Web 的 Widget。見 [SDK/API 平台](https://www.audioshake.ai/developer-home) 與 [drums model](https://www.audioshake.ai/audioshake-models/drums-separation)。 | 無公開自助每分鐘價，需聯絡 sales；官方 2026 use cases 明示 API 與 SDK、batch 及 real-time 皆可用，為成熟企業級 offering。 | 需要低延遲／端側隱私或先做大型 catalog 的最佳候選，但 PoC 前先索取 SDK 的 platform、模型大小、離線授權、最低量、DPA 和重試計費。不要基於 legacy server-to-server docs 開新整合。|
| **LALAL.AI API** | 雲端 REST／OpenAPI v1；供應商產品頁明示把 stem splitting、noise reduction 整合到自己的 software/service，並給文件、code example、OpenAPI：[API 頁](https://www.lalal.ai/api/)。 | Stem splitting、noise／voice processing；適合後端 upload/job adapter（實際 upload/callback、速率／保留期依 API 文件與合約）。Desktop/VST 的離線 Lyra 是終端產品功能，**不是 API SDK**。 | consumer 方案為免費試用 + 訂閱／top-up，API／enterprise 取決於授權 package；另有 2026 changelog 持續維護（如 API 連結與本機功能更新）：[changelog](https://www.lalal.ai/changelog/)。 | 快速加入多種樂器音訊輸出的供應商候選；在採用前取得 API 價格、商業再散布、資料刪除、webhook／poll 限制的書面條款。|
| **Fadr API** | 雲端。Server 先取得 presigned upload URL、PUT 音檔、建 Asset、建立 stem task、約每 5 秒 poll，再以 presigned URL 下載；詳見官方 [stems tutorial](https://fadr.com/docs/api-stems-tutorial)。 | `main` 一次產生 vocals/drums/bass/melodies + instrumental，並產出 MIDI、chord TXT/MIDI、key、tempo；詳細 endpoint 說 main 會產生 vocal/drums/bass/melody MIDI，但 overview 頁對 drums 的敘述不一致，正式導入務必以測試輸出確認。後續 `vocal-stem`、`melodic-stem`、`drum-stem` 可細拆；[endpoint 規格](https://fadr.com/docs/api-endpoints) 載明任務狀態。 | 需 Fadr Plus；官方文件公開會員費與 API credit，並公開 Create Stem Task 的每分鐘費率，應以 [API billing](https://fadr.com/docs/api-billing) 當下頁面為準。技術 docs 有 2025 新入口但 core endpoints 標 2023，因此成熟且能用、**但必須先做 smoke test**。 | **最適合少量、快速驗證 audio-to-sheet**：先把它的 melody／vocal/bass MIDI、和弦、key、tempo 匯入本專案，再以演算法校正節奏／notation。不要將其 MIDI 視為正確成譜保證；先測多曲風、長音檔與付費用量。|
| **Gaudio Developers（Gaudiolab）** | 雲端 developer API；以選取的模型／stem 提交音檔處理。 | 官方 developer pricing 資源列 Music HQ 的 vocals/drums/bass/electric guitar/piano/others，並另有 lyrics line sync；屬 API 而非消費者 GUI。見 [官方模型與 pricing](https://www.gaudiolab.com/developers/resources/pricing)。 | credit／每分鐘、按所選 stem 計費；精確金額依官方頁與商務方案變動。 | 值得列為第五家技術評估對象，尤其需要歌詞行級時間資訊時；公開整合文件與市場採用訊號較前三者少，先做 API access、輸出格式與商用條款的 PoC。|
| **Moises Developer Platform（條件式）** | 文件化的 URL input + `POST /api/media` + GET status 的雲端 API，具有 vocals/accompaniment、4-stem 及 guitar/strings/piano/background vocals 模式：[官方 endpoint](https://developer-legacy-stage.moises.ai/docs/media/stems-separation)。 | 能回 stem list；Moises consumer app 本身也有 chord／tempo 工作流。 | 文檔網域明帶 `legacy-stage`，且公開頁未能取代 API 商用合約、SLA 或 pricing；因此不在首選一般可自助 API。 | 只在 Moises 確認此帳戶可正式上線、資料處理與價格可接受後，才把它列入供應商 adapter；否則採用已明確生產化的 Music AI／AudioShake／LALAL／Fadr。|

## 導入前共同檢核表

- 把廠商 API key 僅放在 server secret；瀏覽器只向本專案取得短期 upload／job token，不能直連付費廠商 API。
- 上傳採用 object storage／signed URL；一律做非同步 job、指數退避 poll 或 webhook、可重試的 idempotency key、超時／取消與自動刪除。不要在 HTTP request 期間等待長音檔推論。
- 保存原檔、輸出、錯誤與 vendor job 的最短保留期；確認每一家對 uploads、輸出 URLs、訓練用途、跨境處理、DPA、刪除請求與 model version 的規則。
- 用一組有權使用、涵蓋人聲、鋼琴、吉他、鼓、現場錄音、古典／電子、mono／stereo 的測試曲；以主觀聽感、BLEED、onset／pitch error、MIDI/和弦準確度及每分鐘端到端成本比較，而非只看 marketing 品質聲明。
- 讓使用者選擇「快速四 stem」與「樂譜導向（melody/vocal/bass + chords）」；後者應選 Fadr 或 Music AI 相應 workflow，而不是 DJ 產品的即時 mute。

## 一手來源範圍與限制

上述連結均為產品供應商的官方網站、官方 help、手冊、release notes 或 developer docs；沒有以評測、媒體報導或第三方 benchmark 作為事實依據。價格、配額、模型和支援的 OS／DAW 會變動，所列「公開計費」是核對日可見的模式；採購前必須回到各官方 pricing／contract 頁重新確認。對「沒有 API」的表述意為：在本研究查核的第一方公開資料中，未發現可供第三方嵌入的 stem API/SDK，並非法律上保證該公司不存在私有合作方案。
