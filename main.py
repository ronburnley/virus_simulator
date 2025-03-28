# Highlighted change: "immunity_duration": 600

import pygame
import random
import math
from collections import deque

# --- Configuration Parameters ---
WIDTH, HEIGHT = 900, 750  # Increased height for UI
POPULATION_SIZE = 150
PERSON_RADIUS = 6
INITIAL_INFECTED = 4

# --- Dynamic Variables (Initial Values) ---
# These will be controlled by the UI
current_vars = {
    "move_speed": 1.2,
    "infection_chance": 0.50, # Probability (0.0 to 1.0)
    "infection_duration": 700, # Frames
    "immunity_duration": 600  # Frames (600f / 60fps = 10s)   # <<< CHANGED DEFAULT
}

# --- Simulation Constants ---
RECOVERY_GRANTS_IMMUNITY = True # Essential for waning immunity feature

# --- Visual Enhancements ---
ENABLE_GLOW = True
GLOW_LAYERS = 4
GLOW_ALPHA = 40
GLOW_EXPANSION = 1.5
ENABLE_TRAILS = True
TRAIL_LENGTH = 10
TRAIL_ALPHA_START = 60
ENABLE_INFECTION_FLASH = True
FLASH_DURATION = 15
FLASH_MAX_RADIUS = PERSON_RADIUS * 4

# --- Colors ---
BACKGROUND_TOP = (10, 0, 20)
BACKGROUND_BOTTOM = (30, 0, 50)
HEALTHY_COLOR = (0, 220, 120)
INFECTED_COLOR = (255, 50, 50)
RECOVERED_COLOR = (100, 100, 180) # Immune individuals will show this color
FLASH_COLOR = (255, 255, 200)
UI_TEXT_COLOR = (230, 230, 230)
UI_BG_COLOR = (40, 40, 70, 200) # Semi-transparent UI background
BUTTON_COLOR = (80, 80, 120)
BUTTON_HOVER_COLOR = (110, 110, 160)

# --- UI Configuration ---
UI_AREA_HEIGHT = 100 # Space at the bottom for controls
UI_PADDING = 15
BUTTON_WIDTH = 25
BUTTON_HEIGHT = 20
LABEL_SPACING = 140 # Horizontal space allocated for each variable label + buttons (Adjust if needed)
VALUE_STEP = { # How much each button click changes the value
    "move_speed": 0.1,
    "infection_chance": 0.05,
    "infection_duration": 30, # 0.5 seconds at 60fps
    "immunity_duration": 60   # 1 second at 60fps
}
VALUE_LIMITS = { # Min/Max limits for variables
    "move_speed": (0.1, 5.0),
    "infection_chance": (0.0, 1.0),
    "infection_duration": (30, 3000),
    "immunity_duration": (0, 6000) # 0 means no immunity
}

# --- Global list for temporary effects ---
active_flashes = []

