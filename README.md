# The World in One Day — 27 November 2026

[![make.fun](https://make.fun/badge/news-image-20261127.svg)](https://make.fun/bounty/news-image-20261127)
[![rank](https://make.fun/badge/news-image-20261127/Rkasyz/makefun-news-image-20261127/rank.svg)](https://make.fun/bounty/news-image-20261127)
[![reward](https://make.fun/badge/news-image-20261127/Rkasyz/makefun-news-image-20261127/reward.svg)](https://make.fun/bounty/news-image-20261127)

A one-page newspaper front page summing up Friday 27 November 2026's world news, drawn entirely in code.

[make.fun bounty: Sum up 27 November's world news in one image](https://make.fun/bounty/news-image-20261127)

## The front page

**Lead:** a drone strike in Kuwait kills two Italian workers; Iran denies involvement and Rome demands answers.

**Panels:** the Thanksgiving storm halts the 100th Macy's parade; Gukesh–Sindarov draw Game 3 of the World Chess Championship; Kim Jong Un vows more nuclear weapons; Depardieu is ordered to stand trial over an alleged 2018 rape.

**Wide panel:** Hamas weighs its answer as Israel kills 10 in Gaza. **Ticker:** Black Friday, UK net migration at its lowest since 1997, SpaceX cleared for 1 million satellites, Ebola in Congo passes 12,000 cases, Nepal declares 4,000 landslide victims dead, Trump urges Putin to pull back.

## How it works

`main.py` is pure Python 3 standard library — a hand-rolled 5x7 bitmap font and a hand-rolled PNG encoder, no network, no randomness. It draws the 1024x1024 front page and writes it deterministically to `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`).

```sh
python3 main.py
```

Two runs produce byte-identical output (sha256 `eb5214182b22c630bf74eb8903e3551a10ae971d3d568ebaffd9d07166b1f89e`, 22,836 bytes). `entry.png` in this repo is that exact output.

## License

MIT
