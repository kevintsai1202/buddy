# 🐉 Claude Code Buddy Reroll

> 刷出你想要的 Claude Code `/buddy` 五星寵物

![五星傳奇龍](assets/5star-dragon.png)

---

## 介紹

Claude Code 的 `/buddy` 功能可以領養一隻專屬寵物，但官方沒有提供重置入口。

本工具透過逆向分析寵物生成演算法，暴力搜尋能生成**指定物種 + 稀有度**的 salt，直接 patch Claude Code binary，永久生效。

---

## 原理

寵物的外觀、稀有度、屬性全部由以下公式確定性生成：

```
hash(userID + SALT)  →  Mulberry32 PRNG  →  寵物屬性
```

- **SALT**：`friend-2026-401`（Claude Code 2.1.89+）
- **Hash**：使用 Bun 的 wyhash，Python 腳本內部呼叫 Bun subprocess 計算
- **userID 來源**：`oauthAccount.accountUuid`（OAuth 用戶）> `userID`（API Key 用戶）

**reroll 方式**：搜尋新的 15 字元 salt，使 `hash(userID + newSalt)` 骰出目標寵物，然後將 Claude Code binary 中的舊 salt 替換為新 salt，重啟後永久生效，OAuth 和 API Key 用戶均適用。

---

## 可用寵物

| 物種 | 中文名 | Emoji | 物種 | 中文名 | Emoji |
| --- | --- | --- | --- | --- | --- |
| duck | 小鴨 | 🦆 | snail | 蝸牛 | 🐌 |
| goose | 鵝鵝 | 🪿 | ghost | 幽靈 | 👻 |
| blob | 軟泥怪 | 🫧 | axolotl | 六角恐龍 | 🦎 |
| cat | 貓貓 | 🐱 | capybara | 水豚 | 🦫 |
| dragon | 龍 | 🐉 | cactus | 仙人掌 | 🌵 |
| octopus | 章魚 | 🐙 | robot | 機器人 | 🤖 |
| owl | 貓頭鷹 | 🦉 | rabbit | 兔兔 | 🐰 |
| penguin | 企鵝 | 🐧 | mushroom | 蘑菇 | 🍄 |
| turtle | 烏龜 | 🐢 | chonk | 肥貓 | 🐈 |

稀有度機率：common(60%) → uncommon(25%) → rare(10%) → epic(4%) → **legendary(1%)**

---

## 需求

- **Python 3.8+**
- **[Bun](https://bun.sh)**（Python 腳本內部用來計算 hash）

```bash
# 安裝 Bun（Windows PowerShell）
powershell -c "irm bun.sh/install.ps1 | iex"

# 安裝 Bun（Mac / Linux）
curl -fsSL https://bun.sh/install | bash
```

---

## 使用方法

### 方法一：直接指定特徵（推薦）

```bash
cd scripts/claude-pet-rebirth
python reroll.py --species owl --rarity legendary
```

常用選項：

```bash
# 指定物種 + 稀有度
python reroll.py --species dragon --rarity legendary

# 指定眼睛 + 帽子
python reroll.py --species cat --rarity legendary --eye ✦ --hat wizard

# 閃光版
python reroll.py --species owl --rarity legendary --shiny

# 指定最強屬性
python reroll.py --species penguin --rarity epic --peak PATIENCE
```

| 選項 | 說明 | 預設 |
| --- | --- | --- |
| `--species` | 物種 | 任意 |
| `--rarity` | 稀有度 | legendary |
| `--eye` | 眼睛（`· ✦ × ◉ @ °`） | 任意 |
| `--hat` | 帽子（none/crown/tophat/propeller/halo/wizard/beanie/tinyduck） | 任意 |
| `--shiny` | 閃光版 | false |
| `--peak` | 最強屬性（DEBUGGING/PATIENCE/CHAOS/WISDOM/SNARK） | 任意 |
| `--dump` | 最弱屬性 | 任意 |

搜尋完成後會詢問寵物名字，輸入後直接 patch binary，重啟 Claude Code 執行 `/buddy` 即可。

---

### 方法二：互動介面

```bash
cd scripts/claude-pet-rebirth
python main.py
```

| 按鍵 | 功能 |
| --- | --- |
| `Enter` | 重新抽取隨機寵物 |
| `k` | 收藏當前寵物 |
| `p` | 自選模式（指定物種/稀有度/眼睛/帽子/最強屬性） |
| `f` | 查看收藏並套用到 Claude Code |
| `q` | 離開 |

---

## Claude Code Skill

本專案附帶 Claude Code skill，讓 AI 助手自動執行整個流程。

### 安裝

```bash
npx skills add https://github.com/kevintsai1202/buddy
```

### 使用方式

安裝後直接告訴 Claude 你想要的寵物，例如：

> 「幫我刷一隻 legendary dragon」
> 「我要閃光版的 legendary cat，帽子要皇冠」
> 「幫我換一隻 legendary owl，最強屬性是 PATIENCE」

Claude 會詢問物種、稀有度等偏好後自動執行腳本、patch binary，完成後提示重啟。

---

## 注意事項

- 本工具基於 Claude Code **2.1.89** 版本分析，若 SALT 更新需同步修改 `patcher.py` 的 `ORIGINAL_SALT`
- patch 前會自動備份 binary（`<binary>.rebirth-bak`），可隨時還原
- `userID` 僅用於遙測分析（匿名）與寵物種子，與對話歷史、API key 完全無關

---

## 致謝

本工具基於以下社群研究成果：

- **[Claude Code /buddy 宠物系统逆向分析](https://linux.do/t/topic/1871870)**
  by [@nemomen](https://linux.do/u/nemomen)（LINUX DO）
  — 核心逆向分析：SALT、hash 算法、userID 機制

- **[Claude Oauth登录刷 /buddy 宠物的方法找到了](https://linux.do/t/topic/1873901)**
  by [@NaynIruR / ruri39](https://linux.do/u/ruri39)（LINUX DO）
  — OAuth 用戶解法研究

- **[ClaudePetRebirth](https://github.com/mitchhuang777/ClaudePetRebirth)**
  by [@mitchhuang777](https://github.com/mitchhuang777)
  — Python 互動介面、binary patch 實作

---

## 授權

MIT
