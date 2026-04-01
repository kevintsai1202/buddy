# Buddy Reroll Script

腳本執行前請確認 Bun 已安裝：`bun --version`

執行方式：
```bash
bun buddy-reroll.js --species dragon --rarity legendary --count 1
```

若腳本不存在，將以下內容寫入工作目錄的 `buddy-reroll.js`：

```javascript
#!/usr/bin/env node
// buddy-reroll.js
// Buddy reroll script — supports both Node.js and Bun
// Bun.hash results match actual Claude Code; Node.js (FNV-1a) results do NOT.
//
// Usage:
//   node buddy-reroll.js [options]    # runs with FNV-1a (Node mode)
//   bun  buddy-reroll.js [options]    # runs with Bun.hash (Bun mode)
//
// Options:
//   --species <name>       Target species (duck, cat, dragon, ...)
//   --rarity <name>        Minimum rarity (common, uncommon, rare, epic, legendary)
//   --eye <char>           Target eye style (· ✦ × ◉ @ °)
//   --hat <name>           Target hat (none, crown, tophat, propeller, halo, wizard, beanie, tinyduck)
//   --shiny                Require shiny
//   --min-stats [value]    Require ALL stats >= value (default: 90)
//   --max <number>         Max iterations (default: 50000000)
//   --count <number>       Number of results to find (default: 3)
//   --check <uid>          Check what buddy a specific userID produces
//
// Examples:
//   bun buddy-reroll.js --species duck --rarity legendary --shiny
//   bun buddy-reroll.js --species dragon --min-stats 80
//   bun buddy-reroll.js --check f17c2742a00b2345c22fddc830959a6847ceb561fa06adb26b74b1a91ac657bc

const crypto = require('crypto')

// --- Constants (must match Claude Code source) ---
const SALT = 'friend-2026-401'
const SPECIES = ['duck', 'goose', 'blob', 'cat', 'dragon', 'octopus', 'owl', 'penguin', 'turtle', 'snail', 'ghost', 'axolotl', 'capybara', 'cactus', 'robot', 'rabbit', 'mushroom', 'chonk']
const RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary']
const RARITY_WEIGHTS = { common: 60, uncommon: 25, rare: 10, epic: 4, legendary: 1 }
const RARITY_RANK = { common: 0, uncommon: 1, rare: 2, epic: 3, legendary: 4 }
const EYES = ['·', '✦', '×', '◉', '@', '°']
const HATS = ['none', 'crown', 'tophat', 'propeller', 'halo', 'wizard', 'beanie', 'tinyduck']
const STAT_NAMES = ['DEBUGGING', 'PATIENCE', 'CHAOS', 'WISDOM', 'SNARK']
const RARITY_FLOOR = { common: 5, uncommon: 15, rare: 25, epic: 35, legendary: 50 }

// --- Hash functions ---
function hashFNV1a(s) {
    let h = 2166136261
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i)
        h = Math.imul(h, 16777619)
    }
    return h >>> 0
}

function hashBun(s) {
    return Number(BigInt(Bun.hash(s)) & 0xffffffffn)
}

// --- PRNG (Mulberry32 — same as Claude Code) ---
function mulberry32(seed) {
    let a = seed >>> 0
    return function () {
        a |= 0
        a = (a + 0x6d2b79f5) | 0
        let t = Math.imul(a ^ (a >>> 15), 1 | a)
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296
    }
}

function pick(rng, arr) {
    return arr[Math.floor(rng() * arr.length)]
}

function rollRarity(rng) {
    let roll = rng() * 100
    for (const r of RARITIES) {
        roll -= RARITY_WEIGHTS[r]
        if (roll < 0) return r
    }
    return 'common'
}

function rollStats(rng, rarity) {
    const floor = RARITY_FLOOR[rarity]
    const peak = pick(rng, STAT_NAMES)
    let dump = pick(rng, STAT_NAMES)
    while (dump === peak) dump = pick(rng, STAT_NAMES)
    const stats = {}
    for (const name of STAT_NAMES) {
        if (name === peak) stats[name] = Math.min(100, floor + 50 + Math.floor(rng() * 30))
        else if (name === dump) stats[name] = Math.max(1, floor - 10 + Math.floor(rng() * 15))
        else stats[name] = floor + Math.floor(rng() * 40)
    }
    return stats
}

function createRoller(hashFn) {
    return function rollFull(uid) {
        const rng = mulberry32(hashFn(uid + SALT))
        const rarity = rollRarity(rng)
        const species = pick(rng, SPECIES)
        const eye = pick(rng, EYES)
        const hat = rarity === 'common' ? 'none' : pick(rng, HATS)
        const shiny = rng() < 0.01
        const stats = rollStats(rng, rarity)
        return { rarity, species, eye, hat, shiny, stats }
    }
}

// --- Parse CLI args ---
function parseArgs() {
    const args = process.argv.slice(2)
    const opts = { max: 50_000_000, count: 3 }

    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--species': opts.species = args[++i]; break
            case '--rarity': opts.rarity = args[++i]; break
            case '--eye': opts.eye = args[++i]; break
            case '--hat': opts.hat = args[++i]; break
            case '--shiny': opts.shiny = true; break
            case '--min-stats': {
                const next = args[i + 1]
                opts.minStatsVal = (next && !next.startsWith('--')) ? parseInt(args[++i]) : 90
                break
            }
            case '--max': opts.max = parseInt(args[++i]); break
            case '--count': opts.count = parseInt(args[++i]); break
            case '--check': opts.check = args[++i]; break
            case '--help': case '-h':
                console.log(`Usage: node/bun buddy-reroll.js [options]

