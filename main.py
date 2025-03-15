import pygame
import psycopg2
import socket
import sys

# ---------------------------------------------------------
# Configuration and Initialization
# ---------------------------------------------------------
# Database parameters for connecting to PostgreSQL.
DB_NAME = "photon"
DB_USER = "student"
DB_PASSWORD = "student"
DB_HOST = "localhost"

# Default UDP port and IP used for sending messages.
UDP_PORT = 7500
DEFAULT_UDP_IP = "127.0.0.1"

# Initialize Pygame and font system.
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
COLOR_INACTIVE = pygame.Color('lightskyblue3')  # For unfocused input boxes
COLOR_ACTIVE = pygame.Color('dodgerblue2')     # For focused/hovered input boxes or outlines
BUTTON_COLOR = pygame.Color('gray')
WHITE = pygame.Color('white')
STORMY_BLUE = (50, 70, 90)

# Team color constants.
GREEN = (0, 128, 0)
RED = (200, 0, 0)

# Subheader colors used in the table sections.
GREEN_SUBHEADER = (0, 100, 0)
RED_SUBHEADER = (150, 0, 0)

# ---------------------------------------------------------
# Attempt to Load a Splash Image
# ---------------------------------------------------------
# This is displayed briefly at program startup.
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
    """
    Attempts to connect to the PostgreSQL database using the
    global parameters. Returns the connection object if successful,
    or None if there's an error.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST
        )
        return conn
    except Exception as e:
        print("Database connection error:", e)
        return None

def send_udp_message(target_ip, message, port=UDP_PORT):
    """
    Sends a UDP message to the specified target IP and port.
    If the target_ip is broadcast, it sets the socket to broadcast mode.
    """
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
    """
    Creates a table named 'players' in the database if it does not exist.
    It has columns 'id' (int) and 'codename' (varchar).
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS players (
        id INT PRIMARY KEY,
        codename VARCHAR(30)
    );
    """
    cursor.execute(create_table_query)

# ---------------------------------------------------------
# Database Initialization (Create Table If Needed)
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
    """
    Represents a text input box where the user can type.
    Tracks whether it is active (focused) or inactive.
    """
    def __init__(self, x, y, w, h, text='', text_color=pygame.Color('black'), bg_color=pygame.Color('white')):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.text_color = text_color
        self.bg_color = bg_color
        self.txt_surface = FONT.render(text, True, self.text_color)
        self.active = False
        self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

    def set_focus(self, focus):
        """
        Sets whether this input box is focused (active) or not.
        The border color changes accordingly.
        """
        self.active = focus
        self.color = COLOR_ACTIVE if focus else COLOR_INACTIVE

    def handle_event(self, event):
        """
        Handles keyboard input events when the box is active.
        - Enter key does nothing by default here.
        - Backspace deletes one character.
        - Other keys append their unicode character to self.text.
        """
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                pass
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = FONT.render(self.text, True, self.text_color)

    def update(self):
        """
        Dynamically adjusts the width of the input box so it can grow
        as the user types, up to a minimum of 200 px.
        """
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        """
        Draws the input box onto the screen with its current text.
        """
        pygame.draw.rect(screen, self.bg_color, self.rect)
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

class Button:
    """
    Represents a clickable button with optional focus highlight.
    Also changes outline color on hover or focus.
    """
    def __init__(self, x, y, w, h, text, callback, bg_color=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.callback = callback
        self.txt_surface = FONT.render(text, True, TEXT_COLOR)
        self.focused = False
        self.bg_color = bg_color if bg_color is not None else BUTTON_COLOR

    def set_focus(self, focus):
        """
        Sets whether this button is focused (for keyboard navigation).
        """
        self.focused = focus

    def handle_event(self, event):
        """
        Handles mouse and keyboard events:
        - Mouse click within the button calls the callback.
        - Keyboard Enter press while focused also calls the callback.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_RETURN:
                self.callback()

    def update(self):
        """
        Updates the hover state (whether the mouse is over the button).
        """
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen, disable_tab_highlight=False):
        """
        Draws the button rectangle and text. If hovered or focused,
        draws a highlight outline in blue.
        """
        self.update()
        pygame.draw.rect(screen, self.bg_color, self.rect, border_radius=5)
        if self.hovered:
            pygame.draw.rect(screen, COLOR_ACTIVE, self.rect, 3, border_radius=5)
        elif self.focused and not disable_tab_highlight:
            pygame.draw.rect(screen, COLOR_ACTIVE, self.rect, 3, border_radius=5)
        text_rect = self.txt_surface.get_rect(center=self.rect.center)
        screen.blit(self.txt_surface, text_rect)

