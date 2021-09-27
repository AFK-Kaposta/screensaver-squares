import arcade
from arcade_screensaver_framework import screensaver_framework
import pyglet
import random
import math
import PIL.Image
import time

DARK_THEME = True
COLOR_CHANGE_RATE = 3000
UPDATES_PER_SECOND = 15
TILE_SIZE = 35  # in pixels
DEBUG = False


def get_corners(screens):
    """returns a list of coordinates, which are all the corners of the inputted screens"""
    points = []
    for screen in screens:
        points += [(screen.x, screen.y),
                   (screen.x + screen.width, screen.y),
                   (screen.x, screen.y + screen.height),
                   (screen.x + screen.width, screen.y + screen.height)]
    return points


def comb_screens(screens):
    """combines all the screens into one, so every screen would be used for the screensaver."""
    if len(screens) > 1:
        the_screen = screens[-1]  # the_screen must be based on the last screen for some reason
        points = get_corners(screens)
        points = get_farthest_points(points)
        the_screen.width = abs(points[1][0] - points[0][0])
        the_screen.height = abs(points[1][1] - points[0][1])
        the_screen.x = points[0][0]
        the_screen.y = points[0][1]
        return the_screen
    else:
        return screens[0]


def get_farthest_points(points: list):
    """returns the two sets of points which are farthest apart (x, y)"""
    min_x = min(points, key=lambda x: x[0])[0]
    min_y = min(points, key=lambda x: x[1])[1]
    max_x = max(points, key=lambda x: x[0])[0]
    max_y = max(points, key=lambda x: x[1])[1]
    return [(min_x, min_y), (max_x, max_y)]


def random_color() -> arcade.Color:
    if DARK_THEME:
        return random.randint(0, 128), random.randint(0, 128), random.randint(0, 128)
    else:
        return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


class Square(arcade.SpriteSolidColor):
    def __init__(self,
                 center_x: int,
                 center_y: int,
                 size: int,
                 index: int = None,
                 color: arcade.Color = random_color(),
                 next_color: arcade.Color = random_color(),
                 lives: int = None,
                 max_lives: int = None,
                 min_lives: int = None,
                 visible: bool = False):
        """Square has a certain number lives, when a square runs out of lives it becomes active and reduces other
        square's lives."""
        super().__init__(width=size, height=size, color=color)

        self._hit_box_algorithm = 'None'
        self.visible = visible
        self.index = index
        self.size = size
        self.center_x = center_x
        self.center_y = center_y
        self.next_color = next_color
        self.max_lives = max_lives
        self.min_lives = min_lives
        self.active = False
        if lives is None:
            self.randomize_lives()
        else:
            self.lives = lives

    def reduce_lives(self, amount: int = 1) -> None:
        """reduces lives from the square."""
        if not self.active and self.lives > 0:
            self.lives -= amount

    def make_active(self):
        self.active = True
        self.set_color(self.next_color)
        self.next_color = None
        self.lives = 0

    def make_passive(self, next_color: arcade.Color, lives: int = None):
        """resets the square to passive with a new next color and lives."""
        self.next_color = next_color
        self.active = False
        if lives is None:
            self.randomize_lives()
        if DEBUG:
            print(f'making index {self.index:5d} passive: lives={self.lives:3d}, active={self.active}')

    def set_color(self, color: arcade.Color):
        """for proper setting of the color one must run this function."""  # (that came out poetic)
        self.color = color  # idk wtf but for the color to change these next two lines need to be here (copied from
        image = PIL.Image.new('RGBA', (self.size, self.size), self.color)  # SpriteSolidColor.__init__())
        self.texture = arcade.Texture(f"Solid-{self.color[0]}-{self.color[1]}-{self.color[2]}", image)

    def set_next_color(self, next_color: arcade.Color):
        self.next_color = next_color

    def reduce_life(self) -> None:
        """reduces a life from the square."""
        self.reduce_lives(1)

    def set_lives(self, exact_amount: int = None, max_lives: int = None, min_lives: int = None) -> None:
        """sets a random amount of lives based on the given range, or an exact amount."""
        if exact_amount is None:
            low_num = 'low'
            choice = random.choice([low_num] + [""] * 12)
            if choice is low_num:
                self.lives = random.randint(min_lives, int((max_lives + 49 * min_lives) / (50 * min_lives)))
            else:
                self.lives = random.randint(min_lives, max_lives)
        else:
            self.lives = exact_amount

    def randomize_lives(self):
        """sets the lives to a random integer based on the minimum and maximum lives."""
        self.set_lives(max_lives=self.max_lives, min_lives=self.min_lives)

    def update(self):
        if not self.active and self.lives < 1:
            self.make_active()


