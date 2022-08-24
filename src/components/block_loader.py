from PIL import Image, ImageEnhance
from typing import Tuple, Any

from context import Context
from components import tag_loader

import util
import numpy


def get_multi_block_image(context: Context, data: Any) -> str:
    if 'multiblocks' in data:
        images = []
        for b in data['multiblocks']:
            images += get_multi_block_images(context, b)
    elif 'multiblock' in data:
        images = get_multi_block_images(context, data['multiblock'])
    else:
        util.error('Multiblock defined in code', muted=True)
    
    if len(images) == 1:
        return context.loader.save_image(context.next_id('block_'), images[0])
    else:
        return context.loader.save_gif(context.next_id('block_'), images)


def get_multi_block_images(context: Context, data: Any):
    pattern = data['pattern']
    util.require(pattern == [['X'], ['0']] or pattern == [['X'], ['Y'], ['0']], 'Only simple patterns are supported', muted=True)

    block = data['mapping']['X']

    if block.startswith('#'):
        blocks = tag_loader.load_block_tag(context, block[1:])
    else:
        util.require('[' not in block, 'No support for blocks with properties yet: \'%s\'' % block, muted=True)
        blocks = [block]

    return [
        get_block_image(context, block)
        for block in blocks
    ]


@util.context(lambda _, b: 'block = \'%s\'' % b)
def get_block_image(context: Context, block: str) -> Image.Image:

    state = context.loader.load_block_state(block)
    util.require('variants' in state, 'No support for multipart states yet', muted=True)
    util.require('' in state['variants'], 'No support for states with properties yet', muted=True)
    util.require('model' in state['variants'][''], 'Missing model')

    model = context.loader.load_model(state['variants']['']['model'])
    
    return create_block_model_image(context, model)


def create_block_model_image(context: Context, model: Any) -> Image.Image:
    util.require('parent' in model, 'Missing parent')
    parent = model['parent']
    if parent == 'block/cube_all':
        _, texture = context.loader.load_image(model['textures']['all'])
        return create_block_model_projection(texture, texture, texture)
    elif parent == 'block/cube_column':
        _, side = context.loader.load_image(model['textures']['side'])
        _, end = context.loader.load_image(model['textures']['end'])
        return create_block_model_projection(side, side, end)
    elif parent == 'tfc:block/ore':
        _, texture = context.loader.load_image(model['textures']['all'])
        _, overlay = context.loader.load_image(model['textures']['overlay'])
        texture.paste(overlay, (0, 0), overlay)
        return create_block_model_projection(texture, texture, texture)
    else:
        util.error('Unsupported parent: %s' % parent, muted=True)


def create_block_model_projection(left: Image.Image, right: Image.Image, top: Image.Image) -> Image.Image:
    # Shading
    left = ImageEnhance.Brightness(left).enhance(0.85)
    right = ImageEnhance.Brightness(right).enhance(0.6)

    # (Approx) Dimetric Projection
    left = left.transform((256, 256), Image.Transform.PERSPECTIVE, LEFT, Image.Resampling.NEAREST)
    right = right.transform((256, 256), Image.Transform.PERSPECTIVE, RIGHT, Image.Resampling.NEAREST)
    top = top.transform((256, 256), Image.Transform.PERSPECTIVE, TOP, Image.Resampling.NEAREST)

    left.paste(right, (0, 0), right)
    left.paste(top, (0, 0), top)

    return left

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
