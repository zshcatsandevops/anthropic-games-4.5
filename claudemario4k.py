#!/usr/bin/env python3
"""
Ultra Mario 2D Bros - FIXED VERSION
A 2D platformer with SMB3 graphics style and BS Satellaview UI
5 Worlds x 3 Levels + Bowser Jr. Boss Fights
"""

import sys
import math
import random
from enum import Enum

# Initialize Pygame FIRST, with explicit font init
import pygame
pygame.init()
pygame.font.init()  # Explicitly initialize font module to avoid circular imports

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRAVITY = 0.8
JUMP_STRENGTH = -15
MOVE_SPEED = 5
FPS = 60

# Colors (SMB3 palette inspired)
SKY_BLUE = (146, 189, 221)
GROUND_BROWN = (139, 69, 19)
PIPE_GREEN = (0, 148, 0)
BRICK_RED = (183, 73, 0)
COIN_YELLOW = (255, 215, 0)
MARIO_RED = (228, 0, 0)
MARIO_BLUE = (0, 0, 228)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

class GameState(Enum):
    OVERWORLD = 1
    LEVEL = 2
    BOSS = 3
    GAME_OVER = 4
    VICTORY = 5
    BS_MENU = 6

class Mario:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.width = 32
        self.height = 48
        self.on_ground = False
        self.facing_right = True
        self.lives = 3
        self.coins = 0
        self.power_up = 0  # 0=small, 1=big, 2=fire
        
    def update(self, platforms):
        # Apply gravity
        self.vy += GRAVITY
        
        # Update position
        self.x += self.vx
        self.y += self.vy
        
        # Check platform collisions
        self.on_ground = False
        for platform in platforms:
            if self.check_collision(platform):
                # Landing on top
                if self.vy > 0 and self.y < platform.y:
                    self.y = platform.y - self.height
                    self.vy = 0
                    self.on_ground = True
                # Hitting from below
                elif self.vy < 0 and self.y > platform.y:
                    self.y = platform.y + platform.height
                    self.vy = 0
                # Side collisions
                elif self.vx > 0:
                    self.x = platform.x - self.width
                    self.vx = 0
                elif self.vx < 0:
                    self.x = platform.x + platform.width
                    self.vx = 0
        
        # Screen boundaries
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        
        # Death by falling
        if self.y > SCREEN_HEIGHT:
            self.lives -= 1
            return False
        return True
        
    def jump(self):
        if self.on_ground:
            self.vy = JUMP_STRENGTH
            
    def move_left(self):
        self.vx = -MOVE_SPEED
        self.facing_right = False
        
    def move_right(self):
        self.vx = MOVE_SPEED
        self.facing_right = True
        
    def stop(self):
        self.vx = 0
        
    def check_collision(self, other):
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)
                
    def draw(self, screen):
        # Draw Mario (simplified)
        color = MARIO_RED if self.power_up >= 1 else MARIO_BLUE
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        # Hat
        pygame.draw.rect(screen, MARIO_RED, (self.x + 8, self.y, 16, 8))
        # Face
        pygame.draw.rect(screen, (255, 220, 177), (self.x + 8, self.y + 8, 16, 16))
        # Eyes
        pygame.draw.rect(screen, BLACK, (self.x + 10, self.y + 12, 4, 4))
        pygame.draw.rect(screen, BLACK, (self.x + 18, self.y + 12, 4, 4))

class Platform:
    def __init__(self, x, y, width, height, color=GROUND_BROWN, type="solid"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.type = type
        
    def draw(self, screen):
        if self.type == "brick":
            # Draw brick pattern
            for i in range(0, self.width, 32):
                for j in range(0, self.height, 16):
                    pygame.draw.rect(screen, BRICK_RED, (self.x + i, self.y + j, 30, 14))
                    pygame.draw.rect(screen, BLACK, (self.x + i, self.y + j, 30, 14), 1)
        elif self.type == "pipe":
            pygame.draw.rect(screen, PIPE_GREEN, (self.x, self.y, self.width, self.height))
            pygame.draw.rect(screen, (0, 100, 0), (self.x, self.y, self.width, self.height), 3)
        else:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))

