import sys
import pygame

# --- Stałe ---
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 200

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# ------------------------------------------------------
# Tintowanie PNG
# ------------------------------------------------------
def tint_image(base, color):
    tinted = base.copy()
    r, g, b = color
    tint_surface = pygame.Surface(base.get_size(), pygame.SRCALPHA)
    tint_surface.fill((r, g, b, 255))
    tinted.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


# ------------------------------------------------------
# Player
# ------------------------------------------------------
class Player:
    def __init__(self, x, y, image_path="dodo.png", scale=(64, 64)):
        self.x = x
        self.y = y

        self.base_image = pygame.image.load(image_path).convert_alpha()
        if scale:
            self.base_image = pygame.transform.smoothscale(self.base_image, scale)

        self.color = (255, 255, 255)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(x), int(y)))

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    def set_color(self, color):
        self.color = color
        self.image = tint_image(self.base_image, color)
        self.rect = self.image.get_rect(center=self.rect.center)

    def move(self, dx, dy):
        self.x += dx
        self.y += dy
        self.rect.center = (int(self.x), int(self.y))

    def set_pos(self, x, y):
        self.x = x
        self.y = y
        self.rect.center = (int(x), int(y))

    def clamp(self, w, h):
        self.rect.clamp_ip(pygame.Rect(0, 0, w, h))
        self.x, self.y = self.rect.center

    def draw(self, surf):
        surf.blit(self.image, self.rect)


# ------------------------------------------------------
# Path manager
# ------------------------------------------------------
class PathManager:
    def __init__(self):
        self.stack = []

    def push(self, pos):
        if not self.stack or self.stack[-1] != pos:
            self.stack.append(pos)

    def clear(self):
        self.stack.clear()

    def draw(self, surface):
        if len(self.stack) > 1:
            pygame.draw.lines(surface, (200, 200, 200), False, self.stack, 2)
            for p in self.stack:
                pygame.draw.circle(surface, (200, 200, 200), p, 3)


# ------------------------------------------------------
# Game
# ------------------------------------------------------
class GameApp:
    def __init__(self, w=WIDTH, h=HEIGHT):
        pygame.init()
        pygame.display.set_caption("Pygame - Optymalizacja")
        self.screen = pygame.display.set_mode((w, h))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20)

        # tło
        try:
            bg = pygame.image.load("tlo.jpg").convert()
            self.background = pygame.transform.smoothscale(bg, (w, h))
        except:
            self.background = None

        self.player = Player(w // 2, h // 2)
        self.path = PathManager()
        self.path.push(self.player.pos)

        # playback
        self.playback = False
        self.play_stack = []
        self.frame_delay = 3
        self.frame_counter = 0

        # wygenerowany HUD (tekst)
        self.hud_surf = self.render_hud()

        self.w, self.h = w, h

    # ----------------------------------------------
    # HUD renderowany raz
    # ----------------------------------------------
    def render_hud(self):
        lines = [
            "Strzałki - ruch | Lewy klik - teleport | SPACJA - cofanie",
            "R/G/B - kolor PNG | C - reset trasy | ESC - wyjscie",
        ]
        surf_height = len(lines) * 18 + 5
        hud = pygame.Surface((400, surf_height), pygame.SRCALPHA)

        y = 0
        for line in lines:
            text = self.font.render(line, True, WHITE)
            hud.blit(text, (0, y))
            y += 18
        return hud

    # ----------------------------------------------
    # Playback
    # ----------------------------------------------
    def start_playback(self):
        if not self.playback and self.path.stack:
            self.playback = True
            self.play_stack = self.path.stack.copy()
            self.frame_counter = 0

    def update_playback(self):
        if not self.playback:
            return
        if not self.play_stack:
            self.playback = False
            return

        self.frame_counter += 1
        if self.frame_counter >= self.frame_delay:
            self.frame_counter = 0
            x, y = self.play_stack.pop()
            self.player.set_pos(x, y)

    # ----------------------------------------------
    # Events
    # ----------------------------------------------
    def handle_events(self, dt):
        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_RIGHT] - keys[pygame.K_LEFT]) * PLAYER_SPEED * dt
        dy = (keys[pygame.K_DOWN] - keys[pygame.K_UP]) * PLAYER_SPEED * dt

        if not self.playback and (dx or dy):
            self.player.move(dx, dy)
            self.player.clamp(self.w, self.h)
            self.path.push(self.player.pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_SPACE:
                    self.start_playback()
                elif event.key == pygame.K_c:
                    self.path.clear()
                    self.path.push(self.player.pos)
                elif event.key == pygame.K_r:
                    self.player.set_color((255, 0, 0))
                elif event.key == pygame.K_g:
                    self.player.set_color((0, 255, 0))
                elif event.key == pygame.K_b:
                    self.player.set_color((0, 0, 255))

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.player.set_pos(*event.pos)
                self.player.clamp(self.w, self.h)
                self.path.push(self.player.pos)

    # ----------------------------------------------
    # Main loop
    # ----------------------------------------------
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events(dt)
            self.update_playback()

            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(WHITE)

            self.path.draw(self.screen)
            self.player.draw(self.screen)

            # HUD
            self.screen.blit(self.hud_surf, (5, 5))

            pygame.display.flip()

    def quit(self):
        pygame.quit()
        sys.exit()


# ------------------------------------------------------
# START
# ------------------------------------------------------
if __name__ == "__main__":
    GameApp().run()
