"""
Excel generation utility helpers (openpyxl) for templates, cell formatting,
borders, alignments, and fonts.
"""

from typing import Any, Dict, Optional, Tuple
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side


class BorderAccumulator:
    """
    Tracks and accumulates borders for cells without overwriting earlier sides.
    Useful for complex grid drawing where adjacent boxes share borders.
    """

    def __init__(self, thin_side: Optional[Side] = None, double_side: Optional[Side] = None):
        self.thin = thin_side or Side(border_style="thin", color="000000")
        self.double = double_side or Side(border_style="double", color="000000")
        self.edges: Dict[Tuple[int, int], Dict[str, Side]] = {}

    def edge(self, row: int, col: int, **sides: Side) -> None:
        d = self.edges.setdefault((row, col), {})
        d.update(sides)

    def hline(self, row: int, col_start: int, col_end: int, side: Optional[Side] = None, where: str = "top") -> None:
        target_side = side or self.thin
        for c in range(col_start, col_end + 1):
            self.edge(row, c, **{where: target_side})

    def vline(self, col: int, row_start: int, row_end: int, side: Optional[Side] = None, where: str = "left") -> None:
        target_side = side or self.thin
        for r in range(row_start, row_end + 1):
            self.edge(r, col, **{where: target_side})

    def box(self, col_start: int, row_start: int, col_end: int, row_end: int, side: Optional[Side] = None) -> None:
        target_side = side or self.thin
        self.hline(row_start, col_start, col_end, target_side, "top")
        self.hline(row_end, col_start, col_end, target_side, "bottom")
        self.vline(col_start, row_start, row_end, target_side, "left")
        self.vline(col_end, row_start, row_end, target_side, "right")

    def apply_to_sheet(self, ws: Any) -> None:
        """Apply all accumulated borders to the openpyxl worksheet."""
        for (r, c), sides in self.edges.items():
            cell = ws.cell(row=r, column=c)
            existing = cell.border
            cell.border = Border(
                left=sides.get("left", existing.left if existing else None),
                right=sides.get("right", existing.right if existing else None),
                top=sides.get("top", existing.top if existing else None),
                bottom=sides.get("bottom", existing.bottom if existing else None),
            )


def make_alignment(
    horizontal: Optional[str] = None,
    vertical: str = "center",
    wrap_text: bool = False,
    indent: int = 0,
    shrink_to_fit: bool = False,
) -> Alignment:
    """Helper to create openpyxl Alignment object."""
    return Alignment(
        horizontal=horizontal,
        vertical=vertical,
        wrap_text=wrap_text,
        indent=indent,
        shrink_to_fit=shrink_to_fit,
    )


def style_cell(
    cell: Any,
    value: Any = None,
    font: Optional[Font] = None,
    align: Optional[Alignment] = None,
    number_format: Optional[str] = None,
    fill: Optional[PatternFill] = None,
) -> Any:
    """Apply styling attributes to a single openpyxl cell."""
    if value is not None:
        cell.value = value
    if font:
        cell.font = font
    if align:
        cell.alignment = align
    if number_format:
        cell.number_format = number_format
    if fill:
        cell.fill = fill
    return cell