class Enemy:
    def __init__(self, x, y, type="goomba"):
        self.x = x
        self.y = y
        self.width = 32
        self.height = 32
        self.vx = -2
        self.vy = 0
        self.type = type
        self.alive = True
        
    def update(self, platforms):
        if not self.alive:
            return
            
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy
        
        # Platform collision
        for platform in platforms:
            if (self.x < platform.x + platform.width and
                self.x + self.width > platform.x and
                self.y < platform.y + platform.height and
                self.y + self.height > platform.y):
                if self.vy > 0:
                    self.y = platform.y - self.height
                    self.vy = 0
                    
        # Reverse at edges
        if self.x <= 0 or self.x >= SCREEN_WIDTH - self.width:
            self.vx *= -1
            
    def draw(self, screen):
        if not self.alive:
            return
        if self.type == "goomba":
            # Goomba body
            pygame.draw.ellipse(screen, (139, 90, 43), (self.x, self.y + 8, self.width, 24))
            # Feet
            pygame.draw.ellipse(screen, BLACK, (self.x + 4, self.y + 24, 10, 8))
            pygame.draw.ellipse(screen, BLACK, (self.x + 18, self.y + 24, 10, 8))
        elif self.type == "koopa":
            # Koopa shell
            pygame.draw.ellipse(screen, (0, 180, 0), (self.x, self.y + 4, self.width, 28))
            pygame.draw.ellipse(screen, (0, 255, 0), (self.x + 4, self.y + 8, 24, 20))

class BowserJr:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 64
        self.height = 64
        self.vx = 0
        self.vy = 0
        self.hp = 3
        self.attack_timer = 0
        self.jump_timer = 0
        self.fireballs = []
        
    def update(self, mario, platforms):
        # AI behavior
        self.attack_timer += 1
        self.jump_timer += 1
        
        # Movement AI
        if mario.x < self.x:
            self.vx = -2
        else:
            self.vx = 2
            
        # Jump occasionally
        if self.jump_timer > 120 and self.vy == 0:
            self.vy = -12
            self.jump_timer = 0
            
        # Shoot fireballs
        if self.attack_timer > 90:
            self.fireballs.append(Fireball(self.x + self.width//2, self.y + self.height//2, 
                                          1 if mario.x > self.x else -1))
            self.attack_timer = 0
            
        # Physics
        self.vy += GRAVITY * 0.7
        self.x += self.vx
        self.y += self.vy
        
        # Platform collision
        for platform in platforms:
            if (self.x < platform.x + platform.width and
                self.x + self.width > platform.x and
                self.y < platform.y + platform.height and
                self.y + self.height > platform.y):
                if self.vy > 0:
                    self.y = platform.y - self.height
                    self.vy = 0
                    
        # Update fireballs
        for fireball in self.fireballs[:]:
            fireball.update()
            if fireball.x < 0 or fireball.x > SCREEN_WIDTH:
                self.fireballs.remove(fireball)
                
    def draw(self, screen):
        # Draw Bowser Jr (simplified)
        # Body
        pygame.draw.ellipse(screen, (0, 180, 0), (self.x, self.y, self.width, self.height))
        # Shell spikes
        for i in range(3):
            x = self.x + 16 + i * 16
            y = self.y + 20
            pygame.draw.polygon(screen, WHITE, [(x, y), (x-5, y+10), (x+5, y+10)])
        # Head
        pygame.draw.ellipse(screen, (255, 220, 177), (self.x + 16, self.y - 10, 32, 32))
        # Hair tuft
        pygame.draw.polygon(screen, ORANGE, [(self.x + 32, self.y - 10), 
                                            (self.x + 28, self.y - 20), 
                                            (self.x + 36, self.y - 20)])
        # Eyes
        pygame.draw.circle(screen, BLACK, (self.x + 24, self.y + 4), 3)
        pygame.draw.circle(screen, BLACK, (self.x + 40, self.y + 4), 3)
        
        # Draw fireballs
        for fireball in self.fireballs:
            fireball.draw(screen)
            
        # HP bar
        pygame.draw.rect(screen, BLACK, (self.x, self.y - 25, 64, 8))
        pygame.draw.rect(screen, (255, 0, 0), (self.x + 1, self.y - 24, 20 * self.hp, 6))

