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
    def __init__(self, lives: int = None, max_lives: int = None, min_lives: int = None, *args, **kwargs):
        """Square has a certain number lives, when a square runs out of lives it becomes active and reduces other
        square's lives."""
        super().__init__(*args, **kwargs)

        self.lives = None
        self.set_lives(lives, max_lives, min_lives)

    def is_active(self) -> bool:
        """returns whether or not the square has lives."""
        return not bool(self.lives)

    def is_passive(self):
        """returns whether or not the square has lives."""
        return bool(self.lives)

    def reduce_lives(self, amount: int = 1) -> None:
        """reduces lives from the square."""
        if self.is_passive():
            self.lives -= amount

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
                curr = self.grid_list[x][y]
                if curr.is_active():
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


class SpriteScreens(arcade.Sprite):
    def __init__(self, corners: list, center_x: int, center_y: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.corners = corners
        self.center_x = center_x
        self.center_y = center_y

        self.relative_hit_box = []
        for point in self.corners:
            self.relative_hit_box += [[point[0] - center_x, point[1] - center_y]]

        self.set_hit_box(self.relative_hit_box)

    def draw(self):
        self.draw_hit_box(color=arcade.color.PINK, line_thickness=5)


class Saver(arcade.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        """converting from the pyglet graphing system to the arcade one"""
        self.corners = get_corners(pyglet.canvas.get_display().get_screens())
        diff = get_farthest_points(self.corners)
        x_diff, y_diff = diff[0][0], diff[1][1]  # the most bottom left corner (where the arcade 0,0 is)
        for i in range(len(self.corners)):
            self.corners[i] = (self.corners[i][0] - x_diff, -self.corners[i][1] + y_diff)

        """setting key attributes"""
        self.view_corners = get_farthest_points(self.corners)
        self.screen_color = arcade.color.DARK_ELECTRIC_BLUE
        self.ups = 20  # Updates Per Second (basically useless above 60)
        self.set_update_rate(1 / self.ups)

        for i in range(len(self.corners)):  # making it so I can connect each of the neighboring dots to make a
            # rectangle
            if i % 4 == 2:
                self.corners[i], self.corners[i + 1] = self.corners[i + 1], self.corners[i]
        self.line_list = []  # the borders of the screen
        for i in range(0, len(self.corners), 2):
            self.line_list += [(self.corners[i], self.corners[i + 1])]
            if i % 4 == 0:
                self.line_list += [(self.corners[i], self.corners[i + 3])] + \
                                  [(self.corners[i + 1], self.corners[i + 2])]
        line_combs = itertools.combinations(self.line_list, 2)
        # self.borders = arcade.SpriteList(is_static=True, use_spatial_hash=True)
        for line1, line2 in line_combs:
            if line1[0][0] == line1[1][0] == line2[0][0] == line2[1][0]:
                out = sorted(line1 + line2, key=lambda x: x[1])
                self.line_list.remove(line1)
                self.line_list.remove(line2)
                self.line_list += ((out[0], out[1]), (out[2], out[3]))
            elif line1[0][1] == line1[1][1] == line2[0][1] == line2[1][1]:
                out = sorted(line1 + line2, key=lambda x: x[0])
                self.line_list.remove(line1)
                self.line_list.remove(line2)
                self.line_list += ((out[0], out[1]), (out[2], out[3]))
        # for line in self.line_list:
        #     border = arcade.SpriteSolidColor(width=abs(line[0][0] - line[1][0]) + 2,
        #                                      height=abs(line[0][1] - line[1][1]) + 2,
        #                                      color=arcade.color.PINK)
        #     border.bottom = min(line[0][1], line[1][1])
        #     border.left = min(line[0][0], line[1][0])
        #     self.borders.append(border)
        # self.borders.move(-1, -1)

        self.corners_sorted = self.convert_to_hit_box(self.line_list)
        center_x = int((self.view_corners[0][0] + self.view_corners[1][0]) / 2)
        center_y = int((self.view_corners[0][1] + self.view_corners[1][1]) / 2)
        self.screens_sprite = SpriteScreens(corners=self.corners_sorted, center_x=center_x, center_y=center_y)

    def convert_to_hit_box(self, lines) -> list:
        """gets a list of corners and sorts them such as if each neighbour is connected, the shape of all the
        screens combined would be drawn."""

        def locate(list_of_lines, line):
            """locates the first occurrence on n in a list of points"""
            for i in range(len(list_of_lines)):
                if list_of_lines[i][0] == line[1]:
                    return i, False
                elif list_of_lines[i][1] == line[1]:
                    return i, True
            return None, None

        new = [lines[0]]
        del lines[0]
        while len(lines) > 0:
            index, reverse = locate(lines, new[-1])
            if reverse:
                lines[index] = (lines[index][1], lines[index][0])
            if index is None:
                new = new[1:] + [new[0]]
            else:
                new.append(lines[index])
                del lines[index]

        out = []
        for point1, point2 in new:
            out += [point1, point2]
        return out

    def on_update(self, delta_time):
        pass

    def on_draw(self):
        arcade.start_render()
        self.screens_sprite.draw()
        # self.borders.draw()


if __name__ == "__main__":
    screensaver_framework._get_preferred_screen = comb_screens
    screensaver_framework.create_screensaver_window(Saver)
    arcade.run()
