import hashlib
import random

from PIL import Image, ImageDraw, ImageOps


def get_participant_color(name: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(name.encode("utf-8")).digest()
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


def build_mosaic_positions(
    item_count: int,
    participant_names: tuple[str, ...] | list[str] | None = None,
) -> list[int]:
    cols, rows = get_mosaic_dimensions(item_count)
    total_cells = cols * rows

    if participant_names is None:
        return random.sample(range(total_cells), item_count)

    seed_payload = ("birthday\0" + "\0".join(participant_names)).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(seed_payload).digest(), "big")
    return random.Random(seed).sample(range(total_cells), item_count)


def get_mosaic_image(
    revealed_portraits: dict[int, dict],
    grid_cols: int,
    grid_rows: int,
) -> Image.Image:
    tile_w = 225
    tile_h = 300
    canvas = Image.new(
        "RGB",
        (tile_w * grid_cols, tile_h * grid_rows),
        (255, 244, 179),
    )
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
                    (x0, y0, x1 - 1, y1 - 1),
                    fill=(18, 22, 34),
                )
                continue

            entry = revealed_portraits[cell_id]
            portrait = entry.get("portrait")
            if portrait is not None:
                portrait = ImageOps.exif_transpose(portrait)
                portrait = ImageOps.fit(
                    portrait,
                    (tile_w, tile_h),
                    method=Image.Resampling.LANCZOS,
                )
                canvas.paste(portrait, (x0, y0))
            else:
                draw.rectangle(
                    (x0, y0, x1 - 1, y1 - 1),
                    fill=get_participant_color(entry["name"]),
                )

    return canvas
