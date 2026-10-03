from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2

from tile_v2 import Tile
from transforms_v2 import create_transformations


BOARD_SIZE = 480
MAX_IMAGE_SIZE = 460
GRID_CHOICES = ("3 x 3", "4 x 4", "5 x 5")


def prepare_image(image, grid_size):
    height, width = image.shape[:2]
    scale = min(1.0, MAX_IMAGE_SIZE / width, MAX_IMAGE_SIZE / height)
    new_width = max(1, round(width * scale))
    new_height = max(1, round(height * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    image = cv2.resize(image, (new_width, new_height), interpolation=interpolation)

    pad_right = (-new_width) % grid_size
    pad_bottom = (-new_height) % grid_size
    if pad_right or pad_bottom:
        image = cv2.copyMakeBorder(
            image,
            0,
            pad_bottom,
            0,
            pad_right,
            cv2.BORDER_REPLICATE,
        )
    return image


def split_into_tiles(image, grid_size):
    if grid_size < 1:
        raise ValueError("Grid size must be positive")

    height, width = image.shape[:2]
    if height % grid_size or width % grid_size:
        raise ValueError("Image dimensions must divide evenly by the grid size")

    tile_height = height // grid_size
    tile_width = width // grid_size
    tiles = []

    for row in range(grid_size):
        for col in range(grid_size):
            y1 = row * tile_height
            x1 = col * tile_width
            piece = image[y1:y1 + tile_height, x1:x1 + tile_width]
            tiles.append(Tile(piece, (row, col)))

    return tiles


class PuzzleGame:

    def __init__(self, root):
        self.root = root
        self.root.title("Picture Puzzle")
        self.root.geometry("1080x700")
        self.root.minsize(1000, 660)
        self.root.configure(bg="#f2f4f1")

        self.grid_choice = tk.StringVar(value="3 x 3")
        self.moves_text = tk.StringVar(value="Moves: 0")
        self.incorrect_text = tk.StringVar(value="Tiles incorrect: 0")
        self.hints_text = tk.StringVar(value="Hints: 0 / 3")
        self.status_text = tk.StringVar(value="Choose a grid, then load an image.")

        self.tiles = []
        self.original_image = None
        self.image_path = None
        self.grid_size = 3
        self.tile_width = 0
        self.tile_height = 0
        self.image_origin = (0, 0)
        self.selected_tile = None
        self.hint_tile = None
        self.moves = 0
        self.hints_used = 0
        self.completed = False
        self.original_display_path = Path.cwd() / "_puzzle_original_display.png"
        self.puzzle_display_path = Path.cwd() / "_puzzle_board_display.png"
        self.original_photo = None
        self.puzzle_photo = None

        self._build_interface()
        self._draw_empty_canvases()

    def _build_interface(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f2f4f1")
        style.configure(
            "TLabel",
            background="#f2f4f1",
            foreground="#24332f",
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            font=("Segoe UI", 19, "bold"),
            foreground="#000000",
        )
        style.configure("TButton", font=("Segoe UI", 10), padding=(10, 6))

        page = ttk.Frame(self.root, padding=(20, 16))
        page.pack(fill="both", expand=True)

        heading = ttk.Frame(page)
        heading.pack(fill="x", pady=(0, 14))
        ttk.Label(heading, text="Picture Puzzle", style="Title.TLabel").pack(
            side="left"
        )

        controls = ttk.Frame(page)
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="Grid size").pack(side="left", padx=(0, 7))
        self.grid_menu = ttk.Combobox(
            controls,
            textvariable=self.grid_choice,
            values=GRID_CHOICES,
            state="readonly",
            width=8,
        )
        self.grid_menu.pack(side="left", padx=(0, 14))

        self.load_button = ttk.Button(
            controls, text="Load image", command=self.load_image
        )
        self.load_button.pack(side="left")
        self.hint_button = ttk.Button(
            controls, text="Hint", command=self.give_hint, state="disabled"
        )
        self.hint_button.pack(side="left", padx=(8, 0))
        self.solve_button = ttk.Button(
            controls, text="Solve", command=self.solve, state="disabled"
        )
        self.solve_button.pack(side="left", padx=(8, 0))

        views = ttk.Frame(page)
        views.pack(fill="both", expand=True)
        original_panel = ttk.Frame(views)
        original_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        puzzle_panel = ttk.Frame(views)
        puzzle_panel.pack(side="left", fill="both", expand=True, padx=(8, 0))

        ttk.Label(original_panel, text="Original image").pack(anchor="w", pady=(0, 6))
        ttk.Label(puzzle_panel, text="Scrambled puzzle").pack(anchor="w", pady=(0, 6))

        canvas_options = {
            "width": BOARD_SIZE,
            "height": BOARD_SIZE,
            "background": "#e4e8e4",
            "highlightthickness": 0,
        }
        self.original_canvas = tk.Canvas(original_panel, **canvas_options)
        self.original_canvas.pack()
        self.puzzle_canvas = tk.Canvas(puzzle_panel, **canvas_options)
        self.puzzle_canvas.pack()
        self.puzzle_canvas.bind("<Button-1>", self._on_left_click)
        self.puzzle_canvas.bind("<Shift-Button-1>", self._on_shift_click)
        self.puzzle_canvas.bind("<Shift-Button-3>", self._on_shift_click)
        self.puzzle_canvas.bind("<Button-3>", self._on_right_click)

        score = ttk.Frame(page)
        score.pack(fill="x", pady=(12, 0))
        ttk.Label(score, textvariable=self.moves_text).pack(side="left", padx=(0, 24))
        ttk.Label(score, textvariable=self.incorrect_text).pack(
            side="left", padx=(0, 24)
        )
        ttk.Label(score, textvariable=self.hints_text).pack(side="left")
        ttk.Label(page, textvariable=self.status_text).pack(anchor="w", pady=(8, 0))

    def _draw_empty_canvases(self):
        self.original_canvas.create_text(
            BOARD_SIZE // 2,
            BOARD_SIZE // 2,
            text="Load an image to begin",
            fill="#697873",
            font=("Segoe UI", 12),
        )
        self.puzzle_canvas.create_text(
            BOARD_SIZE // 2,
            BOARD_SIZE // 2,
            text="Puzzle appears here",
            fill="#697873",
            font=("Segoe UI", 12),
        )

    def load_image(self):
        selected_path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=(
                ("Image files", "*.jpg *.jpeg *.png *.bmp"),
                ("All files", "*.*"),
            ),
        )
        if not selected_path:
            return

        image = cv2.imread(selected_path)
        if image is None:
            messagebox.showerror("Image error", "That file could not be opened as an image.")
            return

        self._start_puzzle(image, Path(selected_path))

    def _start_puzzle(self, image, image_path):
        self.grid_size = int(self.grid_choice.get().split()[0])
        self.original_image = prepare_image(image, self.grid_size)
        self.image_path = image_path
        self.tiles = split_into_tiles(self.original_image, self.grid_size)

        transformations = create_transformations(self.tiles, self.grid_size)
        for transformation in transformations:
            transformation.apply()

        image_height, image_width = self.original_image.shape[:2]
        self.tile_height = image_height // self.grid_size
        self.tile_width = image_width // self.grid_size
        self.image_origin = (
            (BOARD_SIZE - image_width) // 2,
            (BOARD_SIZE - image_height) // 2,
        )
        self.selected_tile = None
        self.hint_tile = None
        self.moves = 0
        self.hints_used = 0
        self.completed = False
        self.status_text.set(f"Loaded {image_path.name}")
        self._refresh_display()

    def _compose_puzzle(self):
        tiles_by_position = {
            tile.get_current_position(): tile for tile in self.tiles
        }
        image_rows = []

        for row in range(self.grid_size):
            image_row = []
            for col in range(self.grid_size):
                tile_image = tiles_by_position[(row, col)].get_image()
                if tile_image.shape[:2] != (self.tile_height, self.tile_width):
                    tile_image = cv2.resize(
                        tile_image,
                        (self.tile_width, self.tile_height),
                        interpolation=cv2.INTER_LINEAR,
                    )
                image_row.append(tile_image)
            image_rows.append(cv2.hconcat(image_row))

        return cv2.vconcat(image_rows)

    def _make_photo(self, image, image_path):
        if not cv2.imwrite(str(image_path), image):
            raise ValueError("The image could not be prepared for display")
        return tk.PhotoImage(master=self.root, file=str(image_path))

    def _refresh_display(self):
        if self.original_image is None:
            return

        self.original_photo = self._make_photo(
            self.original_image, self.original_display_path
        )
        self.puzzle_photo = self._make_photo(
            self._compose_puzzle(), self.puzzle_display_path
        )
        self._draw_canvas_image(self.original_canvas, self.original_photo)
        self._draw_canvas_image(self.puzzle_canvas, self.puzzle_photo)
        self._draw_overlays()
        self._refresh_score()

    def _draw_canvas_image(self, canvas, photo):
        canvas.delete("all")
        x, y = self.image_origin
        canvas.create_image(x, y, anchor="nw", image=photo)

    def _draw_overlays(self):
        x, y = self.image_origin

        for line in range(1, self.grid_size):
            grid_x = x + line * self.tile_width
            grid_y = y + line * self.tile_height
            self.puzzle_canvas.create_line(
                grid_x,
                y,
                grid_x,
                y + self.tile_height * self.grid_size,
                fill="#d5ddd8",
                width=1,
            )
            self.puzzle_canvas.create_line(
                x,
                grid_y,
                x + self.tile_width * self.grid_size,
                grid_y,
                fill="#d5ddd8",
                width=1,
            )

        for tile in self.tiles:
            row, col = tile.get_current_position()
            left = x + col * self.tile_width
            top = y + row * self.tile_height

            if tile.is_correct():
                self._draw_check_mark(left, top)
            if tile is self.selected_tile:
                self.puzzle_canvas.create_rectangle(
                    left + 2,
                    top + 2,
                    left + self.tile_width - 2,
                    top + self.tile_height - 2,
                    outline="#e6a93b",
                    width=4,
                )

        if self.hint_tile is not None:
            self._draw_hint_circle(
                self.original_canvas, self.hint_tile.get_correct_position()
            )
            self._draw_hint_circle(
                self.puzzle_canvas, self.hint_tile.get_current_position()
            )

    def _draw_check_mark(self, left, top):
        self.puzzle_canvas.create_line(
            left + self.tile_width - 31,
            top + 20,
            left + self.tile_width - 24,
            top + 27,
            fill="#16834a",
            width=4,
            capstyle="round",
        )
        self.puzzle_canvas.create_line(
            left + self.tile_width - 24,
            top + 27,
            left + self.tile_width - 12,
            top + 12,
            fill="#16834a",
            width=4,
            capstyle="round",
        )

    def _draw_hint_circle(self, canvas, position):
        row, col = position
        center_x = self.image_origin[0] + col * self.tile_width + self.tile_width // 2
        center_y = self.image_origin[1] + row * self.tile_height + self.tile_height // 2
        radius = max(10, min(self.tile_width, self.tile_height) // 5)
        canvas.create_oval(
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
            outline="#168ee3",
            width=4,
        )

    def _tile_at(self, event):
        if not self.tiles:
            return None

        local_x = event.x - self.image_origin[0]
        local_y = event.y - self.image_origin[1]
        image_width = self.tile_width * self.grid_size
        image_height = self.tile_height * self.grid_size
        if not (0 <= local_x < image_width and 0 <= local_y < image_height):
            return None

        col = local_x // self.tile_width
        row = local_y // self.tile_height
        position = (row, col)
        for tile in self.tiles:
            if tile.get_current_position() == position:
                return tile
        return None

    def _on_left_click(self, event):
        if self.completed:
            return "break"

        clicked_tile = self._tile_at(event)
        if clicked_tile is None:
            return "break"

        if self.selected_tile is None:
            self.selected_tile = clicked_tile
        elif self.selected_tile is clicked_tile:
            self.selected_tile = None
        else:
            self.selected_tile.swap_with(clicked_tile)
            self.selected_tile = None
            self.moves += 1
            self._after_move()
            return "break"

        self._refresh_display()
        return "break"

    def _on_shift_click(self, event):
        if self.completed:
            return "break"

        tile = self._tile_at(event)
        if tile is not None:
            tile.flip_horizontal()
            self.moves += 1
            self._after_move()
        return "break"

    def _on_right_click(self, event):
        if self.completed:
            return "break"

        tile = self._tile_at(event)
        if tile is not None:
            tile.rotate_90()
            self.moves += 1
            self._after_move()
        return "break"

    def _after_move(self):
        self.selected_tile = None
        self.hint_tile = None
        self._refresh_display()
        if self._incorrect_tile_count() == 0:
            self._finish_game()

    def _incorrect_tile_count(self):
        return sum(not tile.is_correct() for tile in self.tiles)

    def _refresh_score(self):
        incorrect_count = self._incorrect_tile_count()
        self.moves_text.set(f"Moves: {self.moves}")
        self.incorrect_text.set(f"Tiles incorrect: {incorrect_count}")
        self.hints_text.set(f"Hints: {self.hints_used} / 3")
        self.hint_button.configure(
            state="normal"
            if self.tiles and self.hints_used < 3 and not self.completed
            else "disabled"
        )
        self.solve_button.configure(
            state="normal" if self.tiles and not self.completed else "disabled"
        )

    def give_hint(self):
        incorrect_tiles = [tile for tile in self.tiles if not tile.is_correct()]
        if not incorrect_tiles or self.hints_used >= 3 or self.completed:
            return

        self.hint_tile = incorrect_tiles[0]
        self.hints_used += 1
        self._refresh_display()

    def solve(self):
        if not self.tiles or self.completed:
            return

        for tile in self.tiles:
            tile.reset()
        self.moves = 0
        self.hint_tile = None
        self.selected_tile = None
        self.completed = True
        self.status_text.set("Solved. Load another image to play again.")
        self._refresh_display()
        messagebox.showinfo("Puzzle solved", "The picture has been restored.")

    def _finish_game(self):
        self.completed = True
        self.status_text.set("Solved. Load another image to play again.")
        self._refresh_score()
        self._refresh_display()
        messagebox.showinfo("Puzzle solved", "The picture has been restored.")


def main():
    root = tk.Tk()
    game = PuzzleGame(root)

    def close_game():
        game.original_display_path.unlink(missing_ok=True)
        game.puzzle_display_path.unlink(missing_ok=True)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", close_game)
    root.mainloop()


if __name__ == "__main__":
    main()
