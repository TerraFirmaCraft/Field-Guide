from PIL import Image, ImageEnhance
from typing import Tuple, List, Any, Dict

from context import Context
from components import tag_loader

import util
import numpy

CACHE: Dict[str, str] = {}


def get_multi_block_image(context: Context, data: Any) -> str:
    if 'multiblocks' in data:
        images = []
        key = 'multiblocks-'
        for b in data['multiblocks']:
            name, values = get_multi_block_images(context, b)
            key += name
            images += values
    elif 'multiblock' in data:
        key, images = get_multi_block_images(context, data['multiblock'])
    else:
        return util.error('Multiblock : Custom Multiblock \'%s\'' % data['multiblock_id'], True)
    
    if key in CACHE:
        return CACHE[key]

    if len(images) == 1:
        path = context.loader.save_image(context.next_id('block'), images[0])
    else:
        path = context.loader.save_gif(context.next_id('block'), images)
    
    CACHE[key] = path
    return path


def get_multi_block_images(context: Context, data: Any) -> Tuple[str, List[Image.Image]]:
    util.require('pattern' in data, 'Multiblock : No \'pattern\' field', True)
    util.require(data['pattern'] == [['X'], ['0']] or data['pattern'] == [['X'], ['Y'], ['0']], 'Multiblock : Complex Pattern \'%s\'' % repr(data['pattern']), True)

    block = data['mapping']['X']

    if block.startswith('#'):
        blocks = tag_loader.load_block_tag(context, block[1:])
    else:
        blocks = [block]

    return block, [
        get_block_image(context, b)
        for b in blocks
    ]


def get_block_image(context: Context, block_state: str) -> Image.Image:

    block, state = parse_block_state(block_state)
    state_data = context.loader.load_block_state(block)

    util.require('variants' in state_data and isinstance(state_data['variants'], dict), 'BlockState : Must be a \'variants\' block state: \'%s\'' % block_state, True)

    # This is not perfectly accurate since we are completely unaware of default property values, but it should be close enough
    # The ones this fails for are un-renderable anyway due to having complex models
    variants = state_data['variants']
    default_model_data = None
    for key, value in variants.items():
        if default_model_data is None:
            default_model_data = value
        if parse_block_properties(key).items() <= state.items():  # If the variant properties are a subset of the target state properties
            model_data = value
            break
    else:
        # Assume a default state, i.e. with default properties
        if state == {} and variants:
            model_data = default_model_data
        else:
            util.error('BlockState: No matching state found for \'%s\' in \'%s\'' % (block_state, variants), True) 

    util.require('model' in model_data, 'BlockState : No Model \'%s\'' % block, True)

    model = context.loader.load_model(model_data['model'])
    
    return create_block_model_image(context, block, model)


def parse_block_state(block_state: str) -> Tuple[str, Dict[str, str]]:
    if '[' in block_state:
        block, properties = block_state[:-1].split('[')
        return block, parse_block_properties(properties)
    else:
        return block_state, {}  # Default variant

def parse_block_properties(properties: str) -> Dict[str, str]:
    # Format: namespace:path[key1=value1,key2=value2,...]
    state = {}
    if '=' in properties:  # Has at least one pair
        for property in properties.split(','):
            key, value = property.split('=')
            state[key] = value
    return state


def create_block_model_image(context: Context, block: str, model: Any) -> Image.Image:
    util.require('parent' in model, 'Block Model : No Parent : \'%s\'' % block, True)
    
    parent = util.resource_location(model['parent'])
    if parent == 'minecraft:block/cube_all':
        texture = context.loader.load_texture(model['textures']['all'])
        return create_block_model_projection(texture, texture, texture)
    elif parent == 'minecraft:block/cube_column':
        side = context.loader.load_texture(model['textures']['side'])
        end = context.loader.load_texture(model['textures']['end'])
        return create_block_model_projection(side, side, end)
    elif parent == 'minecraft:block/cube_column_horizontal':
        side = context.loader.load_texture(model['textures']['side'])
        end = context.loader.load_texture(model['textures']['end'])
        return create_block_model_projection(end, side, side, rotate=True)
    elif parent == 'minecraft:block/template_farmland':
        side = context.loader.load_texture(model['textures']['dirt'])
        end = context.loader.load_texture(model['textures']['end'])
        return create_block_model_projection(side, side, end)
    elif parent == 'tfc:block/ore':
        texture = context.loader.load_texture(model['textures']['all'])
        overlay = context.loader.load_texture(model['textures']['overlay'])
        texture.paste(overlay, (0, 0), overlay)
        return create_block_model_projection(texture, texture, texture)
    elif parent == 'minecraft:block/slab':
        top = context.loader.load_texture(model['textures']['top'])
        side = context.loader.load_texture(model['textures']['side'])
        return create_slab_block_model_projection(side, side, top)
    elif parent == 'minecraft:block/crop':
        crop = context.loader.load_texture(model['textures']['crop'])
        return create_crop_model_projection(crop)
    else:
        util.error('Block Model : Unknown Parent \'%s\' : at \'%s\'' % (parent, block), True)


