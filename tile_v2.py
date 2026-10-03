import cv2


class Tile:
    def __init__(self, image_data, correct_position):
        self._original_image = image_data.copy()
        self._image_data = image_data.copy()
        self._correct_position = correct_position
        self._current_position = correct_position
        self._rotation = 0
        self._flipped = False

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

    def set_current_position(self, new_position):
        self._current_position = new_position

    def rotate_90(self):
        self._image_data = cv2.rotate(self._image_data, cv2.ROTATE_90_CLOCKWISE)
        self._rotation = (self._rotation + 90) % 360

    def flip_horizontal(self):
        self._image_data = cv2.flip(self._image_data, 1)
        quarter_turns = self._rotation // 90
        self._rotation = ((-quarter_turns) % 4) * 90
        self._flipped = not self._flipped

    def swap_with(self, other_tile):
        my_position = self._current_position
        self._current_position = other_tile.get_current_position()
        other_tile.set_current_position(my_position)

    def is_correct(self):
        return (self._current_position == self._correct_position
                and self._rotation == 0
                and not self._flipped)

    def reset(self):
        self._image_data = self._original_image.copy()
        self._current_position = self._correct_position
        self._rotation = 0
        self._flipped = False
