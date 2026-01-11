from PIL import Image
import colorsys
from typing import Tuple, Dict


def colorize_grayscale_texture(texture: Image.Image, color: Tuple[int, int, int]) -> Image.Image:
    """
    Colorize a grayscale texture with the given RGB color.
    Uses HSV color space to preserve brightness information from the grayscale.

    Args:
        texture: Grayscale RGBA image to colorize
        color: Target RGB color tuple (0-255 range)

    Returns:
        Colorized RGBA image
    """
    texture = texture.convert('RGBA')
    result = texture.copy()
    pixels = result.load()
    width, height = result.size

    # Convert target color to HSV
    hue, sat, val = colorsys.rgb_to_hsv(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:  # Skip transparent pixels
                continue

            # Use the grayscale value as brightness
            grayscale = (r + g + b) / 3.0 / 255.0

            # Convert to target color with grayscale as value
            new_r, new_g, new_b = colorsys.hsv_to_rgb(hue, sat, grayscale * val)
            pixels[x, y] = (int(new_r * 255), int(new_g * 255), int(new_b * 255), a)

    return result


def put_on_all_pixels(img: Image.Image, color: Tuple[int, int, int], dark_threshold: int = 50) -> Image.Image:
    """
    Apply a color to all non-transparent pixels in an image using HSV color space.
    Preserves the original value (brightness) of each pixel.

    Args:
        img: Image to colorize
        color: Target RGB color tuple (0-255 range)
        dark_threshold: Threshold for darkening effect

    Returns:
        Colorized image
    """
    img = img.convert('HSV')
    hue, sat, val = colorsys.rgb_to_hsv(color[0], color[1], color[2])
    for x in range(0, img.width):
        for y in range(0, img.height):
            dat = img.getpixel((x, y))
            tup = (int(hue * 255), int(sat * 255), int(dat[2] if val > dark_threshold else dat[2] * 0.5))
            img.putpixel((x, y), tup)
    img = img.convert('RGBA')
    return img


def apply_paletted_permutation(base_texture: Image.Image, palette_key: Image.Image, permutation: Image.Image) -> Image.Image:
    """
    Apply a paletted permutation to a base texture.

    This is used for Minecraft's paletted_permutations system where a grayscale palette key
    maps to actual colors in a permutation palette, allowing one texture to be recolored
    for multiple variants (e.g., different wood types).

    Args:
        base_texture: The base RGBA texture to colorize
        palette_key: The palette key image (typically 7x1 grayscale)
        permutation: The permutation palette image (typically 7x1 with colors)

    Returns:
        Colorized RGBA image
    """
    # Convert to RGB for processing
    base_texture = base_texture.convert('RGBA')
    palette_key = palette_key.convert('RGB')
    permutation = permutation.convert('RGB')

    # Build a color mapping from palette_key to permutation
    # palette_key is typically 7x1, permutation is also 7x1
    palette_width = palette_key.size[0]
    color_map: Dict[Tuple[int, int, int], Tuple[int, int, int]] = {}
    for i in range(palette_width):
        key_color = palette_key.getpixel((i, 0))
        perm_color = permutation.getpixel((i, 0))
        color_map[key_color] = perm_color

    # Create output image
    result = base_texture.copy()
    pixels = result.load()
    width, height = result.size

    # For each pixel in the base texture, find the closest palette key color
    # and replace with the corresponding permutation color
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if a == 0:  # Skip transparent pixels
                continue

            rgb = (r, g, b)

            # Find exact match in palette key
            if rgb in color_map:
                new_color = color_map[rgb]
                pixels[x, y] = (new_color[0], new_color[1], new_color[2], a)
            else:
                # Find closest color in palette key
                min_dist = float('inf')
                closest_color = None
                for key_color in color_map.keys():
                    dist = sum((a - b) ** 2 for a, b in zip(rgb, key_color))
                    if dist < min_dist:
                        min_dist = dist
                        closest_color = key_color

                if closest_color and min_dist < 10000:  # Threshold to avoid recoloring unrelated pixels
                    new_color = color_map[closest_color]
                    pixels[x, y] = (new_color[0], new_color[1], new_color[2], a)

    return result
