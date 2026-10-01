from tile import Tile


def split_into_tiles(image, grid_size):
    """
    Cuts an image into grid_size x grid_size equal pieces and
    wraps each piece in a Tile object.

    IMPORTANT: the image must already be resized/cropped so that
    its height and width divide evenly by grid_size, otherwise the
    tiles will not be equal sizes. That resize/crop step happens
    BEFORE this function is called.
    """
    height, width = image.shape[:2]   # OpenCV order is (rows, columns, channels)
    tile_height = height // grid_size
    tile_width = width // grid_size

    tiles = []
    for row in range(grid_size):
        for col in range(grid_size):
            y1 = row * tile_height
            y2 = y1 + tile_height
            x1 = col * tile_width
            x2 = x1 + tile_width

            piece = image[y1:y2, x1:x2]   # numpy slice = one tile's pixels
            tile = Tile(piece, (row, col))
            tiles.append(tile)

    return tiles
