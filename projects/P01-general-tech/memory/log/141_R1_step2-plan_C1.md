# 141_R1_step2-plan_C1.md

## 狀況理解

Step 2 C1：取得 Openship repo 的 metadata、README、關鍵子文件與架構資訊，為後續分析報告提供原始資料。Openship 為 GitHub 上 oblien/openship 的開源專案，定位為自託管部署平台。

## 執行的動作與結果

| 動作 | 目的 | 預期效果 | 實際結果 |
|------|------|----------|----------|
| `gh api repos/oblien/openship` | 取得 repo metadata | 名稱、描述、星數、語言、授權等 | 成功取得完整 metadata |
| `gh api repos/oblien/openship/languages` | 取得語言分佈 | 了解技術棧組成 | TypeScript 為主（13M），含 MDX/Shell/CSS/Lua 等 |
| `gh api repos/oblien/openship/topics` | 取得 topics | 了解分類標籤 | agents, ai, deployments, self-hosted |
| `gh api repos/oblien/openship/releases/latest` | 最新 release | 了解版本狀態 | v0.3.0（2026-07-22） |
| `gh api .../readme` + base64 decode | 讀取 README.md | 了解專案定位、功能、快速開始 | 完整取得（含 Quick Start、How It Works、Features、Interfaces） |
| `gh api .../contents/docs/installation.md` | 讀取安裝文件 | 了解三種部署模式細節 | 完整取得（Desktop / Self-hosted / Cloud） |
| `gh api .../contents/package.json` | 讀取 package.json | 了解 monorepo 結構、版本、scripts | 確認 pnpm workspaces + turbo monorepo，版本 0.3.0 |
| `gh api .../contents/docker/docker-compose.yml` | 讀取 Docker Compose | 了解容器化部署架構 | postgres + redis + api + dashboard + edge（OpenResty） |
| `gh api .../contents/apps` + `packages` | 列舉子目錄 | 了解 monorepo 結構 | apps: api/cli/dashboard/desktop/edge/email/web；packages: adapters/core/db/db-email/onboarding/ui |
| `gh api .../contents/CONTRIBUTING.md` | 讀取貢獻指南 | 了解開發流程與專案結構 | 確認 Hono API、Next.js dashboard、Electron desktop |
| `gh api .../contents/CHANGELOG.md` | 讀取更新日誌 | 了解近期變更 | v0.2.4 新增 railway.toml/vercel.json 相容、openship.json 設定檔 |
| `gh api .../contents/docs/oblien-edge-routing-requirements.md` | 讀取 edge routing 文件 | 了解路由架構設計 | OpenResty 編譯 vercel.json 路由規則，支援 proxy/rewrite/redirect |

## 動作結束後的現狀

| 驗證面向 | 驗證內容 | 結果 |
|----------|----------|------|
| Repo metadata | 名稱、星數、語言、授權、版本 | 8,414 stars, TypeScript, Apache-2.0, v0.3.0 |
| 架構理解 | monorepo 結構、部署模式 | 7 apps + 6 packages，三種部署模式（Desktop/Self-hosted/Cloud） |
| 核心機制 | pipeline 流程、技術棧偵測 | Detect→Build→Run→Route+Secure→Push-to-deploy，零配置自動偵測 |
| 文件完整性 | 關鍵文件是否取得 | README、installation、docker-compose、CONTRIBUTING、CHANGELOG、edge-routing 均已取得 |
| 資訊缺口 | 需補查的項目 | Vercel/Railway 比較、實際使用案例、技術棧偵測實作細節 |

## 其中的決斷點

| 決斷面向 | 可選選項 | 選擇結果 | 理由 |
|----------|----------|----------|------|
| 文件擷取範圍 | 僅 README / README+docs 全部 / 含原始碼 | README + installation + docker-compose + CHANGELOG + edge-routing | 覆蓋定位、安裝、架構、版本歷史、路由設計，足夠 C1 需求 |
| 原始碼深度 | 不讀 / 讀 api 核心 / 讀 cli 核心 | 僅列舉目錄結構 | C1 為 metadata 收集，原始碼細節留給 C2 |
| 背景補查 | 不查 / 查 Vercel/Railway 比較 | 暫不查 | 留給 C2 專注比較分析 |
