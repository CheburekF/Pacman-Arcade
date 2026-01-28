import arcade

from constants import WINDOW_HEIGHT


class Brick(arcade.Sprite):
    brick_image = [
        arcade.load_texture("images/brick0.png"),
        arcade.load_texture("images/brick1.png"),
        arcade.load_texture("images/brick2.png"),
        arcade.load_texture("images/brick3.png"),
        arcade.load_texture("images/penOpening.png"),
    ]
    BRICK = 1
    OPENING = 4

    def __init__(self, element, x, y):
        image = Brick.brick_image[element]
        x = x * 20 + 20
        y = WINDOW_HEIGHT - (y * 20 + 40)
        super().__init__(image, 1, x, y)
        if element < 4:
            self.type = Brick.BRICK
        else:
            self.type = Brick.OPENING
