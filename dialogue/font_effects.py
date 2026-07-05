import pygame

from core.config import FONT_EFFECTS, TEXT_RENDERER_CONFIG


def apply_font_effects(text_surface):
    """Apply the same post-processing used by dialogue text."""
    if not FONT_EFFECTS:
        return text_surface

    orig_w, orig_h = text_surface.get_size()
    stretch_factor = (
        float(FONT_EFFECTS.get("stretch_factor", 1.25))
        if FONT_EFFECTS.get("enable_stretched", False)
        else 1.0
    )
    final_w = int(round(orig_w * stretch_factor))
    final_h = orig_h
    processed_surface = text_surface

    if FONT_EFFECTS.get("enable_pixelated", False):
        pixelate_factor = max(1, int(FONT_EFFECTS.get("pixelate_factor", 2)))
        small_w = max(1, orig_w // pixelate_factor)
        small_h = max(1, orig_h // pixelate_factor)
        small_surface = pygame.transform.smoothscale(processed_surface, (small_w, small_h))
        processed_surface = pygame.transform.smoothscale(small_surface, (final_w, final_h))
    elif stretch_factor != 1.0:
        processed_surface = pygame.transform.smoothscale(processed_surface, (final_w, final_h))

    return processed_surface.convert_alpha()


def render_text_with_effects(font, text, color):
    """Render text with the same black outline style as dialogue body text."""
    text_surface = apply_font_effects(font.render(text, True, color))

    if not FONT_EFFECTS.get("enable_shadow", False):
        return text_surface

    outline_surface = apply_font_effects(font.render(text, True, (0, 0, 0)))
    shadow_offset = FONT_EFFECTS.get("shadow_offset", (6, 6))
    outline_width = max(
        2,
        min(3, int(round(max(abs(shadow_offset[0]), abs(shadow_offset[1]))) // 2)),
    )

    tw, th = text_surface.get_size()
    ow, oh = outline_surface.get_size()
    padding = outline_width
    final_surface = pygame.Surface(
        (max(tw, ow) + padding * 2, max(th, oh) + padding * 2),
        pygame.SRCALPHA,
    )

    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx == 0 and dy == 0:
                continue
            final_surface.blit(outline_surface, (padding + dx, padding + dy))

    final_surface.blit(text_surface, (padding, padding))
    return final_surface.convert_alpha()


def get_grid_char_width(font, color, char_spacing):
    sample_surface = font.render("あ", True, color)
    stretch_factor = (
        FONT_EFFECTS.get("stretch_factor", 1.0)
        if FONT_EFFECTS.get("enable_stretched", False)
        else 1.0
    )
    return (
        int(sample_surface.get_width() * stretch_factor * TEXT_RENDERER_CONFIG["grid_char_width_margin"])
        + char_spacing
    )
