# Releasing Lumberjack

This document describes how to release a new version of Lumberjack.

## Prerequisites

1. **PyPI Trusted Publishing** must be configured:
   - Go to https://pypi.org/manage/account/publishing/
   - Add trusted publisher with:
     - Owner: `jwmossmoz`
     - Repository: `lumberjack`
     - Workflow: `release.yml`
     - Environment: `pypi`

2. **GitHub Environment** `pypi` must exist (already created)

## Release Process

### 1. Update Version Numbers

Update the version in these files:

```bash
# pyproject.toml
version = "X.Y.Z"

# src/lumberjack/__init__.py
__version__ = "X.Y.Z"

# src/lumberjack/client.py (User-Agent string)
"User-Agent": "lumberjack/X.Y.Z",
```

### 2. Update CHANGELOG.md

Move items from `[Unreleased]` to a new version section:

```markdown
## [Unreleased]

## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature

### Changed
- Changed behavior

### Fixed
- Bug fix
```

Update the links at the bottom:

```markdown
[Unreleased]: https://github.com/jwmossmoz/lumberjack/compare/vX.Y.Z...HEAD
[X.Y.Z]: https://github.com/jwmossmoz/lumberjack/releases/tag/vX.Y.Z
```

### 3. Commit and Tag

```bash
git add -A
git commit -m "Release vX.Y.Z"
git tag vX.Y.Z
git push && git push --tags
```

### 4. Verify Release

1. Check GitHub Actions: https://github.com/jwmossmoz/lumberjack/actions
2. Verify PyPI: https://pypi.org/project/lumberjack/
3. Verify GitHub Release: https://github.com/jwmossmoz/lumberjack/releases

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):

- **MAJOR** (X): Breaking API changes
- **MINOR** (Y): New features, backward compatible
- **PATCH** (Z): Bug fixes, backward compatible

## Troubleshooting

### PyPI Publishing Fails

1. Verify trusted publisher is configured on PyPI
2. Check the `pypi` environment exists in GitHub repo settings
3. Review the workflow logs for specific errors

### Tag Already Exists

```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag (if pushed)
git push origin :refs/tags/vX.Y.Z
```
