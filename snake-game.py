import pygame
import random
import sys
import time
from enum import Enum

# Initialize pygame
pygame.init()

# Game constants
CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 30
SCREEN_WIDTH = CELL_SIZE * GRID_WIDTH
SCREEN_HEIGHT = CELL_SIZE * GRID_HEIGHT
SCORE_AREA_HEIGHT = 60
TOTAL_HEIGHT = SCREEN_HEIGHT + SCORE_AREA_HEIGHT

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
DARK_GREEN = (0, 100, 0)

# Fonts
FONT_SMALL = pygame.font.Font(None, 24)
FONT_MEDIUM = pygame.font.Font(None, 32)
FONT_LARGE = pygame.font.Font(None, 48)

# Direction enum
class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

# Power-up types
class PowerUpType(Enum):
    SPEED = 1
    SLOW = 2
    SCORE_BOOST = 3
    INVINCIBILITY = 4

class PowerUp:
    def __init__(self, position, power_type):
        self.position = position
        self.type = power_type
        self.time_created = pygame.time.get_ticks()
        self.lifespan = 10000  # 10 seconds lifespan

    def is_expired(self):
        return pygame.time.get_ticks() - self.time_created > self.lifespan

    def draw(self, screen):
        color = YELLOW
        if self.type == PowerUpType.SPEED:
            color = CYAN
        elif self.type == PowerUpType.SLOW:
            color = PURPLE
        elif self.type == PowerUpType.SCORE_BOOST:
            color = YELLOW
        elif self.type == PowerUpType.INVINCIBILITY:
            color = WHITE
            
        x, y = self.position
        pygame.draw.rect(screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Add a pulsing effect
        time_alive = pygame.time.get_ticks() - self.time_created
        pulse = abs(int(127 * (1 + (time_alive % 1000) / 500.0)))
        pygame.draw.rect(screen, (pulse, pulse, pulse), 
                        (x * CELL_SIZE + 2, y * CELL_SIZE + 2, CELL_SIZE - 4, CELL_SIZE - 4), 1)

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, TOTAL_HEIGHT))
        pygame.display.set_caption("Retro Snake Game")
        self.clock = pygame.time.Clock()
        
        # Initialize attributes that are needed in spawn_food
        self.snake = []
        self.power_ups = []
        
        # Now reset the game safely
        self.reset_game()

    def reset_game(self):
        # Snake properties
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = Direction.RIGHT
        self.direction_queue = []
        self.grow_snake = False
        
        # Game state
        self.score = 0
        self.game_over = False
        self.paused = False
        self.level = 1
        self.base_speed = 8
        self.current_speed = self.base_speed
        
        # Power-ups (initialize before food)
        self.power_ups = []
        self.active_effects = {
            "speed": 0,
            "slow": 0,
            "score_boost": 0,
            "invincibility": 0
        }
        self.last_power_up_time = 0
        self.power_up_chance = 0.15
        
        # Food (spawn after power_ups is initialized)
        self.food = self.spawn_food()
        
        # Decoration grid for background
        self.decoration_grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                self.decoration_grid[i][j] = random.randint(0, 10)

    def spawn_food(self):
        while True:
            position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if position not in self.snake and position not in [p.position for p in self.power_ups]:
                return position

    def spawn_power_up(self):
        if random.random() < self.power_up_chance:
            while True:
                position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
                if position not in self.snake and position != self.food and position not in [p.position for p in self.power_ups]:
                    power_type = random.choice(list(PowerUpType))
                    self.power_ups.append(PowerUp(position, power_type))
                    break

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.paused = not self.paused
                elif event.key == pygame.K_r and self.game_over:
                    self.reset_game()
                elif not self.paused:
                    if event.key == pygame.K_UP and self.direction != Direction.DOWN:
                        self.direction_queue.append(Direction.UP)
                    elif event.key == pygame.K_DOWN and self.direction != Direction.UP:
                        self.direction_queue.append(Direction.DOWN)
                    elif event.key == pygame.K_LEFT and self.direction != Direction.RIGHT:
                        self.direction_queue.append(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT and self.direction != Direction.LEFT:
                        self.direction_queue.append(Direction.RIGHT)

    def update(self):
        if self.paused or self.game_over:
            return
            
        # Process direction queue for smoother controls
        if self.direction_queue:
            next_dir = self.direction_queue.pop(0)
            # Only change direction if it's not opposite to current movement
            if (self.direction == Direction.UP and next_dir != Direction.DOWN) or \
               (self.direction == Direction.DOWN and next_dir != Direction.UP) or \
               (self.direction == Direction.LEFT and next_dir != Direction.RIGHT) or \
               (self.direction == Direction.RIGHT and next_dir != Direction.LEFT):
                self.direction = next_dir
        
        # Update power-up effects
        current_time = pygame.time.get_ticks()
        
        # Speed effects
        if self.active_effects["speed"] > current_time:
            self.current_speed = self.base_speed + 4
        elif self.active_effects["slow"] > current_time:
            self.current_speed = max(3, self.base_speed - 3)
        else:
            self.current_speed = self.base_speed
        
        # Move snake
        head_x, head_y = self.snake[0]
        dx, dy = self.direction.value
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)
        
        # Check for collisions
        if not self.active_effects["invincibility"] > current_time:
            if new_head in self.snake:
                self.game_over = True
                return
        
        self.snake.insert(0, new_head)
        
        # Check for food
        if new_head == self.food:
            self.food = self.spawn_food()
            self.score += 10 * (2 if self.active_effects["score_boost"] > current_time else 1)
            
            # Increase difficulty every 5 food items eaten
            if self.score % 50 == 0:
                self.level += 1
                self.base_speed = min(15, self.base_speed + 1)
                
            # Spawn a power-up with increasing likelihood as game progresses
            if random.random() < min(0.5, self.power_up_chance + (self.level * 0.03)):
                self.spawn_power_up()
                
            # Snake grows
            self.grow_snake = True
        
        # Check for power-ups
        for power_up in self.power_ups[:]:
            if new_head == power_up.position:
                self.apply_power_up(power_up)
                self.power_ups.remove(power_up)
            elif power_up.is_expired():
                self.power_ups.remove(power_up)
        
        # Remove tail if snake didn't grow
        if not self.grow_snake:
            self.snake.pop()
        else:
            self.grow_snake = False

    def apply_power_up(self, power_up):
        current_time = pygame.time.get_ticks()
        effect_duration = 5000  # 5 seconds
        
        if power_up.type == PowerUpType.SPEED:
            self.active_effects["speed"] = current_time + effect_duration
            # Cancel slow effect if active
            self.active_effects["slow"] = 0
        elif power_up.type == PowerUpType.SLOW:
            self.active_effects["slow"] = current_time + effect_duration
            # Cancel speed effect if active
            self.active_effects["speed"] = 0
        elif power_up.type == PowerUpType.SCORE_BOOST:
            self.active_effects["score_boost"] = current_time + effect_duration
        elif power_up.type == PowerUpType.INVINCIBILITY:
            self.active_effects["invincibility"] = current_time + effect_duration

    def draw_grid(self):
        # Draw decorative background
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.decoration_grid[y][x] > 8:  # Only draw some cells for subtle effect
                    pygame.draw.rect(self.screen, (20, 20, 20), 
                                    (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # Draw grid lines for retro feel
        for x in range(0, SCREEN_WIDTH, CELL_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
            pygame.draw.line(self.screen, (30, 30, 30), (0, y), (SCREEN_WIDTH, y))

    def draw_snake(self):
        # Draw snake body
        for i, (x, y) in enumerate(self.snake):
            # Head is brighter
            if i == 0:
                color = GREEN
            # Tail gradually gets darker
            else:
                darkness = min(100, i * 5)
                color = (0, max(50, 255 - darkness), 0)
                
            # Add glow effect if invincible
            if self.active_effects["invincibility"] > pygame.time.get_ticks():
                glow_size = abs(int(5 * (1 + (pygame.time.get_ticks() % 1000) / 500.0)))
                pygame.draw.rect(self.screen, (100, 100, 255), 
                               (x * CELL_SIZE - glow_size, y * CELL_SIZE - glow_size, 
                                CELL_SIZE + 2*glow_size, CELL_SIZE + 2*glow_size))
                
            pygame.draw.rect(self.screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            
            # Draw eyes on head
            if i == 0:
                eye_size = CELL_SIZE // 4
                dx, dy = self.direction.value
                
                # Eye positions depend on direction
                if dx == 1:  # Right
                    left_eye = (x * CELL_SIZE + CELL_SIZE - eye_size, y * CELL_SIZE + eye_size)
                    right_eye = (x * CELL_SIZE + CELL_SIZE - eye_size, y * CELL_SIZE + CELL_SIZE - 2*eye_size)
                elif dx == -1:  # Left
                    left_eye = (x * CELL_SIZE, y * CELL_SIZE + eye_size)
                    right_eye = (x * CELL_SIZE, y * CELL_SIZE + CELL_SIZE - 2*eye_size)
                elif dy == 1:  # Down
                    left_eye = (x * CELL_SIZE + eye_size, y * CELL_SIZE + CELL_SIZE - eye_size)
                    right_eye = (x * CELL_SIZE + CELL_SIZE - 2*eye_size, y * CELL_SIZE + CELL_SIZE - eye_size)
                else:  # Up
                    left_eye = (x * CELL_SIZE + eye_size, y * CELL_SIZE)
                    right_eye = (x * CELL_SIZE + CELL_SIZE - 2*eye_size, y * CELL_SIZE)
                
                pygame.draw.rect(self.screen, BLACK, (*left_eye, eye_size, eye_size))
                pygame.draw.rect(self.screen, BLACK, (*right_eye, eye_size, eye_size))

    def draw_food(self):
        x, y = self.food
        # Make the food pulsate slightly
        pulse = abs(int(50 * (1 + (pygame.time.get_ticks() % 1000) / 500.0)))
        color = (255, pulse, pulse)
        pygame.draw.rect(self.screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    def draw_score_area(self):
        # Draw score area background
        pygame.draw.rect(self.screen, (40, 40, 40), (0, SCREEN_HEIGHT, SCREEN_WIDTH, SCORE_AREA_HEIGHT))
        pygame.draw.line(self.screen, WHITE, (0, SCREEN_HEIGHT), (SCREEN_WIDTH, SCREEN_HEIGHT), 2)
        
        # Draw score
        score_text = FONT_MEDIUM.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, SCREEN_HEIGHT + 10))
        
        # Draw level
        level_text = FONT_MEDIUM.render(f"LEVEL: {self.level}", True, WHITE)
        self.screen.blit(level_text, (20, SCREEN_HEIGHT + 35))
        
        # Draw active power-ups
        power_up_text = "ACTIVE: "
        current_time = pygame.time.get_ticks()
        
        if self.active_effects["speed"] > current_time:
            power_up_text += "SPEED! "
        if self.active_effects["slow"] > current_time:
            power_up_text += "SLOW! "
        if self.active_effects["score_boost"] > current_time:
            power_up_text += "2X SCORE! "
        if self.active_effects["invincibility"] > current_time:
            power_up_text += "INVINCIBLE! "
            
        if power_up_text != "ACTIVE: ":
            power_text = FONT_SMALL.render(power_up_text, True, YELLOW)
            self.screen.blit(power_text, (SCREEN_WIDTH // 2 - power_text.get_width() // 2, SCREEN_HEIGHT + 20))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, TOTAL_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = FONT_LARGE.render("GAME OVER", True, RED)
        score_text = FONT_MEDIUM.render(f"Final Score: {self.score}", True, WHITE)
        restart_text = FONT_MEDIUM.render("Press 'R' to Restart", True, WHITE)
        
        self.screen.blit(game_over_text, 
                       (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                        TOTAL_HEIGHT // 2 - 60))
        self.screen.blit(score_text, 
                       (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
                        TOTAL_HEIGHT // 2))
        self.screen.blit(restart_text, 
                       (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                        TOTAL_HEIGHT // 2 + 40))

    def draw_paused(self):
        overlay = pygame.Surface((SCREEN_WIDTH, TOTAL_HEIGHT))
        overlay.set_alpha(120)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        paused_text = FONT_LARGE.render("PAUSED", True, WHITE)
        continue_text = FONT_MEDIUM.render("Press 'P' to Continue", True, WHITE)
        
        self.screen.blit(paused_text, 
                       (SCREEN_WIDTH // 2 - paused_text.get_width() // 2, 
                        TOTAL_HEIGHT // 2 - 40))
        self.screen.blit(continue_text, 
                       (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 
                        TOTAL_HEIGHT // 2 + 20))

    def draw(self):
        self.screen.fill(BLACK)
        self.draw_grid()
        
        # Draw power-ups
        for power_up in self.power_ups:
            power_up.draw(self.screen)
            
        self.draw_food()
        self.draw_snake()
        self.draw_score_area()
        
        if self.paused:
            self.draw_paused()
        elif self.game_over:
            self.draw_game_over()
            
        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.current_speed)

if __name__ == "__main__":
    game = SnakeGame()
    game.run()