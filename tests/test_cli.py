from mdlinkcheck.cli import check_link, extract_links, main, slugify


def write(p, s):
    p.write_text(s, encoding="utf-8")
    return p


def test_slugify():
    assert slugify("Getting Started!") == "getting-started"


def test_extract_skips_code_blocks(tmp_path):
    f = write(tmp_path / "a.md", "[x](b.md)\n```\n[y](nope.md)\n```\n![img](pic.png)\n[r]: ref.md\n")
    assert [(l.line, l.target) for l in extract_links(f)] == [(1, "b.md"), (5, "pic.png"), (6, "ref.md")]


def test_local_and_anchor_checks(tmp_path):
    write(tmp_path / "b.md", "# Usage Guide\n")
    f = write(tmp_path / "a.md", "[ok](b.md#usage-guide) [bad](b.md#nope) [gone](c.md) [web](https://x.y) [m](mailto:a@b.c)\n")
    errs = [check_link(l) for l in extract_links(f)]
    assert errs == [None, "missing anchor #nope", "file not found", None, None]


def test_main_exit_codes(tmp_path, capsys):
    write(tmp_path / "ok.md", "# Top\n[self](#top)\n")
    assert main([str(tmp_path)]) == 0
    write(tmp_path / "bad.md", "[x](missing.md)\n")
    assert main([str(tmp_path)]) == 1
    assert "missing.md (file not found)" in capsys.readouterr().out
