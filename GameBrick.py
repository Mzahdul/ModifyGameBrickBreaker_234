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
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.pack(fill=tk.BOTH, expand=True)

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 375)
        self.items[self.paddle.item] = self.paddle

        for x in range(15, self.width - 15, 78):
            self.add_brick(x + 37.5, 60, 3)
            self.add_brick(x + 37.5, 85, 2)
            self.add_brick(x + 37.5, 110, 1)

        self.hud = None
        self.hud_score = None
        self.score = 0
        self.text = None
        self.is_game_over = False
        self.is_won = False

        self.pressed_keys = set()
        
        self.canvas.focus_set()
        self.canvas.bind('<KeyPress>', self.on_key_press)
        self.canvas.bind('<KeyRelease>', self.on_key_release)
        self.canvas.bind('<Button-1>', lambda e: self.canvas.focus_set())

        self.setup_game()
        self.animate()

    def on_key_press(self, event):
        self.pressed_keys.add(event.keysym)
        if event.keysym == 'space':
            if self.is_game_over or self.is_won:
                # Restart permainan dari awal
                self.master.destroy()
                import subprocess, sys
                subprocess.Popen([sys.executable] + sys.argv)
                return

            if self.ball and self.ball.stuck:
                self.ball.stuck = False
                if self.text:
                    self.canvas.delete(self.text)
                    self.text = None
                try: winsound.Beep(650, 80)
                except: pass

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
        # Pergerakan paddle yang sangat responsif & mulus
        paddle_speed = 12
        if 'Left' in self.pressed_keys or 'a' in self.pressed_keys or 'A' in self.pressed_keys:
            self.paddle.move(-paddle_speed, self.width)
        if 'Right' in self.pressed_keys or 'd' in self.pressed_keys or 'D' in self.pressed_keys:
            self.paddle.move(paddle_speed, self.width)

        if self.ball and not self.ball.stuck and not self.is_game_over and not self.is_won:
            self.check_collisions()
            num_bricks = len(self.canvas.find_withtag('brick'))
            
            if num_bricks == 0:
                self.is_won = True
                self.ball.speed = 0
                self.canvas.create_text(self.width / 2, 230, text='YOU WIN! Breaker of Bricks!', font=('Arial', 22, 'bold'), fill='#007A00')
                self.canvas.create_text(self.width / 2, 270, text='Tekan SPACE untuk Main Lagi', font=('Arial', 14, 'bold'), fill='#4A3060')
                try: winsound.Beep(900, 200)
                except: pass
            elif self.ball.get_position()[3] >= self.height:
                # Kehilangan 1 nyawa
                self.lives -= 1
                self.update_lives_text()
                try: winsound.Beep(220, 250) # Suara kalah nyawa
                except: pass
                
                if self.lives < 0:
                    self.is_game_over = True
                    self.canvas.create_text(self.width / 2, 230, text='GAME OVER!', font=('Arial', 22, 'bold'), fill='#B30000')
                    self.canvas.create_text(self.width / 2, 270, text='Tekan SPACE untuk Coba Lagi', font=('Arial', 14, 'bold'), fill='#4A3060')
                    self.ball.speed = 0
                else:
                    # Reset bola kembali ke atas paddle (bisa lanjut main lagi!)
                    self.ball.delete()
                    paddle_coords = self.paddle.get_position()
                    x = (paddle_coords[0] + paddle_coords[2]) * 0.5
                    self.ball = Ball(self.canvas, x, 360, self)
                    self.paddle.set_ball(self.ball)
                    self.text = self.canvas.create_text(self.width / 2, 230, 
                                                        text='Kehilangan Nyawa! Tekan SPACE', 
                                                        font=('Arial', 18, 'bold'), 
                                                        fill='#B30000')
            else:
                self.ball.update()

        # Frame rate tinggi 15ms (~60 FPS) agar pergerakan sangat mulus
        self.master.after(15, self.animate)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        self.ball.collide(objects)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Break those Bricks! - Fully Fixed & Smooth Edition')
    game = Game(root)
    root.mainloop()