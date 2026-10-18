#!/usr/bin/env python3
"""
Guidebook Generator - Professional Application User Guide & Manual Deck Creator
Converts structured JSON/YAML specs into 16:9 PDF presentations & HTML slide decks.
Features:
- Pixel-perfect 16:9 widescreen layout (1920x1080)
- Auto-synchronized callout badges (Action 1 -> Badge 1, Action 2 -> Badge 2)
- Target UI bounding boxes with rounded corners & custom colors
- Smart screenshot cropping & sensitive data redaction (NIK, phone, etc.)
- Multi-role support (Peserta, Admin DPC, Tim Pengawas)
- Full slide suite: Cover, Metrics Cards, Checklist, Roadmap, Timeline, Step Guides, FAQ, Outro
"""

import os
import sys
import json
import math
import argparse
import html
from urllib.parse import quote
from pathlib import Path
from PIL import ImageColor


def rectangle_pixels(rect, size, units="auto"):
    """Legacy auto: x,y <=100 means percent; explicit units avoid ambiguity."""
    if (not isinstance(rect, (list, tuple)) or len(rect) != 4 or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in rect)):
        raise ValueError("Rectangle must contain four finite numbers [x,y,w,h]")
    x, y, w, h = rect
    percent = units == "percent" or (units == "auto" and x <= 100 and y <= 100)
    limit_x, limit_y = (100, 100) if percent else size
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x+w > limit_x or y+h > limit_y:
        raise ValueError("Rectangle outside image bounds or non-positive size")
    sx, sy = (size[0]/100, size[1]/100) if percent else (1, 1)
    box = tuple(round(v) for v in (x*sx, y*sy, (x+w)*sx, (y+h)*sy))
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("Rectangle rounds to an empty area")
    return box


def validate_spec(spec, base_dir):
    """Fail before creating output; this checks structure/assets, not application truth."""
    if not isinstance(spec, dict):
        raise ValueError("Spec must be an object")
    for key in ("title", "subtitle", "organization", "author"):
        if key in spec and not isinstance(spec[key], str):
            raise ValueError(f"{key} must be text")
    slides = spec.get("slides")
    if not isinstance(slides, list) or not slides:
        raise ValueError("slides must be a non-empty list")
    theme = spec.get("theme") or {}
    if not isinstance(theme, dict):
        raise ValueError("theme must be an object")
    for color in theme.values():
        try:
            ImageColor.getrgb(color)
        except (ValueError, TypeError, AttributeError):
            raise ValueError("Invalid theme color") from None
    types = {"cover", "section_header", "cards", "checklist", "roadmap", "timeline", "faq", "outro", "step", "feature"}
    for i, slide in enumerate(slides, 1):
        if not isinstance(slide, dict) or slide.get("type", "step") not in types:
            raise ValueError(f"Slide {i}: unknown type or not an object")
        for key in ("title", "subtitle", "organization", "author", "role", "category", "purpose", "instruction", "warning", "limitations", "notes", "description", "message", "contact"):
            if key in slide and not isinstance(slide[key], str):
                raise ValueError(f"Slide {i}: {key} must be text")
        for key in ("items", "steps", "capabilities", "callouts"):
            if key in slide and (not isinstance(slide[key], list) or any(not isinstance(v, dict) for v in slide[key])):
                raise ValueError(f"Slide {i}: {key} must be a list of objects")
        for key in ("actions", "meta"):
            if key in slide and (not isinstance(slide[key], list) or any(not isinstance(v, str) for v in slide[key])):
                raise ValueError(f"Slide {i}: {key} must be a list of text")
        units = slide.get("coordinate_units", "auto")
        if units not in ("auto", "percent", "pixels"):
            raise ValueError("coordinate_units must be auto, percent or pixels")
        screenshot = slide.get("screenshot")
        if slide.get("type", "step") in ("step", "feature") and not screenshot:
            raise ValueError(f"Slide {i}: screenshot is required (use synthetic assets for demos)")
        size = None
        for asset in (screenshot, slide.get("image")):
            if asset is not None:
                if not isinstance(asset, str) or not asset:
                    raise ValueError(f"Slide {i}: asset path must be non-empty text")
                path = Path(base_dir) / asset
                try:
                    with Image.open(path) as image:
                        image.load()
                        if asset == screenshot:
                            size = image.size
                except (OSError, ValueError) as exc:
                    raise ValueError(f"Slide {i}: unreadable image {path}: {exc}") from exc
        if size:
            if "crop" in slide:
                box = rectangle_pixels(slide["crop"], size, units)
                size = (box[2]-box[0], box[3]-box[1])
            redact = slide.get("redact", [])
            if not isinstance(redact, list):
                raise ValueError("redact must be a list")
            for rect in redact:
                rectangle_pixels(rect, size, units)
            for callout in slide.get("callouts", []):
                if "box" in callout:
                    rectangle_pixels(callout["box"], size, units)
                for key, count in (("arrow", 4), ("badge", 3)):
                    if key in callout:
                        coords = callout[key]
                        if not isinstance(coords, list) or len(coords) != count:
                            raise ValueError(f"{key} must contain {count} values")
                        # Arrows are always percent; legacy badges infer per axis.
                        for axis, value in enumerate(coords[:4 if key == "arrow" else 2]):
                            bound = 100 if key == "arrow" or units == "percent" or (units == "auto" and isinstance(value, (int, float)) and value <= 100) else size[axis % 2]
                            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= bound:
                                raise ValueError(f"{key} coordinate outside image")
                if "color" in callout:
                    ImageColor.getrgb({**DEFAULT_THEME, **theme}.get(callout["color"], callout["color"]))
        # Reject malformed nested display text before Pillow receives it.
        for key in ("items", "steps", "capabilities"):
            for item in slide.get(key, []):
                for field, value in item.items():
                    if field != "highlight" and not isinstance(value, (str, int, float)):
                        raise ValueError(f"Slide {i}: invalid {key}.{field}")
    return spec

from typing import List, Dict, Any, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ---------------------------------------------------------
# CONSTANTS & DEFAULTS
# ---------------------------------------------------------
CANVAS_W = 1920
CANVAS_H = 1080

