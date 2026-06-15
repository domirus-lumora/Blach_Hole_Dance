import numpy as np
import math
import pygame

window_width = 1280
window_height = 720
background = (0, 0, 0)
G = 1.0
C = 1200.0
dt = 1.0 / 240.0
substeps = 4 #Count 4 times of physics update per frame to improve accuracy without needing to increase the frame rate

pygame.init()
screen = pygame.display.set_mode((window_width, window_height))
pygame.display.set_caption("Dance of Black Hole, Made by Oon Jia Bao (Domirus)")
clock = pygame.time.Clock()
running = True

# Black hole
black_hole_pos = np.array([window_width / 2, window_height / 2], dtype=float)
black_hole_radius = 50
black_hole_mass = 220000.0
photon_ring_radius = int(black_hole_radius * 1.6)

# Neptune
initial_planet_pos = np.array([window_width / 2 + 280, window_height / 2 - 40], dtype=float)

# Slow initial speed
initial_planet_vel = np.array([0.0, 10.0], dtype=float)
planet_pos = initial_planet_pos.copy() #Copy a array but not using = bacause it will use same RAM unit.
planet_vel = initial_planet_vel.copy()
planet_radius = 26

trail = [] # Should be list of np.array([x, y]) to record the path of the planet for drawing the trail effect
escaped = False
fallen = False

# Mouse drag
dragging = False
drag_start = np.array([0.0, 0.0], dtype=float)
drag_current = np.array([0.0, 0.0], dtype=float)

# Click reset
click_count = 0
last_click_time = 0
click_reset_window = 500  # Click three times within 500 milliseconds (0.5 second) to reset

font = pygame.font.SysFont("monospace", 20)

# Neptune colour
NEPTUNE_MAIN = (40, 90, 255)
NEPTUNE_DARK = (15, 45, 170)
NEPTUNE_LIGHT = (130, 180, 255)
NEPTUNE_SPOT = (35, 70, 180)

def reset_simulation():
    global planet_pos, planet_vel, trail, escaped, fallen, dragging #To change these variable outside
    planet_pos = initial_planet_pos.copy()
    planet_vel = initial_planet_vel.copy()
    trail = []
    escaped = False
    fallen = False
    dragging = False

def compute_physics(pos, vel):
    # The vector pointing from the planet to the black hole, for example, if you first go left 3 steps and then up 5 steps, it would be (-3, 5).
    direction = black_hole_pos - pos
    
    # Vector length, also known as the distance between the planet and the black hole.
    # The formula is derived from the Pythagorean theorem: c^2 = a^2 + b^2, so c = sqrt(a^2 + b^2).
    # Here, a and b are the absolute differences in the x and y coordinates of the two points, and c is the distance between them.
    r = np.linalg.norm(direction)
    
    if r < 1e-8:
        r = 1e-8
    
    # Gravitational acceleration magnitude, which is the magnitude of the acceleration due to gravity.
    # The formula is derived from Newton's law of universal gravitation: F = G * m1 * m2 / r^2, and Newton's second law: a = F / m.
    # Therefore, a = G * M / r^2. Here, it represents the gravitational constant multiplied by the black hole mass and the square of the distance between the two points.
    a_magnitude = G * black_hole_mass / (r * r)
    
    # Gravitational acceleration vector, which stores both the magnitude and direction of the acceleration.
    # The direction is determined by the unit vector, which is the direction vector divided by its length,
    # resulting in a vector of length 1 to avoid scaling the direction by the step distance, thus representing the direction.
    # Multiplying by a_magnitude gives a velocity vector with both magnitude and direction.
    a_vector = a_magnitude * (direction / r)
    
    # Kinetic energy (per unit mass), which is the energy the planet has due to its motion.
    kinetic = 0.5 * (vel[0]**2 + vel[1]**2)
    
    # Potential energy (per unit mass), which is the energy the planet has due to its position.
    potential = -G * black_hole_mass / r
    
    # Total mechanical energy (per unit mass), which is the sum of kinetic and potential energies.
    # This determines the type of orbit, such as elliptical, parabolic, or hyperbolic.
    total_energy = kinetic + potential
    
    # Angular momentum (per unit mass)
    # Calculate the planet's position relative to the black hole
    rel_pos = pos - black_hole_pos
    L = rel_pos[0] * vel[1] - rel_pos[1] * vel[0]
    
    return a_vector, r, direction, kinetic, potential, total_energy, L

