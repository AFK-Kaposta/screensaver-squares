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


class Square(arcade.Sprite):
    def __init__(self, color: arcade.color, lives: int, chance_to_affect: float):
        """Square has a certain number lives, when a square runs out of lives it becomes active and reduces other
        square's lives."""
        super().__init__()
        self.color = color
        self.lives = lives
        self.chance_to_affect = chance_to_affect

    def active(self):
        """returns whether or not the square has lives."""
        return bool(self.lives)


class Squares(arcade.Window):
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
        self.ups = 60  # Updates Per Second (basically useless above 60)
        self.set_update_rate(1 / self.ups)

        for i in range(len(self.corners)):  # making it so I can connect each of the neighboring dots to make a square
            if i % 4 == 2:
                self.corners[i], self.corners[i + 1] = self.corners[i + 1], self.corners[i]
        self.line_list = []  # the borders of the screen
        for i in range(0, len(self.corners), 2):
            self.line_list += [(self.corners[i], self.corners[i + 1])]
            if i % 4 == 0:
                self.line_list += [(self.corners[i], self.corners[i + 3])] + \
                                  [(self.corners[i + 1], self.corners[i + 2])]
        line_combs = itertools.combinations(self.line_list, 2)
        self.borders = arcade.SpriteList(is_static=True, use_spatial_hash=True)
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
        for line in self.line_list:
            border = arcade.SpriteSolidColor(width=abs(line[0][0] - line[1][0]) + 2,
                                             height=abs(line[0][1] - line[1][1]) + 2,
                                             color=arcade.color.PINK)
            border.bottom = min(line[0][1], line[1][1])
            border.left = min(line[0][0], line[1][0])
            self.borders.append(border)
        self.borders.move(-1, -1)

    def on_update(self, delta_time):
        pass

    def on_draw(self):
        arcade.start_render()
        self.borders.draw()


if __name__ == "__main__":
    screensaver_framework._get_preferred_screen = comb_screens
    screensaver_framework.create_screensaver_window(Squares)
    arcade.run()
