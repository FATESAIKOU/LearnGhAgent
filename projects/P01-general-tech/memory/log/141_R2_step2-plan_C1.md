# 141_R2_step2-plan_C1.md

## 狀況理解

R2 使用者針對 R1 報告提出 3 個追問：(1) Openship 的 PaaS 架構模式——兩種分發模式（Cloud / 自託管）的具體關係，以及自託管是否等同於「私有 AWS」；(2) 對於不想自己營運伺服器的使用者，Openship 的優勢何在，以及它是否比 AWS 便宜（是否收費）；(3) 具體的建置與操作指令——從在自己的機器上安裝 server，到用 Mac 筆電操作 client 的完整步驟。

本 step（C1）目標：針對這 3 個問題，從 repo 文件與官方網站補查必要資訊。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| 讀取 README.md（完整內容） | 取得三種部署模式說明、CLI 指令、架構概覽 | 回答 Q1（架構模式）與 Q3（具體指令） | 取得完整 Quick Start 表格（Desktop / Self-hosted / Cloud）、`openship up` 指令、`openship init` + `openship deploy` 流程 |
| 讀取 openship.io/pricing | 確認收費模式 | 回答 Q2（是否收費、比 AWS 便宜？） | 明確：Self-hosted 永久免費（Apache 2.0），Cloud 定價尚未公布 |
| 讀取 openship.io/docs（Introduction + Installation + Quickstart + Architecture） | 補足架構細節與逐步操作說明 | 回答 Q1（私有 AWS 類比）與 Q3（Mac 操作步驟） | 取得：控制平面 vs 平台層架構圖、三種 runtime（local / server / cloud）、CLI 安裝與啟動完整指令 |
| 讀取 CHANGELOG.md | 確認版本狀態與功能成熟度 | 輔助判斷產品階段 | 最新 v0.2.4，仍在早期開發階段，Cloud 有 per-user project cap（預設 2） |

## 動作結束後的現狀

| 驗證面向 | 驗證內容 | 結果 |
|----------|----------|------|
| Q1 資訊充足度 | 三種部署模式的具體關係、控制平面 vs 執行平面分離 | 已取得：Desktop App（控制平面在本機，透過 SSH 驅動遠端伺服器）、Self-hosted Server（控制平面在伺服器上，Compose mode 可同時 host app）、Cloud（全託管） |
| Q2 資訊充足度 | 收費模式、與 AWS 成本比較 | 已取得：Self-hosted 永久免費（Apache 2.0），Cloud 定價未公布。無直接 AWS 價格比較資料 |
| Q3 資訊充足度 | 從零開始的逐步指令（server 安裝 + Mac 操作） | 已取得：server 端 `curl -fsSL https://get.openship.io | sh` + `openship up`；Mac 端 Desktop App 下載或 CLI 安裝；`openship init` + `openship deploy` |
| 資訊缺口 | 仍有不足的面向 | Openship Cloud 的具體定價未公布，無法回答「是否比 AWS 便宜」；私有 AWS 類比需自行推論 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|----------|----------|----------|----------|
| 資料來源 | 僅 README / README + docs + pricing + changelog | README + docs（4 頁）+ pricing + changelog | 覆蓋 Q1 架構、Q2 收費、Q3 指令三個面向 |
| 架構資訊深度 | 僅 README 表格 / 含 Architecture docs | 含 Architecture docs | 取得控制平面/平台層分離圖，有助於回答「私有 AWS」類比 |
| 收費資訊 | 僅 README / 含 pricing page | 含 pricing page | pricing page 明確寫「Free to self-host. Cloud pricing coming soon.」 |
