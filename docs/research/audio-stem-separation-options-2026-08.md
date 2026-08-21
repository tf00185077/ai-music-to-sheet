# 音訊 Stem Separation 選項研究（2026-08-21）

本報告以官方 GitHub、官方文件與官方產品頁為來源；「開源」只表示程式碼授權，**不等於**預訓練權重、訓練資料或使用者上傳音樂都可商用。產品與價格/配額會變動，以下是 2026-08-21 的核對結果。

## 結論先行

- 要做可長期營運、可控隱私的上傳分離功能：PoC 可先用 **python-audio-separator** 統一包裝多種模型，再以自管 GPU worker 執行；正式上線前仍須逐一取得/稽核每個 **checkpoint** 的商用權利。最乾淨的商用路徑是以有權使用的資料自行訓練並保存資料與模型 provenance。
- 要最快交付、接受雲端與用量成本：**LALAL.AI API** 是目前官方明示可嵌入自家服務的選項；Moises 也有開發者平台，但其公開入口名為 `developer-legacy-stage`，應先向業務確認可用性、SLA、資料處理與正式合約，不應把公開頁當成穩定自助 API。
- **UVR、BandLab Splitter、Moises App** 是可用的終端使用者產品，不是可自管的後端。勿把其 GUI/訂閱權利推論成可轉售或嵌入自己的上傳服務。

## 開源專案／可自行部署的程式碼

