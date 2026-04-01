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
- **重要**：Claude Code 二進位是 Bun 打包的，必須用 **Bun** 執行腳本，Node.js 的 FNV-1a hash 結果完全不同！

### userID 來源
```
config.oauthAccount?.accountUuid  // OAuth 登入用戶
?? config.userID                   // API Key 用戶（存在 ~/.claude.json）
?? 'anon'
```

**OAuth 用戶**：accountUuid 不可直接修改，需使用另一種方法（見下方說明）

## 適用對象

- **API Key 用戶**（非 OAuth）：可直接修改 `~/.claude.json` 的 `userID` 欄位
- **OAuth 用戶**：需參考 OAuth 專用方法

---

## 操作流程（API Key 用戶）

### 步驟 1：確認腳本位置

腳本 `buddy-reroll.js` 預設放在 `d:\GitHub\buddy\` 目錄下。

確認 Bun 已安裝：
```bash
bun --version
```

### 步驟 2：執行 Reroll 腳本

基本用法（找 legendary，預設找 3 個）：
```bash
cd d:\GitHub\buddy
bun buddy-reroll.js --rarity legendary
```

指定物種 + legendary：
```bash
bun buddy-reroll.js --species duck --rarity legendary
```

常用選項：
```bash
bun buddy-reroll.js --species dragon --rarity legendary --count 1
bun buddy-reroll.js --rarity legendary --shiny          # 要閃光版
bun buddy-reroll.js --species cat --min-stats 80        # 所有屬性>=80
```

可用物種：

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

### 步驟 3：確認找到的 UID

輸出格式：
```
#1 [legendary] duck eye=✦ hat=crown shiny=false
   stats: DEBUGGING:97 PATIENCE:62 CHAOS:55 WISDOM:78 SNARK:71
   uid:   3e75bebd7bfcdf36b2234650415ce51a64d37bcdb8f7db0c5f979cbfe5f3bc66
```

複製 `uid:` 那一行的值。

### 步驟 4：寫入設定檔

**Windows 路徑**：`C:\Users\{username}\.claude.json`（注意：是 `.claude.json` 不是 `.claude/settings.json`）

```json
{
  "userID": "這裡填入找到的 uid",
  // 刪除 companion 欄位（如果存在）
}
```

操作方式：
1. 開啟 `C:\Users\{username}\.claude.json`
2. 找到並修改 `"userID"` 的值為找到的 uid
3. **刪除整個 `"companion"` 欄位**（包含 name、personality、hatchedAt）
4. 儲存檔案

### 步驟 5：重啟並領取

1. 完全關閉 Claude Code（VSCode 擴充也要重啟）
2. 重新開啟
3. 輸入 `/buddy` 領取新寵物

---

## Claude Code 輔助執行

當使用者要求 Claude Code 代為執行時，執行以下步驟：

### 自動執行流程

1. **先判斷用戶類型**：
```bash
grep -o '"oauthAccount"' /c/Users/${USER}/.claude.json
# 有輸出 = OAuth 用戶，走 OAuth 流程
# 無輸出 = API Key 用戶，直接改 userID
```

2. **執行 reroll 腳本**（必須用 bun，不能用 node）：
```bash
cd d:\GitHub\buddy
/c/Users/${USER}/.bun/bin/bun buddy-reroll.js --species <物種> --rarity legendary --count 1
```

3. **API Key 用戶 - 直接寫入 userID**：
```bash
# 備份
cp /c/Users/${USER}/.claude.json /c/Users/${USER}/.claude.json.backup
# 用 Edit 工具修改 userID 欄位，並刪除 companion 欄位
```

4. **OAuth 用戶 - 替換整個 .claude.json**：
```bash
cp /c/Users/${USER}/.claude.json /c/Users/${USER}/.claude.json.backup
cat > /c/Users/${USER}/.claude.json << 'EOF'
{
  "hasCompletedOnboarding": true,
  "theme": "light-daltonized",
  "userID": "<找到的 uid>"
}
EOF
```
然後提示使用者用 `$env:CLAUDE_CODE_OAUTH_TOKEN="<token>"; claude` 啟動

5. **提示使用者執行 `/buddy` 領取**

---

## 驗證找到的 UID

可以先用 `--check` 驗證 uid 對應的寵物：
```bash
bun buddy-reroll.js --check <uid>
```

---

## OAuth 用戶完整流程

**原理**：用 `CLAUDE_CODE_OAUTH_TOKEN` 環境變數登入時，Claude Code **不會**把 `accountUuid` 寫入 `~/.claude.json`，因此 buddy 系統退回使用 `userID` 欄位，讓我們可以注入自訂 UID。

### 步驟 1：取得 OAuth Token

在 PowerShell / 終端機執行（不能在 Claude Code 工具環境中執行，需開獨立視窗）：

```powershell
claude setup-token
```

複製輸出的 token（格式：`sk-ant-oat01-...`）。

### 步驟 2：備份並替換 `~/.claude.json`

Claude Code 輔助執行：

```bash
# 備份
cp /c/Users/${USER}/.claude.json /c/Users/${USER}/.claude.json.backup

# 寫入最小設定 + 目標 userID
cat > /c/Users/${USER}/.claude.json << 'EOF'
{
  "hasCompletedOnboarding": true,
  "theme": "light-daltonized",
  "userID": "<在這裡填入 reroll 腳本找到的 uid>"
}
EOF
```

> 注意：`theme` 保留使用者偏好，`companion` 欄位不寫入（讓系統重新生成名字）

### 步驟 3：用環境變數啟動 Claude Code

在 **PowerShell** 執行（讓 accountUuid 不被寫入）：

```powershell
$env:CLAUDE_CODE_OAUTH_TOKEN="<你的token>"; claude
```

### 步驟 4：執行 `/buddy` 領取

啟動後直接輸入 `/buddy` 即可領到目標寵物。

### 注意事項

- 原始備份在 `~/.claude.json.backup`，如需還原：`cp ~/.claude.json.backup ~/.claude.json`
- 若重啟後還是舊寵物，確認 `.claude.json` 沒有 `oauthAccount` 欄位
- 每次正常啟動 claude（不帶環境變數）可能會重新寫入 `accountUuid`，如需長久保留請每次用 `CLAUDE_CODE_OAUTH_TOKEN` 方式啟動

---

## 常見問題

**Q：腳本跑出來是 legendary，但領到的卻不是？**
A：確認用 `bun` 執行腳本，不能用 `node`。兩者 hash 算法不同！

**Q：修改後重啟還是舊寵物？**
A：確認 `companion` 欄位已完全刪除，不只是清空。

**Q：SALT 改了怎麼辦？**
A：檢查腳本裡的 `const SALT = 'friend-2026-401'` 是否與 Claude Code 版本匹配。可以請 Claude 根據新版本更新腳本。

**Q：找 legendary 要多久？**
A：50 萬次迭代（預設 5000 萬）幾秒內完成，legendary 機率 1%，通常幾秒就能找到。
