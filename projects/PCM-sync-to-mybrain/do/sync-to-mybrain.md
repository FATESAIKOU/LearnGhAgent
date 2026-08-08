---
description: 把當前 session 的收穫整理進第二大腦，在 GitHub 開 PR
---

# /sync-to-mybrain

把**當前對話**中值得長期保存的內容寫進第二大腦，開一個 PR 讓使用者 review。

```
REPO = https://github.com/FATESAIKOU/MyBrain
```

`$ARGUMENTS` 若有內容，代表使用者指定了這次要存什麼（例：`只存 OKF 研究那段`）。若含 `--dry-run`，做到步驟 5 為止，把打算寫的內容印出來，**不 push、不開 PR**。

## 這個指令的分工

**所有格式與結構規則都住在那個 repo 裡**（根目錄 `index.md` 的「使用規則」一節）。本檔只負責兩件事：

1. 判斷這次 session 有什麼值得存
2. clone → 寫 → 驗證 → 開 PR 的機制

**不要在本檔複製規則，也不要憑記憶寫格式。** 規則以 repo 內的版本為準，它會演進。

---

## 步驟 1：判斷值不值得存

先想清楚「這次 session 有什麼是三個月後的我會慶幸有記下來的」。如果答案是「沒有」，就直接告訴使用者並停止——**寧可不存，也不要塞垃圾進第二大腦**。

### 該存

- 可重用的**結論**與**決策理由**（為什麼選 A 不選 B）
- 踩過的坑 + 解法
- 對某個工具／技術／方法的**評估結果**
- 生活事件的決策與行動計劃
- 想法、假設（明確標記為未驗證）

### 不該存

- ❌ 任何密鑰、token、密碼、他人個資 —— **絕對禁止，發現就整段拿掉**
- ❌ 大段程式碼 → 改存「連結 + 一句話說明它解決什麼」
- ❌ 操作流水帳（「執行了 ls」「讀了三個檔案」）
- ❌ 網路上一查就有的通用知識，除非你有獨特的理解角度
- ❌ 只在這次 session 有意義、下次用不到的東西
- ❌ 沒把握的事實 —— 要嘛不寫，要嘛明確寫成「推測：…」

### 寫作口吻

寫給**未來的使用者本人**看，不是寫對話紀錄。不要出現「我們剛才討論了…」「使用者問我…」。中文為主，技術術語保留原文。

---

## 步驟 2：取得 repo

**不要假設本機有 clone，也不要動使用者當下的工作目錄。** 每次都從 GitHub 取一份淺 clone 到暫存目錄：

```bash
WORK="$(mktemp -d)/mybrain"
gh repo clone FATESAIKOU/MyBrain "$WORK" -- --depth 1
git -C "$WORK" switch -c "sync/$(date +%F)-<kebab-case-短-slug>"
```

- 用 `gh repo clone`（不是 `git clone`）——這是 private repo，需要 gh 的認證
- branch 名撞到就在 slug 後加 `-2`、`-3`

---

## 步驟 3：讀規則（必做，不可跳過）

```bash
cat "$WORK/index.md"
```

「使用規則」一節是**唯一權威**，涵蓋目錄結構、檔名、日誌與主題檔的連結方式、圖片擺放、外部產出參照、信任狀態。**照它寫。**

同時看一下要寫入的目錄現有內容，避免重複建檔：

```bash
cat "$WORK/技術/index.md"        # 依你要寫的分類調整
ls "$WORK/日誌/" | tail -5
```

---

## 步驟 4：寫檔

**用 Write／Edit 工具寫，不要用 bash heredoc**——中文和 YAML 用 heredoc 極易出錯。路徑一律 `$WORK/...`。

**規則全在步驟 3 讀到的 `index.md`，本檔不重複**——規則只留一份才不會 drift。這裡只擋四個最常寫錯的點：

- **主題檔一定要在對應日期的日誌留一條相對路徑連結**，否則就是沒有時間座標的孤兒，驗證會擋
- **同主題已有檔案就 append**（檔內用 `## YYYY-MM-DD` 分段），不要新建日期碎片檔
- **圖片放進 `<報告名>/image1.png`**，就在報告旁邊；丟在日誌或根目錄會被判 error
- **你是 AI**：產出一律 `status: draft` 且不填 `verified`

另外**手寫**根目錄 `log.md` 的一條記錄（最上面的日期區塊，格式看既有內容）。

**`index.md` 不要手寫**——下一步用腳本重生。

> `--dry-run` 在這裡停下，把打算寫的檔案與內容印出來給使用者看。

---

## 步驟 5：重生 index，然後驗證

**這兩支是這個 bundle 的標準操作腳本，一定要跑，不要自己手工做它們的事。**

```bash
python3 "$WORK/.okf/reindex.py"  "$WORK"   # 依實際檔案重生各層 index.md、同步日誌摘要
python3 "$WORK/.okf/validate.py" "$WORK"   # 驗證標頭、連結鏈、圖片配置
```

`reindex.py` 會讀各檔 frontmatter 的 `title` / `description` 產生 index 條目，並把日誌裡 `→ [名稱](路徑) — 摘要` 的摘要同步成目標檔現行的 description。它只重生自動區塊，`index.md` 裡手寫的「使用規則」原樣保留。

`validate.py` 的結果：

- **有 error 就修好再繼續，不要帶著錯誤開 PR。** 它會指出檔案位置與修法
- warning 是待辦不是壞掉（例如外部 repo 出了新報告還沒接進來），可以放行
- 跑不起來（缺 PyYAML 等）就照 `index.md` 的規則人工自檢，不要中斷流程

---

## 步驟 6：Commit / Push / 開 PR

```bash
git -C "$WORK" add -A
git -C "$WORK" status --short          # 確認只動了你預期的檔案
git -C "$WORK" commit -m "sync: <一句話說明這次存了什麼>"
git -C "$WORK" push -u origin HEAD
```

PR body 先用 Write 工具寫到暫存檔（避免中文換行的 shell escaping 問題），再：

```bash
gh pr create -R FATESAIKOU/MyBrain --base main \
  --head "$(git -C "$WORK" branch --show-current)" \
  --title "sync: <摘要>" --body-file <暫存檔路徑>
```

PR body 要有：這次存了什麼（檔案 + type + 一句說明的表格）、來源（在哪個專案的 session 產生）、Review 重點（內容是否正確、有無誤植密鑰、分類是否合理）。

開完 PR 後 GitHub Actions 會自動再跑一次完整驗證（含外部 repo 覆蓋檢查）。

---

## 步驟 7：清理

**不論成功失敗都要做**：

```bash
rm -rf "$(dirname "$WORK")"
```

分支已經 push 到 remote，PR 不受影響。最後回報 PR 網址 + 一句話說存了什麼。

---

## 失敗處理

| 狀況 | 做法 |
|---|---|
| 沒有值得存的內容 | 直接說明並停止，不開空 PR |
| `gh` 未登入 | 停止並提示 `gh auth login`，不要嘗試改用 https clone |
| clone 失敗 | 回報錯誤並停止，不要退回去找本機路徑 |
| 驗證有 error | 修好再開 PR；修不掉就回報並保留暫存目錄讓使用者接手 |
| push 被拒 | 回報錯誤，清理暫存目錄，不要重試覆蓋 |
| 內容含密鑰 | **立刻停止**，告訴使用者發現了什麼，不要 commit |