| 選項 | 型態、輸出 stem | 自架／整合路徑 | 授權與維護訊號 | 優點與限制 |
|---|---|---|---|---|
| [python-audio-separator](https://github.com/nomadkaraoke/python-audio-separator) | Python library／CLI；可執行主要來自 UVR 生態的 VR、MDX、MDXC／RoFormer 與 Demucs 模型；輸出 stem 依 checkpoint 而定。 | 官方提供 Python API、CPU/GPU Docker image、批次推論，以及可部署至 Modal 的非同步遠端 API 範例；很適合包成 upload queue 的 GPU worker。 | wrapper 程式碼為 [MIT](https://github.com/nomadkaraoke/python-audio-separator/blob/main/LICENSE)；官方 release 頁在 2026-07 仍有 v0.44.x 發版，是本表中較活躍的整合層。**MIT 只涵蓋 wrapper；每個自動下載的模型仍須個別確認權重、訓練資料與商用權利。** | 對現有產品開發最省整合時間，可用同一介面 A/B 測多個模型、格式及 ensemble；但它不是一個品質固定的新模型，模型相容性、GPU 記憶體、併發隔離與授權 registry 都由服務端負責。 |
| [Demucs v4](https://github.com/facebookresearch/demucs) | Python 套件／CLI；標準為 vocals、drums、bass、other（4 stem），另有實驗性 guitar、piano 的 6 stem。 | 以 CLI 處理 worker 工作，或用官方 Python `pretrained.get_model` + `apply_model` 包裝為非同步 job；模型可下載到本機快取。 | 程式碼為 [MIT](https://github.com/facebookresearch/demucs/blob/main/LICENSE)，但官方 Meta repo 已於 2025-01-01 封存，README 指向 adefossez fork 並說明僅處理重要 bug。官方下載清單本身未為每個 checkpoint 列出獨立授權，商用前須另行確認權重與訓練資料權利。 | 成熟、常用的 4-stem 基線，hybrid waveform/spectrogram，官方亦提供 6-stem 實驗模型；但原專案不再主動維護，6-stem 品質被標示為實驗性，GPU/長音檔須分段與併接。 |
| [Spleeter](https://github.com/deezer/spleeter) | Python library／CLI／Docker；2 stem（vocals/accompaniment）、4 stem（vocals/drums/bass/other）、5 stem（再加 piano）。 | 官方支援 `pip`、CLI、直接 Python 呼叫與 Docker，易放入 queue worker。 | [MIT 程式碼](https://github.com/deezer/spleeter/blob/master/LICENSE)；GitHub 最新正式 release 為 v2.3.0（2021-09-03），是明顯的低維護訊號。模型隨 release 分發，仍應將 code 與權重視為獨立授權物逐一審閱。 | 官方宣稱 GPU 4 stem 可達遠快於即時，適合作為快速、可預測的基線；TensorFlow 相依較舊，模型世代較早，對複雜混音的分離品質通常不宜預設為現代最佳。 |
| [Open-Unmix (PyTorch)](https://github.com/sigsep/open-unmix-pytorch) | PyTorch library／CLI 型整合、Dockerfile；預訓練 pop-music 模型為 vocals、drums、bass、other（4 stem）；另有 speech-enhancement `umxse`。 | 直接在 Python worker 載入 Separator；repo 有 Dockerfile，適合容器化。 | [MIT](https://github.com/sigsep/open-unmix-pytorch/blob/master/LICENSE)；官方新聞最後明確相容性更新為 2024-04（升至 Torch 2.0），較 Demucs 原 repo 新但仍非高速演進。預訓練權重應另查其來源/條款。 | 研究導向、架構與 API 清楚、每一 source 可獨立替換或重訓；是 LSTM/magnitude-spectrogram 參考實作，固定 4 stem，非追逐最新品質的現成方案。 |
| [MDX-Net submission](https://github.com/kuielab/mdx-net-submission)／[MSST](https://github.com/ZFTurbo/Music-Source-Separation-Training)／[Ultimate Vocal Remover (UVR)](https://github.com/Anjok07/ultimatevocalremovergui) | MDX-Net 是模型/訓練碼；MSST 是訓練與推論 CLI（含 MDX23C、Demucs、BS/Mel-Band RoFormer 等）；UVR 是 Windows/macOS/Linux 本機 GUI，支援 Demucs v1–v4 與 MDX23C 等模型。輸出 stem 取決於選用 checkpoint。 | 做服務時以 MDX-Net/MSST 的 inference 腳本或自家 PyTorch wrapper 做 worker；UVR 適合人工桌面流程與模型比較，並非乾淨的 server API。 | MDX-Net repo 與 MSST 程式碼均標示 [MIT](https://github.com/kuielab/mdx-net-submission/blob/master/LICENSE)／[MIT](https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/main/LICENSE)；UVR code 也稱 [MIT](https://github.com/Anjok07/ultimatevocalremovergui/blob/master/README.md#license)。MDX-Net 官方 README 更警告目前 branch 正在重構、可能無法運作；UVR 仍有 v5.6 release，並提供模型下載中心。 | 模型選擇最多、可 ensemble、UVR 便於 QA；但「MDX/UVR model」不是單一授權或品質保證，社群 checkpoint 常無明確 license。不可因 GUI 或 code 是 MIT 就把任一下載模型用於商業服務。 |
| [AudioSep](https://github.com/Audio-AGI/AudioSep) | Python research/inference code；非固定 stem：輸入自然語言描述（例如指定聲音/樂器）輸出該目標聲音。 | 官方提供 conda 環境、Python inference、chunk 推論與 checkpoint 下載；可自管部署。 | 程式碼 [MIT](https://github.com/Audio-AGI/AudioSep/blob/main/LICENSE)；官方 repo 指向的 `nielsr/audiosep-demo` [model card 標為 Apache-2.0](https://huggingface.co/nielsr/audiosep-demo)。repo 不見正式 release，應將其視為研究型整合。 | 適合「用文字指定要抽什麼」的長尾需求，不侷限 vocals/drums/bass；非一般音樂 4-stem 的可預測預設，32 kHz 處理、文字 query 與音訊類型都會影響結果，應先做資料集測試。 |
| [BS-RoFormer](https://github.com/lucidrains/BS-RoFormer)／[Mel-Band RoFormer](https://github.com/lucidrains/BS-RoFormer) | PyTorch 實作／可訓練 library，支援 stereo 與多 stem；實際輸出 stem 由 `num_stems` 與訓練 checkpoint 決定。 | 可直接 pip 安裝做研究或以 MSST 訓練、推論；在服務中較合理的是採用自訓 checkpoint。 | code 為 [MIT](https://github.com/lucidrains/BS-RoFormer/blob/main/LICENSE)，但 repo 未提供正式 releases；README 所連的公開權重屬不同發布者。**每一個公開 RoFormer checkpoint 都必須獨立確認權重 license**，沒有明示商用授權就不要佈署。 | 現代 Transformer 架構，適合追求品質與自行訓練；現成權重取得與可商用性不整齊，工程與 MLOps 成本高於 Demucs/Spleeter。 |

### 開源項目的實作備註

1. 將 upload 寫入私有物件儲存後建立 job；GPU worker 下載/轉 WAV、分段推論、合併 stem，最後輸出 ZIP/WAV。不要在 HTTP request 內同步跑模型。
2. 建立模型 registry：`model_id`、程式碼 commit、checkpoint SHA-256、權重 URL、權利人、license、訓練資料、商用核准日期。下載頁沒有 license 時，狀態應是「不可商用」，而非「MIT 推定」。
3. 宣告「分離結果會有漏音、殘響與 musical noise」，並讓使用者重跑其他模型/輸出格式；品質沒有跨曲風的一個贏家。

## 現有消費者服務（非開源）

| 服務 | 型態、可用 stem | 開發者整合／自架 | 商業性與現況 | 優點與限制 |
|---|---|---|---|---|
| [Moises](https://moises.ai/features/vocal-remover/) | 專有 Web、iOS/Android、desktop 與 DAW 整合；官方產品頁為 2/4/5 tracks，免費 4-stem 選項為 vocals/bass/drums/other，付費方案另有 lead/back vocals、guitar、piano、strings、wind 等選擇。 | 有官方 [Developer Platform](https://developer-legacy-stage.moises.ai/)（頁面列 stem separation 與 US$0.10/min），但網域/名稱顯示為 legacy-stage；正式採用前應聯絡銷售核對 API 合約。不能自架其模型。 | 專有、帳戶與訂閱/用量制；官方仍更新產品與 DAW 文件，且其 DAW 整合明確需要網路。 | 成品產品、附節拍/和弦等音樂工作流；服務鎖定、資料須上雲、公開 API 的正式性與條款須採購確認。 |
| [LALAL.AI](https://www.lalal.ai/) | 專有 Web、desktop、iOS/Android、VST 與 API；Stem Splitter 可至 10 類（vocals、instrumental、drums、bass、piano、acoustic/electric guitar、synth、strings、wind），另有 lead/back vocals。 | 官方 [API](https://www.lalal.ai/api/) 明示可將 stem splitting 整合進自家軟體/服務；不能自架雲端模型。其 Lyra 僅在官方 desktop/VST 本機執行，並非可嵌入的 SDK。 | 專有付費/分鐘與訂閱模式；官方 FAQ 說明每次選一種 separation type 會得到一對 stems，並有 Fast/Relaxed queue。 | 對外 API 是最快的產品路徑；需處理用量成本、檔案外送、供應商配額/資料處理與 API 商業條款。 |
| [BandLab Splitter](https://help.bandlab.com/hc/en-us/articles/16560236938777-Using-BandLab-Splitter) | 專有 BandLab Web／mobile／Studio 功能；目前官方 help 指出可處理 vocals、drums、bass、guitar、piano、others，並可匯出 audio/MIDI。免費方案歷來為 4 stem，Membership 提供更多 stem/速度與 Studio 功能。 | 未見官方公開 API 或可自架模型；只可作為 BandLab 內的使用者工具。 | 專有服務；官方 help 在 2026-08 仍更新，Membership FAQ 為訂閱制。 | 對一般使用者方便，附 Studio/MIDI 工作流；不適合作為第三方上傳分離功能的後端依賴。 |

## 授權、權利與上線檢核

- **程式碼、權重、資料三份權利分開看。** MIT/Apache 通常容許商業使用程式碼，但不會替沒有明示條款的 checkpoint 或受限訓練資料授權。上表中明示 model-card Apache-2.0 的 AudioSep checkpoint 仍要保留該卡與版本；其餘標成「另查」者不得只憑 repo LICENSE 放行。
- **音樂著作權另計。** 即使模型與程式碼可用，使用者上傳、儲存、處理與輸出他人錄音/作品仍涉及其授權、服務條款、通知/下架與適用地法律；應要求使用者確認有權處理，設定保留期限與刪除流程。這不是法律意見。
- 對 SaaS API：確認 DPA/資料所在地、是否拿 upload 訓練、結果保存期限、速率/併發/SLA、價格計量（原音檔分鐘 × separation 類型數）、可否轉售結果與失敗重試費用。

## 建議的選型

1. **MVP（最快）**：採 LALAL.AI API，做 upload → 非同步 job → 輪詢/回呼 → ZIP 下載；把 vendor adapter 抽象成 `submit/status/download`，避免被單一服務綁死。
2. **可控成本與隱私（推薦長期）**：用 python-audio-separator 快速建立自管 GPU queue 與模型 A/B 測試，先以已完成權利審查的 Demucs/Open-Unmix checkpoint 提供固定 4 stem；同時開始自訓或取得書面授權的 RoFormer/MDX checkpoint。不要把封存 Demucs repo 或無 license 的 UVR 社群模型當唯一商用基礎。
3. **產品能力**：預設給 4 stem（vocals/drums/bass/other）；再提供「高品質／慢速」與指定樂器實驗選項。AudioSep 宜標為 beta/文字目標分離，而非承諾固定樂器品質。

## 一手來源索引

- 開源： [python-audio-separator README/API/Docker](https://github.com/nomadkaraoke/python-audio-separator)、[python-audio-separator releases](https://github.com/nomadkaraoke/python-audio-separator/releases)、[Demucs README](https://github.com/facebookresearch/demucs)、[Demucs training/API](https://github.com/facebookresearch/demucs/blob/main/docs/training.md)、[Spleeter README](https://github.com/deezer/spleeter)、[Open-Unmix README](https://github.com/sigsep/open-unmix-pytorch)、[MDX-Net README](https://github.com/kuielab/mdx-net-submission)、[UVR README/releases](https://github.com/Anjok07/ultimatevocalremovergui/releases)、[MSST README](https://github.com/ZFTurbo/Music-Source-Separation-Training)、[AudioSep README](https://github.com/Audio-AGI/AudioSep)、[BS-RoFormer README](https://github.com/lucidrains/BS-RoFormer)。
- 服務： [Moises 功能頁](https://moises.ai/features/vocal-remover/)、[Moises 分離選項說明](https://help.moises.ai/hc/en-us/articles/360010972019-Quais-instrumentos-podem-ser-separados-no-Moises)、[LALAL.AI API](https://www.lalal.ai/api/)、[LALAL.AI FAQ](https://www.lalal.ai/guides/faq/)、[BandLab Splitter help](https://help.bandlab.com/hc/en-us/articles/16560236938777-Using-BandLab-Splitter)、[BandLab Membership FAQ](https://help.bandlab.com/hc/en-us/articles/20758981227033-BandLab-Membership-FAQ)。
