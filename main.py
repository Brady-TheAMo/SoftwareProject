import pygame
import psycopg2
import socket
import sys
import random
import threading  # No longer used in our start_game_sequence, but kept if needed later.

# Import external modules for countdown and game screen.
import gameStartTimer
import gameScreen

# ---------------------------------------------------------
# Configuration and Initialization
# ---------------------------------------------------------
# Database connection parameters.
DB_NAME = "photon"
DB_USER = "student"
DB_PASSWORD = "student"
DB_HOST = "localhost"

# Default UDP port and IP used for sending messages.
UDP_PORT = 7500
DEFAULT_UDP_IP = "127.0.0.1"
# Global game-wide UDP address. This can be changed at runtime.
game_udp_address = DEFAULT_UDP_IP

# Initialize Pygame and the font system.
pygame.init()
pygame.font.init()

# Set up main screen dimensions and create a display surface.
SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Laser Tag - Player Entry")

# Basic font for rendering text.
FONT = pygame.font.Font(None, 28)

# Clock for controlling the frame rate.
CLOCK = pygame.time.Clock()

# ---------------------------------------------------------
# Color Definitions
# ---------------------------------------------------------
BG_COLOR = pygame.Color('black')
TEXT_COLOR = pygame.Color('white')
COLOR_INACTIVE = pygame.Color('lightskyblue3')
COLOR_ACTIVE = pygame.Color('dodgerblue2')
BUTTON_COLOR = pygame.Color('gray')
WHITE = pygame.Color('white')
STORMY_BLUE = (50, 70, 90)
GREEN = (0, 128, 0)
RED = (200, 0, 0)
GREEN_SUBHEADER = (0, 100, 0)
RED_SUBHEADER = (150, 0, 0)

# ---------------------------------------------------------
# Attempt to Load a Splash Image
# ---------------------------------------------------------
try:
    splash_image = pygame.image.load("logo.jpg")
    splash_image = pygame.transform.scale(splash_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
except Exception as e:
    print("Error loading splash image:", e)
    splash_image = None

# ---------------------------------------------------------
# Database and UDP Helper Functions
# ---------------------------------------------------------
def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None

def send_udp_message(target_ip, message, port=UDP_PORT):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if target_ip == "255.255.255.255":
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        client_socket.sendto(str(message).encode(), (target_ip, port))
        client_socket.close()
        print(f"Sent message '{message}' to {target_ip}:{port}")
    except Exception as e:
        print("UDP send error:", e)

def create_table_if_not_exists(cursor):
    query = """
    CREATE TABLE IF NOT EXISTS players (
        id INT PRIMARY KEY,
        codename VARCHAR(30)
    );
    """
    cursor.execute(query)

# ---------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------
conn = get_db_connection()
if conn:
    cursor = conn.cursor()
    create_table_if_not_exists(cursor)
    conn.commit()
    cursor.close()
    conn.close()

# ---------------------------------------------------------
# UI Helper Classes
# ---------------------------------------------------------
class InputBox:
    def __init__(self, x, y, w, h, text='', text_color=pygame.Color('black'), bg_color=pygame.Color('white')):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.txt_surface = FONT.render(text, True, self.text_color)
        self.active = False
        self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

    def set_focus(self, focus):
        self.active = focus
        self.color = COLOR_ACTIVE if focus else COLOR_INACTIVE

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = FONT.render(self.text, True, self.text_color)

    def update(self):
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        pygame.draw.rect(screen, self.bg_color, self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Button:
    def __init__(self, x, y, w, h, text, callback, bg_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.txt_surface = FONT.render(text, True, TEXT_COLOR)
        self.focused = False
        self.bg_color = bg_color if bg_color is not None else BUTTON_COLOR

    def set_focus(self, focus):
        self.focused = focus

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_RETURN:
                self.callback()

    def update(self):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, disable_tab_highlight=False):
        self.update()
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=5)
        if self.hovered or (self.focused and not disable_tab_highlight):
            pygame.draw.rect(screen, COLOR_ACTIVE, self.rect, 3, border_radius=5)
        text_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, text_rect)

