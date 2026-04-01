---
name: buddy-reroll
description: 幫助使用者刷出指定物種或稀有度的 Claude Code /buddy 寵物（五星/legendary）。當使用者想要重置 buddy、刷特定物種、刷 legendary 五星寵物時觸發。
---

# Claude Code Buddy Reroll

## 背景原理

Claude Code 的 `/buddy` 寵物系統原理：

- **Bones（骨架）**：外觀、物種、稀有度、屬性，全部由 `hash(userID + SALT)` 確定性生成，每次啟動實時計算
- **Soul（靈魂）**：名字與個性，由模型生成，存在 `~/.claude.json` 的 `companion` 欄位
- **SALT**：`'friend-2026-401'`（Claude Code 2.1.89+）
- **reroll 原理**：暴力搜尋新的 15 字元 salt，使 `hash(userID + newSalt)` 骰出目標寵物，然後 patch Claude Code binary

### userID 來源
```
config.oauthAccount?.accountUuid  // OAuth 登入用戶
?? config.userID                   // API Key 用戶（存在 ~/.claude.json）
?? 'anon'
```

Python 腳本自動偵測 userID，OAuth 和 API Key 用戶均適用。

---

## 操作流程

### 步驟 1：確認系統需求

需要 **Python 3.8+** 與 **Bun**（腳本內部用 Bun 計算 hash）。

```bash
python --version   # 或 python3 / py
bun --version
```

若 Bun 未安裝：

**Windows（PowerShell）：**
```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

**Mac / Linux：**
```bash
curl -fsSL https://bun.sh/install | bash
```

安裝後**重新開啟終端機**再繼續。

### 步驟 2：啟動互動介面

```bash
cd <skill-path>/scripts/claude-pet-rebirth
python main.py
```

### 步驟 3：選取目標寵物

互動介面操作：

| 按鍵 | 功能 |
| --- | --- |
| `Enter` | 重新抽取隨機寵物 |
| `k` | 收藏當前寵物 |
| `p` | 自選模式（指定物種/稀有度/眼睛/帽子/最強屬性） |
| `f` | 查看收藏並套用到 Claude Code |
| `q` | 離開 |

找到喜歡的寵物後按 `k` 收藏，再按 `f` 套用。

### 步驟 4：重啟並領取

1. 完全關閉 Claude Code（VSCode 擴充也要重啟）
2. 正常重新開啟（不需要帶環境變數）
3. 輸入 `/buddy` 領取新寵物

---

## 可用物種

| 物種 | 中文名 | Emoji |
|------|--------|-------|
| duck | 小鴨 | 🦆 |
| goose | 鵝鵝 | 🪿 |
| blob | 軟泥怪 | 🫧 |
| cat | 貓貓 | 🐱 |
| dragon | 龍 | 🐉 |
| octopus | 章魚 | 🐙 |
| owl | 貓頭鷹 | 🦉 |
| penguin | 企鵝 | 🐧 |
| turtle | 烏龜 | 🐢 |
| snail | 蝸牛 | 🐌 |
| ghost | 幽靈 | 👻 |
| axolotl | 六角恐龍 | 🦎 |
| capybara | 水豚 | 🦫 |
| cactus | 仙人掌 | 🌵 |
| robot | 機器人 | 🤖 |
| rabbit | 兔兔 | 🐰 |
| mushroom | 蘑菇 | 🍄 |
| chonk | 肥貓 | 🐈 |

稀有度（由低到高）：common(60%) → uncommon(25%) → rare(10%) → epic(4%) → legendary(1%)

---

## Claude Code 輔助執行

當使用者要求 Claude Code 代為執行時：

### Step 1：確認系統需求

```bash
python --version 2>&1 || python3 --version 2>&1 || py --version 2>&1
bun --version 2>&1
```

若未安裝，依平台引導安裝 Bun 後提示重新開啟終端機。

### Step 2：詢問用戶偏好（若未在對話中指定）

**物種**（必問）：
```
你想要哪種寵物？
🦆 duck  🪿 goose  🫧 blob  🐱 cat  🐉 dragon  🐙 octopus
🦉 owl   🐧 penguin 🐢 turtle 🐌 snail 👻 ghost  🦎 axolotl
🦫 capybara 🌵 cactus 🤖 robot 🐰 rabbit 🍄 mushroom 🐈 chonk
（不指定則任意物種）
```

**稀有度**（必問）：
```
⚪ common  🟢 uncommon  🔵 rare  🟣 epic  🟡 legendary（預設）
```

**眼睛、帽子、閃光、最強/最弱屬性**（選填，可略過）

### Step 3：啟動互動介面

```bash
cd <skill-path>/scripts/claude-pet-rebirth
python main.py
```

引導用戶：按 `p` 進入自選模式輸入偏好，找到目標後按 `k` 收藏，按 `f` 套用。

### Step 4：提示重啟並執行 `/buddy`

---

## 常見問題

**Q：套用後重啟還是舊寵物？**
A：確認 binary 已成功修補（套用時顯示 `verified: True`），且 `companion` 欄位已更新。

**Q：SALT 改了怎麼辦？**
A：更新 `scripts/claude-pet-rebirth/patcher.py` 裡的 `ORIGINAL_SALT` 常數，使其與新版 Claude Code 一致。

**Q：找 legendary 要多久？**
A：腳本多核心並行搜尋，legendary 機率 1%，通常數秒內完成。