# --- Person Class ---
class Person:
    def __init__(self, x, y, status="healthy"):
        self.x = x
        self.y = y
        self.radius = PERSON_RADIUS
        self.status = status
        self.infection_timer = 0
        self.immunity_timer = 0 # New timer for immunity duration

        self.angle = random.uniform(0, 2 * math.pi) # Store angle separately
        # Access global dict directly for initial speed
        self.update_speed(current_vars["move_speed"]) # Set initial velocity

        self._set_color()

        if ENABLE_TRAILS:
            self.trail = deque(maxlen=TRAIL_LENGTH)

    def _set_color(self):
        """Sets color based on status."""
        if self.status == "healthy":
            self.color = HEALTHY_COLOR
        elif self.status == "infected":
            self.color = INFECTED_COLOR
        elif self.status == "recovered": # Represents the immune phase
            self.color = RECOVERED_COLOR
        self.glow_color = (*self.color, GLOW_ALPHA)

    def update_speed(self, new_speed):
        """Recalculates dx, dy based on stored angle and new speed."""
        # Use global limits directly
        self.speed = max(VALUE_LIMITS["move_speed"][0], min(new_speed, VALUE_LIMITS["move_speed"][1])) # Apply limits
        self.dx = math.cos(self.angle) * self.speed
        self.dy = math.sin(self.angle) * self.speed

    def move(self, world_height):
        """Updates position and handles bouncing off walls (excluding UI area)."""
        if ENABLE_TRAILS:
            self.trail.append((self.x, self.y))

        self.x += self.dx
        self.y += self.dy

        # Update angle based on velocity - important if bouncing changes direction
        current_angle = math.atan2(self.dy, self.dx)

        # Bounce off walls (top, left, right, and ceiling of simulation area)
        bounce_dampening = 1.0 # Can adjust if needed
        sim_area_height = world_height - UI_AREA_HEIGHT
        bounced = False

        if self.x <= self.radius:
            self.dx = abs(self.dx) * bounce_dampening
            self.x = self.radius
            bounced = True
        elif self.x >= WIDTH - self.radius:
            self.dx = -abs(self.dx) * bounce_dampening
            self.x = WIDTH - self.radius
            bounced = True

        if self.y <= self.radius:
            self.dy = abs(self.dy) * bounce_dampening
            self.y = self.radius
            bounced = True
        elif self.y >= sim_area_height - self.radius: # Bounce off UI boundary
            self.dy = -abs(self.dy) * bounce_dampening
            self.y = sim_area_height - self.radius
            bounced = True

        # Update angle only if bounce occurred to prevent drifting
        if bounced:
             self.angle = math.atan2(self.dy, self.dx)


    def update_status(self, current_frame):
        """Updates infection and immunity timers, handles recovery and immunity waning."""
        global current_vars # Need access to check durations

        if self.status == "infected":
            self.infection_timer += 1
            effective_infection_duration = max(1, int(current_vars["infection_duration"])) # Ensure > 0
            if self.infection_timer >= effective_infection_duration:
                if RECOVERY_GRANTS_IMMUNITY:
                    self.status = "recovered" # Enter immune state
                    self.immunity_timer = 0 # Start immunity timer
                else:
                    self.status = "healthy" # Recover directly to susceptible
                self.infection_timer = 0
                self._set_color()

        elif self.status == "recovered": # If currently immune
             effective_immunity_duration = max(0, int(current_vars["immunity_duration"])) # Allow 0 immunity
             if effective_immunity_duration == 0: # If duration is zero, immediately become healthy
                 self.status = "healthy"
                 self._set_color()
                 self.immunity_timer = 0 # Reset timer
             else:
                self.immunity_timer += 1
                if self.immunity_timer >= effective_immunity_duration:
                    self.status = "healthy" # Immunity waned, become susceptible
                    self.immunity_timer = 0
                    self._set_color()

        # Subtle pulsating effect for infected
        if self.status == "infected":
             pulsation = (math.sin(current_frame * 0.1) + 1) / 2
             self.current_radius = self.radius + pulsation * 2
        else:
             self.current_radius = self.radius


    def draw(self, screen):
        """Draws the person with trails and glow."""
        pos = (int(self.x), int(self.y))

        # 1. Draw Trail
        if ENABLE_TRAILS and len(self.trail) > 1:
             for i, p_pos in enumerate(reversed(self.trail)):
                 alpha = TRAIL_ALPHA_START * (i / TRAIL_LENGTH)
                 # Ensure alpha doesn't go negative due to float inaccuracies
                 safe_alpha = max(0, int(alpha))
                 trail_color = (*self.color[:3], safe_alpha)
                 # Calculate shrinking radius, ensure it's not negative
                 trail_rad_factor = max(0.0, 1.0 - i / TRAIL_LENGTH)
                 current_trail_radius = int(self.radius * trail_rad_factor)
                 # Only draw if radius is positive
                 if current_trail_radius > 0:
                     trail_surf = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
                     pygame.draw.circle(trail_surf, trail_color, (self.radius, self.radius), current_trail_radius)
                     screen.blit(trail_surf, (int(p_pos[0]-self.radius), int(p_pos[1]-self.radius)))

        # 2. Draw Glow
        if ENABLE_GLOW:
            for i in range(GLOW_LAYERS, 0, -1):
                glow_radius = int(self.current_radius + i * GLOW_EXPANSION)
                if glow_radius <= 0: continue # Skip if radius is zero or negative

                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                current_glow_alpha = max(0, int(GLOW_ALPHA / i)) # Ensure non-negative alpha
                if current_glow_alpha > 0:
                    try:
                        pygame.draw.circle(glow_surf, (*self.color[:3], current_glow_alpha), (glow_radius, glow_radius), glow_radius)
                        screen.blit(glow_surf, (pos[0] - glow_radius, pos[1] - glow_radius), special_flags=pygame.BLEND_RGBA_ADD)
                    except pygame.error: # Catch potential errors if radius/alpha are invalid somehow
                        pass # Just skip drawing this glow layer

        # 3. Draw the main circle
        main_rad = int(self.current_radius)
        if main_rad > 0:
            pygame.draw.circle(screen, self.color, pos, main_rad)


    def infect(self):
        """Infects the person if they are susceptible ('healthy'). Returns True if infection occurred."""
        global current_vars # Need access to infection chance
        # Waning immunity logic means only 'healthy' are susceptible
        if self.status == "healthy":
            # Apply infection chance
            if random.random() < current_vars["infection_chance"]:
                old_status = self.status
                self.status = "infected"
                self.infection_timer = 0
                self.immunity_timer = 0 # Reset just in case
                self._set_color()

                # Use global active_flashes list here (modification is okay without global keyword in this context)
                if old_status != "infected" and ENABLE_INFECTION_FLASH:
                     active_flashes.append({
                         'x': self.x, 'y': self.y, 'timer': 0,
                         'max_timer': FLASH_DURATION, 'max_radius': FLASH_MAX_RADIUS
                     })
                return True # Infection occurred
        return False # No infection occurred


    def distance_to(self, other_person):
        return math.hypot(self.x - other_person.x, self.y - other_person.y)

