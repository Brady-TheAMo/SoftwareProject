import pygame
import sys
import random
import time
import socket

def init_udp_socket():
    """
    Initialize and return a non-blocking UDP socket bound to 127.0.0.1 on port 7501.
    """
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("127.0.0.1", 7501))
    udp_socket.setblocking(False)
    print("UDP socket initialized", flush=True)
    return udp_socket

def process_transmission(code, player, green_team, red_team):
    """
    Process a transmission code for scoring (base events only):
      - Code 53: Green team player scores at Red Base.
      - Code 43: Red team player scores at Green Base.
    Updates the player's 'hit_base' status and points.
    """
    if code == 53 and player in green_team and not player.get('hit_base', False):
        player['hit_base'] = True
        player['points'] = player.get('points', 0) + 100
        print(f"[CODE 53] {player['codename']} scored on Red Base", flush=True)
    elif code == 43 and player in red_team and not player.get('hit_base', False):
        player['hit_base'] = True
        player['points'] = player.get('points', 0) + 100
        print(f"[CODE 43] {player['codename']} scored on Green Base", flush=True)

def get_codename_from_equipment(equip, green_team, red_team):
    """
    Returns the codename of the player whose equipment ID matches the provided equip.
    If not found, returns the equipment ID (as a string).
    """
    for player in green_team + red_team:
        if str(player.get("equipment")) == str(equip):
            return player.get("codename")
    return str(equip)

def update_individual_scores(shooter_equip, target_equip, green_team, red_team):
    """
    Updates the shooter's score based on a hit event.
      - Adds 10 points for tagging an opposing player.
      - Subtracts 10 points for tagging a teammate.
    """
    shooter = None
    target = None
    for player in green_team:
        if str(player.get("equipment")) == str(shooter_equip):
            shooter = player
        if str(player.get("equipment")) == str(target_equip):
            target = player
    for player in red_team:
        if str(player.get("equipment")) == str(shooter_equip):
            shooter = player
        if str(player.get("equipment")) == str(target_equip):
            target = player
    if shooter and target:
        shooter_team = "green" if shooter in green_team else "red"
        target_team = "green" if target in green_team else "red"
        if shooter_team != target_team:
            shooter["points"] = shooter.get("points", 0) + 10
            print(f"{shooter['codename']} (+10) on hitting opposing team {target['codename']}", flush=True)
        else:
            shooter["points"] = shooter.get("points", 0) - 10
            print(f"{shooter['codename']} (-10) for tagging teammate {target['codename']}", flush=True)

def draw_team_section(surface, team_area, team_color, team_subheader_color, team_data, font, text_color, flash_score=False):
    """
    Draws a team section (for the left or right side) and displays:
      - The team name in the header.
      - The cumulative team score in the subheader (as a score box).
      - A sorted list of individual players (from highest to lowest score).
    
    If flash_score is True, the score flashes (toggling between the normal color and gold).
    """
    # Sort team data by points descending.
    sorted_team = sorted(team_data, key=lambda p: p.get("points", 0), reverse=True)
    
    header_height = 40
    subheader_height = 30
    header_rect = pygame.Rect(team_area.x, team_area.y, team_area.width, header_height)
    subheader_rect = pygame.Rect(team_area.x, team_area.y + header_height, team_area.width, subheader_height)
    
    pygame.draw.rect(surface, team_color, header_rect)
    pygame.draw.rect(surface, team_subheader_color, subheader_rect)
    
    team_name = "Green Team" if team_color == (0, 128, 0) else "Red Team"
    header_text = font.render(team_name, True, text_color)
    surface.blit(header_text, header_text.get_rect(center=(header_rect.centerx, header_rect.centery - 4)))
    
    cumulative_score = sum([p.get("points", 0) for p in team_data])
    if flash_score:
        flash_color = (255, 215, 0) if int(time.time() * 2) % 2 == 0 else text_color
        score_text = font.render(f"Score: {cumulative_score}", True, flash_color)
    else:
        score_text = font.render(f"Score: {cumulative_score}", True, text_color)
    surface.blit(score_text, score_text.get_rect(center=(subheader_rect.centerx, subheader_rect.centery)))
    
    body_rect = pygame.Rect(team_area.x, team_area.y + header_height + subheader_height, 
                            team_area.width, team_area.height - header_height - subheader_height)
    body_color = (0, 70, 0) if team_color == (0, 128, 0) else (100, 0, 0)
    pygame.draw.rect(surface, body_color, body_rect)
    
    rows = 10
    row_height = body_rect.height / rows
    grid_color = pygame.Color('grey50')
    for i in range(rows + 1):
        y = body_rect.y + i * row_height
        pygame.draw.line(surface, grid_color, (body_rect.x, y), (body_rect.x + body_rect.width, y), 1)
    left_offset = 50
    pygame.draw.line(surface, grid_color, (body_rect.x + left_offset, body_rect.y), 
                     (body_rect.x + left_offset, body_rect.y + body_rect.height), 1)
    
    for i in range(rows):
        y = body_rect.y + i * row_height
        number_text = font.render(f"{i+1}", True, text_color)
        surface.blit(number_text, (body_rect.x + 10, y + row_height/2 - number_text.get_height()/2))
        if i < len(sorted_team):
            player = sorted_team[i]
            tag = "[B] " if player.get('hit_base') else ""
            player_str = f"{tag}{player['codename']} - {player.get('points', 0)} pts"
            player_text = font.render(player_str, True, text_color)
            surface.blit(player_text, (body_rect.x + left_offset + 10, y + row_height/2 - player_text.get_height()/2))

