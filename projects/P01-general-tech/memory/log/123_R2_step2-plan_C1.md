# 123_R2_step2-plan_C1.md

## 狀況理解

本 sub-step 為 R2 的第一個調研動作。使用者 R2 提出 3 個問題：(1) 確認 OfficeCLI 是否為「Office 系列軟體的程式友善 CLI 套組」；(2) 詢問其功能表現性與限制；(3) 要求逐步安裝使用指令與 GitHub Actions 相容性。本 step 目標：取得 repo metadata、README、安裝腳本、CI 設定，為後續回答提供原始資料。

## 執行的動作與結果

| 動作 | 目的 | 預期達成效果 | 實際結果 |
|------|------|-------------|---------|
| `gh repo view iOfficeAI/OfficeCLI --json` | 取得 repo metadata | 名稱、描述、語言、stars、license、topics 等 | 成功 — C#、Apache-2.0、15k stars、22 open issues、topics 含 agent/ai/cli/docx/xlsx/pptx |
| `gh api repos/.../readme` + base64 decode | 取得 README.md 全文 | 了解專案定位、功能列表、安裝方式、比較表 | 成功 — 取得完整 README（含 Comparison 表、Installation 章節、GitHub Actions 支援證據） |
| `gh api repos/.../releases/latest` | 取得最新 release 資訊 | 版本號、binary 清單 | 成功 — v1.0.135，8 個平台 binary + SHA256SUMS |
| 下載 install.sh | 分析安裝腳本邏輯 | 確認安裝流程、平台偵測、PATH 設定、AI skill 安裝 | 成功 — 支援 macOS/Linux，含 mirror/github 雙重下載、checksum 驗證、原子性搬移、macOS codesign/notarization 處理 |
| 下載 build.yml (GitHub Actions) | 確認 CI 相容性 | 確認能否在 GitHub Actions 環境執行 | 成功 — 8 平台 matrix build，含 smoke test（create/add/get/close）、install test、install.sh/install.ps1 test，全部在 ubuntu/macos/windows-latest 執行 |
| 下載 troubleshooting wiki | 取得常見錯誤與限制 | 了解已知限制與使用陷阱 | 成功 — 取得 resident mode flush 問題、路徑索引 1-based、屬性大小寫等常見問題 |
| 下載 command-install wiki | 取得 install 子命令細節 | 了解 `officecli install` 的行為 | 成功 — binary 複製到 ~/.local/bin、AI skill 安裝、MCP 註冊 |

## 動作結束後的現狀

| 驗證面向 | 驗證內容與方式 | 驗證結果 |
|---------|---------------|---------|
| Q1 答案素材 | README 開頭定位描述 | OfficeCLI 是「專為 AI agent 設計的 Office 套件 CLI」，支援 Word/Excel/PowerPoint 的讀寫改，單一二進位檔，不需安裝 Office |
| Q2 答案素材 | README Comparison 表 + 功能列表 | 支援 .docx/.xlsx/.pptx（不含 .doc/.xls）；功能覆蓋率高（文字、表格、圖表、樞紐分析、動畫、公式引擎等）；限制：僅 OOXML 格式、無原生 PDF 輸出（需 plugin）、渲染需 headless browser（screenshot 模式） |
| Q3 答案素材 | README Installation + build.yml + install.sh | 安裝方式：curl\|bash / brew / scoop / npm / 手動下載；GitHub Actions 可直接執行（binary 無依賴、smoke test 已在 CI 驗證）；需注意 resident mode flush 時機 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 選擇理由 |
|---------|---------|---------|---------|
| 是否下載 install.ps1（Windows） | 1. 下載 2. 跳過 | 跳過 | 使用者問題未指定 Windows，且 install.sh 已涵蓋 Linux/macOS 邏輯；Windows 安裝指令 README 已有 |
| 是否下載更多 wiki 頁面 | 1. 只下 troubleshooting + install 2. 下載全部相關 wiki | 只下載 troubleshooting + install | 其他 wiki（如 word-paragraph、excel-cell）與 R2 問題無直接關聯，後續若需要可再補 |
| 是否讀取 SKILL.md | 1. 讀取 2. 跳過 | 跳過 | SKILL.md 是給 AI agent 的指令檔，與使用者的安裝/使用/限制問題無直接關係 |