# ---------------------------------------------------------
# Global State and Variables
# ---------------------------------------------------------
# The application states: splash, main, popup, game.
state = "splash"

# In-memory data for teams: "green" and "red" each hold a list of player dictionaries.
players_table = {"green": [], "red": []}

# Variables to handle popups (the "wizard" for adding players, or update popup).
popup_rect = None
popup_widgets = []
popup_focus_index = 0
popup_info_text = ""
popup_mode = None     # "add" or "update"
popup_step = 0        # For multi-step add wizard

# Variables for the add-player wizard. They store data between steps.
wizard_player_id = None
wizard_codename = ""
wizard_equipment = None
wizard_udp_ip = ""
wizard_team = ""

# ---------------------------------------------------------
# Focus Handling for Popups
# ---------------------------------------------------------
def set_popup_focus(index):
    """
    Sets the focus to the widget at the given index in popup_widgets.
    All others lose focus.
    """
    global popup_focus_index, popup_widgets
    popup_focus_index = index
    for i, widget in enumerate(popup_widgets):
        widget.set_focus(i == index)

def move_focus_next():
    """
    Moves focus to the next widget in popup_widgets (circular).
    """
    global popup_focus_index, popup_widgets
    next_index = (popup_focus_index + 1) % len(popup_widgets)
    set_popup_focus(next_index)

# ---------------------------------------------------------
# Add Player Wizard (Four Steps)
# ---------------------------------------------------------
# Step 1: Ask for Player ID
def init_popup_step1():
    """
    Creates a small popup asking the user for a Player ID.
    """
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 1
    pr_width, pr_height = 400, 200
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)

    # One input for Player ID and a "Next" button.
    player_id_box = InputBox(pr_x + 20, pr_y + 60, pr_width - 40, 30)
    next_button = Button(pr_x + 20, pr_y + 120, 100, 32, "Next", add_player_step1_next)

    popup_widgets = [player_id_box, next_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step1_next():
    """
    Reads the Player ID from the input box.
    If valid, tries to look up an existing codename in the database.
    Then moves to Step 2.
    """
    global wizard_player_id, popup_widgets, popup_info_text, wizard_codename
    player_id_str = popup_widgets[0].text.strip()
    if not player_id_str.isdigit():
        popup_info_text = "Player ID must be an integer."
        return

    wizard_player_id = int(player_id_str)

    # Check database for an existing codename.
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (wizard_player_id,))
        result = cursor.fetchone()
        if result:
            wizard_codename = result[0]
        else:
            wizard_codename = ""
        cursor.close()
        conn.close()
    else:
        popup_info_text = "Database connection error."
        return

    init_popup_step2()

# Step 2: Ask for Codename
def init_popup_step2():
    """
    Creates a small popup to let the user keep or change the codename.
    """
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
    """
    Stores the entered/updated codename and proceeds to Step 3.
    """
    global wizard_codename, popup_widgets
    wizard_codename = popup_widgets[0].text.strip()
    init_popup_step3()

# Step 3: Ask for Equipment ID and UDP Target IP
def init_popup_step3():
    """
    Creates a popup that asks for equipment ID and UDP target IP.
    """
    global popup_rect, popup_widgets, popup_focus_index, popup_step
    popup_step = 3
    pr_width, pr_height = 400, 280
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)

    equipment_box = InputBox(pr_x + 20, pr_y + 70, pr_width - 40, 30)
    udp_box = InputBox(pr_x + 20, pr_y + 130, pr_width - 40, 30, text=DEFAULT_UDP_IP)
    next_button = Button(pr_x + 20, pr_y + 190, 100, 32, "Next", add_player_step3_next)

    popup_widgets = [equipment_box, udp_box, next_button]
    popup_focus_index = 0
    set_popup_focus(0)

def add_player_step3_next():
    """
    Validates equipment ID as an integer, stores both equipment and IP,
    then moves to Step 4 (choose team).
    """
    global wizard_equipment, wizard_udp_ip, popup_widgets
    equip_str = popup_widgets[0].text.strip()
    if not equip_str.isdigit():
        return
    wizard_equipment = int(equip_str)
    wizard_udp_ip = popup_widgets[1].text.strip()
    init_popup_step4()

