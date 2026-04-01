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

### 步驟 1：確認 Bun 已安裝

腳本路徑：`<skill-path>/scripts/buddy-reroll.js`

> ⚠️ **必須使用 Bun 執行，不可使用 Node.js！**
> Claude Code 二進位以 Bun 打包，使用 `Bun.hash()`。
> Node.js 使用 FNV-1a，hash 結果完全不同，寫入後領到的寵物不符預期。

**Claude 執行：先檢查 Bun 是否已安裝**

```bash
bun --version
```

若指令不存在（exit code 127），依作業系統引導安裝：

**Windows（PowerShell）：**
```powershell
powershell -c "irm bun.sh/install.ps1 | iex"
```

**Mac / Linux：**
```bash
curl -fsSL https://bun.sh/install | bash
```

安裝完成後提示使用者：**重新開啟終端機** 才能使用 `bun` 指令，然後繼續後續步驟。

### 步驟 2：執行 Reroll 腳本

基本用法（找 legendary，預設找 3 個）：
```bash
bun <skill-path>/scripts/buddy-reroll.js --rarity legendary
```

指定物種 + legendary：
```bash
bun <skill-path>/scripts/buddy-reroll.js --species duck --rarity legendary
```

常用選項：
```bash
bun <skill-path>/scripts/buddy-reroll.js --species dragon --rarity legendary --count 1
bun <skill-path>/scripts/buddy-reroll.js --rarity legendary --shiny
bun <skill-path>/scripts/buddy-reroll.js --species cat --min-stats 80
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

#### Step 0：偵測用戶類型

```bash
grep -o '"oauthAccount"' /c/Users/${USER}/.claude.json
# 有輸出 = OAuth 用戶 → 走 ClaudePetRebirth 流程
# 無輸出 = API Key 用戶 → 走 reroll 腳本流程
```

---

### OAuth 用戶流程（ClaudePetRebirth）

> 原理：暴力搜尋 salt，patch Claude Code binary，永久生效，不需環境變數。

#### Step 1：確認系統需求

```bash
bun --version   # 需要 Bun
python --version  # 需要 Python 3.8+
git --version
```

#### Step 2：clone 並啟動

```bash
git clone https://github.com/mitchhuang777/ClaudePetRebirth
cd ClaudePetRebirth
python main.py
```

#### Step 3：引導用戶操作互動介面

告知用戶操作方式：
- `Enter` → 重新抽取隨機寵物
- `k` → 收藏當前寵物
- `p` → 自選模式（指定物種/稀有度/眼睛/帽子/最強屬性）
- `f` → 查看收藏並套用到 Claude Code
- `q` → 離開

套用後重啟 Claude Code，執行 `/buddy` 即可看到新寵物。

---

### API Key 用戶流程（reroll 腳本）

#### Step 0：詢問用戶偏好（若未在對話中指定）

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

   **眼睛、帽子、閃光、屬性下限**（選填，可略過）

#### Step 1：確認 Bun 已安裝

```bash
bun --version
```

#### Step 2：執行 reroll 腳本

```bash
bun <skill-path>/scripts/buddy-reroll.js --species <物種> --rarity legendary --count 1
```

#### Step 3：寫入 userID

```bash
# 備份
cp /c/Users/${USER}/.claude.json /c/Users/${USER}/.claude.json.backup
# 用 Edit 工具修改 userID 欄位，並刪除 companion 欄位
```

#### Step 4：提示重啟並執行 `/buddy`

---

## 驗證找到的 UID

可以先用 `--check` 驗證 uid 對應的寵物：
```bash
bun buddy-reroll.js --check <uid>
```

---

## OAuth 用戶完整流程

**原理**：用 `CLAUDE_CODE_OAUTH_TOKEN` 環境變數啟動時，若 `.claude.json` 只含最小設定（無 `oauthAccount`），buddy 系統會使用 `userID` 欄位計算 hash，而非 `accountUuid`。

> ⚠️ **每次啟動都必須帶環境變數**，否則 `oauthAccount` 會被寫回，reroll 失效。
> ⚠️ **請勿將 token 貼入對話中**，token 一旦暴露應立即在 claude.ai 撤銷並重新產生。

### 步驟 1：取得 OAuth Token

在**獨立 PowerShell**（非 VSCode 終端機）執行：

```powershell
claude setup-token
```

複製輸出的 token（格式：`sk-ant-oat01-...`）。

或至 claude.ai → 帳號設定 → API Keys 產生。

### 步驟 2：執行 reroll 腳本找到目標 UID

```bash
bun <skill-path>/scripts/buddy-reroll.js --species owl --rarity legendary --count 1
```

複製輸出的 `uid:` 值。

### 步驟 3：將 `.claude.json` 設為最小值 + 目標 userID

```bash
# 備份
cp /c/Users/${USER}/.claude.json /c/Users/${USER}/.claude.json.backup

# 寫入最小設定（關鍵：不含 oauthAccount、不含 companion）
cat > /c/Users/${USER}/.claude.json << 'EOF'
{
  "hasCompletedOnboarding": true,
  "theme": "dark",
  "userID": "<在這裡填入 reroll 腳本找到的 uid>"
}
EOF
```

> 關鍵：`hasCompletedOnboarding: true` 防止啟動時觸發完整 OAuth 流程。

### 步驟 4：用環境變數啟動並領取

在**獨立 PowerShell**（不可用 VSCode）執行：

```powershell
$env:CLAUDE_CODE_OAUTH_TOKEN="<你的token>"; claude
```

啟動後立刻輸入 `/buddy` 領取目標寵物。

### 注意事項

- 每次想用目標寵物，都需要用環境變數方式啟動
- 若透過 VSCode 擴充或直接執行 `claude` 啟動，`oauthAccount` 會被寫回，恢復原本寵物
- 備份還原：`cp ~/.claude.json.backup ~/.claude.json`

---

## 常見問題

**Q：腳本跑出來是 legendary，但領到的卻不是？**
A：確認用 `bun` 執行腳本，不能用 `node`。兩者 hash 算法不同！

**Q：修改後重啟還是舊寵物？**
A：OAuth 用戶應改用 ClaudePetRebirth（patch binary）。若使用環境變數方式，確認每次都帶 `CLAUDE_CODE_OAUTH_TOKEN`。

**Q：ClaudePetRebirth 套用後重啟還是舊寵物？**
A：確認 binary 已成功修補（`patch_binary` 步驟顯示 verified），且 `companion` 欄位已更新。

**Q：SALT 改了怎麼辦？**
A：檢查腳本裡的 `const SALT = 'friend-2026-401'` 是否與 Claude Code 版本匹配。可以請 Claude 根據新版本更新腳本。

**Q：找 legendary 要多久？**
A：50 萬次迭代（預設 5000 萬）幾秒內完成，legendary 機率 1%，通常幾秒就能找到。