DEFAULT_THEME = {
    "primary": "#D61A1A",       # Brand red
    "primary_dark": "#991B1B",
    "secondary": "#0F172A",     # Slate dark
    "accent": "#10B981",        # Emerald green for target boxes
    "warning": "#F59E0B",       # Amber for notes
    "danger": "#EF4444",        # Red for callout badges
    "bg": "#F8FAFC",            # Clean light slate
    "card_bg": "#FFFFFF",       # White card
    "text_main": "#0F172A",     # Deep navy black
    "text_muted": "#475569",    # Dark slate gray for high readability
    "border": "#E2E8F0",        # Subtle border
}

# ---------------------------------------------------------
# FONT HELPER
# ---------------------------------------------------------
class FontManager:
    """Finds best available system TrueType fonts with fallbacks and env overrides."""
    def __init__(self):
        env_bold = os.environ.get("GUIDEBOOK_FONT_BOLD")
        env_reg = os.environ.get("GUIDEBOOK_FONT_REG") or os.environ.get("GUIDEBOOK_FONT")

        font_candidates_bold = ([env_bold] if env_bold else []) + [
            r"C:\Windows\Fonts\segoeuib.ttf",
            r"C:\Windows\Fonts\arialbd.ttf",
            r"C:\Windows\Fonts\calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
        ]
        font_candidates_reg = ([env_reg] if env_reg else []) + [
            r"C:\Windows\Fonts\segoeui.ttf",
            r"C:\Windows\Fonts\arial.ttf",
            r"C:\Windows\Fonts\calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/System/Library/Fonts/SFNSText.ttf",
        ]

        self.bold_path = next((p for p in font_candidates_bold if p and os.path.exists(p)), None)
        self.reg_path = next((p for p in font_candidates_reg if p and os.path.exists(p)), None)

    def get_font(self, size: int, bold: bool = False) -> ImageFont.ImageFont:
        path = self.bold_path if bold else self.reg_path
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default(size=size)

FONTS = FontManager()

# ---------------------------------------------------------
# TEXT WRAPPING UTILITY
# ---------------------------------------------------------
def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> List[str]:
    """Wraps text within a given pixel width."""
    if not text:
        return []
    lines = []
    paragraphs = str(text).split("\n")
    for para in paragraphs:
        if not para.strip():
            lines.append("")
            continue
        words = para.split(" ")
        current_line = []
        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_w = bbox[2] - bbox[0]
            if line_w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
        if current_line:
            lines.append(" ".join(current_line))
    return lines

# ---------------------------------------------------------
# DRAWING PRIMITIVES
# ---------------------------------------------------------
def draw_rounded_card(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], radius: int = 16,
                      fill: str = "#FFFFFF", outline: str = "#E2E8F0", width: int = 1):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)