class Grid:
    def __init__(self, width: int, height: int, sq: Square, infection_range: int, initial_active_index: int = 0):
        """A grid of squares, using the "Square" class. The grid will start filled with copies of "sq"."""
        self.width = width
        self.height = height
        self.fill_sq = sq
        self.infection_range = infection_range
        self.out_of_passives = False
        self.random_next_color = None
        self.initial_active_index = initial_active_index
        self._len = self.width * self.height

        self.grid_list = arcade.SpriteList(use_spatial_hash=False)  # , is_static=True)
        initial_color = random_color()
        for col in range(self.width):
            for row in range(self.height):
                clone = Square(center_x=int(sq.size * (col + 0.5)),
                               center_y=int(sq.size * (row + 0.5)),
                               size=sq.size,
                               index=self.to_index(col, row),
                               color=initial_color,
                               next_color=sq.next_color,
                               max_lives=sq.max_lives,
                               min_lives=sq.min_lives)
                self.grid_list.append(clone)

    def __len__(self):
        return self._len

    def update(self) -> None:
        """updates all the squares in the grid"""
        passives_exist = False
        for col in range(self.width):
            for row in range(self.height):
                current: Square = self.grid_list[self.to_index(col, row)]
                if self.out_of_passives:
                    current.make_passive(self.random_next_color)
                    if current.index == self.initial_active_index:
                        current.make_active()
                    if not passives_exist:
                        passives_exist = True
                elif current.active:
                    self.reduce_around(col, row)
                else:
                    current.update()
                    passives_exist = True
        self.out_of_passives = False if passives_exist else True
        if self.out_of_passives:
            self.random_next_color = random_color()
            self.initial_active_index = random.randint(0, len(self))

    def reduce_around(self, col: int, row: int) -> None:
        """reduces one life in a range around the given position."""
        min_x = col - self.infection_range
        max_x = col + self.infection_range
        min_y = row - self.infection_range
        max_y = row + self.infection_range

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                self.grid_list[self.to_index(x, y)].reduce_lives(1)

    def to_index(self, col, row):
        return self.height * (col % self.width) + (row % self.height)

    def draw(self):
        self.grid_list.draw()

    def set_visibility(self, screens_list: arcade.SpriteList) -> None:  # unused
        """goes through all the sprites and checks if they will be visible on the given screens list.
        if a sprite won't be visible on the screen his 'visible' attribute will be set to False."""
        visible_sprites = []
        for screen in screens_list:
            visible_sprites += arcade.check_for_collision_with_list(screen, self.grid_list)
        for sq in visible_sprites:
            sq.visibility = True


class Saver(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # converting from the pyglet graphing system to the arcade one
        self.corners = get_corners(pyglet.canvas.get_display().get_screens())
        diff = get_farthest_points(self.corners)
        x_diff, y_diff = diff[0][0], diff[1][1]  # the most bottom left corner (where the arcade 0,0 is)
        for i in range(len(self.corners)):
            self.corners[i] = (self.corners[i][0] - x_diff, -self.corners[i][1] + y_diff)

        # setting key attributes
        self.view_corners = get_farthest_points(self.corners)
        self.view_width = self.view_corners[1][0]
        self.view_height = self.view_corners[1][1]
        self.ups = UPDATES_PER_SECOND  # Updates Per Second (basically useless above 60)
        self.set_update_rate(1 / self.ups)
        self.square_size = TILE_SIZE  # square width and height in pixels.
        self.square_count_x = math.ceil(self.view_width / self.square_size)
        self.square_count_y = math.ceil(self.view_height / self.square_size)
        self.base_square = Square(center_x=0, center_y=0, size=self.square_size, max_lives=COLOR_CHANGE_RATE,
                                  min_lives=1)
        self.grid = Grid(width=self.square_count_x, height=self.square_count_y, infection_range=2, sq=self.base_square)
        self.screens_sprites = arcade.SpriteList(use_spatial_hash=False, is_static=True)
        for i in range(0, len(self.corners), 4):
            a, b, c, d = self.corners[i], self.corners[i + 1], self.corners[i + 2], self.corners[i + 3]
            if a[0] != b[0] and a[1] != b[1]:
                center_x = (a[0] + b[0]) / 2
                center_y = (a[1] + b[1]) / 2
                width = abs(a[0] - b[0])
                height = abs(a[1] - b[1])
            elif a[0] != c[0] and a[1] != c[1]:
                center_x = (a[0] + c[0]) / 2
                center_y = (a[1] + c[1]) / 2
                width = abs(a[0] - c[0])
                height = abs(a[1] - c[1])
            else:
                center_x = (a[0] + d[0]) / 2
                center_y = (a[1] + d[1]) / 2
                width = abs(a[0] - d[0])
                height = abs(a[1] - d[1])
            screen = arcade.SpriteSolidColor(width=width, height=height, color=arcade.color.PINK)
            screen.set_position(center_x, center_y)
            self.screens_sprites.append(screen)
        self.grid.grid_list[random.randint(0, len(self.grid))].make_active()
        if DEBUG:
            print(f'amount of squares: {self.square_count_x * self.square_count_y}')

    def on_update(self, delta_time):
        self.grid.update()

    def on_draw(self):
        arcade.start_render()
        self.grid.draw()


def main():
    if DEBUG:
        start = time.time()
    screensaver_framework._get_preferred_screen = comb_screens
    screensaver_framework.create_screensaver_window(Saver)
    if DEBUG:
        end = time.time()
        print(f'time to initialize: {end - start:.4f} seconds')
    arcade.run()


if __name__ == "__main__":
    main()
