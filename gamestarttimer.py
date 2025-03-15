import pygame
import os

def load_images():
    images = {}
    for i in range(31):  # 0 to 30
        filename = f"countdown_images/{i}.tif"
        if os.path.exists(filename):
            image = pygame.image.load(filename)
            images[i] = image  # Use the original image size.
        else:
            print(f"Warning: {filename} not found")
    return images

def run_countdown(screen):
    pygame.font.init()
    images = load_images()
    try:
        # Load the original background image.
        background_orig = pygame.image.load("countdown_images/background.tif")
    except Exception as e:
        print("Error loading background:", e)
        background_orig = None

    # Define original background dimensions (as provided originally).
    orig_bg_width, orig_bg_height = 586, 445
    # Calculate scale factor based on the target screen width.
    scale_factor = screen.get_width() / orig_bg_width  # ~1.75 for 1024 width

    # Scale the background to fill the screen (using the calculated scale factor).
    if background_orig:
        bg_scaled = pygame.transform.scale(background_orig, (int(orig_bg_width * scale_factor), int(orig_bg_height * scale_factor)))
    else:
        bg_scaled = None

    # Fixed coordinates in original image: (171, 204).
    # Scale these coordinates.
    fixed_x = int(171 * scale_factor)
    fixed_y = int(204 * scale_factor)

    running = True
    start_time = pygame.time.get_ticks()
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        # Draw the scaled background covering the full screen.
        if bg_scaled:
            # Optionally, you can center the background if needed.
            screen.blit(bg_scaled, (0, 0))
        else:
            screen.fill((0, 0, 0))

        elapsed_time = (pygame.time.get_ticks() - start_time) // 1000
        remaining_time = max(30 - elapsed_time, 0)
        
        if remaining_time in images:
            image = images[remaining_time]
            # Scale the countdown number image using the same scale factor.
            new_width = int(image.get_width() * scale_factor)
            new_height = int(image.get_height() * scale_factor)
            scaled_image = pygame.transform.scale(image, (new_width, new_height))
            # Blit the scaled countdown image at the fixed scaled coordinates.
            screen.blit(scaled_image, (fixed_x, fixed_y))
            
        if elapsed_time >= 30:
            running = False

        pygame.display.flip()
        clock.tick(30)