def draw_badge(draw: ImageDraw.ImageDraw, x: int, y: int, radius: int, text: str,
               bg_color: str, text_color: str = "#FFFFFF"):
    """Draws a circular numbered badge with white outline."""
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=bg_color, outline="#FFFFFF", width=3)
    font_size = max(13, int(radius * 1.15))
    font = FONTS.get_font(font_size, bold=True)
    bbox = draw.textbbox((0, 0), str(text), font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x - tw // 2, y - th // 2 - 2), str(text), font=font, fill=text_color)

def draw_arrow(draw: ImageDraw.ImageDraw, p1: Tuple[int, int], p2: Tuple[int, int], color: str, width: int = 5):
    """Draws a prominent directional arrow."""
    draw.line([p1, p2], fill=color, width=width)
    x1, y1 = p1
    x2, y2 = p2
    angle = math.atan2(y2 - y1, x2 - x1)
    head_len = 22
    arrow_angle = math.pi / 6
    h1 = (x2 - head_len * math.cos(angle - arrow_angle), y2 - head_len * math.sin(angle - arrow_angle))
    h2 = (x2 - head_len * math.cos(angle + arrow_angle), y2 - head_len * math.sin(angle + arrow_angle))
    draw.polygon([p2, h1, h2], fill=color)

# ---------------------------------------------------------
# SLIDE BUILDER CLASS
# ---------------------------------------------------------
class GuidebookBuilder:
    def __init__(self, spec: Dict[str, Any], base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or os.getcwd())
        validate_spec(spec, self.base_dir)
        self.spec = spec
        self.theme = {**DEFAULT_THEME, **(spec.get("theme") or {})}
        self.title = spec.get("title", "Panduan Aplikasi")
        self.subtitle = spec.get("subtitle", "")
        self.org = spec.get("organization", "")
        self.author = spec.get("author", "")
        self.slides_spec = spec.get("slides", [])

    def resolve_path(self, rel_or_abs: str) -> Path:
        p = Path(rel_or_abs)
        if p.is_absolute():
            return p
        return self.base_dir / p

    def create_canvas(self) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
        im = Image.new("RGB", (CANVAS_W, CANVAS_H), color=self.theme["bg"])
        draw = ImageDraw.Draw(im)
        return im, draw

    def draw_header_footer(self, draw: ImageDraw.ImageDraw, category: str, page_num: int, total_pages: int):
        """Header and footer with contrast and clear visual hierarchy."""
        # Top Accent Ribbon
        draw.rectangle([80, 48, 88, 108], fill=self.theme["primary"])
        
        # Category/Role Kicker
        f_kicker = FONTS.get_font(18, bold=True)
        draw.text((105, 50), (category or self.title).upper(), font=f_kicker, fill=self.theme["primary"])
        
        # Header Title
        f_title = FONTS.get_font(32, bold=True)
        draw.text((105, 72), self.title, font=f_title, fill=self.theme["text_main"])

        # Footer divider line
        draw.line([80, CANVAS_H - 55, CANVAS_W - 80, CANVAS_H - 55], fill=self.theme["border"], width=1)
        
        # Footer text
        f_foot = FONTS.get_font(16, bold=False)
        footer_text = f"{self.org} • {self.author}" if self.author else self.org
        draw.text((80, CANVAS_H - 42), footer_text, font=f_foot, fill=self.theme["text_muted"])
        
        # Page counter
        page_str = f"{page_num} / {total_pages}"
        f_page = FONTS.get_font(16, bold=True)
        bbox = draw.textbbox((0, 0), page_str, font=f_page)
        draw.text((CANVAS_W - 80 - (bbox[2] - bbox[0]), CANVAS_H - 42), page_str, font=f_page, fill=self.theme["text_muted"])

    # -----------------------------------------------------
    # SLIDE TYPE: COVER
    # -----------------------------------------------------
    def render_cover(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        
        # Top-right decorative brand wedges
        draw.polygon([(CANVAS_W - 420, 0), (CANVAS_W, 0), (CANVAS_W, 520)], fill=self.theme["primary"])
        draw.polygon([(CANVAS_W - 240, 0), (CANVAS_W, 0), (CANVAS_W, 300)], fill=self.theme["primary_dark"])

        # Main Card
        card_w, card_h = 1320, 800
        cx, cy = 100, 140
        draw_rounded_card(draw, (cx, cy, cx + card_w, cy + card_h), radius=24, fill=self.theme["card_bg"],
                          outline=self.theme["border"], width=2)
        
        # Brand red indicator bar
        draw.rectangle([cx + 60, cy + 70, cx + 72, cy + 220], fill=self.theme["primary"])
        
        # Organization
        f_org = FONTS.get_font(24, bold=True)
        draw.text((cx + 90, cy + 70), (data.get("organization") or self.org).upper(), font=f_org, fill=self.theme["primary"])
        
        # Main Title
        f_main = FONTS.get_font(56, bold=True)
        draw.text((cx + 90, cy + 110), data.get("title", self.title), font=f_main, fill=self.theme["text_main"])
        
        # Subtitle
        sub = data.get("subtitle", self.subtitle)
        if sub:
            f_sub = FONTS.get_font(28, bold=False)
            draw.text((cx + 90, cy + 180), sub, font=f_sub, fill=self.theme["text_muted"])

        # Divider
        draw.line([cx + 60, cy + 250, cx + card_w - 60, cy + 250], fill=self.theme["border"], width=1)

        # Description paragraph
        desc = data.get("description", "")
        if desc:
            f_body = FONTS.get_font(22, bold=False)
            lines = wrap_text(desc, f_body, card_w - 180, draw)
            y_pos = cy + 290
            for line in lines:
                draw.text((cx + 90, y_pos), line, font=f_body, fill=self.theme["text_main"])
                y_pos += 38

        # Status Chips / Pills
        meta_items = data.get("meta", [])
        if meta_items:
            mx = cx + 90
            my = cy + 560
            for item in meta_items:
                badge_text = str(item)
                f_m = FONTS.get_font(18, bold=True)
                bbox = draw.textbbox((0, 0), badge_text, font=f_m)
                bw = (bbox[2] - bbox[0]) + 40
                draw.rounded_rectangle([mx, my, mx + bw, my + 50], radius=10, fill=self.theme["bg"], outline=self.theme["border"], width=1)
                draw.text((mx + 20, my + 13), badge_text, font=f_m, fill=self.theme["primary"])
                mx += bw + 20

        # Author signature
        author = data.get("author", self.author)
        if author:
            f_auth = FONTS.get_font(20, bold=True)
            draw.text((cx + 90, cy + card_h - 65), author, font=f_auth, fill=self.theme["text_main"])

        # Optional cover image
        img_path = data.get("image")
        if img_path:
            p = self.resolve_path(img_path)
            if p.exists():
                try:
                    cov_img = Image.open(p)
                    cov_img.thumbnail((360, 520))
                    im.paste(cov_img, (CANVAS_W - 480, 260))
                except Exception:
                    pass

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: SECTION HEADER (Divider slide)
    # -----------------------------------------------------
    def render_section_header(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()

        # Side bar accent
        draw.rectangle([0, 0, 36, CANVAS_H], fill=self.theme["primary"])

        card_box = (140, 180, CANVAS_W - 140, CANVAS_H - 180)
        draw_rounded_card(draw, card_box, radius=24, fill=self.theme["card_bg"], outline=self.theme["border"], width=2)

        cx, cy = 200, 280
        # Role / Section Badge
        sec_num = data.get("section_number", "")
        if sec_num:
            draw_badge(draw, cx + 45, cy + 50, 42, str(sec_num), self.theme["primary"])
            cx += 130

        f_sec = FONTS.get_font(26, bold=True)
        draw.text((cx, cy + 15), data.get("role", "BAGIAN PANDUAN").upper(), font=f_sec, fill=self.theme["primary"])

        f_title = FONTS.get_font(56, bold=True)
        lines = wrap_text(data.get("title", ""), f_title, CANVAS_W - cx - 260, draw)
        ty = cy + 70
        for l in lines:
            draw.text((cx, ty), l, font=f_title, fill=self.theme["text_main"])
            ty += 70

        desc = data.get("description", "")
        if desc:
            f_desc = FONTS.get_font(24, bold=False)
            dlines = wrap_text(desc, f_desc, CANVAS_W - cx - 260, draw)
            ty += 20
            for dl in dlines:
                draw.text((cx, ty), dl, font=f_desc, fill=self.theme["text_muted"])
                ty += 36

        self.draw_header_footer(draw, "MODUL PANDUAN", page_num, total_pages)
        return im

    # -----------------------------------------------------
    # SLIDE TYPE: CARDS (Grid of metrics or topics)
    # -----------------------------------------------------
    def render_cards(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, data.get("category", "OVERVIEW"), page_num, total_pages)

        # Slide Title
        f_st = FONTS.get_font(36, bold=True)
        draw.text((80, 130), data.get("title", "Materi & Struktur"), font=f_st, fill=self.theme["text_main"])

        items = data.get("items", [])
        if not items:
            return im

        n = len(items)
        spacing = 28
        margin_x = 80
        total_w = CANVAS_W - (margin_x * 2)
        card_w = (total_w - (spacing * (n - 1))) // n
        card_h = 700
        card_y = 210

        for idx, it in enumerate(items):
            cx = margin_x + idx * (card_w + spacing)
            is_highlight = it.get("highlight", False)
            bg_col = self.theme["primary"] if is_highlight else self.theme["card_bg"]
            border_col = self.theme["primary"] if is_highlight else self.theme["border"]
            txt_head = "#FFFFFF" if is_highlight else self.theme["text_main"]
            txt_num = "#FFFFFF" if is_highlight else self.theme["primary"]
            txt_body = "#FFFFFF" if is_highlight else self.theme["text_muted"]

            draw_rounded_card(draw, (cx, card_y, cx + card_w, card_y + card_h), radius=20,
                              fill=bg_col, outline=border_col, width=2)

            # Hero metric
            num_str = str(it.get("value", ""))
            if num_str:
                f_num = FONTS.get_font(74, bold=True)
                draw.text((cx + 36, card_y + 45), num_str, font=f_num, fill=txt_num)
                unit_str = it.get("unit", "")
                if unit_str:
                    f_unit = FONTS.get_font(24, bold=True)
                    draw.text((cx + 36, card_y + 135), unit_str, font=f_unit, fill=txt_body)

            # Divider line inside card
            draw.line([cx + 36, card_y + 195, cx + card_w - 36, card_y + 195],
                      fill=self.theme["border"] if not is_highlight else "#FFFFFF", width=1)

            # Card Title
            f_ct = FONTS.get_font(28, bold=True)
            t_lines = wrap_text(it.get("title", ""), f_ct, card_w - 72, draw)
            ty = card_y + 225
            for tl in t_lines:
                draw.text((cx + 36, ty), tl, font=f_ct, fill=txt_head)
                ty += 38

            # Card Description
            desc = it.get("description", "")
            if desc:
                f_cd = FONTS.get_font(20, bold=False)
                d_lines = wrap_text(desc, f_cd, card_w - 72, draw)
                ty += 18
                for dl in d_lines:
                    draw.text((cx + 36, ty), dl, font=f_cd, fill=txt_body)
                    ty += 32

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: CHECKLIST / RULES
    # -----------------------------------------------------
    def render_checklist(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, data.get("category", "KETENTUAN"), page_num, total_pages)

        f_st = FONTS.get_font(36, bold=True)
        draw.text((80, 130), data.get("title", "Ketentuan Pelaksanaan"), font=f_st, fill=self.theme["text_main"])

        items = data.get("items", [])
        col_w = (CANVAS_W - 160 - 36) // 2
        for idx, it in enumerate(items):
            col = idx % 2
            row = idx // 2
            x = 80 + col * (col_w + 36)
            y = 210 + row * 180

            draw_rounded_card(draw, (x, y, x + col_w, y + 155), radius=16, fill=self.theme["card_bg"],
                              outline=self.theme["border"], width=1)

            step_str = f"{idx + 1:02d}"
            draw_badge(draw, x + 50, y + 50, 26, step_str, self.theme["primary"])

            # Item title
            f_it = FONTS.get_font(24, bold=True)
            draw.text((x + 95, y + 25), it.get("title", ""), font=f_it, fill=self.theme["text_main"])

            # Item description
            f_id = FONTS.get_font(19, bold=False)
            lines = wrap_text(it.get("description", ""), f_id, col_w - 115, draw)
            ly = y + 62
            for l in lines[:3]:
                draw.text((x + 95, ly), l, font=f_id, fill=self.theme["text_muted"])
                ly += 28

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: ROADMAP (Optimized Horizontal Pipeline)
    # -----------------------------------------------------
    def render_roadmap(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, data.get("category", "ALUR SISTEM"), page_num, total_pages)

        f_st = FONTS.get_font(36, bold=True)
        draw.text((80, 130), data.get("title", "Alur Proses"), font=f_st, fill=self.theme["text_main"])

        steps = data.get("steps", [])
        n = len(steps)
        if n == 0:
            return im

        margin_x = 80
        total_w = CANVAS_W - (margin_x * 2)
        step_w = (total_w - (30 * (n - 1))) // n
        step_h = 560
        y = 230

        for i, s in enumerate(steps):
            x = margin_x + i * (step_w + 30)
            draw_rounded_card(draw, (x, y, x + step_w, y + step_h), radius=18, fill=self.theme["card_bg"],
                              outline=self.theme["border"], width=2)

            # Top Ribbon
            ribbon_h = 64
            draw.rounded_rectangle([x, y, x + step_w, y + ribbon_h], radius=18, fill=self.theme["secondary"])
            draw.rectangle([x, y + 30, x + step_w, y + ribbon_h], fill=self.theme["secondary"])

            f_rib = FONTS.get_font(22, bold=True)
            step_label = s.get("label", f"STEP {i+1:02d}")
            r_bbox = draw.textbbox((0, 0), step_label, font=f_rib)
            rw = r_bbox[2] - r_bbox[0]
            draw.text((x + (step_w - rw) // 2, y + 19), step_label, font=f_rib, fill="#FFFFFF")

            # Step title
            f_ti = FONTS.get_font(26, bold=True)
            t_lines = wrap_text(s.get("title", ""), f_ti, step_w - 40, draw)
            ty = y + 95
            for tl in t_lines:
                draw.text((x + 22, ty), tl, font=f_ti, fill=self.theme["text_main"])
                ty += 34

            # Consistent divider across all steps
            draw.line([x + 22, ty + 15, x + step_w - 22, ty + 15], fill=self.theme["border"], width=2)
            ty += 35

            # Step description with increased size & contrast
            f_det = FONTS.get_font(20, bold=False)
            d_lines = wrap_text(s.get("description", ""), f_det, step_w - 44, draw)
            for dl in d_lines:
                draw.text((x + 22, ty), dl, font=f_det, fill=self.theme["text_muted"])
                ty += 30

            # Prominent Arrow between cards (vertically centered)
            if i < n - 1:
                arrow_x = x + step_w + 4
                arrow_y = y + 160
                draw_arrow(draw, (arrow_x, arrow_y), (arrow_x + 22, arrow_y), self.theme["primary"], width=5)

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: TIMELINE / RUNDOWN
    # -----------------------------------------------------
    def render_timeline(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, data.get("category", "JADWAL PELAKSANAAN"), page_num, total_pages)

        f_st = FONTS.get_font(36, bold=True)
        draw.text((80, 130), data.get("title", "Time Frame Pelaksanaan"), font=f_st, fill=self.theme["text_main"])

        items = data.get("items", [])
        y = 220
        for idx, it in enumerate(items):
            card_h = 110
            draw_rounded_card(draw, (80, y, CANVAS_W - 80, y + card_h), radius=14, fill=self.theme["card_bg"],
                              outline=self.theme["border"], width=1)

            # Left number badge
            draw_badge(draw, 130, y + 55, 28, f"{idx+1}", self.theme["secondary"])

            # Activity text
            f_act = FONTS.get_font(24, bold=True)
            draw.text((180, y + 26), it.get("activity", ""), font=f_act, fill=self.theme["text_main"])

            # Detail subtext
            detail = it.get("detail", "")
            if detail:
                f_det = FONTS.get_font(19, bold=False)
                draw.text((180, y + 62), detail, font=f_det, fill=self.theme["text_muted"])

            # Duration badge on the right
            dur = it.get("duration", "")
            if dur:
                f_dur = FONTS.get_font(22, bold=True)
                d_bbox = draw.textbbox((0, 0), dur, font=f_dur)
                dw = (d_bbox[2] - d_bbox[0]) + 40
                dx = CANVAS_W - 120 - dw
                draw.rounded_rectangle([dx, y + 28, dx + dw, y + 82], radius=10, fill=self.theme["primary"])
                draw.text((dx + 20, y + 41), dur, font=f_dur, fill="#FFFFFF")

            y += card_h + 20

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: FAQ
    # -----------------------------------------------------
    def render_faq(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, data.get("category", "FAQ"), page_num, total_pages)

        f_st = FONTS.get_font(36, bold=True)
        draw.text((80, 130), data.get("title", "Pertanyaan & Solusi Kendala"), font=f_st, fill=self.theme["text_main"])

        items = data.get("items", [])
        y = 220
        for it in items:
            q = it.get("question", "")
            a = it.get("answer", "")

            f_q = FONTS.get_font(22, bold=True)
            f_a = FONTS.get_font(20, bold=False)

            qlines = wrap_text(q, f_q, CANVAS_W - 250, draw)
            alines = wrap_text(a, f_a, CANVAS_W - 250, draw)

            ch = 40 + (len(qlines) * 32) + (len(alines) * 30) + 24
            draw_rounded_card(draw, (80, y, CANVAS_W - 80, y + ch), radius=16, fill=self.theme["card_bg"],
                              outline=self.theme["border"], width=1)

            # Left red indicator
            draw.rectangle([80, y, 90, y + ch], fill=self.theme["primary"])
            draw_badge(draw, 130, y + 42, 22, "Q", self.theme["secondary"])

            ty = y + 25
            for ql in qlines:
                draw.text((170, ty), ql, font=f_q, fill=self.theme["text_main"])
                ty += 32

            ty += 8
            for al in alines:
                draw.text((170, ty), al, font=f_a, fill=self.theme["primary"])
                ty += 30

            y += ch + 22

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: STEP (THE CORE SCREENSHOT ANNOTATION SLIDE)
    # -----------------------------------------------------
    def render_step(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        category = data.get("role") or data.get("category") or "PANDUAN SISTEM"
        self.draw_header_footer(draw, category, page_num, total_pages)

        step_num = data.get("step_number", page_num)
        step_title = data.get("title", "Langkah Penggunaan")

        # Step badge & title header
        draw_badge(draw, 120, 150, 32, str(step_num), self.theme["primary"])
        f_st = FONTS.get_font(34, bold=True)
        draw.text((175, 130), step_title, font=f_st, fill=self.theme["text_main"])

        # Geometry: Screenshot Card (Left) vs Instructions Card (Right)
        shot_x, shot_y = 80, 200
        shot_w, shot_h = 1180, 780

        panel_x = 1300
        panel_y = 200
        panel_w = CANVAS_W - panel_x - 80
        panel_h = 780

        # Draw Screenshot Container Card
        draw_rounded_card(draw, (shot_x, shot_y, shot_x + shot_w, shot_y + shot_h), radius=16,
                          fill="#FFFFFF", outline=self.theme["border"], width=2)

        # Load screenshot
        shot_path_str = data.get("screenshot")
        shot_img = None
        if shot_path_str:
            sp = self.resolve_path(shot_path_str)
            if not sp.exists():
                raise FileNotFoundError(f"Screenshot not found: {sp}")
            try:
                shot_img = Image.open(sp).convert("RGB")
            except Exception as e:
                raise ValueError(f"Failed to open screenshot {sp}: {e}") from e

        units = data.get("coordinate_units", "auto")

        # Optional crop (zoom into specific form area)
        crop_box = data.get("crop")
        if shot_img and crop_box:
            box_px = rectangle_pixels(crop_box, shot_img.size, units)
            shot_img = shot_img.crop(box_px)

        # Optional redaction for personal data (e.g. NIK, phone)
        redact_boxes = data.get("redact", [])
        if shot_img and redact_boxes:
            r_draw = ImageDraw.Draw(shot_img)
            sw, sh = shot_img.size
            for rb in redact_boxes:
                r_px = list(rectangle_pixels(rb, (sw, sh), units))
                r_draw.rectangle(r_px, fill="#334155")
                r_draw.text((r_px[0] + 6, r_px[1] + 2), "[DIREDAKSI]", font=FONTS.get_font(12, bold=True), fill="#FFFFFF")

        inner_pad = 16
        inner_w = shot_w - (inner_pad * 2)
        inner_h = shot_h - (inner_pad * 2)

        if shot_img:
            img_w, img_h = shot_img.size
            ratio = min(inner_w / img_w, inner_h / img_h)
            new_w = int(img_w * ratio)
            new_h = int(img_h * ratio)
            resized = shot_img.resize((new_w, new_h), Image.Resampling.LANCZOS)

            paste_x = shot_x + inner_pad + (inner_w - new_w) // 2
            paste_y = shot_y + inner_pad + (inner_h - new_h) // 2
            im.paste(resized, (paste_x, paste_y))

            scale_x = new_w / 100.0
            scale_y = new_h / 100.0

            # Render Annotations & Sync with Actions!
            callouts = data.get("callouts", [])
            for c_idx, c in enumerate(callouts):
                col_name = c.get("color", "accent")
                color = self.theme.get(col_name, col_name)

                # Target Box
                if "box" in c:
                    bx, by, bw, bh = c["box"]
                    if units == "percent" or (units == "auto" and bx <= 100 and by <= 100):
                        real_x = int(paste_x + bx * scale_x)
                        real_y = int(paste_y + by * scale_y)
                        real_w = int(bw * scale_x)
                        real_h = int(bh * scale_y)
                    else:
                        real_x = int(paste_x + bx * (new_w / img_w))
                        real_y = int(paste_y + by * (new_h / img_h))
                        real_w = int(bw * (new_w / img_w))
                        real_h = int(bh * (new_h / img_h))

                    real_w = max(4, real_w)
                    real_h = max(4, real_h)

                    draw.rounded_rectangle([real_x, real_y, real_x + real_w, real_y + real_h],
                                           radius=8, outline=color, width=4)

                    # Auto badge at top-left of box if specified or matching action index
                    badge_label = c.get("badge_label") or str(c_idx + 1)
                    if c.get("auto_badge", True):
                        draw_badge(draw, real_x, real_y, 22, badge_label, self.theme["primary"])

                # Explicit Badge
                elif "badge" in c:
                    bgx, bgy, bgt = c["badge"][0], c["badge"][1], c["badge"][2]
                    if units == "percent" or (units == "auto" and bgx <= 100 and bgy <= 100):
                        real_bx = int(paste_x + bgx * scale_x)
                        real_by = int(paste_y + bgy * scale_y)
                    else:
                        real_bx = int(paste_x + bgx * (new_w / img_w))
                        real_by = int(paste_y + bgy * (new_h / img_h))
                    draw_badge(draw, real_bx, real_by, 22, str(bgt), self.theme["primary"])

                # Arrow
                if "arrow" in c:
                    ax1, ay1, ax2, ay2 = c["arrow"]
                    p1 = (int(paste_x + ax1 * scale_x), int(paste_y + ay1 * scale_y))
                    p2 = (int(paste_x + ax2 * scale_x), int(paste_y + ay2 * scale_y))
                    draw_arrow(draw, p1, p2, color, width=5)
        else:
            draw.rectangle([shot_x + 40, shot_y + 40, shot_x + shot_w - 40, shot_y + shot_h - 40],
                           fill="#F1F5F9", outline=self.theme["border"], width=1)
            f_ph = FONTS.get_font(26, bold=True)
            draw.text((shot_x + 300, shot_y + 350), "[ AREA TAMPILAN SCREENSHOT ]", font=f_ph, fill=self.theme["text_muted"])

        # -------------------------------------------------
        # INSTRUCTION / CAPABILITY PANEL (Right Column)
        # -------------------------------------------------
        draw_rounded_card(draw, (panel_x, panel_y, panel_x + panel_w, panel_y + panel_h), radius=18,
                          fill=self.theme["card_bg"], outline=self.theme["border"], width=2)

        # Check if this slide is a Feature Tour ("capabilities") or Step Procedure ("actions")
        capabilities = data.get("capabilities", [])
        panel_title = "KEMAMPUAN FITUR" if capabilities else "PETUNJUK TINDAKAN"

        # Panel top ribbon
        draw.rounded_rectangle([panel_x, panel_y, panel_x + panel_w, panel_y + 60], radius=18, fill=self.theme["secondary"])
        draw.rectangle([panel_x, panel_y + 30, panel_x + panel_w, panel_y + 60], fill=self.theme["secondary"])

        f_phd = FONTS.get_font(20, bold=True)
        draw.text((panel_x + 30, panel_y + 18), panel_title, font=f_phd, fill="#FFFFFF")

        py = panel_y + 85
        # Main purpose / instruction
        purpose = data.get("purpose") or data.get("instruction", "")
        if purpose:
            f_ins = FONTS.get_font(21, bold=False)
            in_lines = wrap_text(purpose, f_ins, panel_w - 60, draw)
            for il in in_lines:
                draw.text((panel_x + 30, py), il, font=f_ins, fill=self.theme["text_main"])
                py += 30
            py += 15

        # IF CAPABILITIES ARE SPECIFIED (Feature breakdown: What user can do)
        if capabilities:
            f_cap_head = FONTS.get_font(18, bold=True)
            draw.text((panel_x + 30, py), "BISA MELAKUKAN APA SAJA?", font=f_cap_head, fill=self.theme["primary"])
            py += 28

            for c_idx, cap in enumerate(capabilities):
                draw_badge(draw, panel_x + 45, py + 15, 17, str(c_idx + 1), self.theme["primary"])
                f_cname = FONTS.get_font(19, bold=True)
                cap_name = cap.get("name", f"Kemampuan {c_idx+1}")
                draw.text((panel_x + 75, py + 2), cap_name, font=f_cname, fill=self.theme["text_main"])
                py += 26

                cap_desc = cap.get("desc") or cap.get("description", "")
                if cap_desc:
                    f_cdesc = FONTS.get_font(17, bold=False)
                    cd_lines = wrap_text(cap_desc, f_cdesc, panel_w - 95, draw)
                    for cdl in cd_lines:
                        draw.text((panel_x + 75, py), cdl, font=f_cdesc, fill=self.theme["text_muted"])
                        py += 24
                py += 10
            py += 6

        # ELSE IF STEP ACTIONS ARE SPECIFIED (Step by step procedure)
        else:
            actions = data.get("actions", [])
            if actions:
                for a_idx, act in enumerate(actions):
                    draw_badge(draw, panel_x + 45, py + 15, 17, str(a_idx + 1), self.theme["primary"])
                    f_act = FONTS.get_font(19, bold=False)
                    act_lines = wrap_text(str(act), f_act, panel_w - 95, draw)
                    for al in act_lines:
                        draw.text((panel_x + 75, py), al, font=f_act, fill=self.theme["text_main"])
                        py += 28
                    py += 12
                py += 10

        # Limitations / Warning / Alert Card (Red)
        warning = data.get("limitations") or data.get("warning", "")
        if warning:
            f_wn = FONTS.get_font(18, bold=True)
            wlines = wrap_text(warning, f_wn, panel_w - 80, draw)
            wh = 30 + (len(wlines) * 26)
            draw.rounded_rectangle([panel_x + 25, py, panel_x + panel_w - 25, py + wh], radius=10, fill=self.theme["primary"])
            wy = py + 15
            for wl in wlines:
                draw.text((panel_x + 40, wy), wl, font=f_wn, fill="#FFFFFF")
                wy += 26
            py += wh + 18

        # Note / Tip Box (Light background with contrast text)
        notes = data.get("notes", "")
        if notes:
            f_nt = FONTS.get_font(18, bold=False)
            nlines = wrap_text(notes, f_nt, panel_w - 80, draw)
            nh = 30 + (len(nlines) * 25)
            draw.rounded_rectangle([panel_x + 25, py, panel_x + panel_w - 25, py + nh], radius=10,
                                   fill=self.theme["bg"], outline=self.theme["border"], width=1)
            ny = py + 15
            for nl in nlines:
                draw.text((panel_x + 40, ny), nl, font=f_nt, fill=self.theme["text_muted"])
                ny += 25

        return im

    # -----------------------------------------------------
    # SLIDE TYPE: OUTRO (Closing / Support / WhatsApp)
    # -----------------------------------------------------
    def render_outro(self, data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        im, draw = self.create_canvas()
        self.draw_header_footer(draw, "SELESAI", page_num, total_pages)

        card_w, card_h = 1320, 700
        cx = (CANVAS_W - card_w) // 2
        cy = 210
        draw_rounded_card(draw, (cx, cy, cx + card_w, cy + card_h), radius=24, fill=self.theme["card_bg"],
                          outline=self.theme["border"], width=2)

        # Big Thank You Header
        f_ty = FONTS.get_font(64, bold=True)
        main_text = data.get("title", "MATURNUWUN")
        draw.text((cx + 80, cy + 80), main_text, font=f_ty, fill=self.theme["primary"])

        f_org = FONTS.get_font(32, bold=True)
        draw.text((cx + 80, cy + 165), data.get("organization", self.org), font=f_org, fill=self.theme["text_main"])

        author = data.get("author", self.author)
        if author:
            f_au = FONTS.get_font(24, bold=False)
            draw.text((cx + 80, cy + 220), author, font=f_au, fill=self.theme["text_muted"])

        # Divider
        draw.line([cx + 80, cy + 290, cx + card_w - 80, cy + 290], fill=self.theme["border"], width=1)

        # Message
        msg = data.get("message", "Ujian selesai. Silahkan pastikan akun anda telah logout dan konfirmasi ke panitia.")
        f_msg = FONTS.get_font(24, bold=False)
        lines = wrap_text(msg, f_msg, card_w - 160, draw)
        my = cy + 330
        for l in lines:
            draw.text((cx + 80, my), l, font=f_msg, fill=self.theme["text_main"])
            my += 38

        # Support Contact Card
        contact = data.get("contact", "")
        if contact:
            draw.rounded_rectangle([cx + 80, cy + 490, cx + card_w - 80, cy + 590], radius=14,
                                   fill=self.theme["bg"], outline=self.theme["border"], width=1)
            draw_badge(draw, cx + 130, cy + 540, 26, "WA", self.theme["accent"])
            f_ct = FONTS.get_font(22, bold=True)
            draw.text((cx + 180, cy + 520), "LAYANAN BANTUAN & KOORDINASI", font=f_ct, fill=self.theme["text_main"])
            f_cd = FONTS.get_font(20, bold=False)
            draw.text((cx + 180, cy + 552), contact, font=f_cd, fill=self.theme["primary"])

        return im

    # -----------------------------------------------------
    # DISPATCHER & BUILD PIPELINE
    # -----------------------------------------------------
    def render_slide(self, slide_data: Dict[str, Any], page_num: int, total_pages: int) -> Image.Image:
        s_type = slide_data.get("type", "step")
        if s_type == "cover":
            return self.render_cover(slide_data, page_num, total_pages)
        elif s_type == "section_header":
            return self.render_section_header(slide_data, page_num, total_pages)
        elif s_type == "cards":
            return self.render_cards(slide_data, page_num, total_pages)
        elif s_type == "checklist":
            return self.render_checklist(slide_data, page_num, total_pages)
        elif s_type == "roadmap":
            return self.render_roadmap(slide_data, page_num, total_pages)
        elif s_type == "timeline":
            return self.render_timeline(slide_data, page_num, total_pages)
        elif s_type == "faq":
            return self.render_faq(slide_data, page_num, total_pages)
        elif s_type == "outro":
            return self.render_outro(slide_data, page_num, total_pages)
        else:
            return self.render_step(slide_data, page_num, total_pages)

    def generate_all_images(self) -> List[Image.Image]:
        validate_spec(self.spec, self.base_dir)
        images = []
        total = len(self.slides_spec)
        for idx, s_data in enumerate(self.slides_spec):
            im = self.render_slide(s_data, idx + 1, total)
            images.append(im)
        return images

    def build_pdf(self, output_path: str):
        images = self.generate_all_images()
        if not images:
            raise ValueError("No slides to render!")
        out_file = Path(output_path)
        if out_file.is_dir() or (not out_file.suffix and not str(output_path).endswith(".pdf")):
            out_file = out_file / "guidebook.pdf"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        first, rest = images[0], images[1:]
        first.save(out_file, save_all=True, append_images=rest, resolution=100.0)
        return out_file

    def export_images(self, output_dir: str) -> List[Path]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        images = self.generate_all_images()
        saved = []
        for idx, im in enumerate(images):
            p = out_dir / f"slide-{idx+1:02d}.png"
            im.save(p)
            saved.append(p)
        return saved

    def build_html(self, output_path: str, image_dir_rel: str = "slides"):
        """Generates standalone interactive HTML presentation with slide switcher."""
        validate_spec(self.spec, self.base_dir)
        total = len(self.slides_spec)
        esc_title = html.escape(self.title)
        esc_org = html.escape(self.org)
        clean_img_dir = quote(image_dir_rel.replace("\\", "/"), safe="/:-_.")

        html_code = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc_title}</title>
<style>
  :root {{
    --primary: rgb{ImageColor.getrgb(self.theme["primary"])[:3]};
    --bg: #0f172a;
    --card: #1e293b;
    --text: #f8fafc;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: var(--bg);
    color: var(--text);
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
  }}
  header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 24px;
    background: var(--card);
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }}
  .logo {{ font-weight: 700; font-size: 1.1rem; color: var(--text); }}
  .nav-controls {{ display: flex; gap: 8px; align-items: center; }}
  button {{
    background: rgba(255,255,255,0.1);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    font-weight: 600;
  }}
  button:hover {{ background: var(--primary); }}
  main {{
    flex: 1;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 20px;
  }}
  .slide-container {{
    max-width: 95vw;
    max-height: 85vh;
    aspect-ratio: 16 / 9;
    box-shadow: 0 20px 40px rgba(0,0,0,0.6);
    border-radius: 8px;
    overflow: hidden;
    background: #fff;
    display: flex;
    justify-content: center;
    align-items: center;
  }}
  .slide-container img {{
    width: 100%;
    height: 100%;
    object-fit: contain;
  }}
  footer {{
    text-align: center;
    padding: 10px;
    font-size: 0.85rem;
    color: #94a3b8;
  }}
</style>
</head>
<body>
<header>
  <div class="logo">{esc_title} <span style="font-size:0.8rem; opacity:0.7;">({esc_org})</span></div>
  <div class="nav-controls">
    <button onclick="prevSlide()">◀ Prev</button>
    <span id="counter" style="font-weight:600; margin: 0 8px;">1 / {total}</span>
    <button onclick="nextSlide()">Next ▶</button>
    <button onclick="toggleFullScreen()">⛶ Fullscreen</button>
  </div>
</header>
<main>
  <div class="slide-container" id="slideBox">
    <img id="currentSlide" src="{clean_img_dir}/slide-01.png" alt="Slide 1">
  </div>
</main>
<footer>Gunakan tombol panah keyboard ◄ / ► atau Spacebar untuk navigasi</footer>
<script>
  let current = 1;
  const total = {total};
  const imgEl = document.getElementById('currentSlide');
  const counterEl = document.getElementById('counter');

  function update() {{
    const numStr = String(current).padStart(2, '0');
    imgEl.src = `{clean_img_dir}/slide-${{numStr}}.png`;
    counterEl.innerText = `${{current}} / ${{total}}`;
  }}
  function nextSlide() {{
    if (current < total) {{ current++; update(); }}
  }}
  function prevSlide() {{
    if (current > 1) {{ current--; update(); }}
  }}
  function toggleFullScreen() {{
    if (!document.fullscreenElement) {{
      document.documentElement.requestFullscreen();
    }} else {{
      if (document.exitFullscreen) {{ document.exitFullscreen(); }}
    }}
  }}
  window.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
    if (e.key === 'ArrowLeft') prevSlide();
    if (e.key === 'f') toggleFullScreen();
  }});
</script>
</body>
</html>
"""
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(html_code)
        return out_p

# ---------------------------------------------------------
# CLI & DEMO RUNNER
# ---------------------------------------------------------
def load_spec_file(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in [".yaml", ".yml"]:
        try:
            import yaml
            return yaml.safe_load(text)
        except ImportError:
            raise RuntimeError("PyYAML not installed! Run `pip install pyyaml` or use JSON format.")
    return json.loads(text)

def main():
    parser = argparse.ArgumentParser(description="Guidebook Generator - Application Manual Creator")
    subparsers = parser.add_subparsers(dest="command")

    build_parser = subparsers.add_parser("build", help="Build PDF and/or HTML from spec file")
    build_parser.add_argument("spec", help="Path to spec JSON or YAML file")
    build_parser.add_argument("-o", "--output", default="guidebook.pdf", help="Output PDF path")
    build_parser.add_argument("--html", action="store_true", help="Also generate HTML presentation deck")
    build_parser.add_argument("--html-out", default="guidebook.html", help="HTML presentation output path")
    build_parser.add_argument("--export-images", action="store_true", help="Also export individual slide PNGs")
    build_parser.add_argument("--images-dir", default="slides", help="Directory for exported PNGs")

    init_parser = subparsers.add_parser("init", help="Generate a starter spec JSON or YAML file")
    init_parser.add_argument("output", default="guidebook_spec.json", nargs="?", help="Starter spec destination")

    validate_parser = subparsers.add_parser("validate", help="Validate spec syntax and asset references")
    validate_parser.add_argument("spec", help="Path to spec JSON or YAML file")

    args = parser.parse_args()

    if args.command == "init":
        starter = {"title": "DEMO - Panduan aplikasi", "organization": "DEMO",
                   "slides": [{"type": "cover", "title": "DEMO - Template panduan",
                               "description": "Template awal. Tambahkan fitur dan bukti runtime sebelum digunakan."}]}
        out_p = Path(args.output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        if out_p.suffix.lower() in [".yaml", ".yml"]:
            try:
                import yaml
                out_p.write_text(yaml.dump(starter, sort_keys=False, allow_unicode=True), encoding="utf-8")
            except ImportError:
                out_p.write_text(json.dumps(starter, indent=2, ensure_ascii=False), encoding="utf-8")
        else:
            out_p.write_text(json.dumps(starter, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Starter spec initialized: {out_p.resolve()}")
        return

    if args.command == "validate":
        spec_path = Path(args.spec)
        base_dir = spec_path.parent.resolve()
        spec_data = load_spec_file(args.spec)
        validate_spec(spec_data, base_dir)
        print(f"[OK] Spec syntax and assets valid: {spec_path.resolve()}")
        return

    if args.command == "build":
        base_dir = Path(args.spec).parent.resolve()
        spec_data = load_spec_file(args.spec)
        validate_spec(spec_data, base_dir)
        builder = GuidebookBuilder(spec_data, base_dir=str(base_dir))

        pdf_path = builder.build_pdf(args.output)
        print(f"[OK] PDF Guidebook generated: {pdf_path.resolve()}")

        images_dir_path = Path(args.images_dir)
        if args.export_images or args.html:
            imgs = builder.export_images(str(images_dir_path))
            print(f"[OK] Exported {len(imgs)} slide images to: {images_dir_path.resolve()}")

        if args.html:
            html_out_path = Path(args.html_out)
            try:
                rel_images_dir = os.path.relpath(images_dir_path.resolve(), html_out_path.resolve().parent)
            except ValueError:
                raise ValueError("HTML and images must be on the same drive") from None
            rel_images_dir_url = rel_images_dir.replace("\\", "/")
            html_p = builder.build_html(str(html_out_path), image_dir_rel=rel_images_dir_url)
            print(f"[OK] Interactive HTML Deck generated: {html_p.resolve()}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