def draw_background_stars(surface): #Draw star randomly.
    rng = np.random.default_rng(7)
    for _ in range(90):
        x = int(rng.integers(0, window_width))
        y = int(rng.integers(0, window_height))
        b = int(rng.integers(40, 120))
        pygame.draw.circle(surface, (b, b, b), (x, y), 1)

def draw_black_hole(surface, center):
    # Soft light at outside of the black hole
    glow = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    for i, alpha in enumerate([18, 12, 8, 5]):
        radius = black_hole_radius + 35 + i * 18
        pygame.draw.circle(glow, (255, 120, 40, alpha), center, radius)

    # Elliptical ring
    disk = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
    cx, cy = center

    for i in range(26):
        w = 170 + i * 8
        h = 42 + i * 2
        alpha = max(8, 120 - i * 4)
        color = (255, 120 + i * 2, 30, alpha)
        rect = pygame.Rect(cx - w // 2, cy - h // 2 + 8, w, h)
        pygame.draw.ellipse(disk, color, rect, 2)

    pygame.draw.ellipse(
        disk,
        (255, 210, 120, 80),
        pygame.Rect(cx - 75, cy - 18 + 8, 150, 36),
        2
    )

    # Photon ring
    pygame.draw.circle(disk, (255, 200, 100, 150), center, photon_ring_radius, 2)

    surface.blit(glow, (0, 0))
    surface.blit(disk, (0, 0))

    # Event horizon
    pygame.draw.circle(surface, (0, 0, 0), center, black_hole_radius)
    pygame.draw.circle(surface, (40, 0, 0), center, black_hole_radius, 2)

def draw_neptune(surface, pos, radius):
    x, y = int(pos[0]), int(pos[1])

    # Soft light at outside of the Neptune
    glow = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
    pygame.draw.circle(glow, (80, 130, 255, 45), (radius * 3, radius * 3), radius * 2)
    surface.blit(glow, (x - radius * 3, y - radius * 3))

    # Its body
    pygame.draw.circle(surface, NEPTUNE_MAIN, (x, y), radius)

    # Rings
    band1_rect = pygame.Rect(x - radius, y - radius // 3, radius * 2, radius // 3)
    band2_rect = pygame.Rect(x - radius, y + radius // 10, radius * 2, radius // 4)
    band3_rect = pygame.Rect(x - radius, y + radius // 2 - 4, radius * 2, radius // 5)

    pygame.draw.ellipse(surface, NEPTUNE_DARK, band1_rect)
    pygame.draw.ellipse(surface, (25, 60, 200), band2_rect)
    pygame.draw.ellipse(surface, (30, 80, 210), band3_rect)

    # Spot
    spot_rect = pygame.Rect(x + radius // 5 - 10, y - radius // 6 - 8, 20, 14)
    pygame.draw.ellipse(surface, NEPTUNE_SPOT, spot_rect)

    # Highlight
    highlight = pygame.Surface((radius * 2 + 20, radius * 2 + 20), pygame.SRCALPHA)
    pygame.draw.circle(highlight, (180, 220, 255, 60), (radius // 2, radius // 2), radius // 2)
    surface.blit(highlight, (x - radius, y - radius))

    # Outline
    pygame.draw.circle(surface, NEPTUNE_LIGHT, (x, y), radius, 1)

#main()

while running:
    clock.tick(60)

    # Monitor events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                dragging = True
                drag_start = np.array(event.pos, dtype=float)
                drag_current = np.array(event.pos, dtype=float)

        elif event.type == pygame.MOUSEMOTION:
            if dragging:
                drag_current = np.array(event.pos, dtype=float)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                now = pygame.time.get_ticks()
                drag_len = np.linalg.norm(drag_current - drag_start)

                # Clicking without dragging (or very short drag) counts as a click for reset.
                if drag_len < 8:
                    if now - last_click_time > click_reset_window:
                        click_count = 0

                    last_click_time = now
                    click_count += 1

                    if click_count >= 3:
                        reset_simulation()
                        click_count = 0
                else:
                    dragging = False
                    drag_vec = drag_current - drag_start

                    # Velocity vector.
                    new_vel = drag_vec * 0.35

                    # Max speed
                    speed = np.linalg.norm(new_vel)
                    max_speed = 140.0
                    if speed > max_speed:
                        new_vel = new_vel / speed * max_speed

                    planet_vel = new_vel
                    trail = []
                    escaped = False
                    fallen = False

    if not escaped and not fallen:
        for _ in range(substeps):
            a_total_vec, r, direction, kinetic, potential, total_energy, L = compute_physics(planet_pos, planet_vel)

            # Condition of drop inside black hole
            if r <= black_hole_radius:
                fallen = True
                planet_vel[:] = 0.0
                break

            # Update velocity
            planet_vel = planet_vel + a_total_vec * dt

            # Update where is it
            planet_pos = planet_pos + planet_vel * dt

            # Trail
            trail.append(planet_pos.copy())
            if len(trail) > 400:
                trail.pop(0)

        # Escape
        margin = 180
        if (
            planet_pos[0] < -margin or
            planet_pos[0] > window_width + margin or
            planet_pos[1] < -margin or
            planet_pos[1] > window_height + margin
        ):
            escaped = True

    # Draw
    screen.fill(background)
    draw_background_stars(screen)

    center = (int(black_hole_pos[0]), int(black_hole_pos[1]))
    draw_black_hole(screen, center)

    # Trail
    if len(trail) > 0:
        for i, point in enumerate(trail):
            size = max(2, int(5 * (i / len(trail))))
            pygame.draw.circle(screen, (17, 2, 125), (int(point[0]), int(point[1])), size)

    # Neptune
    if not escaped and not fallen:
        draw_neptune(screen, planet_pos, planet_radius)
    elif escaped:
        text = font.render("ESCAPED! Click to reset", True, (255, 255, 255))
        screen.blit(text, (window_width // 2 - 120, window_height // 2))
    elif fallen:
        text = font.render("FELL INTO BLACK HOLE! Click to reset", True, (255, 100, 100))
        screen.blit(text, (window_width // 2 - 170, window_height // 2))

    # Lines of dragging
    if dragging:
        start_pos = (int(drag_start[0]), int(drag_start[1]))
        current_pos = (int(drag_current[0]), int(drag_current[1]))
        pygame.draw.line(screen, (255, 255, 255), start_pos, current_pos, 2)

        arrow_dir = drag_current - drag_start
        if np.linalg.norm(arrow_dir) > 5:
            arrow_end = drag_current
            angle = math.atan2(arrow_dir[1], arrow_dir[0])
            arrow_head1 = arrow_end - 10 * np.array([math.cos(angle + math.pi / 6), math.sin(angle + math.pi / 6)])
            arrow_head2 = arrow_end - 10 * np.array([math.cos(angle - math.pi / 6), math.sin(angle - math.pi / 6)])
            pygame.draw.polygon(screen, (255, 255, 255), [
                (int(arrow_end[0]), int(arrow_end[1])),
                (int(arrow_head1[0]), int(arrow_head1[1])),
                (int(arrow_head2[0]), int(arrow_head2[1]))
            ])

    # Speed config
    if not escaped and not fallen:
        a_total_vec, r, direction, kinetic, potential, total_energy, L = compute_physics(planet_pos, planet_vel)

        v_speed = np.linalg.norm(planet_vel)
        v_esc = math.sqrt(2 * G * black_hole_mass / r) if r > 0 else 0.0

        speed_text = font.render(f"Speed: {v_speed:.1f}", True, (200, 200, 200))
        esc_text = font.render(f"Escape Speed: {v_esc:.1f}", True, (200, 200, 200))
        energy_text = font.render(f"Energy: {total_energy:.1f}", True, (200, 200, 200))
        screen.blit(speed_text, (10, 10))
        screen.blit(esc_text, (10, 35))
        screen.blit(energy_text, (10, 60))

        if total_energy >= 0:
            status_text = font.render("Status: OUTBOUND", True, (100, 255, 100))
        else:
            status_text = font.render("Status: BOUND", True, (255, 200, 100))
        screen.blit(status_text, (10, 85))

    hint_text = font.render("Click 3 times to reset | Drag mouse to throw Neptune", True, (150, 150, 150))
    screen.blit(hint_text, (10, window_height - 30))

    pygame.display.flip()

pygame.quit()