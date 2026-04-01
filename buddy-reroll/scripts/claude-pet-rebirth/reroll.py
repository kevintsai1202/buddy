#!/usr/bin/env python3
"""
reroll.py - 直接指定特徵，一鍵搜尋並套用目標寵物。

用法：
  python reroll.py --species owl --rarity legendary
  python reroll.py --species dragon --rarity legendary --hat wizard --shiny
  python reroll.py --species cat --rarity epic --eye ✦ --peak PATIENCE

選項：
  --species   物種（duck/goose/blob/cat/dragon/octopus/owl/penguin/
                    turtle/snail/ghost/axolotl/capybara/cactus/robot/
                    rabbit/mushroom/chonk）
  --rarity    稀有度（common/uncommon/rare/epic/legendary，預設 legendary）
  --eye       眼睛（· / ✦ / × / ◉ / @ / °，不指定則任意）
  --hat       帽子（none/crown/tophat/propeller/halo/wizard/beanie/tinyduck，
                    不指定則任意）
  --shiny     閃光版（加上此旗標即啟用）
  --peak      最強屬性（DEBUGGING/PATIENCE/CHAOS/WISDOM/SNARK，不指定則任意）
  --dump      最弱屬性（同上，不指定則任意）
  --name      套用後的寵物名字（不指定則使用物種名）
"""

import argparse
import multiprocessing
import sys
import time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    import os
    os.system("")