# --- Helper: Draw Background Gradient ---
def draw_background(screen):
    """Draws a vertical gradient."""
    try:
        screen_height = screen.get_height()
        screen_width = screen.get_width()
        for y in range(screen_height):
            # Interpolate color from top to bottom
            ratio = y / screen_height
            color = (
                int(BACKGROUND_TOP[0] * (1 - ratio) + BACKGROUND_BOTTOM[0] * ratio),
                int(BACKGROUND_TOP[1] * (1 - ratio) + BACKGROUND_BOTTOM[1] * ratio),
                int(BACKGROUND_TOP[2] * (1 - ratio) + BACKGROUND_BOTTOM[2] * ratio)
            )
            pygame.draw.line(screen, color, (0, y), (screen_width, y))
    except Exception as e:
        print(f"Error drawing background: {e}") # Basic error handling


# --- Helper: Draw UI ---
def draw_ui(screen, font, ui_button_rects_map, mouse_pos):
    """Draws the control UI at the bottom."""
    ui_rect = pygame.Rect(0, HEIGHT - UI_AREA_HEIGHT, WIDTH, UI_AREA_HEIGHT)
    # Use SRCALPHA surface for transparency
    ui_surf = pygame.Surface(ui_rect.size, pygame.SRCALPHA)
    ui_surf.fill(UI_BG_COLOR)

    # Draw labels and buttons
    x_offset = UI_PADDING
    y_offset = UI_PADDING # Relative Y within UI surface

    var_display_names = {
        "move_speed": "Speed",
        "infection_chance": "Inf. Chance",
        "infection_duration": "Inf. Duration",
        "immunity_duration": "Imm. Duration"
    }

    for var_name, display_name in var_display_names.items():
        # Label
        label_text = f"{display_name}:"
        label_surf = font.render(label_text, True, UI_TEXT_COLOR)
        ui_surf.blit(label_surf, (x_offset, y_offset))

        # Value (formatted)
        if "chance" in var_name:
            value_text = f"{current_vars[var_name]:.2f}"
        elif "speed" in var_name:
             value_text = f"{current_vars[var_name]:.1f}"
        else: # Durations
             # Display immunity duration=0 as "None" or "0s"
             if var_name == "immunity_duration" and current_vars[var_name] == 0:
                 value_text = "None"
             else:
                 value_text = f"{int(current_vars[var_name]/60)}s" # Show in seconds

        value_surf = font.render(value_text, True, UI_TEXT_COLOR)
        val_rect = value_surf.get_rect(left=x_offset, top=y_offset + 25)
        ui_surf.blit(value_surf, val_rect)


        # Buttons (using the map to find rects)
        button_y = y_offset + 50 # Y position relative to UI surface origin (This seems off, should match rect creation)
                                 # Let's adjust based on how rects are created later.

        # Get the global rects from the map
        try:
            global_minus_rect = ui_button_rects_map[var_name]['minus']
            global_plus_rect = ui_button_rects_map[var_name]['plus']

            # Create local rects relative to the UI surface for drawing/hover check
            minus_rect_local = global_minus_rect.move(-ui_rect.left, -ui_rect.top)
            plus_rect_local = global_plus_rect.move(-ui_rect.left, -ui_rect.top)

            # Get mouse position relative to UI surface
            mouse_local_x = mouse_pos[0] - ui_rect.left
            mouse_local_y = mouse_pos[1] - ui_rect.top

            # Minus Button
            is_hovering_minus = minus_rect_local.collidepoint(mouse_local_x, mouse_local_y)
            btn_color_minus = BUTTON_HOVER_COLOR if is_hovering_minus else BUTTON_COLOR
            pygame.draw.rect(ui_surf, btn_color_minus, minus_rect_local, border_radius=3)
            minus_surf = font.render("-", True, UI_TEXT_COLOR)
            minus_rect_text = minus_surf.get_rect(center=minus_rect_local.center)
            ui_surf.blit(minus_surf, minus_rect_text)

            # Plus Button
            is_hovering_plus = plus_rect_local.collidepoint(mouse_local_x, mouse_local_y)
            btn_color_plus = BUTTON_HOVER_COLOR if is_hovering_plus else BUTTON_COLOR
            pygame.draw.rect(ui_surf, btn_color_plus, plus_rect_local, border_radius=3)
            plus_surf = font.render("+", True, UI_TEXT_COLOR)
            plus_rect_text = plus_surf.get_rect(center=plus_rect_local.center)
            ui_surf.blit(plus_surf, plus_rect_text)

        except KeyError:
            print(f"Warning: UI button rects not found for variable '{var_name}'")


        x_offset += LABEL_SPACING # Move to next variable's position


    # Blit the entire UI surface onto the main screen
    screen.blit(ui_surf, ui_rect.topleft)


