import arcade
from arcade_screensaver_framework import screensaver_framework
import pyglet
import random
import math
import itertools
import copy
import PIL.Image


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


class Square(arcade.SpriteSolidColor):
    def __init__(self,
                 center_x: int,
                 center_y: int,
                 size: int,
                 index: int = None,
                 color: arcade.Color = arcade.color.DARK_RED,
                 next_color: arcade.Color = arcade.color.GREEN,
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
        self.lives = lives
        self.max_lives = max_lives
        self.min_lives = min_lives
        self.active = False

    def reduce_lives(self, amount: int = 1) -> None:
        """reduces lives from the square."""
        if not self.active:
            self.lives -= amount
            # print(f'reduced at index {self.index}, position ({self.center_x}, {self.center_y})')

    def make_active(self):
        self.active = True
        self.set_color(self.next_color)
        self.next_color = None

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
    def __init__(self, width: int, height: int, sq: Square, infection_range: int):
        """A grid of squares, using the "Square" class. The grid will start filled with copies of "sq"."""
        self.width = width
        self.height = height
        self.fill_sq = sq
        self.infection_range = infection_range
        self.out_of_passives = False

        self.grid_list = arcade.SpriteList()  # use_spatial_hash=False, is_static=True)
        for col in range(self.width):
            for row in range(self.height):
                clone = copy.copy(sq)
                clone.index = self.to_index(self.height, col, row)
                clone.set_position(clone.size * (col + 0.5), clone.size * (row + 0.5))
                # print(f'set {clone.size * (col + 0.5)},{clone.size * (row + 0.5)}')
                clone.randomize_lives()
                self.grid_list.append(clone)

    def update(self) -> None:
        """updates all the squares in the grid"""
        passives_exist = False
        for col in range(self.width):
            for row in range(self.height):
                if self.grid_list[self.to_index(self.height, col, row)].active:
                    self.reduce_around(col, row)
                else:
                    self.grid_list[self.to_index(self.height, col, row)].update()
                    passives_exist = True
        self.out_of_passives = False if passives_exist else True

    def reduce_around(self, col: int, row: int) -> None:
        """reduces one life in a range around the given position."""
        min_x = col - self.infection_range
        max_x = col + self.infection_range
        min_y = row - self.infection_range
        max_y = row + self.infection_range

        # max_x %= self.width  # making sure the index won't be out of bounds
        # max_y %= self.height
        # min_x = abs(min_x)
        # min_y = abs(min_y)

        print(f'min: ({min_x:2d},{min_y:2d}), max: ({max_x:2d},{max_y:2d})')
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                # print(f'row {row}, col {col}')
                self.grid_list[self.to_index(self.height, x, y)].reduce_lives(1000)

    def to_index(self, height, col, row):
        return (height * col + row) % (self.width * self.height)

    def draw(self):
        self.grid_list.draw()

    def set_visibility(self, screens_list: arcade.SpriteList) -> None:
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
        self.background_color = arcade.color.BLUE
        self.ups = 1  # Updates Per Second (basically useless above 60)
        self.set_update_rate(1 / self.ups)
        self.square_size = 50  # square width and height in pixels.
        self.square_count_x = math.ceil(self.view_width / self.square_size)
        self.square_count_y = math.ceil(self.view_height / self.square_size)
        self.base_square = Square(center_x=0, center_y=0, size=self.square_size, max_lives=33, min_lives=1)
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
            screen = arcade.SpriteSolidColor(width=width,
                                             height=height,
                                             color=arcade.color.PINK)
            screen.set_position(center_x, center_y)
            self.screens_sprites.append(screen)
        # self.grid.set_visibility(self.screens_sprites)
        self.grid.grid_list[int(len(self.grid.grid_list) * (8 / 10))].make_active()
        print(self.grid.grid_list[int(len(self.grid.grid_list) * (8 / 10))].position)

    def on_update(self, delta_time):
        self.grid.update()

    def on_draw(self):
        arcade.start_render()
        # self.screens_sprites.draw()
        self.grid.draw()


if __name__ == "__main__":
    screensaver_framework._get_preferred_screen = comb_screens
    screensaver_framework.create_screensaver_window(Saver)
    arcade.run()
