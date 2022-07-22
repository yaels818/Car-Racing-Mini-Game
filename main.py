import pygame
import time
import math
from utils import scale_image, blit_rotate_center, blit_text_center

pygame.font.init()
MAIN_FONT = pygame.font.SysFont("centurygothic", 36)
SMALL_FONT = pygame.font.SysFont("centurygothic", 26)

GRASS = scale_image(pygame.image.load("img/grass.jpg"), 3)
TRACK = scale_image(pygame.image.load("img/track.png"), 0.7)
TRACK_BORDER = scale_image(pygame.image.load("img/track-border.png"), 0.7)

FINISH = scale_image(pygame.image.load("img/finish.png"), 0.75)
FINISH_POS = (100, 190) # Finish position

RED_CAR = scale_image(pygame.image.load("img/red-car.png"), 0.4)
GREEN_CAR = scale_image(pygame.image.load("img/green-car.png"), 0.4)

# Create a mask from track border
TRACK_BORDER_MASK = pygame.mask.from_surface(TRACK_BORDER)
FINISH_MASK = pygame.mask.from_surface(FINISH)

# Set up the window (display surface) for the game based on track img size
WIDTH, HEIGHT = TRACK.get_width(), TRACK.get_height()
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game!")

FPS = 60    # Frame per second
clock = pygame.time.Clock()

PATH = [(138, 108), (93, 47), (42, 92), (51, 368), (254, 571), 
        (317, 416), (393, 360), (464, 417), (474, 551), (563, 572), 
        (570, 305), (341, 280), (341, 196), (557, 199), (566, 72), 
        (243, 55), (218, 275), (133, 200)]

class GameInfo:
    LEVELS = 7

    def __init__(self, level = 1):
        self.level = level
        self.started = False
        self.level_start_time = 0

    def next_level(self):
        self.level += 1
        self.started = False

    def reset(self):
        self.level = 1
        self.started = False
        self.level_start_time = 0

    def game_finished(self):
        return self.level > self.LEVELS

    def start_level(self):
        self.started = True
        self.level_start_time = time.time()

    def get_level_time(self):
        if not self.started:
            return 0
        else:
            # round to a whole number
            return round(time.time() - self.level_start_time)

class AbstractCar:
    def __init__(self, max_vel, rotation_vel):
        self.img = self.IMG
        self.max_vel = max_vel
        self.vel = 0
        self.rotation_vel = rotation_vel
        self.angle = 0
        self.x, self.y = self.START_POS
        self.acceleration = 0.08 

    def rotate(self, left = False, right = False):
        if left:
            self.angle += self.rotation_vel
        elif right:
            self.angle -= self.rotation_vel

    def draw(self, win):
        blit_rotate_center(win,self.img, (self.x, self.y), self.angle)

    def move_forward(self):
        # Increase velocity without going over maximum velocity
        self.vel = min(self.vel + self.acceleration, self.max_vel)
        self.move()

    def move_backward(self):
        # We want the max velocity backwards to be half of the max velocity forward
        # (Reverse gear cant reach top speed like forward gears)
        self.vel = max(self.vel - self.acceleration, -self.max_vel / 2)
        self.move()

    def move(self):
        # Using basic Trigonometry, calculate vertical and horizontal movement 
        radians = math.radians(self.angle)
        vertical = math.cos(radians) * self.vel
        horizontal = math.sin(radians) * self.vel

        # Move the car in whatever direction it is facing
        self.y -= vertical
        self.x -= horizontal

    def collide(self, mask, x = 0, y = 0):
        car_mask = pygame.mask.from_surface(self.img)

        # Calculate displacement between the 2 masks
        offset = (int(self.x - x), int(self.y - y))

        # Point of intersection - if there was poi, the objects did collide
        poi = mask.overlap(car_mask, offset) 
        return poi

    def reset(self):
        self.x, self.y = self.START_POS
        self.angle = 0
        self.vel = 0

class PlayerCar(AbstractCar): # Inherit from AbstractCar
    IMG = RED_CAR
    START_POS = (140, 150)

    def reduce_speed(self):
        # Reduce the velocity by half the acceleration, if negative then just stop moving 
        self.vel = max(self.vel - self.acceleration / 2, 0)
        self.move()

    def bounce(self):
        # Bounce back from a wall
        self.vel = -self.vel/2
        self.move()

    def reset(self):
        super().reset()

