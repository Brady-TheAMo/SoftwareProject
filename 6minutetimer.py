import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 300, 100
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("6 Minute Timer")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Font
font = pygame.font.Font(None, 60)

# Timer setup (6 minutes = 360 seconds)
start_time = time.time()
duration = 6 * 60  # seconds

# Clock for framerate
clock = pygame.time.Clock()

# Main loop
running = True
while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # Time left
    elapsed_time = time.time() - start_time
    time_left = max(0, duration - int(elapsed_time))
    minutes = time_left // 60
    seconds = time_left % 60

    # Clear screen
    screen.fill(WHITE)

    # Render the timer
    timer_text = font.render(f"{minutes:02}:{seconds:02}", True, BLACK)
    text_rect = timer_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(timer_text, text_rect)

    # Update display
    pygame.display.flip()

    # If time is up, wait and quit
    if time_left <= 0:
        pygame.time.wait(2000)
        running = False

    # Cap the framerate
    clock.tick(30)

# Quit gracefully
pygame.quit()
sys.exit()