# --- Simulation Functions ---
def run_simulation():
    global current_vars # Allow modification of global dict
    global active_flashes # <<< USE GLOBAL SCOPE for assignment below

    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Interactive Virus Simulator")
    clock = pygame.time.Clock()
    font_stats = pygame.font.Font(None, 30)
    font_ui = pygame.font.Font(None, 24)

    # Create population
    people = []
    for i in range(POPULATION_SIZE):
        # Ensure people spawn above the UI area
        sim_area_height = HEIGHT - UI_AREA_HEIGHT
        x = random.uniform(PERSON_RADIUS, WIDTH - PERSON_RADIUS)
        y = random.uniform(PERSON_RADIUS, sim_area_height - PERSON_RADIUS)
        status = "infected" if i < INITIAL_INFECTED else "healthy"
        people.append(Person(x, y, status))

    # --- Create UI Button Rects and Action List (Corrected Setup) ---
    ui_button_actions = [] # List: [(rect_object, (variable_name, delta))] for click detection
    ui_button_rects_map = {} # Dict: {var_name: {'minus': rect_object, 'plus': rect_object}} for drawing

    x_offset = UI_PADDING
    # Calculate absolute Y position for button creation (Top of UI area + padding + space for label/value)
    button_abs_y = HEIGHT - UI_AREA_HEIGHT + UI_PADDING + 50 # Y pos relative to screen

    for var_name in current_vars.keys():
        # Create Rects with absolute screen coordinates
        minus_rect = pygame.Rect(x_offset, button_abs_y, BUTTON_WIDTH, BUTTON_HEIGHT)
        plus_rect = pygame.Rect(x_offset + BUTTON_WIDTH + 5, button_abs_y, BUTTON_WIDTH, BUTTON_HEIGHT)

        # Add to action list for click detection
        ui_button_actions.append((minus_rect, (var_name, -VALUE_STEP[var_name])))
        ui_button_actions.append((plus_rect, (var_name, VALUE_STEP[var_name])))

        # Add to map for drawing reference (store the absolute rects)
        ui_button_rects_map[var_name] = {'minus': minus_rect, 'plus': plus_rect}

        x_offset += LABEL_SPACING
    # --- End of UI Setup ---

    running = True
    frame_count = 0
    while running:
        mouse_pos = pygame.mouse.get_pos() # Get mouse position once per frame

        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left mouse button
                    # Use the corrected list for collision detection
                    for rect, (var_name, delta) in ui_button_actions:
                        if rect.collidepoint(event.pos):
                            # Update the variable
                            current_value = current_vars[var_name]
                            new_value = current_value + delta

                            # Apply limits
                            min_val, max_val = VALUE_LIMITS[var_name]
                            new_value = max(min_val, min(new_value, max_val))

                            # Prevent floating point inaccuracies for chance
                            if var_name == "infection_chance":
                                new_value = round(new_value, 2)
                            # Ensure durations are reasonably stepped and integer
                            elif "duration" in var_name:
                                # Round to nearest step value, ensure it's >= 0
                                step = VALUE_STEP[var_name]
                                new_value = max(0, round(new_value / step) * step)
                                new_value = max(min_val, int(new_value)) # Ensure int and min value (min is likely 0 or 30)


                            current_vars[var_name] = new_value

                            # If move speed changed, update all people
                            if var_name == "move_speed":
                                for person in people:
                                    person.update_speed(new_value)
                            break # Process only one button click

        # --- Update Logic ---
        frame_count += 1
        for person in people:
            person.move(HEIGHT) # Pass world height for boundary check
            person.update_status(frame_count)

        # --- Interaction & Infection Logic ---
        infection_radius = PERSON_RADIUS * 3.0 # Consider making this dynamic later
        for i in range(POPULATION_SIZE):
            p1 = people[i]
            # Optimization: Don't check pairs twice
            for j in range(i + 1, POPULATION_SIZE):
                p2 = people[j]

                # Quick distance check approximation (Manhattan distance) - optional optimization
                # if abs(p1.x - p2.x) > infection_radius or abs(p1.y - p2.y) > infection_radius:
                #    continue

                dist = p1.distance_to(p2)

                if dist < infection_radius:
                    # Try infection based on status (infect() method handles chance and susceptibility)
                    if p1.status == "infected" and p2.status == "healthy":
                        p2.infect()
                    elif p2.status == "infected" and p1.status == "healthy":
                        p1.infect()


        # --- Update Flash Effects ---
        flashes_to_remove = []
        # This loop now correctly reads the global active_flashes
        for flash in active_flashes:
            flash['timer'] += 1
            if flash['timer'] > flash['max_timer']:
                flashes_to_remove.append(flash)
        # This assignment now correctly modifies the global active_flashes
        active_flashes = [f for f in active_flashes if f not in flashes_to_remove]


        # --- Drawing ---
        draw_background(screen)

        # Draw flashes
        for flash in active_flashes:
             progress = flash['timer'] / flash['max_timer']
             current_radius = int(progress * flash['max_radius'])
             alpha = int(200 * (1 - progress**2)) # Non-linear fade
             if alpha > 0 and current_radius > 0:
                 try:
                     flash_surf = pygame.Surface((current_radius*2, current_radius*2), pygame.SRCALPHA)
                     pygame.draw.circle(flash_surf, (*FLASH_COLOR[:3], alpha), (current_radius, current_radius), current_radius)
                     screen.blit(flash_surf, (int(flash['x'] - current_radius), int(flash['y'] - current_radius)), special_flags=pygame.BLEND_RGBA_ADD)
                 except pygame.error: # Catch errors drawing flashes
                     pass


        # Draw people
        for person in people:
            person.draw(screen)

        # --- Draw UI ---
        # Pass the map needed for drawing, and current mouse pos for hover effect
        draw_ui(screen, font_ui, ui_button_rects_map, mouse_pos)

        # --- Statistics ---
        counts = {"healthy": 0, "infected": 0, "recovered": 0}
        for person in people:
            counts[person.status] += 1

        healthy_text = font_stats.render(f"Healthy: {counts['healthy']}", True, HEALTHY_COLOR)
        infected_text = font_stats.render(f"Infected: {counts['infected']}", True, INFECTED_COLOR)
        recovered_text = font_stats.render(f"Immune: {counts['recovered']}", True, RECOVERED_COLOR) # Label reflects immunity

        # Stats position (top left)
        stats_bg_rect = pygame.Rect(5, 5, 200, 95)
        try: # Add try-except for drawing operations
            pygame.draw.rect(screen, (0,0,0, 150), stats_bg_rect) # Semi-transparent black background
            screen.blit(healthy_text, (15, 15))
            screen.blit(infected_text, (15, 45))
            screen.blit(recovered_text, (15, 75))
        except Exception as e:
            print(f"Error drawing stats: {e}")


        # --- Update Display ---
        pygame.display.flip()

        # --- Frame Rate Control ---
        clock.tick(60) # Aim for 60 FPS

    pygame.quit()

# --- Main Execution ---
if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        print(f"An error occurred during simulation: {e}")
        pygame.quit() # Ensure pygame quits even if error happens early