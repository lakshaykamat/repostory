# CLAUDE.md

## Writing code

**Read first.** Before writing anything, explore existing files in that area. Match the patterns, naming, and structure already in place. Do not invent conventions.

**Layered architecture.** Every app separates transport, business logic, and data access. Route handlers don't contain logic. Services don't query the DB if there's a data layer. Don't collapse layers.

**One file, one job.** Files over ~150 lines should be split. Group by feature, not by type.

**Use shared packages.** If the same logic appears in two or more apps, it belongs in a shared package.

**Structured output for LLM calls.** Always use a schema validation library (e.g. Zod, Pydantic). Never parse raw LLM string responses.

**No import-time side effects.** No DB connections, client instantiation, or config loading at module load. Initialize lazily.

**Validate at boundaries only.** Validate user input and external API responses. Trust internal code.

## Git & GitHub

**Commits.** Do not commit or push unless explicitly asked. Do not add `Co-Authored-By: Claude` (or any assistant attribution) to commit messages. Commit as the current git user only.

**PR titles must use conventional commits format.** Squash-merge is the strategy. The PR title becomes the squash commit subject, which is parsed by `python-semantic-release` on every push to `main` — get the prefix wrong and the release won't fire (or will fire with the wrong bump).

`<type>(<scope>): <Description>`

- `type` — one of:
  - `feat` → **minor** bump
  - `fix`, `perf` → **patch** bump
  - `refactor` → **patch** bump (per `[tool.semantic_release.commit_parser_options]` in `pyproject.toml`)
  - `chore` / `docs` / `test` / `ci` / `build` / `style` / `revert` → **no release**
- `scope` — the primary package or area being changed, for changelog grouping
- `Description` — must start with an uppercase letter or digit. Example: `feat(auth): Add OAuth2 login` — not `add OAuth2 login`
- Append `!` after the scope (or include `BREAKING CHANGE:` in the body) to mark a breaking change, triggering a **major** bump: `feat(auth)!: Rename auth header`

**Multi-package PRs.** Touch any number of packages in one PR. If you need different bump types per package, split the PR.

**Pull requests.** Keep descriptions short, professional, free of decoration — no emojis, no assistant-generated footers, no verbose recaps. Write for a product manager, not an engineer: describe behavior, user impact, and flow — not file names, classes, or implementation details. Include an ASCII diagram of the user/system flow whenever the change affects a multi-step interaction, an integration boundary, or a state transition. Structure:

- **Summary** — one or two sentences on what changed and why, in product terms.
- **Flow** — ASCII diagram showing the new or updated flow (omit only if the change has no flow to depict).
- **Changes** — short bullet list of material edits, phrased as user-visible behavior.
- **Test plan** — checklist of what was verified.

Always set labels and an assignee when opening a PR:

- **Assignee** — resolve the current git user to a GitHub handle (`gh api user --jq .login`). Confirm if uncertain rather than guessing.
- **Labels** — pick from `gh label list` for this repo. Choose whatever matches the change. Never invent labels.

## Releases

Releases are **fully automated** by `.github/workflows/release.yml`. Never bump versions, edit `CHANGELOG.md`, create tags, or run `twine upload` by hand. The pipeline does all of it.

- **Trigger.** Every push to `main` (i.e. every squash-merged PR).
- **Driver.** [`python-semantic-release`](https://python-semantic-release.readthedocs.io/) reads commits since the last tag, picks the next version, updates `pyproject.toml` and `CHANGELOG.md`, commits as `chore(release): vX.Y.Z [skip ci]`, tags `vX.Y.Z`, creates a GitHub Release, builds sdist + wheel, and publishes to PyPI via OIDC trusted publishing.
- **Version source of truth.** `project.version` in `pyproject.toml`. Do not edit this manually — the bot owns it.
- **Skip condition.** If no commits since the last tag are `feat`, `fix`, `perf`, or `refactor` (or breaking), no release is cut.
- **The `chore(release): …` commit on `main`** is the bot's. Do not amend it, rebase it away, or revert it without understanding the downstream effect on the next version calculation.

### Previewing a release locally

```bash
pip install python-semantic-release
semantic-release --noop version --print   # prints next version, makes no changes
```

### Don'ts

- Don't run `git tag` manually on `main`. The bot tags.
- Don't add `version =` overrides anywhere else in `pyproject.toml`.
- Don't disable `[skip ci]` in the release commit message — it prevents the test workflow from re-running on the bot's commit and burning a CI cycle.
- Don't merge release-bumping PRs (`feat:` / `fix:`) and non-releasing PRs (`chore:` / `docs:`) in a way that hides the intended bump. If a PR contains a feature, its title must be `feat:`.