# ---------------------------------------------------------
# Global State and Variables
# ---------------------------------------------------------
state = "splash"
splash_start_time = None
players_table = {"green": [], "red": []}
popup_rect = None
popup_widgets = []
popup_focus_index = 0
popup_info_text = ""
popup_mode = None
popup_step = 0
wizard_player_id = None
wizard_codename = ""
wizard_equipment = None
wizard_team = ""

def set_popup_focus(index):
    global popup_focus_index, popup_widgets
    popup_focus_index = index
    for i, widget in enumerate(popup_widgets):
        widget.set_focus(i == index)

def move_focus_next():
    global popup_focus_index, popup_widgets
    next_index = (popup_focus_index + 1) % len(popup_widgets)
    set_popup_focus(next_index)

def draw_table_background(surface, rect, shadow_offset=(5, 5), shadow_color=(0, 0, 0, 80), bg_color=pygame.Color('grey20')):
    shadow = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    shadow.fill(shadow_color)
    surface.blit(shadow, (rect.x + shadow_offset[0], rect.y + shadow_offset[1]))
    pygame.draw.rect(surface, bg_color, rect, border_radius=10)

def draw_grid_for_column(surface, column_rect, rows=10, left_offset=50, line_color=pygame.Color('grey50')):
    row_height = column_rect.height / rows
    for i in range(rows + 1):
        y = column_rect.y + i * row_height
        pygame.draw.line(surface, line_color, (column_rect.x, y), (column_rect.x + column_rect.width, y), 1)
    pygame.draw.line(surface, line_color, (column_rect.x + left_offset, column_rect.y),
                     (column_rect.x + left_offset, column_rect.y + column_rect.height), 1)
    return row_height

def draw_team_column_data(surface, column_rect, rows, row_height, left_offset, team_data, font, text_color):
    for i in range(rows):
        y = column_rect.y + i * row_height
        number_text = font.render(f"{i+1}", True, text_color)
        surface.blit(number_text, (column_rect.x + 10, y + row_height/2 - number_text.get_height()/2))
        if i < len(team_data):
            codename_text = font.render(team_data[i]["codename"], True, text_color)
            surface.blit(codename_text, (column_rect.x + left_offset + 10, y + row_height/2 - codename_text.get_height()/2))

