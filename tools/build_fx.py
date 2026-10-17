"""Astral Magic animations (tools/build_fx.py).

Every ability gets its own FX: the choreography of the vanilla animation that already does that job (a cone breath for the frost
cone, the spectral chain for the rift chain, soul rend for soul rend, deflection for the mantle, phaseshift for the swap, ...)
cloned with fxkit and recoloured in the astral palette. Tiles that would turn muddy under the tint are swapped for the
neutral tile with the closest silhouette. Only the game's particle atlas is used.

    python tools/build_fx.py            writes animations/*.json and sets each ability's `animation`
    python tools/build_fx.py --preview  also writes strip/playback previews (s2_fx_preview)

MiniCyclone / LightningAirBurst (and the other hand-made files) are kept as they are.
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fxkit  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
P = "arendeth_astral_magic_"
HAND_MADE = {"Blank_animation", "Fastball_Storm_Lightning", "LightningAirBurst", "MiniCyclone", "MiniCyclonewithfastball"}

CY, VI, PK, WH = (150, 225, 255), (175, 135, 255), (255, 155, 240), (235, 242, 255)
ICE, GOLD, CORR, WIND, STRAIN = (185, 230, 255), (255, 238, 190), (160, 80, 220), (195, 238, 245), (225, 100, 150)


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


# ability id (without prefix) -> spec
#   ref    vanilla animation to clone (id or file stem)        tint / tint2  colours (tint2 alternates particles)
#   merge  [(ref, tint, delay_ms)] layered on top               power         camera shake power
#   keep   tiles never swapped                                  tmap          explicit tile replacements
PLAN = {
    # cones -------------------------------------------------------------------------------------------------------------
    "Astral_Collapse":   dict(ref="Cold_breath", tint=CY, tint2=VI, keep=[1118], power=3),
    "Astral_Frostline":  dict(ref="142_Unlimited_Power_Lightning", tint=ICE, tint2=CY, tmap={780: 758, 363: 758}, power=1),
    # chains / lines / rushes -------------------------------------------------------------------------------------------
    "frost_charge":      dict(ref="145_Chain_slash", tint=CY, tint2=WH, power=2),
    "riftchain":         dict(ref="Spectral_Chain", tint=VI, tmap={1484: 1499}, power=1),
    "Astral_Soul_Rend":  dict(ref="Soul_Rend", tint=CORR, tint2=VI, power=2),
    "Rupture_Spark_Chain": dict(ref="Energy_Missile", tint=WH, tint2=CY, power=1),
    "Shatterfrost_Collapse": dict(ref="Seismic_Stomp", tint=CY, tint2=WH, power=2),
    "Astral_Wisp_Ambush": dict(ref="31_Lunge", tint=PK, tint2=WH, power=0),
    # sparks / triggers -----------------------------------------------------------------------------------------------
    "Shatterfrost_Surge": dict(ref="Frostbite", tint=CY, tint2=VI, power=0),
    "shatterfrost_surge_trigger": dict(ref="Ice_age", tint=WH, power=0),
    "Rupture_Spark_Trigger": dict(ref="Energy_Missile", tint=ICE, power=0, scale=0.6),
    "Frosty_Trigger":    dict(ref="163_Freeze", tint=ICE, power=0),
    "Stamina_Burning_Light_Trigger": dict(ref="Burning_Light", tint=GOLD, tint2=WH, power=0),
    # corruption ------------------------------------------------------------------------------------------------------
    "Backlash_Surge":    dict(ref="Death_Aura", tint=CORR, tint2=VI, power=1),
    "Corruption_Burst":  dict(ref="Wail_of_Souls", tint=CORR, tint2=VI, power=1),
    # wisps / summons ---------------------------------------------------------------------------------------------------
    "Summon_Astral_Wisp_Swarm": dict(ref="161_Flash_bomb", tint=PK, tmap={328: 1502, 326: 1501, 340: 1344, 282: 1345}, merge=[("Burning_Light", WH, 80)], power=1),
    "Wisp_Powered_Swap": dict(ref="65_Phaseshift", tint=VI, tint2=PK, tmap={523: 1502, 524: 1502}, power=0),
    "Astral_Recrystallization": dict(ref="Resurrection", tint=PK, tint2=WH, power=0),
    "Astral_Crystal_Cage": dict(ref="119_Ground_breaker", tint=PK, tint2=VI, merge=[("4_Fireball_explosion", PK, 100)], power=1,
                                merge_tmap={376: 553, 377: 554, 378: 555, 379: 556, 380: 557, 381: 1344, 382: 1345, 383: 1346, 364: 554}),
    # self buffs / auras -----------------------------------------------------------------------------------------------
    "Astral_Frost_Aura": dict(ref="Frost_armor", tint=CY, tint2=WH, tmap={928: 743, 929: 744, 930: 745, 931: 746}, power=0),
    "Astral_Mantle":     dict(ref="77_Deflection", tint=VI, tint2=PK, tmap={576: 745, 577: 744, 777: 746}, power=0),
    "Astral_Windstorm_Barrier": dict(ref="219_Cleanse", tint=WIND, tint2=WH, power=0),
    "Astral_Overdrawn":  dict(ref="Terrible_Laughter", tint=STRAIN, tint2=CORR, power=0),
    "Astral_Discharge":  dict(ref="Glaciation", tint=WH, tint2=CY, power=0),
}

abil = {}
for f in (ROOT / "abilities").glob("*.json"):
    a = json.load(open(f, encoding="utf-8-sig"))
    abil[a["id"]] = a

anims, fx = {}, {}
for short, spec in PLAN.items():
    aid = P + short
    if aid not in abil:
        print("skip (no ability):", short)
        continue
    name = abil[aid]["name"]
    new_id = P + slug(name) + "_fx"
    out = fxkit.clone(spec["ref"], new_id, f"{name} FX", spec["tint"], spec.get("tint2"), spec.get("power"),
                      scale_range=spec.get("scale"), keep=tuple(spec.get("keep", ())), tmap=spec.get("tmap"))
    main = out[new_id]
    for ref, tint, delay in spec.get("merge", []):
        extra = fxkit.vanilla(ref)
        fxkit.recolor(extra, tint, None, 0.75, True, spec.get("merge_tmap"))
        fxkit.merge(main, extra, delay)
    anims.update(out)
    fx[aid] = new_id

print("animations:", len(anims), "bound abilities:", len(fx))
print("abilities without new FX:", [k.replace(P, "") for k in abil if k not in fx])

adir = ROOT / "animations"
adir.mkdir(exist_ok=True)
for f in adir.glob("*.json"):
    if f.stem not in HAND_MADE:
        f.unlink()
for i, a in anims.items():
    (adir / f"{i[len(P):]}.json").write_text(json.dumps(a, indent="\t", ensure_ascii=False), encoding="utf-8", newline="\n")
patched = 0
for f in (ROOT / "abilities").glob("*.json"):
    a = json.load(open(f, encoding="utf-8-sig"))
    if a.get("id") in fx and a.get("animation") != fx[a["id"]]:
        a["animation"] = fx[a["id"]]
        f.write_text(json.dumps(a, indent="\t", ensure_ascii=False), encoding="utf-8", newline="\n")
        patched += 1
print("wrote", len(anims), "animations, patched", patched, "abilities")

if "--preview" in sys.argv:
    SK = Path(r"D:\games\Ai assisted toolkit\Tools\Soulash2\SkillCreator")
    sys.path.insert(0, str(SK))
    sys.path.insert(0, str(SK.parent))
    from s2_fx_preview import write_preview_pack  # noqa: E402
    dest = Path(r"D:\games\Ai assisted toolkit\Tools\Output\Soulash2\_fx_preview\astral_magic")
    import shutil
    shutil.rmtree(dest, ignore_errors=True)
    for short in PLAN:
        aid = fx.get(P + short)
        if aid:
            children = [x for i, x in anims.items() if i != aid and i.startswith(aid + "_c")]
            write_preview_pack(anims[aid], dest / short, extras=children)
    print("previews written to", dest)



