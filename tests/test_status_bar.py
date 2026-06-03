# -*- coding: utf-8 -*-
"""Status bar: compact token formatting and the in-flight estimate marker."""

from __future__ import annotations

from paw.widgets.status_bar import StatusBar, _fmt_count


def test_fmt_count_compacts_large_numbers():
    assert _fmt_count(0) == "0"
    assert _fmt_count(842) == "842"
    assert _fmt_count(6370) == "6.4k"
    assert _fmt_count(6000) == "6k"  # trailing .0 trimmed
    assert _fmt_count(1_540_000) == "1.54M"
    assert _fmt_count(2_000_000) == "2M"


def test_token_counts_rendered_compactly():
    bar = StatusBar()
    bar.set(tok_in=1200, tok_out=6370)
    summary = bar.summary
    assert "↑1.2k" in summary
    assert "↓6.4k" in summary
    assert "~" not in summary  # exact, not an estimate


def test_estimate_is_marked_with_tilde():
    bar = StatusBar()
    bar.set(tok_in=1200, tok_out=512, tok_out_approx=True)
    assert "↓~512" in bar.summary