def create_block_model_projection(left: Image.Image, right: Image.Image, top: Image.Image, rotate: bool = False) -> Image.Image:
    # Shading
    left = ImageEnhance.Brightness(left).enhance(0.85)
    right = ImageEnhance.Brightness(right).enhance(0.6)

    if rotate:
        right = right.rotate(90, Image.Resampling.NEAREST)
        top = top.rotate(90, Image.Resampling.NEAREST)

    # (Approx) Dimetric Projection
    left = left.transform((256, 256), Image.Transform.PERSPECTIVE, LEFT, Image.Resampling.NEAREST)
    right = right.transform((256, 256), Image.Transform.PERSPECTIVE, RIGHT, Image.Resampling.NEAREST)
    top = top.transform((256, 256), Image.Transform.PERSPECTIVE, TOP, Image.Resampling.NEAREST)

    left.paste(right, (0, 0), right)
    left.paste(top, (0, 0), top)

    return left

def create_slab_block_model_projection(left: Image.Image, right: Image.Image, top: Image.Image) -> Image.Image:
    # Shading
    left = ImageEnhance.Brightness(left).enhance(0.85)
    right = ImageEnhance.Brightness(right).enhance(0.6)
    left = crop_retaining_position(left, 0, 8, 16, 16)
    right = crop_retaining_position(right, 0, 8, 16, 16)

    # (Approx) Dimetric Projection
    left = left.transform((256, 256), Image.Transform.PERSPECTIVE, LEFT, Image.Resampling.NEAREST)
    right = right.transform((256, 256), Image.Transform.PERSPECTIVE, RIGHT, Image.Resampling.NEAREST)
    top = top.transform((256, 256), Image.Transform.PERSPECTIVE, TOP_SLAB, Image.Resampling.NEAREST)

    left.paste(right, (0, 0), right)
    left.paste(top, (0, 0), top)

    return left

def create_crop_model_projection(crop: Image.Image) -> Image.Image:
    # Shading
    left = ImageEnhance.Brightness(crop).enhance(0.85)
    right = ImageEnhance.Brightness(crop).enhance(0.6)
    r_end = crop_retaining_position(right, 0, 0, 5, 16)
    l_end = crop_retaining_position(left, 13, 0, 16, 16)
    
    # (Approx) Dimetric Projection
    left = left.transform((256, 256), Image.Transform.PERSPECTIVE, LEFT, Image.Resampling.NEAREST)
    right = right.transform((256, 256), Image.Transform.PERSPECTIVE, RIGHT, Image.Resampling.NEAREST)
    r_end_t = r_end.transform((256, 256), Image.Transform.PERSPECTIVE, RIGHT, Image.Resampling.NEAREST)
    l_end_t = l_end.transform((256, 256), Image.Transform.PERSPECTIVE, LEFT, Image.Resampling.NEAREST)
    
    base = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
    
    base.paste(left, (98 - 12, 14 - 56), left)
    base.paste(right, (100 - 128, 100 - 114), right)
    base.paste(right, (42 - 128, 72 - 114), right)
    base.paste(left, (42 - 12, 42 - 56), left)
    base.paste(r_end_t, (100 - 128, 100 - 114), r_end_t)
    base.paste(r_end_t, (42 - 128, 72 - 114), r_end_t)
    base.paste(l_end_t, (98 - 12, 14 - 56), l_end_t)
    base.paste(l_end_t, (42 - 12, 42 - 56), l_end_t)
    
    return base

def crop_retaining_position(img: Image.Image, u1: int, v1: int, u2: int, v2: int):
    base = img.copy()
    base = base.crop((u1, v1, u2, v2))
    img = Image.new('RGBA', (img.width, img.height), (0, 0, 0, 0))
    img.paste(base, (u1, v1))
    return img

def perspective_transformation(*pa: Tuple[int, int]):
    """ Calculates coefficients for a perspective transformation to a specific quad
    From: https://stackoverflow.com/questions/14177744/how-does-perspective-transformation-work-in-pil
    """
    matrix = []
    for p1, p2 in zip(pa, ROOT):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])

    A = numpy.matrix(matrix, dtype=numpy.float64)
    B = numpy.array(ROOT).reshape(8)

    res = numpy.dot(numpy.linalg.inv(A.T * A) * A.T, B)
    return numpy.array(res).reshape(8)


ROOT = ((0, 0), (16, 0), (16, 16), (0, 16))
LEFT = perspective_transformation((13, 57), (128, 114), (128, 255), (13, 198))
RIGHT = perspective_transformation((128, 114), (242, 58), (242, 197), (128, 255))
TOP = perspective_transformation((13, 57), (127, 0), (242, 58), (128, 114))
TOP_SLAB = perspective_transformation((13, 57 + 71), (127, 0 + 71), (242, 58 + 71), (128, 114 + 71))
