"""fxkit: clone vanilla core_2 animation choreography, recolour it properly, and bind it to abilities.

The engine only has the vanilla particle atlas (particles32) and multiplies each tile by the particle's `color`. That is why a
plain tint of a fire template looks muddy: a red tile times a cyan tint is nearly black. This kit
  1. clones the choreography (flags / velocity / delays / on_impact chains / inner containers) of any core_2 animation,
  2. replaces every tile that would render muddy under the requested tint with the neutral tile whose silhouette matches it best,
  3. rewrites the colour rows so the original fade/brightness profile is kept but the hue is ours,
  4. recursively clones on_impact / inner animations so the whole chain is ours.
"""
import copy
import json
import os
from pathlib import Path

import numpy as np
from PIL import Image

CORE = Path(os.environ.get("S2_CORE_DIR") or Path(__file__).resolve().parent.parent.parent / "core_2")
TILE = 16

_ATLAS = None
_STATS = None
_INDEX = None


def atlas():
    global _ATLAS
    if _ATLAS is None:
        im = Image.open(CORE / "assets" / "gfx" / "particles.png").convert("RGBA")
        cols, rows = im.width // TILE, im.height // TILE
        arr = np.asarray(im, dtype=np.float32) / 255.0
        tiles = np.zeros((cols * rows, TILE, TILE, 4), dtype=np.float32)
        for i in range(cols * rows):
            r, c = divmod(i, cols)
            tiles[i] = arr[r * TILE:(r + 1) * TILE, c * TILE:(c + 1) * TILE]
        _ATLAS = tiles
    return _ATLAS


def _lum(rgb):
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def retained(tile_id, tint):
    """Fraction of the tint's brightness that survives multiplying tile * tint (1.0 = tile is white)."""
    t = atlas()[tile_id]
    a = t[..., 3]
    w = a.sum()
    if w < 1e-3:
        return 1.0
    tint = np.asarray(tint[:3], dtype=np.float32) / 255.0
    ty = float(_lum(tint)) or 1.0
    eff = t[..., :3] * tint
    score = float((_lum(eff) * a).sum() / w / ty)
    # hue fidelity: the rendered colour must still point the same way as the tint (green * cyan is not cyan)
    mag = np.linalg.norm(eff, axis=2) * float(np.linalg.norm(tint))
    cos = np.where(mag > 1e-4, (eff @ tint) / np.maximum(mag, 1e-4), 1.0)
    off = float(((cos < 0.96) * a).sum() / w)          # share of the tile that comes out the wrong hue
    return score if off < 0.12 else score * 0.25


def _silhouette(i):
    t = atlas()[i]
    a = t[..., 3]
    y = _lum(t[..., :3])
    if a.sum() > 1e-3:
        y = y / max(1e-3, float((y * a).sum() / a.sum()))   # brightness-normalised structure
    return a, np.clip(y * a, 0, 2)


_SIL = {}


def best_neutral(tile_id, tint, floor=0.8):
    """Closest-looking tile that still shows the tint cleanly."""
    key = (tile_id, tuple(int(x) for x in tint[:3]))
    if key in _SIL:
        return _SIL[key]
    n = atlas().shape[0]
    a0, y0 = _silhouette(tile_id)
    best, best_d = tile_id, 1e9
    for j in range(n):
        if j == tile_id:
            continue
        aj, yj = _silhouette(j)
        if aj.sum() < 4:                       # blank-ish tile
            continue
        if retained(j, tint) < floor:
            continue
        d = float(np.abs(a0 - aj).sum()) + 0.35 * float(np.abs(y0 - yj).sum()) + 0.4 * abs(float(a0.sum()) - float(aj.sum()))
        if d < best_d:
            best, best_d = j, d
    _SIL[key] = best
    return best


