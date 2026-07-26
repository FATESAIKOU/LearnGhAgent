# Openship 技術分析報告

> 調研對象：[oblien/openship](https://github.com/oblien/openship) v0.3.0
> 授權：Apache-2.0 | 語言：TypeScript（13.8MB） | Stars：8,614

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