class Fireball:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.vx = direction * 5
        self.vy = random.uniform(-2, 2)
        
    def update(self):
        self.x += self.vx
        self.y += self.vy
        
    def draw(self, screen):
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), 6)
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 4)

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 24
        self.collected = False
        self.animation = 0
        
    def update(self):
        self.animation = (self.animation + 1) % 60
        
    def draw(self, screen):
        if not self.collected:
            # Animated coin
            scale = 1 + math.sin(self.animation * 0.1) * 0.1
            w = int(self.width * scale)
            h = int(self.height * scale)
            pygame.draw.ellipse(screen, COIN_YELLOW, 
                              (self.x - (w-self.width)//2, self.y - (h-self.height)//2, w, h))
            pygame.draw.ellipse(screen, (255, 255, 0), 
                              (self.x + 4, self.y + 4, w - 8, h - 8))

class Level:
    def __init__(self, world_num, level_num):
        self.world_num = world_num
        self.level_num = level_num
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.goal_x = SCREEN_WIDTH - 100
        self.goal_y = 400
        self.completed = False
        self.generate_level()
        
    def generate_level(self):
        # Ground
        self.platforms.append(Platform(0, 500, SCREEN_WIDTH, 100))
        
        # Generate platforms based on world theme
        if self.world_num == 1:  # Grassland
            self.platforms.append(Platform(200, 400, 100, 20, GROUND_BROWN, "brick"))
            self.platforms.append(Platform(400, 350, 100, 20, GROUND_BROWN, "brick"))
            self.platforms.append(Platform(600, 300, 100, 20, GROUND_BROWN, "brick"))
            self.platforms.append(Platform(550, 420, 60, 80, PIPE_GREEN, "pipe"))
        elif self.world_num == 2:  # Desert
            self.platforms.append(Platform(150, 420, 120, 20, (255, 218, 185), "brick"))
            self.platforms.append(Platform(350, 380, 80, 20, (255, 218, 185), "brick"))
            self.platforms.append(Platform(500, 340, 100, 20, (255, 218, 185), "brick"))
            self.platforms.append(Platform(300, 440, 60, 60, PIPE_GREEN, "pipe"))
        elif self.world_num == 3:  # Water
            self.platforms.append(Platform(180, 450, 100, 20, (0, 119, 190), "brick"))
            self.platforms.append(Platform(380, 400, 100, 20, (0, 119, 190), "brick"))
            self.platforms.append(Platform(580, 350, 100, 20, (0, 119, 190), "brick"))
        elif self.world_num == 4:  # Sky
            self.platforms.append(Platform(100, 450, 80, 20, WHITE, "brick"))
            self.platforms.append(Platform(250, 380, 80, 20, WHITE, "brick"))
            self.platforms.append(Platform(400, 320, 80, 20, WHITE, "brick"))
            self.platforms.append(Platform(550, 380, 80, 20, WHITE, "brick"))
        elif self.world_num == 5:  # Castle
            self.platforms.append(Platform(200, 430, 100, 20, (80, 80, 80), "brick"))
            self.platforms.append(Platform(400, 380, 100, 20, (80, 80, 80), "brick"))
            self.platforms.append(Platform(600, 330, 100, 20, (80, 80, 80), "brick"))
            
        # Add enemies
        for i in range(2 + self.level_num):
            x = 200 + i * 150
            y = 450
            enemy_type = "goomba" if i % 2 == 0 else "koopa"
            self.enemies.append(Enemy(x, y, enemy_type))
            
        # Add coins
        for platform in self.platforms[1:4]:  # Skip ground
            self.coins.append(Coin(platform.x + platform.width//2 - 12, platform.y - 40))
            
    def update(self, mario):
        # Update enemies
        for enemy in self.enemies:
            enemy.update(self.platforms)
            # Check collision with Mario
            if enemy.alive and mario.check_collision(enemy):
                if mario.vy > 0 and mario.y < enemy.y:
                    # Stomp enemy
                    enemy.alive = False
                    mario.vy = -8
                else:
                    # Mario takes damage
                    mario.power_up = max(0, mario.power_up - 1)
                    
        # Update coins
        for coin in self.coins:
            coin.update()
            if not coin.collected and mario.check_collision(coin):
                coin.collected = True
                mario.coins += 1
                
        # Check goal
        if abs(mario.x - self.goal_x) < 50 and abs(mario.y - self.goal_y) < 50:
            self.completed = True
            
    def draw(self, screen):
        for platform in self.platforms:
            platform.draw(screen)
        for enemy in self.enemies:
            enemy.draw(screen)
        for coin in self.coins:
            coin.draw(screen)
        # Draw goal flag
        pygame.draw.rect(screen, (139, 90, 43), (self.goal_x, self.goal_y, 10, 100))
        pygame.draw.polygon(screen, (255, 0, 0), 
                           [(self.goal_x + 10, self.goal_y),
                            (self.goal_x + 60, self.goal_y + 20),
                            (self.goal_x + 10, self.goal_y + 40)])

class BossLevel:
    def __init__(self, world_num):
        self.world_num = world_num
        self.platforms = []
        self.boss = BowserJr(SCREEN_WIDTH - 200, 300)
        self.completed = False
        self.generate_arena()
        
    def generate_arena(self):
        # Ground
        self.platforms.append(Platform(0, 500, SCREEN_WIDTH, 100))
        # Boss platforms
        self.platforms.append(Platform(100, 400, 100, 20, BRICK_RED, "brick"))
        self.platforms.append(Platform(600, 400, 100, 20, BRICK_RED, "brick"))
        self.platforms.append(Platform(350, 350, 100, 20, BRICK_RED, "brick"))
        
    def update(self, mario):
        self.boss.update(mario, self.platforms)
        
        # Check if Mario defeats boss
        if mario.check_collision(self.boss) and mario.vy > 0 and mario.y < self.boss.y:
            self.boss.hp -= 1
            mario.vy = -12
            if self.boss.hp <= 0:
                self.completed = True
                
        # Check fireball collisions
        for fireball in self.boss.fireballs:
            if (abs(fireball.x - mario.x - mario.width//2) < 20 and
                abs(fireball.y - mario.y - mario.height//2) < 20):
                mario.power_up = max(0, mario.power_up - 1)
                self.boss.fireballs.remove(fireball)
                
    def draw(self, screen):
        for platform in self.platforms:
            platform.draw(screen)
        self.boss.draw(screen)

class Overworld:
    def __init__(self):
        self.world_positions = [
            (100, 300),  # World 1
            (250, 250),  # World 2
            (400, 200),  # World 3
            (550, 250),  # World 4
            (700, 300),  # World 5
        ]
        self.current_world = 0
        self.completed_levels = [[False] * 4 for _ in range(5)]  # 3 levels + boss
        
    def draw(self, screen, mario_sprite_x=0, mario_sprite_y=0):
        # Draw SMB3-style overworld paths
        for i in range(len(self.world_positions) - 1):
            x1, y1 = self.world_positions[i]
            x2, y2 = self.world_positions[i + 1]
            # Draw dotted path
            steps = 10
            for j in range(steps):
                t = j / steps
                x = x1 + (x2 - x1) * t
                y = y1 + (y2 - y1) * t
                pygame.draw.circle(screen, WHITE, (int(x), int(y)), 3)
                
        # Draw world nodes
        for i, (x, y) in enumerate(self.world_positions):
            # World circle
            color = (0, 255, 0) if i <= self.current_world else (128, 128, 128)
            pygame.draw.circle(screen, color, (x, y), 30)
            pygame.draw.circle(screen, BLACK, (x, y), 30, 3)
            
            # World number
            font = pygame.font.Font(None, 24)
            text = font.render(str(i + 1), True, BLACK)
            screen.blit(text, (x - 8, y - 10))
            
            # Level indicators
            for j in range(4):  # 3 levels + boss
                lx = x - 30 + j * 20
                ly = y + 40
                if self.completed_levels[i][j]:
                    pygame.draw.rect(screen, (0, 255, 0), (lx, ly, 15, 15))
                else:
                    pygame.draw.rect(screen, (255, 0, 0), (lx, ly, 15, 15))
                pygame.draw.rect(screen, BLACK, (lx, ly, 15, 15), 1)
                
        # Draw mini Mario on current world
        wx, wy = self.world_positions[self.current_world]
        pygame.draw.rect(screen, MARIO_RED, (wx - 8 + mario_sprite_x, wy - 40 + mario_sprite_y, 16, 24))

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Ultra Mario 2D Bros - BS Satellaview Edition")
        self.clock = pygame.time.Clock()
        self.state = GameState.BS_MENU
        self.mario = Mario(100, 400)
        self.overworld = Overworld()
        self.current_level = None
        self.current_boss = None
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.bs_menu_selection = 0
        self.mario_sprite_animation = 0
        
    def draw_bs_menu(self):
        # BS Satellaview style menu
        self.screen.fill((32, 0, 64))  # Deep purple background
        
        # Title with gradient effect
        title = self.font.render("BS ULTRA MARIO 2D BROS", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        self.screen.blit(title, title_rect)
        
        # Satellaview logo area
        pygame.draw.rect(self.screen, (64, 0, 128), (250, 150, 300, 80))
        pygame.draw.rect(self.screen, WHITE, (250, 150, 300, 80), 3)
        bs_text = self.small_font.render("BS-X Satellaview System", True, WHITE)
        self.screen.blit(bs_text, (320, 180))
        
        # Menu options
        menu_items = ["Start Game", "Select World", "Options", "Exit"]
        for i, item in enumerate(menu_items):
            color = COIN_YELLOW if i == self.bs_menu_selection else WHITE
            text = self.font.render(item, True, color)
            self.screen.blit(text, (300, 280 + i * 60))
            if i == self.bs_menu_selection:
                pygame.draw.polygon(self.screen, COIN_YELLOW, 
                                   [(270, 295 + i * 60), (290, 285 + i * 60), (290, 305 + i * 60)])
        
        # Footer
        footer = self.small_font.render("© 1995 St.GIGA / Nintendo", True, WHITE)
        self.screen.blit(footer, (260, 550))
        
    def draw_hud(self):
        # SMB3 style HUD at top
        pygame.draw.rect(self.screen, BLACK, (0, 0, SCREEN_WIDTH, 40))
        
        # Lives
        lives_text = self.small_font.render(f"MARIO x{self.mario.lives}", True, WHITE)
        self.screen.blit(lives_text, (20, 10))
        
        # Coins
        coins_text = self.small_font.render(f"COINS: {self.mario.coins:03d}", True, COIN_YELLOW)
        self.screen.blit(coins_text, (200, 10))
        
        # World/Level
        if self.current_level:
            level_text = self.small_font.render(
                f"WORLD {self.current_level.world_num}-{self.current_level.level_num}", 
                True, WHITE)
            self.screen.blit(level_text, (400, 10))
        elif self.current_boss:
            level_text = self.small_font.render(
                f"WORLD {self.current_boss.world_num} BOSS", 
                True, (255, 100, 100))
            self.screen.blit(level_text, (400, 10))
            
        # Power-up status
        power_text = ["SMALL", "SUPER", "FIRE"][self.mario.power_up]
        power_color = [WHITE, (255, 100, 100), ORANGE][self.mario.power_up]
        p_text = self.small_font.render(power_text, True, power_color)
        self.screen.blit(p_text, (600, 10))
        
    def run(self):
        running = True
        
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                if event.type == pygame.KEYDOWN:
                    if self.state == GameState.BS_MENU:
                        if event.key == pygame.K_UP:
                            self.bs_menu_selection = (self.bs_menu_selection - 1) % 4
                        elif event.key == pygame.K_DOWN:
                            self.bs_menu_selection = (self.bs_menu_selection + 1) % 4
                        elif event.key == pygame.K_RETURN:
                            if self.bs_menu_selection == 0:  # Start Game
                                self.state = GameState.OVERWORLD
                            elif self.bs_menu_selection == 3:  # Exit
                                running = False
                        # Press 'q' to directly load a level from the menu
                        elif event.key == pygame.K_q:
                            self.current_level = Level(1, 1)
                            self.state = GameState.LEVEL
                            self.mario = Mario(100, 400)
                                
                    elif self.state == GameState.OVERWORLD:
                        if event.key == pygame.K_LEFT and self.overworld.current_world > 0:
                            # Check if previous world is completed
                            if self.overworld.completed_levels[self.overworld.current_world - 1][3]:
                                self.overworld.current_world -= 1
                        elif event.key == pygame.K_RIGHT and self.overworld.current_world < 4:
                            # Check if current world boss is defeated
                            if self.overworld.completed_levels[self.overworld.current_world][3]:
                                self.overworld.current_world += 1
                        elif event.key == pygame.K_1:  # Level 1
                            self.current_level = Level(self.overworld.current_world + 1, 1)
                            self.state = GameState.LEVEL
                            self.mario = Mario(100, 400)
                        elif event.key == pygame.K_2:  # Level 2
                            if self.overworld.completed_levels[self.overworld.current_world][0]:
                                self.current_level = Level(self.overworld.current_world + 1, 2)
                                self.state = GameState.LEVEL
                                self.mario = Mario(100, 400)
                        elif event.key == pygame.K_3:  # Level 3
                            if self.overworld.completed_levels[self.overworld.current_world][1]:
                                self.current_level = Level(self.overworld.current_world + 1, 3)
                                self.state = GameState.LEVEL
                                self.mario = Mario(100, 400)
                        elif event.key == pygame.K_b:  # Boss
                            if self.overworld.completed_levels[self.overworld.current_world][2]:
                                self.current_boss = BossLevel(self.overworld.current_world + 1)
                                self.state = GameState.BOSS
                                self.mario = Mario(100, 400)
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.BS_MENU
                        # Press 'q' to directly load a level from overworld
                        elif event.key == pygame.K_q:
                            self.current_level = Level(self.overworld.current_world + 1, 1)
                            self.state = GameState.LEVEL
                            self.mario = Mario(100, 400)
                            
                    elif self.state in [GameState.LEVEL, GameState.BOSS]:
                        if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                            self.mario.jump()
                        elif event.key == pygame.K_ESCAPE:
                            self.state = GameState.OVERWORLD
                        # Press 'q' to load a new level while in a level
                        elif event.key == pygame.K_q:
                            if self.current_level:
                                next_level = (self.current_level.level_num % 3) + 1
                                self.current_level = Level(self.current_level.world_num, next_level)
                            else:
                                self.current_level = Level(1, 1)
                            self.mario = Mario(100, 400)
                            
                    elif self.state == GameState.GAME_OVER:
                        if event.key == pygame.K_RETURN:
                            self.__init__()
                        # Press 'q' to load a level from game over screen
                        elif event.key == pygame.K_q:
                            self.current_level = Level(1, 1)
                            self.state = GameState.LEVEL
                            self.mario = Mario(100, 400)
                            
                    elif self.state == GameState.VICTORY:
                        if event.key == pygame.K_RETURN:
                            self.state = GameState.BS_MENU
                        # Press 'q' to load a level from victory screen
                        elif event.key == pygame.K_q:
                            self.current_level = Level(1, 1)
                            self.state = GameState.LEVEL
                            self.mario = Mario(100, 400)
                            
            # Continuous key input for movement
            if self.state in [GameState.LEVEL, GameState.BOSS]:
                keys = pygame.key.get_pressed()
                if keys[pygame.K_LEFT]:
                    self.mario.move_left()
                elif keys[pygame.K_RIGHT]:
                    self.mario.move_right()
                else:
                    self.mario.stop()
                    
            # Update game logic
            if self.state == GameState.LEVEL:
                if self.current_level:
                    if not self.mario.update(self.current_level.platforms):
                        if self.mario.lives <= 0:
                            self.state = GameState.GAME_OVER
                        else:
                            # Respawn
                            self.mario = Mario(100, 400)
                            
                    self.current_level.update(self.mario)
                    
                    if self.current_level.completed:
                        # Mark level as completed
                        level_index = self.current_level.level_num - 1
                        self.overworld.completed_levels[self.overworld.current_world][level_index] = True
                        # Unlock next level
                        if level_index < 2:
                            self.overworld.completed_levels[self.overworld.current_world][level_index + 1] = True
                        self.state = GameState.OVERWORLD
                        
            elif self.state == GameState.BOSS:
                if self.current_boss:
                    if not self.mario.update(self.current_boss.platforms):
                        if self.mario.lives <= 0:
                            self.state = GameState.GAME_OVER
                        else:
                            # Respawn
                            self.mario = Mario(100, 400)
                            
                    self.current_boss.update(self.mario)
                    
                    if self.current_boss.completed:
                        # Mark boss as defeated
                        self.overworld.completed_levels[self.overworld.current_world][3] = True
                        # Check if all worlds completed
                        if self.overworld.current_world == 4:
                            self.state = GameState.VICTORY
                        else:
                            # Unlock next world
                            if self.overworld.current_world < 4:
                                self.overworld.current_world += 1
                            self.state = GameState.OVERWORLD
                            
            # Animation
            self.mario_sprite_animation = (self.mario_sprite_animation + 1) % 40
            
            # Drawing
            if self.state == GameState.BS_MENU:
                self.draw_bs_menu()
                
            elif self.state == GameState.OVERWORLD:
                # Draw overworld with animated Mario
                self.screen.fill(SKY_BLUE)
                
                # Animated clouds
                for i in range(3):
                    x = (i * 250 + self.mario_sprite_animation * 2) % (SCREEN_WIDTH + 100) - 50
                    y = 50 + i * 30
                    pygame.draw.ellipse(self.screen, WHITE, (x, y, 80, 40))
                    pygame.draw.ellipse(self.screen, WHITE, (x + 20, y - 10, 60, 40))
                    pygame.draw.ellipse(self.screen, WHITE, (x + 40, y, 60, 40))
                    
                # Hills background
                pygame.draw.ellipse(self.screen, (34, 139, 34), (50, 400, 200, 300))
                pygame.draw.ellipse(self.screen, (34, 139, 34), (500, 420, 250, 280))
                
                mario_y = math.sin(self.mario_sprite_animation * 0.15) * 5
                self.overworld.draw(self.screen, 0, mario_y)
                
                # Instructions
                inst = self.small_font.render("Press 1-3 for levels, B for Boss, Arrow keys to select world, Q for quick level", True, WHITE)
                self.screen.blit(inst, (50, 550))
                
            elif self.state == GameState.LEVEL:
                # Draw level
                self.screen.fill(SKY_BLUE)
                self.current_level.draw(self.screen)
                self.mario.draw(self.screen)
                self.draw_hud()
                
            elif self.state == GameState.BOSS:
                # Draw boss arena
                self.screen.fill((64, 0, 0))  # Dark red sky for boss
                self.current_boss.draw(self.screen)
                self.mario.draw(self.screen)
                self.draw_hud()
                
            elif self.state == GameState.GAME_OVER:
                self.screen.fill(BLACK)
                game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
                game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
                self.screen.blit(game_over_text, game_over_rect)
                
                continue_text = self.small_font.render("Press ENTER to restart or Q to play level", True, WHITE)
                continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
                self.screen.blit(continue_text, continue_rect)
                
            elif self.state == GameState.VICTORY:
                self.screen.fill(SKY_BLUE)
                
                # Victory animation
                for i in range(10):
                    x = random.randint(0, SCREEN_WIDTH)
                    y = random.randint(0, SCREEN_HEIGHT)
                    color = random.choice([COIN_YELLOW, ORANGE, (255, 0, 255), (0, 255, 255)])
                    pygame.draw.circle(self.screen, color, (x, y), random.randint(2, 8))
                    
                victory_text = self.font.render("CONGRATULATIONS!", True, COIN_YELLOW)
                victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
                self.screen.blit(victory_text, victory_rect)
                
                complete_text = self.font.render("YOU SAVED THE MUSHROOM KINGDOM!", True, WHITE)
                complete_rect = complete_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.screen.blit(complete_text, complete_rect)
                
                thanks_text = self.small_font.render("Thank you for playing Ultra Mario 2D Bros!", True, WHITE)
                thanks_rect = thanks_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
                self.screen.blit(thanks_text, thanks_rect)
                
                continue_text = self.small_font.render("Press ENTER to return to menu or Q to play level", True, WHITE)
                continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150))
                self.screen.blit(continue_text, continue_rect)
                
            pygame.display.flip()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
