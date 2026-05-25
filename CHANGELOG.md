# CHANGELOG

## v1.0.0 (2026-05-25)

### Fix

* fix(release): Disable 0.x versions so next release is 1.0.0

Set allow_zero_version = false on python-semantic-release so the project
starts at 1.0.0 onward. Without this, psr ignores the version in
pyproject.toml on first release and computes from commits while in 0.x
mode, producing 0.1.0 instead of the intended 1.0.0. ([`359eb5e`](https://github.com/lakshaykamat/repostory/commit/359eb5ed03a54dc0756faf15e77f7c308806f426))

### Unknown

* Merge pull request #2 from lakshaykamat/chore/semantic-release-stable-versions

fix(release): Disable 0.x versions so next release is 1.0.0 ([`c0ceb95`](https://github.com/lakshaykamat/repostory/commit/c0ceb952a1563e39a3ff0a0cbd9cbc90ef9f52d7))

## v0.1.0 (2026-05-25)

### Chore

* chore(release): v0.1.0 [skip ci] ([`03aad61`](https://github.com/lakshaykamat/repostory/commit/03aad612dd6deccc0bca330ffc324435ac5e24ad))

### Feature

* feat(cli): Improve logging output and auto-open report

- Add colored, timed step-by-step CLI output with total elapsed and file size
- Auto-open generated report in default browser (--no-open to opt out)
- Read __version__ from installed metadata so it stays in sync with pyproject
- Rename dashboard title from &#34;git rhythm&#34; to &#34;repostory&#34;
- Trim README to user-facing content
- Add repostory-env/ to .gitignore ([`2ec53ba`](https://github.com/lakshaykamat/repostory/commit/2ec53ba15df753bdf626e3336006f9d4e3a4f54f))

### Fix

* fix(report): Access templates via parent package for Python 3.9 compat

Python 3.9&#39;s importlib.resources.files() treats a directory without
__init__.py as a namespace package and returns a MultiplexedPath whose
joinpath() ends up calling PosixPath(None). Access templates via
resources.files(&#34;repostory&#34;) / &#34;templates&#34; instead — works on all
supported Python versions. ([`0832ed7`](https://github.com/lakshaykamat/repostory/commit/0832ed7957d51d1838337beac2eb20e69f537288))

### Unknown

* Merge pull request #1 from lakshaykamat/feat/improve-cli-ux

feat(cli): Improve logging output and auto-open report ([`941e632`](https://github.com/lakshaykamat/repostory/commit/941e632878ae8a867e0ee8422af2000b2d8b8899))

## v0.0.0 (2026-05-25)

### Chore

* chore(release): v0.0.0 [skip ci] ([`e427826`](https://github.com/lakshaykamat/repostory/commit/e427826262ae42fc5ab24dc6d427c67207f82372))

### Unknown

* Initial Commit ([`8ad5626`](https://github.com/lakshaykamat/repostory/commit/8ad5626a6f567c2b16f472e54229595c3aba1582))
