# repostory

Self-contained HTML commit-analytics dashboard generated from `git log`.

Point `repostory` at any local git repository and it produces a single HTML file with an interactive dashboard: commit cadence, author breakdowns, conventional-commit usage, rework signals, co-change coupling, and more. No server, no external assets — just open the file.

## Install

Requires Python 3.9+ and `git` on `PATH`.

```bash
pip install repostory
```

Or from source:

```bash
git clone https://github.com/<your-user>/repostory.git
cd repostory && pip install .
```

## Usage

```bash
repostory                              # analyse the current directory
repostory --repo /path/to/repo         # point at another repo
repostory --output report.html         # custom output path
repostory --author you@example.com     # filter by author email substring
repostory --fetch                      # `git fetch --all --prune` first
repostory --fast                       # skip --numstat (faster, less detail)
```

### Options

| Flag              | Default          | Description                                                   |
| ----------------- | ---------------- | ------------------------------------------------------------- |
| `--repo`          | `.`              | Path to the git repository.                                   |
| `--output`        | `repostory.html` | Output HTML file path.                                        |
| `--author`        | _all_            | Filter commits by author email substring.                     |
| `--fetch`         | off              | Run `git fetch --all --prune` before reading history.         |
| `--fast`          | off              | Skip file-level analysis (no bus factor, hotspots, coupling). |
| `--no-open`       | off              | Do not auto-open the report in a browser when done.           |
| `-v`, `--verbose` | off              | Verbose (DEBUG) logging.                                      |
| `-q`, `--quiet`   | off              | Only show warnings and errors.                                |
| `--version`       | —                | Print version and exit.                                       |

## What you get

- **Cadence** — commits per day, week, and rolling averages.
- **Author breakdown** — per-author activity, bus factor, contribution share.
- **Commit types** — conventional-commit type distribution (`feat`, `fix`, `refactor`, …).
- **Rework signal** — share of commits matching rework keywords (`fix`, `revert`, `hotfix`, …).
- **Hotspots** — most-touched files and file-size buckets.
- **Co-change coupling** — files that change together.
- **Velocity** — recent vs. prior 4-week window classification (up / steady / down).
- **Night & weekend share** — when work actually happens.

## License

MIT.