# Step 4: Choose Team with Two Buttons
def init_popup_step4():
    """
    Creates a popup with two buttons: Green Team or Red Team.
    """
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
    """
    Final step: uses the chosen team, updates or inserts the player
    in the database, sends a UDP message with the equipment ID,
    and updates the in-memory table for display.
    """
    global wizard_team, wizard_player_id, wizard_codename, wizard_equipment, wizard_udp_ip
    global players_table, state, popup_info_text

    wizard_team = team
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        conn.commit()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (wizard_player_id,))
        result = cursor.fetchone()

        # If the player ID exists, possibly update the codename.
        if result:
            if wizard_codename != result[0]:
                cursor.execute("UPDATE players SET codename = %s WHERE id = %s;", (wizard_codename, wizard_player_id))
                conn.commit()
        else:
            # If no player found, insert new record, requiring a non-empty codename.
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

    # Send the equipment ID via UDP.
    send_udp_message(wizard_udp_ip, wizard_equipment)

    # Update the local table for display.
    players_table[wizard_team].append({
        "player_id": str(wizard_player_id),
        "codename": wizard_codename,
        "equipment": str(wizard_equipment)
    })

    popup_info_text = ""
    state = "main"
    set_main_focus(0)

# ---------------------------------------------------------
# Update Player Popup
# ---------------------------------------------------------
def init_update_popup():
    """
    Creates a popup (height=500) to allow editing a player's info:
    Player ID, Codename, Equipment ID, UDP IP, Team.
    Also includes Submit and Cancel buttons near the bottom.
    """
    global popup_rect, popup_widgets, popup_focus_index
    pr_width, pr_height = 400, 500
    pr_x = (SCREEN_WIDTH - pr_width) // 2
    pr_y = (SCREEN_HEIGHT - pr_height) // 2
    popup_rect = pygame.Rect(pr_x, pr_y, pr_width, pr_height)

    # Vertical spacing to ensure no collisions between labels, input boxes, and buttons.
    header_offset = 80
    label_height = 20
    gap_after_label = 5
    input_height = 30
    field_spacing = 30

    # Position each input box so that there's space for labels above them.
    y1 = pr_y + header_offset
    y2 = y1 + label_height + gap_after_label + input_height + field_spacing
    y3 = y2 + label_height + gap_after_label + input_height + field_spacing
    y4 = y3 + label_height + gap_after_label + input_height + field_spacing
    y5 = y4 + label_height + gap_after_label + input_height + field_spacing

    # Five input boxes for Player ID, Codename, Equipment, UDP IP, Team.
    player_id_box = InputBox(pr_x + 20, y1, pr_width - 40, input_height)
    codename_box = InputBox(pr_x + 20, y2, pr_width - 40, input_height)
    equipment_box = InputBox(pr_x + 20, y3, pr_width - 40, input_height)
    udp_box = InputBox(pr_x + 20, y4, pr_width - 40, input_height, text=DEFAULT_UDP_IP)
    team_box = InputBox(pr_x + 20, y5, pr_width - 40, input_height)

    # Place the Submit and Cancel buttons lower, so they do not overlap the Team box.
    button_y = pr_y + pr_height - 40
    submit_button = Button(pr_x + 50, button_y, 100, 32, "Submit", update_player_submit)
    cancel_button = Button(pr_x + pr_width - 150, button_y, 100, 32, "Cancel", update_player_cancel)

    popup_widgets = [player_id_box, codename_box, equipment_box, udp_box, team_box, submit_button, cancel_button]
    popup_focus_index = 0
    set_popup_focus(0)
    return popup_rect

def update_player_submit():
    """
    Reads the input fields, validates them, updates/inserts the record
    in the database, sends a UDP message, and updates the local table.
    """
    global popup_widgets, players_table, state, popup_info_text
    player_id_str = popup_widgets[0].text.strip()
    codename = popup_widgets[1].text.strip()
    equipment_str = popup_widgets[2].text.strip()
    udp_ip = popup_widgets[3].text.strip()
    team = popup_widgets[4].text.strip().lower()

    # Validate input data.
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

    # Database operations for update or insert.
    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        create_table_if_not_exists(cursor)
        conn.commit()
        cursor.execute("SELECT codename FROM players WHERE id = %s;", (player_id,))
        result = cursor.fetchone()
        if result:
            # If a record exists, update the codename if changed.
            if codename != result[0]:
                cursor.execute("UPDATE players SET codename = %s WHERE id = %s;", (codename, player_id))
                conn.commit()
        else:
            # Insert new record if not found.
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

    # Send the equipment ID via UDP.
    send_udp_message(udp_ip, equipment)

    # Remove any existing entry for this player from both teams.
    for team_key in players_table:
        players_table[team_key] = [p for p in players_table[team_key] if p["player_id"] != player_id_str]

    # Add updated player info to the chosen team.
    players_table[team].append({
        "player_id": player_id_str,
        "codename": codename,
        "equipment": equipment_str
    })

    popup_info_text = ""
    state = "main"
    set_main_focus(0)

