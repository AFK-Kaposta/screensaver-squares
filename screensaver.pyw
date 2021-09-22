import arcade
from arcade_screensaver_framework import screensaver_framework
import pyglet
import random
import math
import itertools


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
                 width: int,
                 color: arcade.Color = arcade.color.WHITE,
                 next_color: arcade.Color = arcade.color.DARK_CYAN,
                 lives: int = None,
                 max_lives: int = None,
                 min_lives: int = None):
        """Square has a certain number lives, when a square runs out of lives it becomes active and reduces other
        square's lives."""
        super().__init__(width=width, height=width, color=color)

        self.center_x = center_x
        self.center_y = center_y
        self.next_color = next_color
        self.lives = None
        self.set_lives(lives, max_lives, min_lives)
        self.active = False

    def reduce_lives(self, amount: int = 1) -> None:
        """reduces lives from the square."""
        if not self.active:
            self.lives -= amount
            if self.lives < 1:
                self.active = True
                self.color = self.next_color
                self.next_color = None

    def reduce_life(self) -> None:
        """reduces a life from the square."""
        self.reduce_lives(1)

    def set_lives(self, exact_amount: int = None, max_lives: int = None, min_lives: int = None) -> None:
        """sets a random amount of lives based on the given range, or an exact amount."""
        if exact_amount is None:
            self.lives = random.randint(min_lives, max_lives)
        else:
            self.lives = exact_amount


class Grid:
    def __init__(self, width: int, height: int, sq: Square, infection_range: int):
        """A grid of squares, using the "Square" class. The grid will start filled with copies of "sq"."""
        self.width = width
        self.height = height
        self.fill_sq = sq
        self.infection_range = infection_range

        self.grid_list = []
        for _ in range(self.width):
            self.grid_list += [[sq for _ in range(self.height)]]

    def update(self) -> None:
        """updates all the squares in the grid"""
        for x in range(self.width):
            for y in range(self.height):
                if self.grid_list[x][y].active:
                    self.reduce_around(x, y)

    def reduce_around(self, x: int, y: int) -> None:
        """reduces one life in a range around the given position."""
        min_x, min_y = x - self.infection_range, y - self.infection_range
        max_x, max_y = x + self.infection_range, y + self.infection_range

        max_x %= self.width  # making sure the index won't be out of bounds
        max_y %= self.height

        for x in range(min_x, max_x):
            for y in range(min_y, max_y):
                self.grid_list[x][y].reduce_lives()

    def draw(self):
        for col in self.grid_list:
            for sq in col:
                sq.draw()


class Saver(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # converting from the pyglet graphing system to the arcade one
        self.corners = get_corners(pyglet.canvas.get_display().get_screens())
        diff = get_farthest_points(self.corners)
        x_diff, y_diff = diff[0][0], diff[1][1]  # the most bottom left corner (where the arcade 0,0 is)
        for i in range(len(self.corners)):
            self.corners[i] = (self.corners[i][0] - x_diff, -self.corners[i][1] + y_diff)
        self.corners2 = self.corners.copy()

        # setting key attributes
        self.view_corners = get_farthest_points(self.corners)
        self.screen_color = arcade.color.DARK_ELECTRIC_BLUE
        self.ups = 20  # Updates Per Second (basically useless above 60)
        self.set_update_rate(1 / self.ups)

        self.screens_sprites = arcade.SpriteList(use_spatial_hash=False, is_static=True)
        for i in range(0, len(self.corners2), 4):
            a, b, c, d = self.corners2[i], self.corners2[i + 1], self.corners2[i + 2], self.corners2[i + 3]
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
            sprite = arcade.SpriteSolidColor(width=width,
                                             height=height,
                                             color=arcade.color.PINK)
            sprite.set_position(center_x, center_y)
            self.screens_sprites.append(sprite)
        print(self.corners2)

    def on_update(self, delta_time):
        pass

    def on_draw(self):
        arcade.start_render()
        self.screens_sprites.draw()
        # self.borders.draw()


if __name__ == "__main__":
    screensaver_framework._get_preferred_screen = comb_screens
    screensaver_framework.create_screensaver_window(Saver)
    arcade.run()
