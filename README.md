# VELMORA — The Poster for a Place That Isn't There

[![make.fun · the-poster-for-a-place-that-i-2-20261121-0539](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![rank](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Anggizx90/the-poster-for-a-place-that-i-2-20261121-0539/rank.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)
[![reward](https://make.fun/badge/the-poster-for-a-place-that-i-2-20261121-0539/Anggizx90/the-poster-for-a-place-that-i-2-20261121-0539/reward.svg)](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?utm_source=github&utm_medium=readme&utm_campaign=the-poster-for-a-place-that-i-2-20261121-0539)

A travel poster for a place that does not exist, drawn entirely in code.
Built for the
[make.fun "The Poster for a Place That Isn't There" bounty](https://make.fun/bounty/the-poster-for-a-place-that-i-2-20261121-0539?ref=ymjg9sbn)
($50, top 20 paid).

## The place

**VELMORA** — a crater lake high in the northern ranges that holds the sky.
On still nights the aurora pools in the water so deeply that glass-sailed
skiffs seem to drift across the stars themselves. A lit boathouse waits on
the shore for the night's last crossing.

## What it does

`main.py` (Python 3.13, Pillow only, no network, no input files) renders the
poster at 1024×1024 and writes it to `/output/entry.png`:

- gradient night sky, aurora curtains with vertical rays, stars, moon
- snow-capped mountain ridges in two depths
- the lake, mirroring the aurora, with a moon path and sail reflections
- two glass-sailed skiffs with warm lanterns, a lit boathouse, pine shore
- the place name **VELMORA** set in Noto Serif Display Black, tracked out
  over a rule with a diamond — the only text in the picture

The render is deterministic: a fixed seed, no timestamps. Re-running
produces byte-identical output.

## Run it

```sh
python3 main.py   # writes /output/entry.png (or ./entry.png if /output is absent)
```

Requires Pillow (`pip install pillow`). The poster font is Noto Serif
Display Black, shipped with most Linux distributions.
