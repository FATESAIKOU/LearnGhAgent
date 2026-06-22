# 44_R1_step2-plan_C2.md

## 狀況理解

C1 已取得 repo metadata 與核心文件。C2 深入技術架構細節：API endpoints、GPU 支援、雲端方案、模型匯入、tool calling 機制，以補足分析報告 §1~§4 所需的技術深度。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| webfetch /api/generate | 取得 generate endpoint 細節 | 了解 prompt/suffix/stream/options/structured output | 成功取得完整 OpenAPI spec |
| webfetch /api/embed | 取得 embedding endpoint 細節 | 了解向量嵌入 API | 成功取得 |
| webfetch /gpu | 取得 GPU 支援列表 | NVIDIA/AMD/Metal/Vulkan 支援範圍 | 成功取得完整 GPU 相容表 |
| webfetch /cloud | 取得雲端方案 | 雲端模型運作方式、定價 | 成功取得（Pro $20/mo, Max $100/mo） |
| webfetch /import | 取得模型匯入方式 | Safetensors/GGUF 匯入流程、量化 | 成功取得完整流程 |
| webfetch /capabilities/tool-calling | 取得 tool calling 機制 | 單工具/平行/多輪 agent loop/串流 | 成功取得完整範例 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|----------|----------------|----------|
| API 完整度 | 比對 llms.txt 索引與實際擷取 | 核心 API 已涵蓋：chat/generate/embed/tags/pull/push/copy/create/delete/ps |
| GPU 支援範圍 | 官方文件 GPU 相容表 | NVIDIA CC 5.0+、AMD ROCm v7、Apple Metal、Vulkan |
| 雲端方案 | 官方文件 | 本地免費 + 雲端付費，支援 cloud model 標籤 |
| 模型自訂 | Modelfile + import 文件 | 支援 FROM/PARAMETER/TEMPLATE/SYSTEM/ADAPTER/LICENSE/MESSAGE/REQUIRES |
| Tool calling | 官方文件範例 | 支援 single-shot、parallel、multi-turn agent loop、streaming |
| 技術棧 | go.mod + development.md | Go 1.26 + gin + cobra + sqlite3 + llama.cpp (C/C++) + MLX |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 深入範圍 | 全部 60+ 頁 / 聚焦核心機制 | 聚焦核心機制 | 6000 字限制，核心機制已涵蓋分析所需 |
| 替代方案調研 | 僅列名 / 深入比較 | 留待 Step 3 報告 §4 處理 | 替代方案比較為報告內容，非本 step 調研範圍 |
