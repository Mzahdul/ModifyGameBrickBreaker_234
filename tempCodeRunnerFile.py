import tkinter as tk

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
        self.speed = 4.5  # Kecepatan awal yang mulus
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
        elif coords[2] >= width:
            self.canvas.coords(self.item, width - self.radius * 2, coords[1], width, coords[3])
            self.direction[0] *= -1

        # Pantulan dinding atas
        if coords[1] <= 0:
            self.canvas.coords(self.item, coords[0], 0, coords[2], self.radius * 2)
            self.direction[1] *= -1

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

        self.update_score()

    def increase_speed(self):
        self.speed += 0.25  # Kecepatan bertambah bertahap setiap kena brick

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

    def hit(self):
        self.hits -= 1
        if self.hits <= 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])

class Game(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.lives = 3
        self.width = 640
        self.height = 430
        self.canvas = tk.Canvas(self, bg='#E7D0F5',
                                width=self.width,
                                height=self.height,
                                highlightthickness=0)
        self.canvas.pack()
        self.pack()

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 375)
        self.items[self.paddle.item] = self.paddle

        # Membentuk susunan Bricks
        for x in range(15, self.width - 15, 78):
            self.add_brick(x + 37.5, 60, 3)
            self.add_brick(x + 37.5, 85, 2)
            self.add_brick(x + 37.5, 110, 1)

        self.hud = None
        self.hud_score = None
        self.score = 0
        self.text = None

        # Sistem penekanan tombol agar pergerakan paddle sangat fluid
        self.pressed_keys = set()
        self.canvas.focus_set()
        self.canvas.bind('<KeyPress>', self.on_key_press)
        self.canvas.bind('<KeyRelease>', self.on_key_release)

        self.setup_game()
        self.animate()

    def on_key_press(self, event):
        self.pressed_keys.add(event.keysym)
        if event.keysym == 'space':
            if self.ball and self.ball.stuck:
                self.ball.stuck = False
                if self.text:
                    self.canvas.delete(self.text)
                    self.text = None

    def on_key_release(self, event):
        if event.keysym in self.pressed_keys:
            self.pressed_keys.remove(event.keysym)

    def setup_game(self):
        self.add_ball()
        self.update_lives_text()
        self.update_score_text()
        if not self.text:
            self.text = self.canvas.create_text(self.width / 2, 230, 
                                                text='Tekan SPACE untuk Mulai', 
                                                font=('Arial', 20, 'bold'), 
                                                fill='#4A3060')

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 360, self)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def update_lives_text(self):
        text = f'Lives: {self.lives}'
        if self.hud is None:
            self.hud = self.canvas.create_text(55, 25, text=text, font=('Arial', 14, 'bold'), fill='#4A3060')
        else:
            self.canvas.itemconfig(self.hud, text=text)

    def update_score_text(self):
        text = f'Score: {self.score}'
        if self.hud_score is None:
            self.hud_score = self.canvas.create_text(self.width - 65, 25, text=text, font=('Arial', 14, 'bold'), fill='#4A3060')
        else:
            self.canvas.itemconfig(self.hud_score, text=text)

    def increment_score(self, points):
        self.score += points
        self.update_score_text()

    def animate(self):
        # Kecepatan geser paddle yang mulus
        paddle_speed = 10
        if 'Left' in self.pressed_keys or 'a' in self.pressed_keys:
            self.paddle.move(-paddle_speed, self.width)
        if 'Right' in self.pressed_keys or 'd' in self.pressed_keys:
            self.paddle.move(paddle_speed, self.width)