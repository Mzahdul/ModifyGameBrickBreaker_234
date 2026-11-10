import tkinter as tk
import winsound

class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)

class Ball(GameObject):
    def __init__(self, canvas, x, y, game):
        self.game = game
        self.radius = 8
        self.direction = [1, -1]
        self.speed = 5.0  # Kecepatan awal stabil & mulus
        self.bricks_hit_this_round = 0
        self.stuck = True
        
        item = canvas.create_oval(x - self.radius, y - self.radius,
                                   x + self.radius, y + self.radius,
                                   fill='white', outline='white')
        super().__init__(canvas, item)

    def update(self):
        if self.stuck:
            return

        coords = self.get_position()
        width = self.game.width
        
        # Pantulan dinding kiri & kanan
        if coords[0] <= 0:
            self.canvas.coords(self.item, 0, coords[1], self.radius * 2, coords[3])
            self.direction[0] *= -1
            try: winsound.Beep(550, 30)
            except: pass
        elif coords[2] >= width:
            self.canvas.coords(self.item, width - self.radius * 2, coords[1], width, coords[3])
            self.direction[0] *= -1
            try: winsound.Beep(550, 30)
            except: pass

        # Pantulan dinding atas
        if coords[1] <= 0:
            self.canvas.coords(self.item, coords[0], 0, coords[2], self.radius * 2)
            self.direction[1] *= -1
            try: winsound.Beep(550, 30)
            except: pass

        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        self.bricks_hit_this_round = 0
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5

        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            obj_coords = game_object.get_position()
            if x > obj_coords[2]:
                self.direction[0] = 1
            elif x < obj_coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                self.bricks_hit_this_round += 1
                self.increase_speed()

        # Efek suara nada tinggi ala Mahjong/Arcade saat mengenai brick
        try:
            winsound.Beep(880, 40)
        except:
            pass

        self.update_score()

    def increase_speed(self):
        self.speed += 0.2

    def update_score(self):
        if self.bricks_hit_this_round == 1:
            self.game.increment_score(10)
        elif self.bricks_hit_this_round >= 2:
            self.game.increment_score(25)

class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 90
        self.height = 12
        self.ball = None
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill='#FFB643', outline='#D69022', width=2)
        super().__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset, max_width):
        coords = self.get_position()
        if coords[0] + offset >= 0 and coords[2] + offset <= max_width:
            super().move(offset, 0)
            if self.ball is not None and self.ball.stuck:
                self.ball.move(offset, 0)

class Brick(GameObject):
    COLORS = {1: '#AF0E00', 2: '#D78100', 3: '#FFD449'}

    def __init__(self, canvas, x, y, hits):
        self.width = 75
        self.height = 20
        self.hits = hits
        color = Brick.COLORS[hits]
        item = canvas.create_rectangle(x - self.width / 2, y - self.height / 2,
                                       x + self.width / 2, y + self.height / 2,
                                       fill=color, outline='#C06C00', width=1, tags='brick')
        super().__init__(canvas, item)