class ComputerCar(AbstractCar):
    IMG = GREEN_CAR
    START_POS = (120, 150)

    # @override
    def __init__(self, max_vel, rotation_vel, path = []):
        # Init() from AbstractCar
        super().__init__(max_vel, rotation_vel)
        self.path = path
        self.current_point = 0
        # Computer car will be moving at max velocity all the time, no acceleration
        self.vel = max_vel 

    # Function for drawing path points
    def draw_points(self, win):
        for point in self.path:
            # Draw a red point of radius 5 in the path
            pygame.draw.circle(win, (255,0,0), point, 5)

    def draw(self, win):
        super().draw(win)
        """
        self.draw_points(win)
        """

    def calculate_angle(self):
        # Get coordinates for target point
        target_x, target_y = self.path[self.current_point]
        x_diff = target_x - self.x
        y_diff = target_y - self.y

        if y_diff == 0:
            # If there is no y difference then the car is horizontal to the point, so either 90 or 270 degrees
            desired_radian_angle = math.pi / 2
        else:
            # The angle between the car and the target point
            desired_radian_angle = math.atan(x_diff / y_diff) # arctan()

        # If the target is downwards from the car
        if target_y > self.y:
            # Correct the angle to make sure the car will be heading in the correct direction
            desired_radian_angle += math.pi

        difference_in_angle = self.angle - math.degrees(desired_radian_angle)

        # If the difference is drastic, then there is a more efficient angle to get to the target point
        if difference_in_angle >= 180:
            difference_in_angle -= 360

        # Make sure the car doesnt over/undershoot the angle (avoid stuttering and over-corrections)
        if difference_in_angle > 0:
            # If the diff is less than rotation_vel we will snap immediately to the diff angle and stay on it
            self.angle -= min(self.rotation_vel, abs(difference_in_angle))
        else:
            self.angle += min(self.rotation_vel, abs(difference_in_angle))

    def update_path_point(self):
        # Get the next target point from the pre-made path
        target = self.path[self.current_point]

        # Create a rectangle with the car as top-left corner 
        # (because we have the img but the img doesn't know where it is)
        rect = pygame.Rect(self.x, self.y, self.img.get_width(), self.img.get_height())

        # If we collided with a target point, move on to the next one
        if rect.collidepoint(*target):
            self.current_point += 1

    def move(self):
        # If there is no point to move to
        if self.current_point >= len(self.path):
            return

        # Calculate and shift the car to the needed angle for the next point
        self.calculate_angle()

        # See if we need to move to the next point
        self.update_path_point()
        super().move()

    def next_level(self, level):
        self.reset()

        # Increase computer's vel 0.2 each level - will never go faster than the player's
        self.vel = self.max_vel + (level + 1) * 0.2

        self.current_point = 0

    def reset(self):
        super().reset()
        self.vel = self.max_vel
        self.current_point = 0
"""
Main function for drawing images unto the game window
"""
def draw(win, images, player_car, computer_car, game_info):
    for img, pos in images:
        # Draw this img in this position
        win.blit(img, pos)  
    
    level_text = SMALL_FONT.render(f"Level {game_info.level}", 1, (255, 255, 255))
    win.blit(level_text, (10, HEIGHT - level_text.get_height() - 90))

    time_text = SMALL_FONT.render(f"Time: {game_info.get_level_time()} sec", 1, (255, 255, 255))
    win.blit(time_text, (10, HEIGHT - time_text.get_height() - 50))

    # round to the first significant digit
    vel_text = SMALL_FONT.render(f"Velocity: {round(player_car.vel, 1)} px/sec", 1, (255, 255, 255))
    win.blit(vel_text, (10, HEIGHT - vel_text.get_height() - 10))

    player_car.draw(win)
    computer_car.draw(win)
    
    # Update the window with everything we have drawn
    pygame.display.update() 

def move_player(player_car):
    keys = pygame.key.get_pressed()
    moved = False

    if keys[pygame.K_a]:
        player_car.rotate(left = True)
    if keys[pygame.K_d]:
        player_car.rotate(right = True)
    if keys[pygame.K_w]:
        # While pressing Gas we do not want to slow
        moved = True 
        player_car.move_forward()
    if keys[pygame.K_s]:
        moved = True 
        player_car.move_backward()

    if not moved:
        player_car.reduce_speed()

def handle_collision(player_car, computer_car, game_info):
    # Check if the player car is colliding with the track walls
    if player_car.collide(TRACK_BORDER_MASK) != None:
        player_car.bounce()

    
    computer_finish_poi_collide = computer_car.collide(FINISH_MASK, *FINISH_POS)
    if computer_finish_poi_collide != None: 
            blit_text_center(WIN, MAIN_FONT, "The computer won!")
            pygame.display.update() 
            # Delay the game for 5 seconds to display the message
            pygame.time.delay(3000)
            game_info.reset()
            player_car.reset()
            computer_car.reset()

    # *FINISH_POS breaks the tuple into 2 args, x and y
    player_finish_poi_collide = player_car.collide(FINISH_MASK, *FINISH_POS)
    if player_finish_poi_collide != None: 
        # If we try to run the finish line backwards
        # finish_poi[1] ==> at index 1
        if player_finish_poi_collide[1] == 0: 
            player_car.bounce()
        else:
            blit_text_center(WIN, MAIN_FONT, "You won!")
            pygame.display.update() 
            pygame.time.delay(3000)
            game_info.next_level()
            player_car.reset()
            # Reset computer_car and increase its velocity
            computer_car.next_level(game_info.level)


run = True
images = [(GRASS, (0,0)), (TRACK, (0,0)), (FINISH, FINISH_POS), (TRACK_BORDER, (0,0))]

player_car = PlayerCar(2,4)
computer_car = ComputerCar(0.5,4, PATH)

game_info = GameInfo()


# Main event loop - keeps the game alive
while run:
    # Limit our window to this max speed
    clock.tick(FPS)     
    
    draw(WIN, images, player_car, computer_car, game_info)

    # While current level did not start
    while not game_info.started:
        blit_text_center(WIN, MAIN_FONT, f"Press any key to start level {game_info.level}!")
        pygame.display.update() 
        pygame.time.delay(1000)

        for event in pygame.event.get():
            # If player clicked X on the window
            if event.type == pygame.QUIT:   
                pygame.quit()   # Close the game cleanly
                break

            # If player pressed ANY key
            if event.type == pygame.KEYDOWN:
                game_info.start_level()

    for event in pygame.event.get():
        # If player clicked X on the window
        if event.type == pygame.QUIT:   
            run = False
            break

        """
        # Create the path for computer car
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            computer_car.path.append(pos)
        """
        
    move_player(player_car)
    computer_car.move()

    handle_collision(player_car, computer_car, game_info)

    if game_info.game_finished():
        blit_text_center(WIN, MAIN_FONT, "YOU WON THE GAME!")
        pygame.time.delay(3000)
        game_info.reset()
        player_car.reset()
        computer_car.reset()
"""
print(computer_car.path)
"""
pygame.quit()   # Close the game cleanly


