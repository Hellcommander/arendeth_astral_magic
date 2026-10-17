"""Wire the generated Astral icon sheets into the mod: copy sheets, declare them in assets.json, give every ability / passive /
amplifier / stacker its own `image` index (order = tools manifest), fix the skill icon index, add the three missing passive
descriptions, bump the version.

usage: astral_wire.py <mod_dir>
"""
import json
import shutil
import sys
from pathlib import Path

mod = Path(sys.argv[1])
STAGE = Path(r"D:\games\Ai assisted toolkit\Tools\Output\Soulash2\arendeth_astral_magic_assets")
P = "arendeth_astral_magic_"
manifest = json.loads((STAGE / "manifest.json").read_text(encoding="utf-8"))
CELL, COLS = 64, 8

from PIL import Image  # noqa: E402


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def save(p, o):
    Path(p).write_text(json.dumps(o, indent="\t", ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


# ---- sheets -------------------------------------------------------------------------------------------------------------
SHEETS = {"abilities": "abilities.png", "passives": "passive_skills.png", "amplifiers": "amplifiers.png", "stackers": "stackers.png"}
(mod / "assets").mkdir(exist_ok=True)
dims = {}
for grid, fname in SHEETS.items():
    src = STAGE / "assets" / fname
    im = Image.open(src)
    assert im.width == COLS * CELL and im.height % CELL == 0, (fname, im.size)
    shutil.copy2(src, mod / "assets" / fname)
    dims[fname] = [COLS, im.height // CELL]

sheets = [{"name": "skills", "tiles": [1, 1], "file": "assets/skills.png"}]
for name, fname in (("abilities", "abilities.png"), ("amplifiers", "amplifiers.png"),
                    ("passive_skills", "passive_skills.png"), ("stackers", "stackers.png")):
    sheets.append({"name": name, "tiles": dims[fname], "file": f"assets/{fname}"})
save(mod / "assets.json", {"graphics": {"tilesheets": sheets}})
print("assets.json:", [(s["name"], s["tiles"]) for s in sheets])

# ---- image indices ------------------------------------------------------------------------------------------------------
def index_map(grid):
    return {e["key"]: e["index"] for e in manifest[grid]}


missing = []
amap = index_map("abilities")
n = 0
for f in (mod / "abilities").glob("*.json"):
    j = load(f)
    k = j["id"].replace(P, "", 1)
    if k in amap:
        j["image"] = amap[k]
        save(f, j)
        n += 1
    else:
        missing.append(("ability", k))
print("abilities re-indexed:", n)

DESC = {
    "astral_resonance": "Astral harmonics ring through your party: members can parry, gain +5% parry chance and +5% dodge chance, and have a 5% chance to strike back after a parried blow.",
    "Astral_Insight": "Magic-attuned companions draw on your astral insight, gaining half of your stats.",
    "empowered_shatterfrost": "Shatterfrost Sparks gain magic power for each Rupture Spark swarming nearby, so a dense surge hits far harder than a lone spark.",
}
for fname, grid in (("passives.json", "passives"), ("ability_amplifiers.json", "amplifiers"), ("ability_stackers.json", "stackers")):
    data = load(mod / fname)
    m = index_map(grid)
    c = 0
    for j in data:
        k = j["id"].replace(P, "", 1)
        if k in m:
            j["image"] = m[k]
            c += 1
        else:
            missing.append((grid, k))
        if grid == "passives" and k in DESC and not j.get("description"):
            j["description"] = DESC[k]
    save(mod / fname, data)
    print(f"{fname}: {c}/{len(data)} re-indexed")

# ---- skill icon: the skills sheet is a single 1x1 tile, index 2 was out of range --------------------------------------------
sk = load(mod / "skills.json")
for s in sk:
    s["image"] = 0
save(mod / "skills.json", sk)

mj = load(mod / "mod.json")
mj["version"] = "0.1.0"
mj["version_name"] = "Astral Magic Experimental"
save(mod / "mod.json", mj)
print("missing from manifest:", missing or "none")
