# repostory

Self-contained HTML commit-analytics dashboard generated from `git log`.

Point `repostory` at any local git repository and it produces a single HTML file containing an interactive dashboard: commit cadence, author breakdowns, conventional-commit usage, rework signals, co-change coupling, and more. No server, no external assets — just open the file.

## Install

Requires Python 3.9+ and a working `git` on `PATH`.

### From source (recommended while unreleased)

```bash
# 1. Clone the repository
git clone https://github.com/<your-user>/repostory.git
cd repostory

# 2. (Optional but recommended) create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .\.venv\Scripts\activate         # Windows PowerShell

# 3. Upgrade pip, then install the package
python -m pip install --upgrade pip
pip install .

# 4. Verify
repostory --version
```

### From PyPI

Once the first release lands on PyPI:

```bash
pip install repostory
```

### For development

```bash
git clone https://github.com/<your-user>/repostory.git
cd repostory
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

`-e` installs in editable mode so source changes take effect without reinstalling. `[dev]` pulls in `pytest`.

## Usage

```bash
repostory                              # analyse the current directory
repostory --repo /path/to/repo         # point at another repo
repostory --output report.html         # custom output path
repostory --author you@example.com     # filter by author email substring
repostory --fetch                      # `git fetch --all --prune` first
repostory --fast                       # skip --numstat (faster, less detail)
```

Or run as a module:

```bash
python -m repostory --repo /path/to/repo
```

### Options

| Flag              | Default           | Description                                                    |
| ----------------- | ----------------- | -------------------------------------------------------------- |
| `--repo`          | `.`               | Path to the git repository.                                    |
| `--output`        | `repostory.html`  | Output HTML file path.                                         |
| `--author`        | _all_             | Filter commits by author email substring.                      |
| `--fetch`         | off               | Run `git fetch --all --prune` before reading history.          |
| `--fast`          | off               | Skip file-level analysis (no bus factor, hotspots, coupling).  |
| `-v`, `--verbose` | off               | Verbose (DEBUG) logging.                                       |
| `-q`, `--quiet`   | off               | Only show warnings and errors.                                 |
| `--version`       | —                 | Print version and exit.                                        |

## What you get

- **Cadence** — commits per day, week, and rolling averages.
- **Author breakdown** — per-author activity, bus factor, contribution share.
- **Commit types** — conventional-commit type distribution (`feat`, `fix`, `refactor`, …).
- **Rework signal** — share of commits matching rework keywords (`fix`, `revert`, `hotfix`, …).
- **Hotspots** — most-touched files and file-size buckets.
- **Co-change coupling** — files that change together.
- **Velocity** — recent vs. prior 4-week window classification (up / steady / down).
- **Night & weekend share** — when work actually happens.

## Project layout

```
.
├── pyproject.toml
├── README.md
├── src/
│   └── repostory/
│       ├── __init__.py
│       ├── __main__.py     # python -m repostory entrypoint
│       ├── cli.py          # argparse, logging, orchestration
│       ├── git_io.py       # subprocess wrappers around `git log`, `git tag`, …
│       ├── cadence.py      # rolling averages, conventional-commit parsing
│       ├── aggregator.py   # raw commits → structured dashboard payload
│       ├── report.py       # template rendering
│       ├── constants.py    # shared constants
│       └── templates/      # dashboard.html, dashboard.js, styles.css
└── tests/
```

Layered: transport (`cli`) → business logic (`aggregator`, `cadence`) → data access (`git_io`) → rendering (`report` + `templates`). Uses the **src layout** so tests can only import the installed package, not a stray in-tree copy.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## Releases

Releases are **fully automated**. You do not bump versions, write changelogs, or push tags by hand. The workflow is driven by [conventional commits](https://www.conventionalcommits.org/):

| Commit type            | What it does                       |
| ---------------------- | ---------------------------------- |
| `feat: …`              | bumps the **minor** version        |
| `fix: …` / `perf: …`   | bumps the **patch** version        |
| `feat!: …` (or `BREAKING CHANGE:` in the body) | bumps the **major** version |
| `chore:` / `docs:` / `test:` / `ci:` / `style:` | no release                     |

### The pipeline

On every push to `main` (typically a squash-merged PR), `.github/workflows/release.yml` runs:

1. Runs `pytest`.
2. [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) inspects commits since the last tag and decides the next version (or skips if nothing releasable).
3. Updates `pyproject.toml` and `CHANGELOG.md`, commits as `chore(release): vX.Y.Z [skip ci]`, tags `vX.Y.Z`, and publishes a GitHub Release.
4. Builds `sdist` + `wheel`, validates with `twine check`, and uploads to PyPI via **trusted publishing** (OIDC — no API tokens stored).

### One-time setup

1. **PyPI account** — register at https://pypi.org/account/register/ and enable 2FA.
2. **Trusted publisher** — at https://pypi.org/manage/account/publishing/ add a pending publisher:
   - Project: `repostory` · Owner: your GitHub user/org · Repo: this repo · Workflow: `release.yml` · Environment: `pypi`
3. **GitHub environment** — repo *Settings → Environments → New environment* named `pypi`. Add yourself as a required reviewer if you want a manual click before each PyPI push.
4. **Branch protection** — if `main` requires PR reviews or status checks, allow the `github-actions[bot]` user to bypass them, or the release commit will be rejected.

### Cutting a release

Just merge a PR with a `feat:` or `fix:` commit. That's it. To verify before pushing:

```bash
# Preview what the next version would be, without changing anything
pip install python-semantic-release
semantic-release --noop version --print
```

## License

MIT.