def draw_team_column(surface, area, header_text, subheader_text, header_color, subheader_color, body_color, team_data, font, text_color):
    header_height = 40
    subheader_height = 30
    header_rect = pygame.Rect(area.x, area.y, area.width, header_height)
    subheader_rect = pygame.Rect(area.x, area.y + header_height, area.width, subheader_height)
    body_rect = pygame.Rect(area.x, area.y + header_height + subheader_height, area.width, area.height - header_height - subheader_height)
    pygame.draw.rect(surface, header_color, header_rect, border_radius=5)
    pygame.draw.rect(surface, subheader_color, subheader_rect, border_radius=5)
    header_surf = font.render(header_text, True, WHITE)
    subheader_surf = font.render(subheader_text, True, WHITE)
    surface.blit(header_surf, (header_rect.centerx - header_surf.get_width() // 2, header_rect.centery - header_surf.get_height() // 2))
    surface.blit(subheader_surf, (subheader_rect.centerx - subheader_surf.get_width() // 2, subheader_rect.y + (subheader_height - subheader_surf.get_height()) // 2))
    pygame.draw.rect(surface, body_color, body_rect)
    row_height = draw_grid_for_column(surface, body_rect, rows=10, left_offset=50)
    draw_team_column_data(surface, body_rect, rows=10, row_height=row_height, left_offset=50, team_data=team_data, font=font, text_color=text_color)

def draw_main_screen():
    screen.fill(BG_COLOR)
    table_area = pygame.Rect(50, 50, SCREEN_WIDTH - 100, 450)
    draw_table_background(screen, table_area)
    col_width = table_area.width // 2
    green_area = pygame.Rect(table_area.x, table_area.y, col_width, table_area.height)
    red_area = pygame.Rect(table_area.x + col_width, table_area.y, col_width, table_area.height)
    draw_team_column(screen, green_area, "Green Team", "Codename", GREEN, GREEN_SUBHEADER, (0, 70, 0), players_table["green"], FONT, WHITE)
    draw_team_column(screen, red_area, "Red Team", "Codename", RED, RED_SUBHEADER, (100, 0, 0), players_table["red"], FONT, WHITE)
    for widget in main_widgets:
        widget.draw(screen)

def draw_popup():
    draw_main_screen()
    pygame.draw.rect(screen, STORMY_BLUE, popup_rect, border_radius=10)
    pygame.draw.rect(screen, pygame.Color('black'), popup_rect, 2, border_radius=10)
    header_text = ""
    if popup_mode == "add":
        if popup_step == 1:
            header_text = "Step 1: Enter Player ID"
        elif popup_step == 2:
            header_text = "Step 2: Enter/Update Codename"
        elif popup_step == 3:
            header_text = "Step 3: Enter Equipment ID"
        elif popup_step == 4:
            header_text = "Step 4: Choose Team"
    elif popup_mode == "update":
        header_text = "Update Player Information"
    elif popup_mode == "udp":
        header_text = "Set Game UDP Address"
    header_surf = FONT.render(header_text, True, WHITE)
    screen.blit(header_surf, (popup_rect.x + 20, popup_rect.y + 20))
    if popup_mode == "update":
        labels = ["Player ID:", "Codename:", "Equipment ID:", "Team:"]
        for i, widget in enumerate(popup_widgets[:4]):
            label_surf = FONT.render(labels[i], True, WHITE)
            screen.blit(label_surf, (widget.rect.x, widget.rect.y - label_surf.get_height() - 5))
    if popup_info_text:
        info_surf = FONT.render(popup_info_text, True, pygame.Color('red'))
        screen.blit(info_surf, (popup_rect.x + 20, popup_rect.bottom - 40))
    for widget in popup_widgets:
        widget.draw(screen)

def init_popup_step1():
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 1
    pr_width, pr_height = 400, 200
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    player_id_box = InputBox(pr_x + 20, pr_y + 60, pr_width - 40, 30)
    next_button = Button(pr_x + 20, pr_y + 120, 100, 32, "Next", add_player_step1_next)
    popup_widgets = [player_id_box, next_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step1_next():
    global wizard_player_id, popup_widgets, popup_info_text, wizard_codename
    player_id_str = popup_widgets[0].text.strip()
    if not player_id_str.isdigit():
        popup_info_text = "Player ID must be an integer."
        return
    wizard_player_id = int(player_id_str)
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (wizard_player_id,))
        result = cursor.fetchone()
        wizard_codename = result[0] if result else ""
        cursor.close()
        conn.close()
    else:
        popup_info_text = "Database connection error."
        return
    init_popup_step2()

def init_popup_step2():
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 2
    pr_width, pr_height = 400, 200
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    codename_box = InputBox(pr_x + 20, pr_y + 60, pr_width - 40, 30, text=wizard_codename)
    next_button = Button(pr_x + 20, pr_y + 120, 100, 32, "Next", add_player_step2_next)
    popup_widgets = [codename_box, next_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step2_next():
    global wizard_codename, popup_widgets
    wizard_codename = popup_widgets[0].text.strip()
    init_popup_step3()

def init_popup_step3():
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 3
    pr_width, pr_height = 400, 220
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    equipment_box = InputBox(pr_x + 20, pr_y + 70, pr_width - 40, 30)
    next_button = Button(pr_x + 20, pr_y + 130, 100, 32, "Next", add_player_step3_next)
    popup_widgets = [equipment_box, next_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step3_next():
    global wizard_equipment, popup_widgets
    equip_str = popup_widgets[0].text.strip()
    if not equip_str.isdigit():
        return
    wizard_equipment = int(equip_str)
    init_popup_step4()

def init_popup_step4():
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 4
    pr_width, pr_height = 400, 250
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    green_button = Button(pr_x + 50, pr_y + 100, 120, 40, "Green Team", lambda: add_player_step4_submit("green"), bg_color=GREEN)
    red_button = Button(pr_x + 230, pr_y + 100, 120, 40, "Red Team", lambda: add_player_step4_submit("red"), bg_color=RED)
    popup_widgets = [green_button, red_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step4_submit(team):
    global wizard_team, wizard_player_id, wizard_codename, wizard_equipment, players_table, state, popup_info_text
    wizard_team = team
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        conn.commit()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (wizard_player_id,))
        result = cursor.fetchone()
        if result:
            if wizard_codename != result[0]:
                cursor.execute("UPDATE players SET codename = %s WHERE id = %s;", (wizard_codename, wizard_player_id))
                conn.commit()
        else:
            if wizard_codename == "":
                popup_info_text = "Codename cannot be empty."
                cursor.close()
                conn.close()
                return
            cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (wizard_player_id, wizard_codename))
            conn.commit()
        cursor.close()
        conn.close()
    else:
        popup_info_text = "Database connection error."
        return
    send_udp_message(game_udp_address, wizard_equipment)
    players_table[wizard_team].append({
        "player_id": str(wizard_player_id),
        "codename": wizard_codename,
        "equipment": str(wizard_equipment)
    })
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def init_update_popup():
    global popup_rect, popup_widgets, popup_focus_index
    pr_width, pr_height = 400, 450
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    header_offset = 80
    label_height = 20
    gap_after_label = 5
    input_height = 30
    field_spacing = 30
    y1 = pr_y + header_offset
    y2 = y1 + label_height + gap_after_label + input_height + field_spacing
    y3 = y2 + label_height + gap_after_label + input_height + field_spacing
    y4 = y3 + label_height + gap_after_label + input_height + field_spacing
    player_id_box = InputBox(pr_x + 20, y1, pr_width - 40, input_height)
    codename_box = InputBox(pr_x + 20, y2, pr_width - 40, input_height)
    equipment_box = InputBox(pr_x + 20, y3, pr_width - 40, input_height)
    team_box = InputBox(pr_x + 20, y4, pr_width - 40, input_height)
    button_y = pr_y + pr_height - 40
    submit_button = Button(pr_x + 50, button_y, 100, 32, "Submit", update_player_submit)
    cancel_button = Button(pr_x + pr_width - 150, button_y, 100, 32, "Cancel", update_player_cancel)
    popup_widgets = [player_id_box, codename_box, equipment_box, team_box, submit_button, cancel_button]
    popup_focus_index = 0
    set_popup_focus(0)
    return popup_rect

def update_player_submit():
    global popup_widgets, players_table, state, popup_info_text
    player_id_str = popup_widgets[0].text.strip()
    codename = popup_widgets[1].text.strip()
    equipment_str = popup_widgets[2].text.strip()
    team = popup_widgets[3].text.strip().lower()
    if not player_id_str.isdigit():
        popup_info_text = "Player ID must be an integer."
        return
    if not equipment_str.isdigit():
        popup_info_text = "Equipment ID must be an integer."
        return
    if team not in ["green", "red"]:
        popup_info_text = "Team must be 'green' or 'red'."
        return
    player_id = int(player_id_str)
    equipment = int(equipment_str)
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        conn.commit()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
        result = cursor.fetchone()
        if result:
            if codename != result[0]:
                cursor.execute("UPDATE players SET codename = %s WHERE id = %s;", (codename, player_id))
                conn.commit()
        else:
            if codename == "":
                popup_info_text = "Codename cannot be empty."
                cursor.close()
                conn.close()
                return
            cursor.execute("INSERT INTO players (id, codename) VALUES (%s, %s);", (player_id, codename))
            conn.commit()
        cursor.close()
        conn.close()
    else:
        popup_info_text = "Database connection error."
        return
    send_udp_message(game_udp_address, equipment)
    for team_key in players_table:
        players_table[team_key] = [p for p in players_table[team_key] if p["player_id"] != player_id_str]
    players_table[team].append({
        "player_id": player_id_str,
        "codename": codename,
        "equipment": equipment_str
    })
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def update_player_cancel():
    global state, popup_info_text
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def init_udp_popup():
    global popup_rect, popup_widgets, popup_focus_index, popup_info_text, popup_mode
    popup_mode = "udp"
    pr_width, pr_height = 400, 200
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)
    udp_input = InputBox(pr_x + 20, pr_y + 60, pr_width - 40, 30, text=game_udp_address)
    submit_button = Button(pr_x + 20, pr_y + 120, 100, 32, "Submit", udp_submit)
    cancel_button = Button(pr_x + pr_width - 120, pr_y + 120, 100, 32, "Cancel", udp_cancel)
    popup_widgets = [udp_input, submit_button, cancel_button]
    popup_focus_index = 0
    set_popup_focus(0)

def udp_submit():
    global game_udp_address, popup_widgets, state, popup_info_text
    new_addr = popup_widgets[0].text.strip()
    if new_addr == "":
        popup_info_text = "UDP address cannot be empty."
        return
    game_udp_address = new_addr
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def udp_cancel():
    global state, popup_info_text
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def start_udp_setting():
    global state, popup_mode, popup_info_text
    popup_mode = "udp"
    popup_info_text = ""
    init_udp_popup()
    state = "popup"

def clear_players():
    global players_table
    players_table = {"green": [], "red": []}

def start_add_player():
    global state, popup_mode, popup_info_text
    popup_mode = "add"
    popup_info_text = ""
    init_popup_step1()
    state = "popup"

def start_update_player():
    global state, popup_mode, popup_info_text
    popup_mode = "update"
    popup_info_text = ""
    init_update_popup()
    state = "popup"

def start_game_sequence():
    # Run the countdown first.
    gameStartTimer.run_countdown(screen)
    
    # **NEW STEP:** Initialize UDP socket for the game.
    # (You must add the following function in gameScreen.py:
    #      def init_udp_socket():
    #            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #            udp_socket.bind(("127.0.0.1", 7501))
    #            udp_socket.setblocking(False)
    #            print("UDP socket initialized", flush=True)
    #            return udp_socket)
    udp_sock = gameScreen.init_udp_socket()
    
    # Now send the start code so that the traffic generator can start transmitting.
    send_udp_message(game_udp_address, 202)
    
    # Call show_game_screen in the main thread, passing the pre-initialized UDP socket.
    gameScreen.show_game_screen(screen, players_table["green"], players_table["red"], game_udp_address, udp_sock)
    
    global state
    state = "main"
    set_main_focus(0)

add_player_button    = Button(20, 720, 180, 40, "Add Player", start_add_player)
update_player_button = Button(220, 720, 180, 40, "Update Player", start_update_player)
clear_players_button = Button(420, 720, 180, 40, "Clear Players", clear_players)
start_game_button    = Button(620, 720, 180, 40, "Start Game", start_game_sequence)
udp_address_button   = Button(820, 720, 180, 40, "Set UDP", start_udp_setting)

main_widgets = [add_player_button, update_player_button, clear_players_button, start_game_button, udp_address_button]
main_focus_index = 0

def set_main_focus(index):
    global main_focus_index, main_widgets
    main_focus_index = index
    for i, widget in enumerate(main_widgets):
        widget.set_focus(i == index)

def move_main_focus_next():
    global main_focus_index, main_widgets
    next_index = (main_focus_index + 1) % len(main_widgets)
    set_main_focus(next_index)

set_main_focus(0)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if state == "main":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    move_main_focus_next()
                    continue
                if event.key == pygame.K_F5:
                    start_game_sequence()
                if event.key == pygame.K_F12:
                    clear_players()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, widget in enumerate(main_widgets):
                    if widget.rect.collidepoint(event.pos):
                        set_main_focus(i)
                        widget.handle_event(event)
                        break
            for widget in main_widgets:
                widget.handle_event(event)
        elif state == "popup":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    move_focus_next()
                elif event.key == pygame.K_RETURN:
                    current = popup_widgets[popup_focus_index]
                    if isinstance(current, Button):
                        current.callback()
                    else:
                        current.handle_event(event)
                else:
                    popup_widgets[popup_focus_index].handle_event(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for i, widget in enumerate(popup_widgets):
                    if widget.rect.collidepoint(event.pos):
                        set_popup_focus(i)
                        widget.handle_event(event)
                        break
        elif state == "game":
            pass
    if state == "splash":
        if splash_start_time is None:
            splash_start_time = pygame.time.get_ticks()
        if splash_image:
            screen.blit(splash_image, (0, 0))
        else:
            screen.fill(BG_COLOR)
        current_time = pygame.time.get_ticks()
        if current_time - splash_start_time >= 3000:
            state = "main"
            set_main_focus(0)
        pygame.display.flip()
        CLOCK.tick(30)
        continue
    if state == "main":
        draw_main_screen()
    elif state == "popup":
        draw_popup()
    pygame.display.flip()
    CLOCK.tick(30)
