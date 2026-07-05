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
    text_surface = apply_font_effects(font.render(text, True, color))

    if FONT_EFFECTS.get("enable_shadow", False):
        shadow_surface = apply_font_effects(font.render(text, True, (0, 0, 0)))
        offx, offy = FONT_EFFECTS.get("shadow_offset", (6, 6))
        offx, offy = int(round(offx)), int(round(offy))

        tw, th = text_surface.get_size()
        sw, sh = shadow_surface.get_size()
        final_w = max(tw, sw + offx)
        final_h = max(th, sh + offy)

        final_surface = pygame.Surface((final_w, final_h), pygame.SRCALPHA)
        final_surface.blit(shadow_surface, (offx, offy))
        final_surface.blit(text_surface, (0, 0))
        return final_surface.convert_alpha()

    return text_surface


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