def vanilla(ref):
    """core_2 animation by id ('3', 'core_2_Cold_breath') or file stem."""
    global _INDEX
    if _INDEX is None:
        _INDEX = {}
        for f in (CORE / "animations").glob("*.json"):
            try:
                a = json.load(open(f, encoding="utf-8-sig"))
            except Exception:
                continue
            _INDEX.setdefault(str(a.get("id")), a)
            _INDEX.setdefault(f.stem, a)
    ref = str(ref)
    for k in (ref, "core_2_" + ref):
        if k in _INDEX:
            return copy.deepcopy(_INDEX[k])
    for k, v in _INDEX.items():
        if k.endswith("_" + ref) or k.startswith(ref + "_"):
            return copy.deepcopy(v)
    raise FileNotFoundError(ref)


def _row_y(row):
    return 0.299 * row[0] + 0.587 * row[1] + 0.114 * row[2]


def recolor(a, tint, tint2=None, floor_k=0.75, retarget=True, tmap=None, keep=()):
    """tint every particle; alternate to tint2 on every second particle when given (two-tone).
    tmap: explicit {old_tile: new_tile}; keep: tiles that are never swapped (e.g. a chain link)."""
    parts = [p for p in a.get("particles", []) if isinstance(p, dict)]
    ymax = max([_row_y(r) for p in parts for r in (p.get("color") or [[255, 255, 255, 255]])] + [1.0])
    swapped = 0
    tmap = tmap or {}
    for n, p in enumerate(parts):
        base = tint2 if (tint2 is not None and n % 2 == 1) else tint
        if "tile_id" in p and int(p["tile_id"]) in tmap:
            p["tile_id"] = tmap[int(p["tile_id"])]
            swapped += 1
        elif retarget and "tile_id" in p and int(p["tile_id"]) not in keep:
            tid = int(p["tile_id"])
            if retained(tid, base) < 0.6:
                new = best_neutral(tid, base)
                if new != tid:
                    p["tile_id"] = new
                    swapped += 1
        rows = p.get("color") or [[255, 255, 255, 255]]
        out = []
        for r in rows:
            k = max(floor_k, _row_y(r) / ymax)
            out.append([int(min(255, base[0] * k)), int(min(255, base[1] * k)), int(min(255, base[2] * k)),
                        int(r[3]) if len(r) > 3 else 255])
        p["color"] = out
    return swapped


def clone(ref, new_id, name, tint, tint2=None, power=None, sound=None, scale_range=None, floor_k=0.75, tmap=None, keep=(),
          _out=None, _depth=0):
    """Clone `ref` (and everything it chains into) as `new_id`, recoloured. Returns {id: animation}."""
    out = _out if _out is not None else {}
    a = vanilla(ref)
    a["id"] = new_id
    a["name"] = name
    recolor(a, tint, tint2, floor_k, True, tmap, keep)
    if power is not None:
        a["camera_shake"] = {"bounces": 4 if power else 0, "duration": 0.25 if power else 0.0, "power": power, "type": 1}
    if sound is not None:
        a["sound"] = {"id": str(sound), "volume": 100}
    if scale_range:
        for p in a.get("particles", []):
            if isinstance(p, dict) and "explosion_range" in p:
                p["explosion_range"] = max(1, int(round(p["explosion_range"] * scale_range)))
    out[new_id] = a
    # chained animations: on_impact + inner container
    child_n = 0
    seen = {}
    refs = []
    for p in a.get("particles", []):
        if isinstance(p, dict) and p.get("on_impact"):
            refs.append(p)
    if a.get("animation"):
        refs.append(a)
    for holder in refs:
        key = "on_impact" if holder is not a else "animation"
        target = str(holder[key])
        if target in seen:
            holder[key] = seen[target]
            continue
        if _depth > 3:
            continue
        try:
            vanilla(target)
        except FileNotFoundError:
            continue
        child_n += 1
        cid = f"{new_id}_c{child_n}"
        seen[target] = cid
        clone(target, cid, f"{name} {child_n}", tint, tint2, None, None, scale_range, floor_k, tmap, keep, out, _depth + 1)
        holder[key] = cid
    return out


def merge(main, extra, delay=0.0):
    """append the particles of `extra` onto `main` (layering two choreographies in one animation)."""
    for p in extra.get("particles", []):
        q = copy.deepcopy(p)
        q["delay"] = float(q.get("delay") or 0) + delay
        main["particles"].append(q)
    return main