def draw_timer(surface, timer_font, time_left, screen_width, screen_height):
    """
    Draws the countdown timer centered at the bottom of the screen.
    """
    minutes = time_left // 60
    seconds = time_left % 60
    timer_str = f"{minutes:02}:{seconds:02}"
    timer_text = timer_font.render(timer_str, True, (255, 255, 255))
    text_rect = timer_text.get_rect(center=(screen_width // 2, screen_height - 40))
    surface.blit(timer_text, text_rect)

def draw_play_by_play(surface, events, rect):
    """
    Draws the play-by-play log within the provided rectangle.
    New events appear at the bottom 
    """
    pygame.draw.rect(surface, (20, 20, 20), rect)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2)
    
    event_font = pygame.font.Font(None, 24)
    line_spacing = 8
    line_height = event_font.get_height() + line_spacing
    margin_top = 30
    margin_bottom = 80
    
    available_height = rect.height - margin_top - margin_bottom
    max_lines = available_height // line_height
    
    events_to_draw = events[-max_lines:]
    
    for idx, event in enumerate(events_to_draw):
        y = rect.y + margin_top + idx * line_height
        text_surface = event_font.render(event, True, (255, 255, 255))
        surface.blit(text_surface, (rect.x + 5, y))

def show_game_screen(screen, green_team, red_team, udp_address, udp_socket):
    """
    Displays the game screen with:
      - Left: Green team area (showing cumulative team score and individual scores).
      - Right: Red team area (showing cumulative team score and individual scores).
      - Center: A play-by-play log for game events.
      - Bottom: A countdown timer.
    
    Processes UDP messages via the provided non-blocking socket.
    UDP messages containing a colon are interpreted as hit events.
    For each hit event, the shooter's individual score is updated:
      - +10 points for tagging an opposing player.
      - -10 points for tagging a teammate.
    """
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    pygame.display.set_caption("Team Interface")
    
    GREEN = (0, 128, 0)
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    
    font = pygame.font.Font(None, 36)
    timer_font = pygame.font.Font(None, 60)
    
    print("Game screen started", flush=True)
    
    play_by_play_events = []
    
    left_section = pygame.Rect(0, 0, WIDTH // 3, HEIGHT)
    center_section = pygame.Rect(WIDTH // 3, 0, WIDTH // 3, HEIGHT)
    right_section = pygame.Rect(WIDTH * 2 // 3, 0, WIDTH // 3, HEIGHT)
    
    duration = 6 * 60  # 6-minute game
    start_time = time.time()
    clock = pygame.time.Clock()
    running = True
    
    game_over = False
    
    while running:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # While the game is running, allow ESC to quit.
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Process all incoming UDP messages.
        while True:
            try:
                data, addr = udp_socket.recvfrom(1024)
                incoming = data.decode('utf-8')
                print("Received from traffic generator: " + incoming, flush=True)
                udp_socket.sendto("ACK".encode('utf-8'), ("127.0.0.1", 7500))
                print("Sent ACK for message: " + incoming, flush=True)
                if ":" in incoming:
                    parts = incoming.split(":")
                    if len(parts) == 2:
                        shooter_equip = parts[0].strip()
                        target_equip = parts[1].strip()
                        shooter_name = get_codename_from_equipment(shooter_equip, green_team, red_team)
                        target_name = get_codename_from_equipment(target_equip, green_team, red_team)
                        event_msg = f"{shooter_name} hit {target_name}"
                        play_by_play_events.append(event_msg)
                        if len(play_by_play_events) > 50:
                            play_by_play_events.pop(0)
                        print("Added event: " + event_msg, flush=True)
                        update_individual_scores(shooter_equip, target_equip, green_team, red_team)
            except BlockingIOError:
                break
            except Exception as e:
                print("UDP recv error:", e, flush=True)
                break
        
        elapsed = time.time() - start_time
        time_left = max(0, duration - int(elapsed))
        
        screen.fill(BLACK)
        draw_team_section(screen, left_section, GREEN, (0, 100, 0), green_team, font, WHITE,
                          flash_score=(sum(p.get("points", 0) for p in green_team) > sum(p.get("points", 0) for p in red_team)))
        draw_team_section(screen, right_section, RED, (150, 0, 0), red_team, font, WHITE,
                          flash_score=(sum(p.get("points", 0) for p in red_team) > sum(p.get("points", 0) for p in green_team)))
        draw_play_by_play(screen, play_by_play_events, center_section)
        draw_timer(screen, timer_font, time_left, WIDTH, HEIGHT)
        
        # Optionally simulate base hit events (for testing):
        if pygame.time.get_ticks() % 1000 < 30:
            all_players = green_team + red_team
            if all_players:
                player = random.choice(all_players)
                code = 53 if player in green_team else 43
                process_transmission(code, player, green_team, red_team)
                event_msg = f"{player['codename']} triggered a base hit"
                play_by_play_events.append(event_msg)
                if len(play_by_play_events) > 50:
                    play_by_play_events.pop(0)
        
        # When the timer expires and game over has not been set, send code 221 and enter game over state.
        if time_left <= 0 and not game_over:
            from main import send_udp_message
            send_udp_message(udp_address, 221)
            game_over = True
            print("Game Over. Displaying overlay indefinitely.", flush=True)
        
        # If in game over state, draw an overlay.
        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            over_font = pygame.font.Font(None, 72)
            over_text = over_font.render("GAME OVER", True, (255, 0, 0))
            screen.blit(over_text, over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 50)))
            info_font = pygame.font.Font(None, 36)
            info_text = info_font.render("Press ESC to exit", True, (255, 255, 255))
            screen.blit(info_text, info_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 10)))
        
        pygame.display.flip()
        clock.tick(30)
    
    # Clean up when the window is closed.
    udp_socket.close()
    print("Exiting game screen.", flush=True)
    return
