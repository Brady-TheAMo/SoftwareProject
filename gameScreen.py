import pygame
import sys
import random
import time

def process_transmission(code, player, green_team, red_team):
    # Red Base scored (only green team can score it)
    if code == 53 and player in green_team and not player.get('hit_base', False):
        player['hit_base'] = True
        player['points'] = player.get('points', 0) + 100
        print(f"[CODE 53] {player['codename']} scored on Red Base")

    # Green Base scored (only red team can score it)
    elif code == 43 and player in red_team and not player.get('hit_base', False):
        player['hit_base'] = True
        player['points'] = player.get('points', 0) + 100
        print(f"[CODE 43] {player['codename']} scored on Green Base")

def show_game_screen(screen, green_team, red_team):
    """
    Displays the play action screen using the provided screen.
    """
    # Use the dimensions of the passed-in screen.
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    pygame.display.set_caption("Team Interface")

    # Colors
    GREEN = (0, 128, 0)
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    # Font setup
    font = pygame.font.Font(None, 36)
    timer_font = pygame.font.Font(None, 60)

    # Timer setup (6 minutes = 360 seconds)
    start_time = time.time()
    duration = 6 * 60  # seconds

    # Clock for framerate
    clock = pygame.time.Clock()

    # Game loop
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
        screen.fill(BLACK)

        # Draw green box (left side)
        pygame.draw.rect(screen, GREEN, (0, 0, WIDTH // 3, HEIGHT))

        # Draw red box (right side)
        pygame.draw.rect(screen, RED, (WIDTH * 2 // 3, 0, WIDTH // 3, HEIGHT))

        # Draw timer at the bottom center
        timer_text = timer_font.render(f"{minutes:02}:{seconds:02}", True, WHITE)
        text_rect = timer_text.get_rect(center=(WIDTH // 2, HEIGHT - 40))  # Position at bottom center
        screen.blit(timer_text, text_rect)

        # Display players under their team
        y_offset = 60
        for i, player in enumerate(green_team):
            tag = "[B] " if player.get('hit_base') else ""
            player_text = font.render(f"{tag}{player['codename']} - {player.get('points', 0)} pts", True, WHITE)
            screen.blit(player_text, (WIDTH // 6 - 80, y_offset + (i * 50)))

        for i, player in enumerate(red_team):
            tag = "[B] " if player.get('hit_base') else ""
            player_text = font.render(f"{tag}{player['codename']} - {player.get('points', 0)} pts", True, WHITE)
            screen.blit(player_text, (WIDTH * 5 // 6 - 80, y_offset + (i * 50)))

        # Simulate transmission every ~1 sec (base hit logic)
        if pygame.time.get_ticks() % 1000 < 30:
            all_players = green_team + red_team
            player = random.choice(all_players)

            # Simulate either scoring red base (53) or green base (43)
            code = 53 if player in green_team else 43
            process_transmission(code, player, green_team, red_team)  # Apply base hit logic

        # If time is up, end the game
        if time_left <= 0:
            pygame.time.wait(2000)  # Wait for 2 seconds before quitting
            running = False

        # Update display
        pygame.display.flip()

        # Cap the framerate
        clock.tick(30)

    # Quit gracefully
    pygame.quit()
    sys.exit()
