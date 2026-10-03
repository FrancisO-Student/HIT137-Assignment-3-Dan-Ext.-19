from tile_v2 import Tile


class TileTransform:
    def apply(self) -> None:
        raise NotImplementedError


class SwapTransform(TileTransform):
    def __init__(self, first_tile: Tile, second_tile: Tile) -> None:
        self._first_tile = first_tile
        self._second_tile = second_tile

    def apply(self) -> None:
        self._first_tile.swap_with(self._second_tile)


class RotateTransform(TileTransform):
    def __init__(self, tile: Tile, degrees: int) -> None:
        self._tile = tile
        self._degrees = degrees

    def apply(self) -> None:
        for _ in range(self._degrees // 90):
            self._tile.rotate_90()


class FlipTransform(TileTransform):
    def __init__(self, tile: Tile) -> None:
        self._tile = tile

    def apply(self) -> None:
        self._tile.flip_horizontal()


def create_transformations(
    tiles: list[Tile], grid_size: int
) -> list[TileTransform]:
    transformation_count = grid_size * (grid_size - 1)
    transformations = []

    for index in range(transformation_count):
        tile_index = index % len(tiles)
        if index % 3 == 0:
            other_index = (tile_index + 1) % len(tiles)
            transformation = SwapTransform(tiles[tile_index], tiles[other_index])
        elif index % 3 == 1:
            transformation = RotateTransform(tiles[tile_index], 90)
        else:
            transformation = FlipTransform(tiles[tile_index])
        transformations.append(transformation)

    return transformations