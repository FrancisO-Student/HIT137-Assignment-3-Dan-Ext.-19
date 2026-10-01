import cv2


class Tile:
    """
    Represents one piece of the scrambled image.
    Keeps track of where the tile currently is, where it SHOULD be,
    and what has been done to it (rotation / flip).
    """

    def __init__(self, image_data, correct_position):
        self._image_data = image_data              # this tile's pixels (numpy array)
        self._correct_position = correct_position   # (row, col) where it belongs
        self._current_position = correct_position   # starts correct, scrambling changes this later
        self._rotation = 0                          # 0, 90, 180, 270
        self._flipped = False

    # ---------- getters ----------
    # These exist so other classes (PuzzleBoard, the GUI) can READ the
    # tile's data without reaching directly into its private variables.

    def get_image(self):
        return self._image_data

    def get_correct_position(self):
        return self._correct_position

    def get_current_position(self):
        return self._current_position

    def get_rotation(self):
        return self._rotation

    def is_flipped(self):
        return self._flipped

    # ---------- setters ----------

    def set_current_position(self, new_position):
        self._current_position = new_position

    # ---------- behaviour ----------

    def rotate_90(self):
        # cv2.rotate needs a specific constant, not just "90"
        self._image_data = cv2.rotate(self._image_data, cv2.ROTATE_90_CLOCKWISE)
        self._rotation = (self._rotation + 90) % 360

    def flip_horizontal(self):
        # cv2.flip: 1 = horizontal, 0 = vertical
        self._image_data = cv2.flip(self._image_data, 1)
        self._flipped = not self._flipped

    def swap_with(self, other_tile):
        """
        Swaps CURRENT POSITIONS with another tile.
        The image data stays with each Tile object — only where
        they sit on the board changes.
        """
        my_position = self._current_position
        self._current_position = other_tile.get_current_position()
        other_tile.set_current_position(my_position)

    def is_correct(self):
        # tile is "done" only if it's back home AND not rotated/flipped
        return (self._current_position == self._correct_position
                and self._rotation == 0
                and not self._flipped)