Options:
  --species <name>       ${SPECIES.join(', ')}
  --rarity <name>        ${RARITIES.join(', ')}
  --eye <char>           ${EYES.join(' ')}
  --hat <name>           ${HATS.join(', ')}
  --shiny                Require shiny
  --min-stats [value]    Require ALL stats >= value (default: 90)
  --max <number>         Max iterations (default: 50000000)
  --count <number>       Results to find (default: 3)
  --check <uid>          Check what buddy a specific userID produces`)
                process.exit(0)
        }
    }

    if (opts.species && !SPECIES.includes(opts.species)) {
        console.error(`Unknown species: ${opts.species}\nAvailable: ${SPECIES.join(', ')}`)
        process.exit(1)
    }
    if (opts.rarity && !RARITIES.includes(opts.rarity)) {
        console.error(`Unknown rarity: ${opts.rarity}\nAvailable: ${RARITIES.join(', ')}`)
        process.exit(1)
    }
    if (opts.eye && !EYES.includes(opts.eye)) {
        console.error(`Unknown eye: ${opts.eye}\nAvailable: ${EYES.join(' ')}`)
        process.exit(1)
    }
    if (opts.hat && !HATS.includes(opts.hat)) {
        console.error(`Unknown hat: ${opts.hat}\nAvailable: ${HATS.join(', ')}`)
        process.exit(1)
    }
    return opts
}

// --- Main ---
const opts = parseArgs()

const isBun = typeof Bun !== 'undefined'
const hashFn = isBun ? hashBun : hashFNV1a
const rollFull = createRoller(hashFn)
const runtimeLabel = isBun ? 'bun (Bun.hash)' : 'node (FNV-1a)'
const RARITY_STARS = { common: '★', uncommon: '★★', rare: '★★★', epic: '★★★★', legendary: '★★★★★' }

// --- Check mode ---
if (opts.check) {
    console.log(`Runtime: ${runtimeLabel}`)
    console.log(`Checking userID: ${opts.check}\n`)
    const r = rollFull(opts.check)
    console.log(`  Species : ${r.species}`)
    console.log(`  Rarity  : ${r.rarity} ${RARITY_STARS[r.rarity]}`)
    console.log(`  Eye     : ${r.eye}`)
    console.log(`  Hat     : ${r.hat}`)
    console.log(`  Shiny   : ${r.shiny}`)
    console.log(`  Stats   :`)
    for (const name of STAT_NAMES) {
        const val = r.stats[name]
        const bar = '█'.repeat(Math.floor(val / 5)) + '░'.repeat(20 - Math.floor(val / 5))
        console.log(`    ${name.padEnd(10)} ${bar} ${val}`)
    }
    process.exit(0)
}

const filters = []
if (opts.species) filters.push(`species=${opts.species}`)
if (opts.rarity) filters.push(`rarity>=${opts.rarity}`)
if (opts.eye) filters.push(`eye=${opts.eye}`)
if (opts.hat) filters.push(`hat=${opts.hat}`)
if (opts.shiny) filters.push('shiny=true')
if (opts.minStatsVal) filters.push(`all stats>=${opts.minStatsVal}`)

console.log(`Runtime: ${runtimeLabel}${isBun ? '' : ' (results will NOT match Claude Code)'}`)
console.log(`Searching: ${filters.join(', ') || 'any'} (max ${opts.max.toLocaleString()}, find ${opts.count})`)
console.log('')

const minRarityRank = opts.rarity ? RARITY_RANK[opts.rarity] : 0
let found = 0
const startTime = Date.now()

for (let i = 0; i < opts.max; i++) {
    const uid = crypto.randomBytes(32).toString('hex')
    const r = rollFull(uid)

    if (opts.rarity && RARITY_RANK[r.rarity] < minRarityRank) continue
    if (opts.species && r.species !== opts.species) continue
    if (opts.eye && r.eye !== opts.eye) continue
    if (opts.hat && r.hat !== opts.hat) continue
    if (opts.shiny && !r.shiny) continue
    if (opts.minStatsVal && !Object.values(r.stats).every(v => v >= opts.minStatsVal)) continue

    found++
    const statsStr = STAT_NAMES.map(n => `${n}:${r.stats[n]}`).join(' ')
    console.log(`#${found} [${r.rarity}] ${r.species} eye=${r.eye} hat=${r.hat} shiny=${r.shiny}`)
    console.log(`   stats: ${statsStr}`)
    console.log(`   uid:   ${uid}`)
    console.log('')

    if (found >= opts.count) break
}

const elapsed = ((Date.now() - startTime) / 1000).toFixed(1)
if (found === 0) {
    console.log(`No match found in ${opts.max.toLocaleString()} iterations (${elapsed}s)`)
} else {
    console.log(`Found ${found} match(es) in ${elapsed}s`)
}
```
