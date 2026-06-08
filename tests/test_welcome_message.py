# -*- coding: utf-8 -*-
"""Welcome logo rendering."""

from __future__ import annotations

from paw.widgets.messages import (
    WelcomeMessage,
    _bright_dot_hex,
    _relative_luminance,
)


def test_welcome_logo_palette_changes_rendered_colors():
    welcome = WelcomeMessage(("#071b2c", "#101f3c", "#163857"))
    before = {str(span.style) for span in welcome._render_body().spans}

    welcome._set_palette_colors(("#281b19", "#38261f", "#563722"))
    rendered = welcome._render_body()
    after = {str(span.style) for span in rendered.spans}

    assert "█" in rendered.plain
    assert before != after
    assert "#ff9d4d" not in after


def test_welcome_logo_gradient_animates_vertically():
    welcome = WelcomeMessage(("#071b2c", "#101f3c", "#163857"))
    first = [welcome._gradient_color(row) for row in range(4)]

    welcome._frame += 1
    second = [welcome._gradient_color(row) for row in range(4)]

    assert len(set(first)) == 4
    assert first != second


def test_welcome_logo_dots_are_brighter_than_current_letter_color():
    welcome = WelcomeMessage(("#071b2c", "#101f3c", "#163857"))

    for frame in range(6):
        welcome._frame = frame
        letter_color = welcome._gradient_color(1)
        dot_color = _bright_dot_hex(letter_color)

        assert _relative_luminance(dot_color) > _relative_luminance(
            letter_color
        )


def test_welcome_logo_is_embossed_with_highlight_and_shadow():
    """Block letters carry top/left highlight and bottom/right shadow cells."""
    welcome = WelcomeMessage(("#071b2c", "#101f3c", "#163857"))
    kinds = {kind for row in welcome._shaded_cells() for kind in row}
    assert {"hi", "sh", "base"} <= kinds