from constants import SPECIES, RARITIES, EYES, HATS, STAT_NAMES, DEFAULT_PERSONALITIES
from patcher import (
    get_user_id,
    find_claude_binary,
    get_current_salt,
    patch_binary,
    save_anybuddy_config,
    update_companion,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="直接指定特徵，搜尋並套用目標寵物",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--species", choices=SPECIES, help="物種")
    parser.add_argument("--rarity", choices=RARITIES, default="legendary", help="稀有度（預設 legendary）")
    parser.add_argument("--eye", choices=EYES, help="眼睛樣式")
    parser.add_argument("--hat", choices=HATS, help="帽子")
    parser.add_argument("--shiny", action="store_true", help="閃光版")
    parser.add_argument("--peak", choices=STAT_NAMES, help="最強屬性")
    parser.add_argument("--dump", choices=STAT_NAMES, help="最弱屬性")
    parser.add_argument("--name", help="套用後的寵物名字（不指定則使用物種名）")
    return parser.parse_args()


def main():
    args = parse_args()

    # 若未指定 species，eye，hat 則填入「任意」佔位，find_salt 需要完整 desired dict
    # 這裡採用「不指定就不限制」策略：隨機補全缺少的欄位後傳入
    import random
    from constants import EYES as ALL_EYES, HATS as ALL_HATS

    desired = {
        "rarity": args.rarity,
        "species": args.species or random.choice(SPECIES),
        "eye": args.eye or random.choice(ALL_EYES),
        "hat": args.hat or ("none" if args.rarity == "common" else random.choice(ALL_HATS)),
        "shiny": args.shiny,
    }
    if args.peak:
        desired["peak"] = args.peak
    if args.dump:
        desired["dump"] = args.dump

    # 若未指定某欄位，find_salt 需要改為「接受任意值」
    # 重新包裝 desired，用 None 表示「不限制」
    desired_filter = {
        "rarity": args.rarity,
        "species": args.species,        # None = 任意
        "eye": args.eye,                # None = 任意
        "hat": args.hat,                # None = 任意
        "shiny": args.shiny if args.shiny else None,
        "peak": args.peak,
        "dump": args.dump,
    }

    print(f"\n目標特徵：")
    print(f"  物種：{args.species or '任意'}")
    print(f"  稀有度：{args.rarity}")
    print(f"  眼睛：{args.eye or '任意'}")
    print(f"  帽子：{args.hat or '任意'}")
    print(f"  閃光：{'是' if args.shiny else '否'}")
    if args.peak:
        print(f"  最強屬性：{args.peak}")
    if args.dump:
        print(f"  最弱屬性：{args.dump}")
    print()

    # 取得 userID
    try:
        user_id = get_user_id()
        print(f"User ID: {user_id[:12]}...")
    except Exception as e:
        print(f"錯誤：無法讀取 userID - {e}")
        sys.exit(1)

    # 取得 binary
    try:
        binary_path = find_claude_binary()
        print(f"Binary: {binary_path}")
    except Exception as e:
        print(f"錯誤：無法找到 Claude Code binary - {e}")
        sys.exit(1)

    # 取得目前 salt
    try:
        old_salt = get_current_salt(binary_path)
        print(f"目前 salt: {old_salt}\n")
    except Exception as e:
        print(f"錯誤：無法讀取目前 salt - {e}")
        sys.exit(1)

    # 搜尋 salt
    cpu_count = multiprocessing.cpu_count()
    print(f"開始搜尋（{cpu_count} 核心）...")

    _last_print = [0.0]

    def on_progress(info):
        now = info["elapsed"]
        if now - _last_print[0] < 2.0:
            return
        _last_print[0] = now
        rate = info["rate"]
        rate_str = f"{rate/1000:.0f}k/s" if rate < 1e6 else f"{rate/1e6:.1f}M/s"
        sys.stdout.write(
            f"\r  {info['attempts']:,} 次嘗試  {rate_str}  {now:.0f}s"
        )
        sys.stdout.flush()

    # 建立實際用於搜尋的 desired（缺少欄位用隨機值填補，讓 find_salt 內部匹配）
    # 採用修改後的 _find_salt_flexible 方式
    result = _find_salt_flexible(user_id, desired_filter, on_progress)

    sys.stdout.write("\r" + " " * 60 + "\r")
    print(f"找到！共嘗試 {result['attempts']:,} 次，耗時 {result['elapsed']:.1f}s")
    print(f"新 salt：{result['salt']}\n")

    # 顯示實際屬性
    stats = result.get("stats", {})
    if stats:
        print("實際屬性：")
        for name, val in stats.items():
            print(f"  {name:<12} {val}")
    print()

    # Patch binary
    try:
        patch = patch_binary(binary_path, old_salt, result["salt"])
        print(f"Binary 已修補（{patch['replacements']} 處，verified={patch['verified']}）")
        print(f"備份：{patch['backup_path']}")
    except Exception as e:
        print(f"錯誤：patch 失敗 - {e}")
        sys.exit(1)

    # 儲存設定
    save_anybuddy_config({
        "salt": result["salt"],
        "previousSalt": old_salt,
        "species": result["species"],
        "rarity": args.rarity,
        "eye": result["eye"],
        "hat": result["hat"],
        "appliedTo": binary_path,
        "appliedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })

    # 更新 companion
    species = result["species"]
    personality = DEFAULT_PERSONALITIES.get(species, "A loyal coding companion.")
    if args.name:
        name = args.name
    else:
        name = input(f"幫你的 {species} 取個名字（直接 Enter 使用 {species.capitalize()}）：").strip()
        if not name:
            name = species.capitalize()
    update_companion(name=name, personality=personality)
    print(f"\n寵物名字：{name}")
    print("完成！重啟 Claude Code 後執行 /buddy 即可看到新寵物。\n")


def _worker_flexible(args):
    """多核心 worker：搜尋一個批次，回傳符合條件的 salt 或 None。"""
    import random
    import string
    from constants import SPECIES, EYES, HATS
    from patcher import bun_hash_batch, mulberry32, pick, roll_rarity, roll_stats_from_rng

    user_id, desired_filter, batch_size, seed = args
    rnd = random.Random(seed)
    chars = string.ascii_letters + string.digits

    rarity = desired_filter["rarity"]
    want_species = desired_filter["species"]
    want_eye = desired_filter["eye"]
    want_hat = desired_filter["hat"]
    want_shiny = desired_filter.get("shiny")
    want_peak = desired_filter.get("peak")
    want_dump = desired_filter.get("dump")

    salts = ["".join(rnd.choices(chars, k=15)) for _ in range(batch_size)]
    keys = [user_id + s for s in salts]
    hashes = bun_hash_batch(keys)

    for salt, h in zip(salts, hashes):
        rng = mulberry32(h)
        r = roll_rarity(rng)
        if r != rarity:
            continue
        sp = pick(rng, SPECIES)
        if want_species and sp != want_species:
            continue
        eye = pick(rng, EYES)
        if want_eye and eye != want_eye:
            continue
        hat = "none" if r == "common" else pick(rng, HATS)
        if want_hat and hat != want_hat:
            continue
        shiny = rng() < 0.01
        if want_shiny and not shiny:
            continue
        stats, peak, dump = roll_stats_from_rng(rng, r)
        if want_peak and peak != want_peak:
            continue
        if want_dump and dump != want_dump:
            continue
        return salt, sp, eye, hat, shiny, stats
    return None


def _find_salt_flexible(user_id, desired_filter, on_progress):
    """
    支援 None 欄位（不限制）的多核心 salt 搜尋。
    """
    import random
    import time
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED

    batch_size = 10000
    num_workers = max(1, multiprocessing.cpu_count())
    queue_depth = num_workers * 2
    total_attempts = 0
    start_time = time.time()

    def make_args():
        return (user_id, desired_filter, batch_size, random.randint(0, 2**32))

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        pending = {executor.submit(_worker_flexible, make_args()) for _ in range(queue_depth)}
        while True:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                total_attempts += batch_size
                result = future.result()
                if result:
                    for f in pending:
                        f.cancel()
                    salt, sp, eye, hat, shiny, stats = result
                    return {
                        "salt": salt,
                        "species": sp,
                        "eye": eye,
                        "hat": hat,
                        "shiny": shiny,
                        "stats": stats,
                        "attempts": total_attempts,
                        "elapsed": time.time() - start_time,
                    }
                pending.add(executor.submit(_worker_flexible, make_args()))
            if on_progress:
                elapsed = time.time() - start_time
                rate = total_attempts / elapsed if elapsed > 0 else 0
                on_progress({"attempts": total_attempts, "elapsed": elapsed, "rate": rate})


if __name__ == "__main__":
    main()
