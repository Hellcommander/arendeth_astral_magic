"""Astral Magic unique icon pass.

Reuses Generate_Astral_Magic_Assets.py (the user's tile maker: SD3.5 on :1338, black background -> alpha, bleed, opacity,
resumable raw cache) but gives every ability / passive / amplifier / stacker its own subject instead of the rotating motif list,
and packs the sheets with index 0 at the BOTTOM-left as Soulash 2 expects.

usage: astral_icons.py gen [--grid abilities,passives,...]   # SD (resumable), writes staging/assets/*.png
       astral_icons.py wire <mod_dir>                        # copies sheets in, rewrites assets.json + image indices
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

TOOLS = Path(r"D:\games\Ai assisted toolkit\Tools")
sys.path.insert(0, str(TOOLS / "Soulash2"))
sys.path.insert(0, str(TOOLS / "Shared"))
os.environ.setdefault("AAMT_SD_KEEP_SERVER", "1")

STAGE = TOOLS / "Output" / "Soulash2" / "arendeth_astral_magic_assets"
RAW = STAGE / "raw"
OUT = STAGE / "assets"
P = "arendeth_astral_magic_"

# key = id without the mod prefix; the motif is the subject of the icon
ABILITIES = [
    ("Air_Burst_Charge", "a compressed orb of charged air throwing chained lightning arcs outward, pale cyan and white"),
    ("Air_Cyclone_Burst", "a tight mini cyclone funnel ringed with rapid lightning flickers"),
    ("shatterfrost_surge_trigger", "a swarm of tiny ice-blue sparks tearing out of a rift in the dark"),
    ("Astral_Collapse", "a wide cone of devastating astral frost blasting outward, a collapsing star and flying ice shards"),
    ("Astral_Crystal_Cage", "a ring of tall thorned pink and violet crystal spikes caging a glowing core"),
    ("Astral_Discharge", "a ring of fatigue sparks bursting outward and dissolving, a long exhale of cold light"),
    ("Astral_Frost_Aura", "a cold snowflake field ring of light around a small floating wisp"),
    ("frost_charge", "a frosty charged projectile leaving a wisp and chaining arrows of ice between targets"),
    ("Astral_Frostline", "a narrow cone of astral frost with crystalline rime lines piercing straight outward"),
    ("Astral_Mantle", "a dense shimmering mantle of astral force wrapped like a cloak with a frosted rim"),
    ("Astral_Overdrawn", "a cracked overloaded star leaking light, strain fractures, a dim warning haze"),
    ("Astral_Recrystallization", "a dormant crystal wisp reigniting, light blooming from a crystal heart"),
    ("riftchain", "a spectral chain of glowing links lashing in a straight line through a rift"),
    ("Astral_Soul_Rend", "a tear in the astral with ghostly chains seizing several minds, mind-control tendrils"),
    ("Astral_Windstorm_Barrier", "a swirling astral windstorm barrier ring deflecting arrows, wind and frost"),
    ("Astral_Wisp_Ambush", "a timid wisp darting forward in a quick frost-charged streak with a fading afterimage"),
    ("Backlash_Surge", "a corruption shockwave erupting from an overloaded rune, jagged dark purple rings"),
    ("Corruption_Burst", "a small square burst of dark violet corruption with black veins and a disorienting swirl"),
    ("Frosty_Trigger", "a brief pulse of frost lashing out and turning into layered frostburn rings"),
    ("MiniCyclone", "a compact cyclone with a bright eye striking the target and the tiles beside it"),
    ("Rupture_Spark_Chain", "a shatterfrost spark rushing between foes leaving ice-blue arcs, a rebound"),
    ("Rupture_Spark_Trigger", "an icy frost pulse converting into stacked sparks pouring into a funnel"),
    ("Shatterfrost_Collapse", "a volatile frost burst imploding inward, ice shards pulled toward a spark"),
    ("Shatterfrost_Surge", "a flood of many tiny frost sparks torn out of the astral"),
    ("Stamina_Burning_Light_Trigger", "a small white-gold flame of burning light consuming a ring of stamina"),
    ("Summon_Astral_Wisp_Swarm", "a burst of light releasing a swarm of small glowing wisps"),
    ("Wisp_Powered_Swap", "a panicked wisp phasing two silhouettes into each other's place, splitting into fragments"),
]
PASSIVES = [
    ("astral_analysis", "an eye of star-sight reading a target with fine analysis glyph lines"),
    ("astral_acuity", "a crystalline frost needle converting a flash of damage into frostbite"),
    ("astral_recovery", "a glowing fountain of light refilling a well of stamina"),
    ("astral_resonance", "two tuning rings resonating together with parry sparks"),
    ("astral_rupture", "a frost spark swarm tearing out of a rift"),
    ("cold_reclamation", "a frozen skull releasing returning motes of light"),
    ("astral_glide", "a boot leaving a smooth trail of gliding astral light"),
    ("astral_momentum", "a swift streaking comet with wind lines"),
    ("Astral_Echo", "a rune repeating itself in a fading echo of ghost copies"),
    ("Astral_Command_Nexus", "a nexus of linked orbs on a many-armed star web with chains"),
    ("Astral_Command", "a crowned authority sigil above a small obedient wisp companion"),
    ("Astral_Insight", "an open third eye above a constellation map"),
    ("empowered_shatterfrost", "a larger, brighter shatterfrost shard crowned with sparks"),
    ("Astral_Perception", "a hand sensing ripples of nearby magic radiating outward"),
    ("Civilized_Storm_Elemental_Crafting", "a small storm cloud figure bound by a violet crafting ring"),
    ("Civil_Animated_Mannequin_Crafting", "a little animated mannequin held up by a violet crafting thread"),
    ("Civilized_Air_Elemental_Crafting", "a humanoid mass of swirling wind bound by a crafting ring"),
    ("Civilized_Animated_Armor_Crafting", "a floating suit of armor with a pale astral glow inside"),
    ("Civilized_Fire_Elemental_Crafting", "a humanoid mass of flame bound by a crafting ring"),
    ("Civilized_Earth_Elemental_Crafting", "a jagged stone golem bound by a crafting ring"),
    ("Wild_Friendly_Astral_Wisp_Crafting", "a friendly smiling wisp resting over a pink crystal"),
    ("Civilized_Pixie_Crafting", "a tiny winged pixie with butterfly wings holding a crafting thread"),
    ("mastery", "a crowned astral star surrounded by a full ring of small stars"),
]
AMPLIFIERS = [
    ("astral_backstep", "a footstep being pulled backward along displacement trails"),
    ("Challenger_1", "a dangerous astral flare with an enemy focus mark, a single fang"),
    ("Challenger_2", "a dangerous astral flare with an enemy focus mark, a double fang, fiercer"),
    ("Amplifier_Charge", "one bold arrow charging forward a single tile"),
    ("Amplifier_Charge_5", "five stacked chevrons charging far forward"),
    ("Amplifier_Sidestep", "a ghosted figure shifting sideways one tile, one afterimage"),
    ("Amplifier_Sidestep_2", "a ghosted figure shifting sideways two tiles, two afterimages"),
    ("Amplifier_Sidestep_3", "a ghosted figure shifting sideways three tiles, three afterimages"),
    ("Amplifier_Sidestep_4", "a ghosted figure shifting sideways four tiles, four afterimages"),
    ("Amplifier_Burning_Light", "a small astral light burning on a target, a lit flame mark"),
    ("Amplifier_Burn_Stamina_5", "five cracked stamina embers burning away"),
    ("arendeth_astral_echo", "a second weapon swing as a ghost echo of the first"),
    ("Frostbite_Convergence", "frost lines converging into a volatile spike surge"),
    ("Frostburn_Nova_Amplifier", "a frostburn star detonating as a pale nova"),
    ("Astral_AoE_Expansion", "a widened ring of geometric lines expanding outward"),
    ("Astral_Clarity_Surge", "a clear crystal lens with a fast clockwork ripple"),
    ("Astral_Overdrawn", "two overlapping cracked stars striking twice"),
    ("Astral_Tempo_Break", "a shattered hourglass releasing time shards"),
]
STACKERS = [
    ("arendeth_astral_astral_fatigue", "a stack of heavy glowing orbs sinking, a tired star"),
    ("frostburn", "layered flames of cold blue-white frost fire"),
    ("astral_wisp_rupture_sparks_stacks", "a tall column of stacked tiny sparks"),
    ("Frosty_Trigger_Stacker", "a frost target ring with a single pulse on it"),
    ("arendeth_corruption", "creeping dark violet corruption tendrils over a dim star"),
]
GRIDS = {"abilities": ABILITIES, "passives": PASSIVES, "amplifiers": AMPLIFIERS, "stackers": STACKERS}

SUFFIX = ("glowing astral energy, shatterfrost sparks, violet and cyan palette, a single centered emblem filling the frame, "
          "isolated on a pure black background, high contrast, crisp readable silhouette, hand-painted game icon art, no text")
ROLE = {"abilities": "active ability icon", "passives": "passive skill sigil icon",
        "amplifiers": "amplifier rune icon", "stackers": "stacking charge icon built from layered glowing orbs"}


def load_gen():
    spec = importlib.util.spec_from_file_location("astral_gen", TOOLS / "Soulash2" / "Generate_Astral_Magic_Assets.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["astral_gen"] = mod
    spec.loader.exec_module(mod)
    return mod


def prompt_for(grid, idx):
    return f"{ROLE[grid]}, {GRIDS[grid][idx][1]}, {SUFFIX}"


def gen(only):
    from PIL import Image
    g = load_gen()
    g.sd_tile_prompt = lambda grid, idx: prompt_for(grid, idx)      # SdTileSource.tile looks this up at call time
    from s2_icon_pipeline import sd_session
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    failures = []
    with sd_session(use_sd=True) as api:
        src = g.SdTileSource(api, RAW, steps=28, attempts=3)
        for grid, items in GRIDS.items():
            if only and grid not in only:
                continue
            cols = 8
            count = len(items)
            rows = (count + cols - 1) // cols
            opacity = float(g.GRID_DEFS[grid]["opacity"])
            T = g.TILE_SIZE
            sheet = Image.new("RGBA", (cols * T, rows * T), (0, 0, 0, 0))
            print(f"== {grid}: {count} tiles, {rows} rows", flush=True)
            for idx, (key, _m) in enumerate(items):
                try:
                    tile = src.tile(grid, idx, opacity)
                except Exception as exc:        # noqa: BLE001
                    print(f"   FAILED {key}: {exc}", flush=True)
                    failures.append((grid, key))
                    continue
                # index 0 sits bottom-left: row counted from the bottom
                x = (idx % cols) * T
                y = (rows - 1 - idx // cols) * T
                sheet.paste(tile, (x, y))
            name = g.GRID_DEFS[grid]["file"]
            sheet.save(OUT / name)
            print(f"   wrote {OUT / name}  ({cols}x{rows} @ {T}px)", flush=True)
    (STAGE / "manifest.json").write_text(json.dumps(
        {gname: [{"index": i, "key": k, "motif": m} for i, (k, m) in enumerate(items)] for gname, items in GRIDS.items()},
        indent=1), encoding="utf-8")
    print("failures:", failures or "none", flush=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "gen"
    if mode == "gen":
        only = sys.argv[sys.argv.index("--grid") + 1].split(",") if "--grid" in sys.argv else None
        gen(only)
