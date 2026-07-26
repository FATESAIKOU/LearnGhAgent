# Openship 技術分析報告

> 調研對象：[oblien/openship](https://github.com/oblien/openship) v0.3.0
> 授權：Apache-2.0 | 語言：TypeScript（13M） | Stars：8,414

---

## 1. 這個技術解決什麼問題？

**Openship 解決的問題：個人開發者與小團隊缺乏低成本、可自託管的現代化 PaaS 部署平台。**

具體來說，它針對以下場景：

- 開發者寫完程式碼後，需要一個「一鍵部署」的管道，但不想使用 Vercel / Railway / Heroku 等付費雲端服務
- 使用者希望在自己的 VPS 上擁有類似 Vercel 的體驗：git push → 自動構建 → 自動部署 → SSL → 自訂網域
- AI 生成專案後，缺乏標準化部署流程，需要零配置自動識別技術棧並完成部署
- 需要一個統一的控制台管理多個專案的部署、資料庫、網域、SSL 憑證、備份

**模糊之處：** Openship 的定位橫跨「個人桌面工具」與「團隊 PaaS」，兩者的使用情境與安全模型差異大。Desktop 模式（控制平面跑在本機，透過 SSH 驅動遠端伺服器）與 Self-hosted 模式（控制平面跑在伺服器上，需登入）是兩種完全不同的架構，但共用同一套 branding，可能造成使用者對安全邊界與可用性的誤解。

---

## 2. 這個問題為什麼會發生？（背景）

### 文章中明確提到的背景

- **雲端 PaaS 成本高：** Vercel、Railway、Heroku 等服務對個人開發者或 side project 來說，免費額度有限，超出後月費不低。對於有多個專案的使用者，總成本可觀。
- **自託管門檻高：** 傳統自託管需要手動設定 Nginx 反向代理、Let's Encrypt SSL、Docker 構建流程、資料庫管理、監控告警等，對非維運人員不友善。
- **AI 生成專案激增：** 2024-2026 年間 AI 輔助程式碼生成工具普及，產出大量「可運作但難以部署」的專案，缺乏標準化部署管道。

### 通用技術背景（文章中未明確提及）

- **容器化技術成熟：** Docker 與容器編排工具（Docker Compose、Kubernetes）已成為部署標準，但 Kubernetes 對個人開發者過於複雜，Docker Compose 仍需手動撰寫。
- **邊緣運算與 Serverless 興起：** Vercel 的 Edge Functions、Cloudflare Workers 等 serverless 平台改變了部署心智模型，但這些平台綁定特定雲端供應商，缺乏可攜性。
- **Monorepo 工具鏈成熟：** pnpm workspaces、turborepo 等 monorepo 工具普及，但部署平台對 monorepo 的支援參差不齊。
- **開源自託管浪潮：** 2023-2026 年間，Coolify、Dokploy、CapRover 等開源自託管平台湧現，反映市場對「自建 PaaS」的強烈需求。

---

## 3. 這個技術是如何解決該問題的？

Openship 的核心機制是一條 **5 階段部署管線（Pipeline）**，搭配三種部署模式與一個 OpenResty 邊緣路由層。

### 3.1 三種部署模式

Openship 提供三種控制平面執行方式，使用者依情境選擇：

| 模式 | 控制平面位置 | 適用場景 | 對外暴露 |
|------|-------------|---------|---------|
| **Desktop App** | 使用者本機（Electron） | 單人、私人使用 | 無（透過 SSH 驅動遠端） |
| **Self-hosted Server** | Linux 伺服器（Docker / bare） | 團隊、always-on、CI/CD | 需設定 public URL + 登入 |
| **Openship Cloud** | 託管雲端 | 零維運 | 由雲端管理 |

Desktop 模式的核心設計：控制平面僅在本機執行時存在，關閉 App 後不留任何常駐服務，無需管理 always-on 伺服器。透過 SSH 連線到遠端 VPS 執行部署操作，Openship 本身不暴露任何埠。

### 3.2 5 階段部署管線

```
[Detect] → [Build] → [Run] → [Route + Secure] → [Push-to-deploy]
```

#### 階段 1：Detect（技術棧自動偵測）

Openship 讀取專案根目錄的以下檔案來判定技術棧：

- `package.json` → Node.js 生態系（框架、套件管理器、建置指令）
- 框架設定檔（`next.config.js`、`vite.config.ts` 等）
- 鎖定檔（`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml`）
- `docker-compose.yml` → Docker Compose 專案
- `railway.toml` / `railway.json` → Railway 相容設定
- `vercel.json` → Vercel 相容設定（build / install / start / output commands、routing）
- `openship.json` → Openship 專屬設定（可覆蓋自動偵測結果，對 monorepo 每個子應用獨立設定）

偵測結果包含：技術棧類型、套件管理器、建置指令、啟動指令、監聽埠號。

#### 階段 2：Build（構建）

在目標伺服器或編排器上執行構建，產出 Docker image 或 bare release。構建時將解析後的設定凍結為 snapshot，確保重新部署與回滾使用完全相同的設定。

支援的構建方式：
- **Docker image 構建**：自動產生 Dockerfile（若專案無自訂 Dockerfile）
- **bare release**：直接在主機上執行構建產物（無容器化）

#### 階段 3：Run（執行）

以容器（僅發布在 loopback，不對外暴露埠）或受監督的主機程序方式執行應用。

#### 階段 4：Route + Secure（路由 + SSL）

OpenResty（基於 Nginx + Lua 的高效能反向代理）在邊緣層處理：

```
使用者請求 → OpenResty Edge (:80/:443)
                ├── 比對 vhost（依 domain）
                ├── 套用 vercel.json 路由規則（proxy / rewrite / redirect / headers）
                ├── 反向代理到部署的應用容器（127.0.0.1:<hostPort>）
                └── Let's Encrypt HTTP-01 自動簽發與續期 SSL
```

路由規則支援（從 `vercel.json` 編譯而來）：
- **proxy**：路徑代理到任意後端 origin（如 `/api/*` → backend container）
- **rewrite**：URL 不變，服務不同靜態資源（SPA fallback `/* → /index.html`）
- **redirect**：301/302/307/308 重新導向
- **headers**：自訂回應標頭
- **cleanUrls** / **trailingSlash**：URL 正規化

路由與 SSL 在應用啟動後才設定，因此 DNS 或憑證問題不會導致部署失敗或應用下線，僅標記為「需處理」。

#### 階段 5：Push-to-deploy（Git 推送自動部署）

透過 GitHub webhook，在追蹤分支每次推送時自動重新執行管線。monorepo 場景下僅重建被變更的服務。

### 3.3 基礎設施元件

Openship Self-hosted 模式的 Docker Compose 堆疊：

```
┌─────────────────────────────────────────────────┐
│                  OpenResty Edge                  │
│              (:80 / :443, host network)          │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│   │  vhost A  │  │  vhost B  │  │  vhost C  │  │
│   └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
└─────────┼──────────────┼──────────────┼────────┘
          │              │              │
    ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
    │ App A     │  │ App B     │  │ App C     │
    │ Container │  │ Container │  │ Container │
    └───────────┘  └───────────┘  └───────────┘
          ▲              ▲              ▲
          └──────────────┼──────────────┘
                         │
              ┌──────────▼──────────┐
              │   API (Control)     │
              │   :4000             │
              ├─────────────────────┤
              │   Dashboard         │
              │   :3001             │
              ├─────────────────────┤
              │   Postgres :5432    │
              │   Redis    :6379    │
              └─────────────────────┘
```

- **Postgres**：主要資料庫（應用狀態、使用者、專案設定）
- **Redis**：佇列、快取、速率限制
- **API**：Hono 框架實作的控制平面 API（Docker socket mount，可操作 host Docker daemon）
- **Dashboard**：Next.js 實作的使用者介面
- **Edge**：OpenResty 容器（host networking，直接綁定 host 的 :80/:443）

### 3.4 技術棧支援範圍

| 類別 | 支援項目 |
|------|---------|
| **語言/框架** | Node.js、Python、Go、Rust、PHP、Ruby、Java、.NET |
| **資料庫** | Postgres、MySQL、MongoDB、Redis（由控制平面管理） |
| **容器** | Docker Compose 專案直接部署 |
| **Monorepo** | pnpm workspaces / turborepo，僅重建變更的服務 |
| **靜態站點** | Vite、CRA、SPA 等（含 SPA fallback） |

### 3.5 內建功能

| 功能 | 實作方式 |
|------|---------|
| **CI/CD** | GitHub webhook → 自動偵測變更 → 重建 → 部署 |
| **Preview Environments** | 分支部署到獨立 URL |
| **SSL** | Let's Encrypt HTTP-01 自動簽發與續期 |
| **CDN** | Edge caching、HTTP/3、Brotli 壓縮 |
| **Mail Server** | 內建 SMTP + DKIM/SPF/DMARC |
| **Backups** | 排程備份（資料庫 + volumes），一鍵還原 |
| **Monitoring** | 即時建置日誌、容器指標、資源使用 |
| **Scaling** | 雲端自動擴展，自託管多節點 |

---

## 4. 是否存在解決類似問題的其他技術 / 框架 / 思考方式？

### DA 表：替代方案比較

| 技術名 | 技術解法 | 技術使用前提 | 技術使用副作用 | 技術使用預期效果 |
|--------|---------|-------------|---------------|-----------------|
| **Coolify** | PHP + Livewire 實作的自託管 PaaS，透過 Docker 管理應用部署，支援 GitHub/GitLab 自動部署、SSL、資料庫 | 需一台 Linux 伺服器（建議 2GB RAM+），安裝 Docker | PHP 生態系，擴展性受限於單一伺服器架構；UI 為 Livewire（非 SPA），互動體驗較傳統 | 快速在 VPS 上建立類似 Heroku 的部署體驗，適合 PHP/Node.js 專案 |
| **Dokploy** | Docker Compose 為基礎的部署平台，提供 Web UI 管理多個 Docker Compose 專案，支援 SSL、網域管理 | 需 Linux 伺服器 + Docker + Docker Compose | 功能較精簡，無內建 CI/CD pipeline，需外部 CI 工具觸發部署 | 輕量級 Docker Compose 管理介面，適合已熟悉 Docker Compose 的使用者 |
| **CapRover** | Node.js + Docker 的自託管 PaaS，提供一鍵安裝的 App Marketplace，支援 SSL、自動部署、監控 | 需 Linux 伺服器 + Docker，最低 1GB RAM | 架構較封閉，擴展性有限；App Marketplace 的維護依賴社群貢獻 | 極簡安裝（一條指令），適合快速建立 side project 部署環境 |
| **Vercel** | 雲端 PaaS，提供 Edge Functions、Serverless Functions、靜態部署，git push 自動部署，全球 CDN | 需綁定 GitHub/GitLab/Bitbucket 帳號，免費方案有使用限制 | 供應商鎖定（Edge Functions 為 Vercel 專有）；自訂 server 端邏輯受限於 serverless 架構 | 零配置部署前端專案（尤其是 Next.js），全球邊緣網路加速 |

### 切入點差異分析

| 面向 | Openship | Coolify | Dokploy | CapRover | Vercel |
|------|----------|---------|---------|----------|--------|
| **部署模式** | Desktop + Self-hosted + Cloud | Self-hosted only | Self-hosted only | Self-hosted only | Cloud only |
| **控制平面位置** | 本機 / 伺服器 / 雲端 | 伺服器 | 伺服器 | 伺服器 | 雲端 |
| **技術棧偵測** | 零配置自動偵測（含 railway.toml/vercel.json） | 需手動設定 | 需手動設定 | 需手動設定 | 零配置（限前端框架） |
| **Edge Routing** | OpenResty 編譯 vercel.json 路由 | Nginx Proxy Manager | Traefik | Nginx | Vercel Edge Network |
| **Desktop App** | 有（Electron） | 無 | 無 | 無 | 無 |
| **內建 Mail** | 有（SMTP + DKIM/SPF/DMARC） | 無 | 無 | 無 | 無 |
| **Monorepo 支援** | 原生（pnpm workspaces + 增量重建） | 有限 | 有限 | 有限 | 有限 |
| **授權** | Apache-2.0 | Apache-2.0 | MIT | Apache-2.0 | 專有軟體 |
| **最低硬體** | 2核 CPU / 2GB RAM / 20GB 磁碟 | 1核 / 1GB RAM | 1核 / 1GB RAM | 1核 / 1GB RAM | 不適用（雲端） |

### 關鍵差異總結

1. **Desktop 模式是 Openship 的獨特定位：** 其他自託管平台都要求控制平面常駐在伺服器上，Openship 的 Desktop 模式讓控制平面跑在本機，僅在需要時透過 SSH 驅動遠端伺服器。這降低了攻擊面（無需暴露管理介面），也適合不想要 always-on 伺服器的個人開發者。

2. **技術棧偵測深度：** Openship 是唯一能讀取 `railway.toml` 和 `vercel.json` 作為設定來源的自託管平台，這意味著從 Railway 或 Vercel 遷移的專案可以無痛部署。

3. **Edge Routing 相容性：** Openship 編譯 `vercel.json` 路由規則到 OpenResty，使 Vercel 的路由行為（rewrite、redirect、headers、cleanUrls）在自託管環境中重現。其他自託管平台不具備此能力。

4. **內建 Mail Server：** Openship 內建完整的郵件伺服器（SMTP + DKIM/SPF/DMARC），其他平台需依賴外部郵件服務（Mailgun、SendGrid 等）。

5. **Vercel 的不可替代性：** Vercel 的 Edge Functions 與全球 CDN 網路是自託管平台無法複製的基礎設施優勢。自託管平台的本質限制在於：部署的應用只能跑在自有伺服器上，無法利用全球邊緣網路。

---

## 5. User Q&A

### Q1：Openship 是 PaaS，有 Cloud 和自託管兩種模式，所以它等於私有 AWS？

**A**：不是。Openship 是 **PaaS（平台即服務）**，不是 **IaaS（基礎設施即服務）**，與 AWS 的定位不同。

| 面向 | AWS | Openship |
|------|-----|----------|
| 服務層級 | IaaS（提供 VM、網路、儲存） | PaaS（提供部署管線、路由、SSL、資料庫） |
| 控制粒度 | 管理 EC2、VPC、Security Group | 管理專案、部署、網域 |
| 使用者操作 | 手動配置 OS、Docker、Nginx | 自動偵測技術棧、自動路由、自動 SSL |
| 私有性 | VPC 隔離 | 自託管時資料完全在自己機器上 |

Openship 的兩種分發模式：

```
┌─────────────────────────────────────────────────────┐
│                  Openship 控制平面                    │
│  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │   Openship Cloud     │  │   Self-hosted        │  │
│  │   (託管在 oblien)    │  │   (跑在你自己的機器)  │  │
│  └─────────┬───────────┘  └──────────┬────────────┘  │
│            │                          │               │
│            ▼                          ▼               │
│     部署到你的 VPS              部署到你的 VPS         │
│     (SSH 驅動)                  (本機 Docker)         │
└─────────────────────────────────────────────────────┘
```

兩種模式的最終部署目標都是**你的機器**。差別在於控制平面（API + Dashboard + DB）由誰營運：
- **Cloud 模式**：控制平面由 oblien 託管，你只需登入、連 SSH、部署
- **Self-hosted 模式**：控制平面也跑在你的機器上，完全自主

**結論**：Openship 不是「私有 AWS」，而是「自建版 Vercel」。它不管理 VM/網路/儲存（那是 IaaS 的事），它管理的是「從程式碼到上線」的管線。

---

### Q2：對於不想自己營運機器的人，Openship 有優勢嗎？比 AWS 便宜嗎？

**A**：分兩個層次回答。

**層次一：不想營運任何機器**

Openship Cloud 提供託管服務，但**定價尚未公布**（openship.io/pricing 標示 "Coming soon"）。目前 Openship Cloud 處於 preview 階段，無法確認是否比 AWS 便宜。

**層次二：願意租一台低價 VPS（自託管）**

自託管模式**完全免費**（Apache-2.0 授權，無計量、無座席上限、無遙測）。成本僅為 VPS 租金：

| 方案 | 月費 | 規格 | 備註 |
|------|------|------|------|
| Hetzner CX22 | €4.49/月 | 2核 / 4GB RAM / 40GB NVMe | 符合 Openship 最低需求 |
| DigitalOcean Basic | $6/月 | 1核 / 1GB RAM / 25GB SSD | 低於最低需求（建議 $12 方案） |
| AWS t3a.nano | ~$5/月 | 2核 / 0.5GB RAM | 低於最低需求（建議 t3a.small ~$15/月） |
| Oracle Cloud Free Tier | $0/月 | 4核 / 24GB RAM | 符合需求，但穩定性有爭議 |

對比使用 Vercel Pro（$20/月/人）+ 資料庫（Neon $19/月）+ 郵件（SendGrid $20/月）的組合，自託管 Openship 在 Hetzner €4.49/月即可涵蓋所有功能。

**層次三：優勢總結**

| 面向 | Openship 自託管 | AWS (手動建 PaaS) | Vercel + 第三方 |
|------|----------------|-------------------|-----------------|
| 月費 | VPS 租金（€4.49 起） | EC2 + RDS + ELB + ACM（$30+） | $20/月 + 資料庫 + 郵件 |
| 設定時間 | 5 分鐘（一條指令） | 數小時（手動配置） | 10 分鐘 |
| 功能完整度 | 部署 + DB + SSL + 郵件 + CDN | 需逐一配置 | 部署 + DB 分開計費 |
| 供應商鎖定 | 無（開源，可遷移） | 高（AWS 生態系） | 中（Vercel Edge 專有） |

**結論**：對於不想營運機器的人，Openship Cloud 的優勢取決於未來定價（目前未知）。對於願意租一台低價 VPS 的人，自託管 Openship 比 AWS 便宜 5-10 倍，且功能更完整。

---

### Q3：在自己機器建置 + Mac 筆電操作的具體指令？

**A**：以下為完整步驟，分為 Server 端安裝與 Mac 端操作。

#### 步驟 1：在 VPS 上安裝 Openship Server

```bash
# SSH 進你的 VPS
ssh root@<你的VPS_IP>

# 安裝 Openship CLI（一條指令）
curl -fsSL https://get.openship.io | sh

# 啟動 Openship（互動式精靈：建立 admin 帳號、設定 domain）
openship
# 或跳過精靈直接啟動：
openship up
```

啟動後 Openship 會：
- 註冊為 systemd 服務（開機自啟）
- 在 `:4000` 啟動 API、`:3001` 啟動 Dashboard
- 自動下載 Dashboard 前端

#### 步驟 2：在 Mac 上安裝 Desktop App

```bash
# 方式 A：透過 CLI 下載並啟動 Desktop App
npm i -g openship
openship install

# 方式 B：直接下載 DMG
# 前往 https://github.com/oblien/openship/releases/latest
# 下載 Openship-arm64.dmg（Apple Silicon）或 Openship-x64.dmg（Intel）
```

#### 步驟 3：在 Desktop App 中連接 VPS

1. 開啟 Desktop App
2. 點擊「Add Server」
3. 填入 VPS 的 SSH 連線資訊：
   - Host：你的 VPS IP
   - Port：22
   - User：root
   - Auth method：key（選擇你的 SSH private key）
4. 點擊「Test Connection」確認連線成功
5. 點擊「Save」

#### 步驟 4：部署專案

```bash
# 在 Mac 終端機中，進到你的專案目錄
cd your-project

# 初始化專案（連結到 Openship）
openship init

# 部署
openship deploy --watch
```

Desktop App 中也可直接操作：點擊「New Project」→ 選擇本地資料夾 → 點擊「Deploy」。

#### 步驟 5：管理部署

```bash
# 查看部署狀態
openship status

# 查看部署列表
openship deployment list

# 串流日誌
openship logs <deployment-id> --follow

# 回滾
openship deployment rollback <deployment-id>
```

#### 完整流程示意

```
Mac (Desktop App / CLI)
    │
    ├── SSH ──────────► VPS (Openship Server)
    │                      ├── API (:4000)
    │                      ├── Dashboard (:3001)
    │                      ├── OpenResty Edge (:80/:443)
    │                      ├── Postgres
    │                      └── Redis
    │
    └── git push ──────► GitHub
                            └── webhook ──► VPS (自動重新部署)
```

**結論**：從零到部署一個專案，約需 5 條指令（server 安裝 1 條 + Desktop App 下載 1 條 + 專案初始化 1 條 + 部署 1 條 + 管理指令視需要）。無需手動設定 Nginx、SSL、Docker。

---

### Q4：Openship 的 Cloud 模式到底是什麼？使用者自己不用準備機器，oblien 會幫忙跑服務嗎？這等於私有 AWS 嗎？

**A**：Openship Cloud **不是** oblien 幫你跑服務的託管運算平台，也不是私有 AWS。

關鍵區別：

| 面向 | 使用者預期（私有 AWS） | Openship Cloud 實際行為 |
|------|----------------------|----------------------|
| 運算資源由誰提供 | oblien 提供 VM/容器 | **使用者自己提供 VPS** |
| 控制平面由誰營運 | 使用者（自建 AWS console） | oblien 託管（API + Dashboard + DB） |
| 使用者需不需要機器 | 不需要（AWS 提供 EC2） | **需要**（至少一台 VPS 跑應用） |
| 可以做什麼操作 | 開 VM、調網路、配儲存 | 部署應用、管理網域、看日誌 |

Openship Cloud 的實際架構：

```
使用者 Mac
    │
    ├── 登入 openship.io ──► oblien 託管的控制平面
    │                            ├── API
    │                            ├── Dashboard
    │                            └── Postgres
    │
    └── 控制平面透過 SSH ──► 使用者的 VPS
                                 └── 跑應用容器
```

Cloud 模式節省的是「營運控制平面」的負擔（你不需自己跑 API + Dashboard + DB），但**運算資源（VPS）仍由使用者提供**。這與 AWS 不同：AWS 提供的是 EC2 運算資源本身，而 Openship Cloud 只提供管理介面。

**結論**：Openship Cloud 不是「私有 AWS」，而是「oblien 幫你管控制平面，你自己出機器跑應用」。使用者仍需一台 VPS。

---

### Q5：對於完全不想碰任何機器的人，Openship 有任何優勢嗎？它比 AWS 便宜嗎？到底要不要錢？

**A**：分三種情境回答。

**情境一：完全不想碰任何機器（連 VPS 都不想租）**

Openship 在這種情境下**沒有優勢**。因為 Openship 的兩種模式（Cloud / Self-hosted）都要求使用者提供一台 VPS 來跑應用。如果使用者連一台低價 VPS 都不願意租，Openship 無法提供服務。

**情境二：願意租 VPS 但不想手動設定 Nginx/SSL/Docker**

這是 Openship 的核心客群。成本僅為 VPS 租金：

| 項目 | Openship 自託管 | 手動建置（Nginx + Docker + Certbot） | AWS 最低方案 |
|------|----------------|-------------------------------------|-------------|
| 月費 | VPS €4.49（Hetzner） | VPS €4.49 + 設定時間 2-4 小時 | t3a.small ~$15/月 + RDS ~$15/月 |
| 設定時間 | 5 分鐘 | 2-4 小時 | 4-8 小時 |
| 後續維護 | 自動（SSL 續期、備份） | 手動（cron job、監控） | 手動（CloudWatch、Auto Scaling） |

**情境三：Openship Cloud 是否收費？**

| 模式 | 費用 | 備註 |
|------|------|------|
| Self-hosted | **永久免費**（Apache-2.0） | 無計量、無座席上限、無遙測 |
| Desktop App | **免費** | 控制平面在本機，無需伺服器端授權 |
| Openship Cloud | **定價尚未公布** | openship.io/pricing 標示 "Coming soon" |

**結論**：
- 不想碰任何機器 → Openship 無優勢，應使用 Vercel（免費方案）或 Railway
- 願意租 VPS（€4.49/月）→ Openship 自託管比 AWS 便宜 5-10 倍
- Openship Cloud 定價未知，無法判斷是否比 AWS 便宜

---

### Q6：從零開始，在自己的 Linux VPS 裝 server + Mac 筆電操作，完整的逐步指令？

**A**：以下為最小可行步驟，從一台全新 VPS 開始。

#### 前置條件

- 一台 Linux VPS（Ubuntu 22.04+，2核 / 2GB RAM / 20GB 磁碟）
- 一個網域（A record 指向 VPS IP）
- Mac 筆電（本機）

#### Step 1：VPS 初始化 + 安裝 Openship Server

```bash
# 1. SSH 進 VPS
ssh root@<你的VPS_IP>

# 2. 更新系統
apt update && apt upgrade -y

# 3. 安裝 Openship（一條指令）
curl -fsSL https://get.openship.io | sh

# 4. 啟動 Openship（首次執行會進入互動式設定精靈）
openship up
```

互動式精靈會問：
- Admin email & password（建立管理員帳號）
- 你的網域（如 `openship.example.com`，指向 Dashboard）
- 是否啟用 SSL（建議 yes）

完成後 Openship 會：
- 下載 Docker images（API、Dashboard、Edge、Postgres、Redis）
- 啟動所有容器
- 註冊 systemd 服務（`systemctl status openship` 可查看）
- 在 `https://openship.example.com` 提供 Dashboard

#### Step 2：Mac 端安裝 Desktop App

```bash
# 方式 A（CLI 安裝，推薦）
npm install -g openship
openship install

# 方式 B（DMG 手動下載）
# 瀏覽器開啟 https://github.com/oblien/openship/releases
# 下載 Openship-<arch>.dmg（Apple Silicon 選 arm64，Intel 選 x64）
# 掛載 DMG，拖到 Applications
```

#### Step 3：Desktop App 連接 VPS

1. 開啟 Desktop App
2. 點擊「Add Server」
3. 填入：
   - **Name**：`my-vps`（任意名稱）
   - **Host**：你的 VPS IP（如 `123.123.123.123`）
   - **Port**：`22`
   - **User**：`root`
   - **Auth**：選擇你的 SSH private key（預設 `~/.ssh/id_rsa`）
4. 點擊「Test Connection」→ 看到綠色勾勾表示成功
5. 點擊「Save」

#### Step 4：部署第一個專案

```bash
# 在 Mac 終端機
cd ~/my-project

# 初始化（連結到 Openship）
openship init
# 選擇剛才新增的 server（my-vps）
# 選擇技術棧（自動偵測或手動指定）

# 部署
openship deploy --watch
```

`--watch` 會即時顯示建置日誌。部署完成後會顯示 URL（如 `https://my-project.openship.example.com`）。

#### Step 5：驗證

```bash
# 查看所有部署
openship deployment list

# 查看特定部署日誌
openship logs <deployment-id> --follow

# 在瀏覽器開啟部署 URL
open https://my-project.openship.example.com
```

#### 完整指令摘要（從 VPS 到上線）

```
VPS:  curl -fsSL https://get.openship.io | sh && openship up
Mac:  npm install -g openship && openship install
Mac:  openship init && openship deploy --watch
```

共 4 條指令（VPS 2 條 + Mac 2 條），無需手動編輯 Nginx 設定檔、無需手動申請 SSL 憑證、無需手動建立 Docker Compose。
