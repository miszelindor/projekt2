import sys
import pygame
from collections import deque

# --- Ustawienia ---
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_SPEED = 200  # px/s

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
GREY = (200, 200, 200)


# ------------------------------------------------------
# FUNKCJA TINTUJĄCA PNG (alpha 255 aby nie znikał obraz)
# ------------------------------------------------------
def tint_image(image, color):
    """Nakłada kolor (tint) na PNG z zachowaniem przezroczystości."""
    tinted = image.copy()
    r, g, b = color
    tint_surface = pygame.Surface(image.get_size(), pygame.SRCALPHA)
    # ważne: alpha = 255, by nie "wyzerować" kanału alpha przy BLEND_RGBA_MULT
    tint_surface.fill((r, g, b, 255))
    tinted.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return tinted


# ------------------------------------------------------
# KLASA PLAYER
# ------------------------------------------------------
class Player:
    """Reprezentuje obiekt poruszany na ekranie (PNG z tintowaniem)."""

    def __init__(self, x: float, y: float, image_path="dodo.png", scale=None):
        self.x = float(x)
        self.y = float(y)

        # wczytanie obrazu bazowego z alpha
        self.base_image = pygame.image.load(image_path).convert_alpha()

        # opcjonalne skalowanie
        if scale is not None:
            self.base_image = pygame.transform.smoothscale(self.base_image, scale)

        # aktualny (tintowany) obraz
        self.color = (255, 255, 255)
        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    def set_color(self, color):
        """Ustaw kolor i zaktualizuj widoczny obraz."""
        self.color = color
        self.image = tint_image(self.base_image, self.color)
        # utrzymaj środek
        self.rect = self.image.get_rect(center=self.rect.center)

    def set_pos(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))

    def move(self, dx: float, dy: float):
        self.x += dx
        self.y += dy
        self.rect.center = (int(self.x), int(self.y))

    def clamp_to_rect(self, w: int, h: int):
        # zapobiega wychodzeniu poza okno (używa rect clamp_ip)
        self.rect.clamp_ip(pygame.Rect(0, 0, w, h))
        self.x, self.y = self.rect.center

    def draw(self, surface: pygame.Surface):
        """Rysuj na podanej powierzchni."""
        surface.blit(self.image, self.rect)


# ------------------------------------------------------
# PATH MANAGER
# ------------------------------------------------------
class PathManager:
    """Zarządza stosem pozycji oraz rysowaniem trasy."""

    def __init__(self):
        self.stack = deque()

    def push(self, pos):
        if not self.stack or self.stack[-1] != pos:
            self.stack.append(pos)

    def pop(self):
        if self.stack:
            return self.stack.pop()
        return None

    def clear(self):
        self.stack.clear()

    def is_empty(self):
        return len(self.stack) == 0

    def as_list(self):
        return list(self.stack)

    def draw_path(self, surface: pygame.Surface):
        pts = self.as_list()
        if len(pts) >= 2:
            pygame.draw.lines(surface, GREY, False, pts, 2)
        for p in pts:
            pygame.draw.circle(surface, GREY, (int(p[0]), int(p[1])), 3)


# ------------------------------------------------------
# GŁÓWNA APLIKACJA
# ------------------------------------------------------
class GameApp:
    def __init__(self, width=WIDTH, height=HEIGHT):
        pygame.init()
        pygame.display.set_caption("Sterowanie PNG - tło i kolory RGB")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20)

        self.width = width
        self.height = height

        # --- wczytaj tło (tlo.jpg) i dopasuj do rozmiaru okna ---
        try:
            bg = pygame.image.load("tlo.jpg").convert()
            self.background = pygame.transform.smoothscale(bg, (self.width, self.height))
        except Exception as e:
            print("Nie udało się wczytać 'tlo.jpg'. Używane będzie jednolite tło. Błąd:", e)
            self.background = None

        # obiekt startowy (możesz podać scale=(w,h) jeśli chcesz zmienić rozmiar)
        self.player = Player(width // 2, height // 2, "dodo.png", scale=(64, 64))
        self.path = PathManager()
        self.path.push(self.player.pos)

        # Playback
        self.playing_back = False
        self.playback_stack = []
        self.playback_delay_frames = 3
        self.playback_frame_counter = 0

    # --- Playback ---
    def start_playback(self):
        if self.playing_back or self.path.is_empty():
            return
        self.playback_stack = list(self.path.as_list())
        self.playing_back = True
        self.playback_frame_counter = 0

    def update_playback(self):
        if not self.playing_back:
            return
        if not self.playback_stack:
            self.playing_back = False
            return

        self.playback_frame_counter += 1
        if self.playback_frame_counter >= self.playback_delay_frames:
            self.playback_frame_counter = 0
            target = self.playback_stack.pop()
            if target:
                self.player.set_pos(*target)

    # --- Events ---
    def handle_events(self, dt):
        keys = pygame.key.get_pressed()
        dx = dy = 0.0

        if not self.playing_back:
            if keys[pygame.K_LEFT]:
                dx -= PLAYER_SPEED * dt
            if keys[pygame.K_RIGHT]:
                dx += PLAYER_SPEED * dt
            if keys[pygame.K_UP]:
                dy -= PLAYER_SPEED * dt
            if keys[pygame.K_DOWN]:
                dy += PLAYER_SPEED * dt

            if dx or dy:
                self.player.move(dx, dy)
                self.player.clamp_to_rect(self.width, self.height)
                self.path.push(self.player.pos)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.quit()
                elif event.key == pygame.K_SPACE:
                    self.start_playback()

                # ZMIANA KOLORU PNG (poprawione tintowanie)
                elif event.key == pygame.K_r:
                    self.player.set_color((255, 0, 0))
                elif event.key == pygame.K_g:
                    self.player.set_color((0, 255, 0))
                elif event.key == pygame.K_b:
                    self.player.set_color((0, 0, 255))

                elif event.key == pygame.K_c:
                    self.path.clear()
                    self.path.push(self.player.pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                self.player.set_pos(mx, my)
                self.player.clamp_to_rect(self.width, self.height)
                self.path.push(self.player.pos)

    # --- HUD ---
    def draw_hud(self):
        lines = [
            "Strzałki - ruch  |  Lewy klik - teleport  |  SPACJA - cofanie trasy",
            "R/G/B - kolor PNG  |  C - wyczysc trase  |  ESC - wyjscie",
            f"Pozycje w stosie: {len(self.path.stack)}",
            f"Playback: {'TAK' if self.playing_back else 'NIE'}",
        ]
        y = 5
        for l in lines:
            surf = self.font.render(l, True, WHITE)
            self.screen.blit(surf, (5, y))
            y += 18

    def quit(self):
        pygame.quit()
        sys.exit(0)

    # --- Main loop ---
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events(dt)
            self.update_playback()

            # rysowanie tła (jeśli wczytane) lub jednolite
            if self.background:
                self.screen.blit(self.background, (0, 0))
            else:
                self.screen.fill(WHITE)

            # rysuj trasę i gracza
            self.path.draw_path(self.screen)
            # WAŻNE: wywołanie zgodne z sygnaturą draw(self, surface)
            self.player.draw(self.screen)
            self.draw_hud()

            pygame.display.flip()


# ------------------------------------------------------
# START
# ------------------------------------------------------
if __name__ == '__main__':
    app = GameApp()
    app.run()
