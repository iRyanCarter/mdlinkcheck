# mdlinkcheck

A small, dependency-free command-line tool that finds broken links in Markdown files.

- Checks relative file links and images
- Validates `#anchor` links against headings
- Ignores links inside fenced code blocks
- Optional `--remote` mode to check `http(s)` URLs
- Exits non-zero when anything is broken, so it drops straight into CI

## Install
```bash
pip install .
```

## Usage
```bash
mdlinkcheck README.md docs/
mdlinkcheck --remote --timeout 5 docs/
```
Example output:
```
docs/guide.md:12: setup.md#install (missing anchor #install)
14 links checked, 1 broken
```

## Development
```bash
pip install pytest
pytest
```

## License
MIT
