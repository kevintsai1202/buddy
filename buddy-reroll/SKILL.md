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

```js
config.oauthAccount?.accountUuid  // OAuth 登入用戶
?? config.userID                   // API Key 用戶（存在 ~/.claude.json）
?? 'anon'
```

Python 腳本自動偵測 userID，OAuth 和 API Key 用戶均適用。

---

## 操作流程

### 步驟 1：確認 Python 已安裝

```bash
py --version      # Windows
python3 --version # Mac / Linux
```

> **Bun 無需另行安裝**：若已安裝 Claude Code，Bun 通常已在系統中。若 `bun --version` 無法執行，再依下方說明安裝。
>
> **Windows（PowerShell）：** `powershell -c "irm bun.sh/install.ps1 | iex"`
> **Mac / Linux：** `curl -fsSL https://bun.sh/install | bash`
>
> 安裝後**重新開啟終端機**再繼續。

### 步驟 2：執行 reroll 腳本

```bash
cd <skill-path>/scripts/claude-pet-rebirth

# Windows
py reroll.py --species owl --rarity legendary

# Mac / Linux
python3 reroll.py --species owl --rarity legendary
```

常用選項：

```bash
# 指定眼睛 + 帽子 + 閃光
py reroll.py --species dragon --rarity legendary --eye ✦ --hat wizard --shiny

# 指定最強屬性
py reroll.py --species cat --rarity epic --peak PATIENCE

# 指定名字（省略則腳本結束前詢問）
py reroll.py --species owl --rarity legendary --name Nipple
```

### 步驟 3：重啟並領取

1. 完全關閉 Claude Code（VSCode 擴充也要重啟）
2. 正常重新開啟
3. 輸入 `/buddy` 領取新寵物

---

## 可用物種

| 物種 | 中文名 | Emoji |
| --- | --- | --- |
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

## 選項說明

| 選項 | 說明 | 預設 |
| --- | --- | --- |
| `--species` | 物種 | 任意 |
| `--rarity` | 稀有度 | legendary |
| `--eye` | 眼睛（`· ✦ × ◉ @ °`） | 任意 |
| `--hat` | 帽子（none/crown/tophat/propeller/halo/wizard/beanie/tinyduck） | 任意 |
| `--shiny` | 閃光版（約 1% 機率，大幅增加搜尋時間） | false |
| `--peak` | 最強屬性（DEBUGGING/PATIENCE/CHAOS/WISDOM/SNARK） | 任意 |
| `--dump` | 最弱屬性 | 任意 |
| `--name` | 寵物名字 | 腳本結束前詢問 |

> ⚠️ **條件越多搜尋越慢**：legendary + shiny + 指定眼睛 + 帽子 + peak 同時指定，期望嘗試次數可達數千萬次。建議優先指定物種與稀有度，其他條件選填。

---

## Claude Code 輔助執行

### Step 1：確認 Python

```bash
py --version 2>&1 || python3 --version 2>&1 || python --version 2>&1
```

### Step 2：詢問用戶偏好（若未在對話中指定）

一次列出所有選項讓用戶選擇：

**物種**（必問）：

```
🦆 duck     🪿 goose    🫧 blob     🐱 cat
🐉 dragon   🐙 octopus  🦉 owl      🐧 penguin
🐢 turtle   🐌 snail    👻 ghost    🦎 axolotl
🦫 capybara 🌵 cactus   🤖 robot    🐰 rabbit
🍄 mushroom 🐈 chonk
（不指定則任意）
```

**稀有度**（必問）：

```
⚪ common  🟢 uncommon  🔵 rare  🟣 epic  🟡 legendary（預設）
```

**眼睛**（選填）：

```
·  ✦  ×  ◉  @  °
（不指定則任意）
```

**帽子**（選填）：

```
none（無）  crown（皇冠）  tophat（大禮帽）  propeller（螺旋帽）
halo（光環） wizard（巫師帽） beanie（毛帽）  tinyduck（小鴨帽）
（不指定則任意）
```

**閃光**（選填）：

```
yes / no（預設 no，開啟後搜尋時間大幅增加）
```

**最強屬性**（選填）：

```
DEBUGGING  PATIENCE  CHAOS  WISDOM  SNARK
（不指定則任意）
```

**名字**（必問）

### Step 3：提醒關閉 Claude Code

> ⚠️ **執行前必須完全關閉 Claude Code**（包含 VSCode 擴充），否則 binary 被佔用會導致 patch 失敗。

### Step 4：組合指令並執行

將偏好組合成 `reroll.py` 參數，帶入 `--name` 避免互動輸入：

```bash
cd <skill-path>/scripts/claude-pet-rebirth
py reroll.py --species <物種> --rarity legendary --name <名字>
```

### Step 5：提示重啟並執行 `/buddy`

---

## 常見問題

**Q：套用後重啟還是舊寵物？**
A：確認 binary 已成功修補（顯示 `verified=True`），且 `companion` 欄位已更新。

**Q：搜尋跑很久找不到？**
A：條件越多越慢。legendary + shiny + 指定眼睛帽子 peak 全部指定，機率約 1/4000萬，需數分鐘。建議減少限制條件。

**Q：SALT 改了怎麼辦？**
A：更新 `scripts/claude-pet-rebirth/patcher.py` 的 `ORIGINAL_SALT` 常數。

**Q：Windows 上 `python` 找不到？**
A：改用 `py` 指令（Windows Python Launcher）。
