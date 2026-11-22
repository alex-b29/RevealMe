import hashlib
import random

from PIL import Image, ImageDraw, ImageOps


def normalize(value: str) -> str:
    return " ".join(value.strip().lower().split())


def get_participant_color(name: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(normalize(name).encode("utf-8")).digest()
    red = 110 + digest[0] % 126
    green = 110 + digest[1] % 126
    blue = 110 + digest[2] % 126
    return red, green, blue


def get_mosaic_dimensions(item_count: int) -> tuple[int, int]:
    if item_count <= 0:
        return 1, 1

    candidates: list[tuple[int, int, int, int]] = []

    for cols in range(1, item_count + 1):
        for rows in range(1, cols + 1):
            if item_count > 3 and rows == 1:
                continue

            cell_count = cols * rows
            if cell_count < item_count:
                continue

            extra = cell_count - item_count
            difference = cols - rows
            candidates.append((extra, difference, cols, rows))

    _, _, cols, rows = min(candidates)
    return cols, rows


def build_mosaic_positions(item_count: int) -> list[int]:
    cols, rows = get_mosaic_dimensions(item_count)
    total_cells = cols * rows
    return random.sample(range(total_cells), item_count)


def get_mosaic_image(
    revealed_portraits: dict[int, dict],
    grid_cols: int,
    grid_rows: int,
) -> Image.Image:
    canvas = Image.new("RGB", (900, 675), (255, 244, 179))
    tile_w = canvas.width // grid_cols
    tile_h = canvas.height // grid_rows
    draw = ImageDraw.Draw(canvas)

    for row in range(grid_rows):
        for col in range(grid_cols):
            cell_id = row * grid_cols + col
            x0 = col * tile_w
            y0 = row * tile_h
            x1 = x0 + tile_w
            y1 = y0 + tile_h

            if cell_id not in revealed_portraits:
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    fill=(18, 22, 34),
                )
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    outline=(112, 128, 170),
                    width=3,
                )
                continue

            entry = revealed_portraits[cell_id]
            portrait = entry.get("portrait")
            if portrait is not None:
                portrait = ImageOps.fit(
                    portrait,
                    (tile_w - 6, tile_h - 6),
                    method=Image.Resampling.LANCZOS,
                )
                canvas.paste(portrait, (x0 + 3, y0 + 3))
            else:
                draw.rectangle(
                    (x0 + 3, y0 + 3, x1 - 3, y1 - 3),
                    fill=get_participant_color(entry["name"]),
                )

    return canvas