def update_player_cancel():
    """
    Closes the update popup and returns to main state without saving.
    """
    global state, popup_info_text
    popup_info_text = ""
    state = "main"
    set_main_focus(0)

# ---------------------------------------------------------
# Main Screen Drawing
# ---------------------------------------------------------
def draw_main_screen():
    """
    Draws the main player-entry screen with a table layout for
    green and red teams, along with the main screen buttons.
    """
    screen.fill(BG_COLOR)

    # Main table area background
    table_area = pygame.Rect(50, 50, SCREEN_WIDTH - 100, 450)
    shadow = pygame.Surface((table_area.width, table_area.height), pygame.SRCALPHA)
    shadow.fill((0, 0, 0, 80))
    screen.blit(shadow, (table_area.x + 5, table_area.y + 5))
    pygame.draw.rect(screen, pygame.Color('grey20'), table_area, border_radius=10)
    
    # Split the table area into two columns (green, red).
    col_width = table_area.width // 2
    green_area = pygame.Rect(table_area.x, table_area.y, col_width, table_area.height)
    red_area = pygame.Rect(table_area.x + col_width, table_area.y, col_width, table_area.height)
    
    # Headers for each team
    header_height = 40
    green_header = pygame.Rect(green_area.x, green_area.y, green_area.width, header_height)
    red_header = pygame.Rect(red_area.x, red_area.y, red_area.width, header_height)
    pygame.draw.rect(screen, GREEN, green_header, border_radius=5)
    pygame.draw.rect(screen, RED, red_header, border_radius=5)
    header_green = FONT.render("Green Team", True, WHITE)
    header_red = FONT.render("Red Team", True, WHITE)
    screen.blit(header_green, (green_header.centerx - header_green.get_width() // 2,
                               green_header.centery - header_green.get_height() // 2))
    screen.blit(header_red, (red_header.centerx - header_red.get_width() // 2,
                             red_header.centery - header_red.get_height() // 2))
    
    # Subheader bars for each team column
    subheader_height = 30
    green_subheader = pygame.Rect(green_area.x, green_area.y + header_height, green_area.width, subheader_height)
    red_subheader = pygame.Rect(red_area.x, red_area.y + header_height, red_area.width, subheader_height)
    pygame.draw.rect(screen, GREEN_SUBHEADER, green_subheader)
    pygame.draw.rect(screen, RED_SUBHEADER, red_subheader)
    subheader_label = FONT.render("Codename", True, WHITE)
    screen.blit(subheader_label, (green_subheader.centerx - subheader_label.get_width() // 2,
                                  green_subheader.y + (subheader_height - subheader_label.get_height()) // 2))
    screen.blit(subheader_label, (red_subheader.centerx - subheader_label.get_width() // 2,
                                  red_subheader.y + (subheader_height - subheader_label.get_height()) // 2))
    
    # Body areas for each team
    green_body = pygame.Rect(green_area.x, green_area.y + header_height + subheader_height,
                             green_area.width, green_area.height - header_height - subheader_height)
    red_body = pygame.Rect(red_area.x, red_area.y + header_height + subheader_height,
                           red_area.width, red_area.height - header_height - subheader_height)
    dark_green = (0, 70, 0)
    dark_red = (100, 0, 0)
    pygame.draw.rect(screen, dark_green, green_body)
    pygame.draw.rect(screen, dark_red, red_body)
    
    # Draw a grid for each team body (10 rows).
    num_rows = 10
    row_height = green_body.height / num_rows
    grid_color = pygame.Color('grey50')
    for i in range(num_rows + 1):
        y = green_body.y + i * row_height
        pygame.draw.line(screen, grid_color, (green_body.x, y), (green_body.x + green_body.width, y), 1)
        pygame.draw.line(screen, grid_color, (red_body.x, y), (red_body.x + red_body.width, y), 1)

    # A vertical line to separate row numbers from codename in each body.
    left_col_width = 50
    pygame.draw.line(screen, grid_color, (green_body.x + left_col_width, green_body.y),
                     (green_body.x + left_col_width, green_body.y + green_body.height), 1)
    pygame.draw.line(screen, grid_color, (red_body.x + left_col_width, red_body.y),
                     (red_body.x + left_col_width, red_body.y + red_body.height), 1)
    
    # Fill in row numbers and codenames for green team.
    for i in range(num_rows):
        y = green_body.y + i * row_height
        number_text = FONT.render(f"{i+1}", True, WHITE)
        screen.blit(number_text, (green_body.x + 10, y + row_height/2 - number_text.get_height()/2))
        if i < len(players_table["green"]):
            codename_text = FONT.render(players_table["green"][i]["codename"], True, WHITE)
            screen.blit(codename_text, (green_body.x + left_col_width + 10,
                                        y + row_height/2 - codename_text.get_height()/2))
    
    # Fill in row numbers and codenames for red team.
    for i in range(num_rows):
        y = red_body.y + i * row_height
        number_text = FONT.render(f"{i+1}", True, WHITE)
        screen.blit(number_text, (red_body.x + 10, y + row_height/2 - number_text.get_height()/2))
        if i < len(players_table["red"]):
            codename_text = FONT.render(players_table["red"][i]["codename"], True, WHITE)
            screen.blit(codename_text, (red_body.x + left_col_width + 10,
                                        y + row_height/2 - codename_text.get_height()/2))
    
    # Draw the main screen buttons (Add Player, Update Player, Clear, Start).
    main_any_hovered = any(widget.rect.collidepoint(pygame.mouse.get_pos()) for widget in main_widgets)
    for widget in main_widgets:
        widget.draw(screen, disable_tab_highlight=main_any_hovered)

# ---------------------------------------------------------
# Main Screen Buttons & Navigation
# ---------------------------------------------------------
# Four buttons at the bottom: Add Player, Update Player, Clear Players, Start Game.
add_player_button = Button(82, 720, 200, 40, "Add Player", lambda: start_add_player())
update_player_button = Button(302, 720, 200, 40, "Update Player", lambda: start_update_player())
clear_players_button = Button(522, 720, 200, 40, "Clear Players", lambda: clear_players())
start_game_button = Button(742, 720, 200, 40, "Start Game", lambda: start_game())

# A list of these buttons so we can tab between them.
main_widgets = [add_player_button, update_player_button, clear_players_button, start_game_button]
main_focus_index = 0

def set_main_focus(index):
    """
    Sets which main button is focused (for keyboard navigation).
    """
    global main_focus_index, main_widgets
    main_focus_index = index
    for i, widget in enumerate(main_widgets):
        widget.set_focus(i == index)

def move_main_focus_next():
    """
    Moves focus to the next main button, in a circular fashion.
    """
    global main_focus_index, main_widgets
    next_index = (main_focus_index + 1) % len(main_widgets)
    set_main_focus(next_index)

# Initialize the first focus on the main screen.
set_main_focus(0)

def clear_players():
    """
    Clears all player entries from both teams in the in-memory table.
    """
    global players_table
    players_table = {"green": [], "red": []}

def start_game():
    """
    Switches the state to 'game' for a future game screen.
    """
    global state
    state = "game"

# ---------------------------------------------------------
# Game Screen (Stub)
# ---------------------------------------------------------
def draw_game_screen():
    """
    Currently displays a placeholder message for the game screen.
    """
    screen.fill(BG_COLOR)
    message = FONT.render("Play Action Screen - Under Construction", True, WHITE)
    screen.blit(message, ((SCREEN_WIDTH - message.get_width())//2,
                          (SCREEN_HEIGHT - message.get_height())//2))
    return_button.draw(screen)

return_button = Button((SCREEN_WIDTH - 200)//2, SCREEN_HEIGHT - 100, 200, 40, "Return", lambda: return_to_main())
def return_to_main():
    """
    Returns to the main state from the game screen.
    """
    global state
    state = "main"
    set_main_focus(0)

# ---------------------------------------------------------
# Popup Starters
# ---------------------------------------------------------
def start_add_player():
    """
    Begins the add-player wizard (4-step popup).
    """
    global state, popup_mode, popup_info_text
    popup_mode = "add"
    popup_info_text = ""
    init_popup_step1()
    state = "popup"

def start_update_player():
    """
    Opens the update-player popup for editing existing or new player info.
    """
    global state, popup_mode, popup_info_text
    popup_mode = "update"
    popup_info_text = ""
    init_update_popup()
    state = "popup"

# ---------------------------------------------------------
# Main Event Loop
# ---------------------------------------------------------
while True:
    # Process events for the current state.
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if state == "main":
            # Handle keyboard shortcuts in the main screen.
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    move_main_focus_next()
                    continue
                if event.key == pygame.K_F5:
                    start_game()
                if event.key == pygame.K_F12:
                    clear_players()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the user clicked on any main button.
                for i, widget in enumerate(main_widgets):
                    if widget.rect.collidepoint(event.pos):
                        set_main_focus(i)
                        widget.handle_event(event)
                        break
            # Pass the event to each main widget (buttons).
            for widget in main_widgets:
                widget.handle_event(event)

        elif state == "popup":
            # In popup state, handle focus switching and widget events.
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    move_focus_next()
                elif event.key == pygame.K_RETURN:
                    current = popup_widgets[popup_focus_index]
                    # If the current widget is a button, trigger it on Enter.
                    if isinstance(current, Button):
                        current.callback()
                    else:
                        current.handle_event(event)
                else:
                    popup_widgets[popup_focus_index].handle_event(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check which widget, if any, was clicked.
                for i, widget in enumerate(popup_widgets):
                    if widget.rect.collidepoint(event.pos):
                        set_popup_focus(i)
                        widget.handle_event(event)
                        break

        elif state == "game":
            # Handle events in the game screen. Currently only the return button.
            return_button.handle_event(event)

        elif state == "splash":
            # If on the splash screen, any key press moves us to 'main'.
            if event.type == pygame.KEYDOWN:
                state = "main"

    # State-specific drawing/logic updates.
    if state == "splash":
        # Display the splash image or a blank screen for 3 seconds, then go to main.
        if splash_image:
            screen.blit(splash_image, (0, 0))
        else:
            screen.fill(BG_COLOR)
        pygame.display.flip()
        pygame.time.delay(3000)
        state = "main"
        set_main_focus(0)
        continue

    if state == "main":
        draw_main_screen()

    elif state == "popup":
        # Draw the main screen behind the popup (for a dim background effect).
        draw_main_screen()
        # Draw the popup area and its contents.
        pygame.draw.rect(screen, STORMY_BLUE, popup_rect, border_radius=10)
        pygame.draw.rect(screen, pygame.Color('black'), popup_rect, 2, border_radius=10)

        # Decide the header text based on the mode and step (for add wizard).
        header_text = ""
        if popup_mode == "add":
            if popup_step == 1:
                header_text = "Step 1: Enter Player ID"
            elif popup_step == 2:
                header_text = "Step 2: Enter/Update Codename"
            elif popup_step == 3:
                header_text = "Step 3: Equipment ID & UDP IP"
            elif popup_step == 4:
                header_text = "Step 4: Choose Team"
        elif popup_mode == "update":
            header_text = "Update Player Information"

        # Render and draw the popup header.
        header_surf = FONT.render(header_text, True, WHITE)
        screen.blit(header_surf, (popup_rect.x + 20, popup_rect.y + 20))

        # If in update mode, label the first five widgets (the input boxes).
        if popup_mode == "update":
            labels = ["Player ID:", "Codename:", "Equipment ID:", "UDP Target IP:", "Team:"]
            for i, widget in enumerate(popup_widgets[:5]):
                label_surf = FONT.render(labels[i], True, WHITE)
                # Position each label just above its input box.
                label_y = widget.rect.y - label_surf.get_height() - 5
                screen.blit(label_surf, (widget.rect.x, label_y))

        # If there's an info/error message, draw it near the bottom of the popup.
        if popup_info_text:
            info_surf = FONT.render(popup_info_text, True, pygame.Color('red'))
            screen.blit(info_surf, (popup_rect.x + 20, popup_rect.bottom - 40))

        # Draw all widgets (inputs, buttons) in the popup.
        for widget in popup_widgets:
            widget.draw(screen)

    elif state == "game":
        draw_game_screen()

    # Update the display and maintain 30 FPS.
    pygame.display.flip()
    CLOCK.tick(30)
