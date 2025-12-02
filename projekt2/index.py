"""
Prosty program w Pygame: sterowanie obiektem klawiaturą i myszką, rejestracja trasy na stosie,
odtwarzanie trasy, zmiana koloru, rysowanie trasy, bez wychodzenia poza okno.
Plik: pygame_path_controller.py
Uruchomienie: python pygame_path_controller.py
Wymagania: pygame (pip install pygame)

Klasy:
 - Player: obiekt poruszany
 - PathManager: zarządza stosem pozycji i rysowaniem trasy
 - GameApp: główna aplikacja (obsługa pętli, eventów, rysowania)

Kontrolki:
 - strzałki: ruch
 - kliknięcie myszy: przeniesienie obiektu do kliknięcia
 - SPACJA: odtwarzanie trasy (cofanie po zapamiętanych pozycjach)
 - R/G/B: zmiana koloru obiektu
 - ESC lub zamknięcie okna: wyjście

"""
import sys
import pygame
from collections import deque

# --- Ustawienia ---
WIDTH, HEIGHT = 800, 600
FPS = 60
PLAYER_RADIUS = 12
PLAYER_SPEED = 200  # px/s

# Kolory
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 100, 255)
GREY = (200, 200, 200)


class Player:
    """Reprezentuje obiekt poruszany na ekranie."""

    def __init__(self, x: float, y: float, image_path="dodo.png"):
        self.x = float(x)
        self.y = float(y)

        # --- wczytanie obrazka ---
        self.image = pygame.image.load(image_path).convert_alpha()

        # opcjonalne skalowanie:
        # self.image = pygame.transform.scale(self.image, (40, 40))

        # zapamiętujemy wymiar (do centrowania)
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))

    @property
    def pos(self):
        return (int(self.x), int(self.y))

    def set_pos(self, x: float, y: float):
        self.x = float(x)
        self.y = float(y)
        self.rect.center = (int(self.x), int(self.y))

    def move(self, dx: float, dy: float):
        self.x += dx
        self.y += dy
        self.rect.center = (int(self.x), int(self.y))

    def clamp_to_rect(self, w: int, h: int):
        self.rect.clamp_ip(pygame.Rect(0, 0, w, h))
        self.x, self.y = self.rect.center

    def draw(self, surface: pygame.Surface):
        surface.blit(self.image, self.rect)


class PathManager:
    """Zarządza stosem pozycji (lista używana jako stos) oraz rysowaniem trasy."""

    def __init__(self):
        # używamy deque, ale operujemy na nim jak na stosie (append/pop)
        self.stack = deque()

    def push(self, pos):
        # pos: tuple(x,y)
        # Ochrona: zapisujemy tylko jeśli stos jest pusty albo pozycja różni się
        if not self.stack or self.stack[-1] != pos:
            self.stack.append(pos)

    def pop(self):
        if self.stack:
            return self.stack.pop()
        return None

    def peek(self):
        if self.stack:
            return self.stack[-1]
        return None

    def clear(self):
        self.stack.clear()

    def is_empty(self):
        return len(self.stack) == 0

    def as_list(self):
        # Zwraca listę pozycji od najstarszej do najnowszej
        return list(self.stack)

    def draw_path(self, surface: pygame.Surface):
        pts = self.as_list()
        if len(pts) >= 2:
            pygame.draw.lines(surface, GREY, False, pts, 2)
        # dodatkowo narysujemy małe kropki
        for p in pts:
            pygame.draw.circle(surface, GREY, (int(p[0]), int(p[1])), 3)


class GameApp:
    """Główna aplikacja obsługująca pętlę gry."""

    def __init__(self, width=WIDTH, height=HEIGHT):
        pygame.init()
        pygame.display.set_caption("Sterowanie obiektem - Pygame (z trasą i GIT)")
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 20)

        self.width = width
        self.height = height

        # obiekt startowy na środku
        self.player = Player(width // 2, height // 2, "dodo.png")
        self.path = PathManager()
        # zapisujemy pozycję startową
        self.path.push(self.player.pos)

        # Playback
        self.playing_back = False
        self.playback_stack = []  # do animacji odtwarzania
        self.playback_delay_frames = 3  # ile fps między krokami odtwarzania
        self.playback_frame_counter = 0

        # zabezpieczenia: timer dla zdarzeń myszy itp.
        self.safe = True

    def start_playback(self):
        if self.playing_back:
            return
        if self.path.is_empty():
            return
        # Stworzymy kopię stosu i będziemy z niej popować (od najnowszej do najstarszej)
        self.playback_stack = list(self.path.as_list())
        # Jeśli chcemy "cofanie", zaczniemy od końca
        self.playing_back = True
        self.playback_frame_counter = 0

    def update_playback(self):
        if not self.playing_back:
            return
        # Jeśli pusta -- zakończ
        if not self.playback_stack:
            self.playing_back = False
            return
        # co kilka klatek przechodzimy do kolejnej pozycji
        self.playback_frame_counter += 1
        if self.playback_frame_counter >= self.playback_delay_frames:
            self.playback_frame_counter = 0
            # pobierz ostatni element (najbliższy w stosie)
            target = self.playback_stack.pop()
            if target:
                # ustaw pozycję bezpośrednio - to tworzy efekt "skoków" cofania
                self.player.set_pos(*target)
                # nie usuwamy tego z głównego stosu automatycznie (można opcjonalnie)

    def handle_events(self, dt):
        # dt w sekundach
        keys = pygame.key.get_pressed()

        move_dx = 0.0
        move_dy = 0.0

        if not self.playing_back:
            # ruch klawiaturą
            if keys[pygame.K_LEFT]:
                move_dx -= PLAYER_SPEED * dt
            if keys[pygame.K_RIGHT]:
                move_dx += PLAYER_SPEED * dt
            if keys[pygame.K_UP]:
                move_dy -= PLAYER_SPEED * dt
            if keys[pygame.K_DOWN]:
                move_dy += PLAYER_SPEED * dt

            if move_dx != 0 or move_dy != 0:
                self.player.move(move_dx, move_dy)
                self.player.clamp_to_rect(self.width, self.height)
                self.path.push(self.player.pos)

        # obsługa zdarzeń (mysz, klawisze jednorazowe)
        for event in pygame.event.get():
            try:
                if event.type == pygame.QUIT:
                    self.quit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.quit()
                    elif event.key == pygame.K_SPACE:
                        # rozpocznij odtwarzanie trasy
                        self.start_playback()
                    elif event.key == pygame.K_r:
                        self.player.color = RED
                    elif event.key == pygame.K_g:
                        self.player.color = GREEN
                    elif event.key == pygame.K_b:
                        self.player.color = BLUE
                    elif event.key == pygame.K_c:
                        # pomocnicze: wyczyść trase (bez usuwania pozycji aktualnej)
                        self.path.clear()
                        self.path.push(self.player.pos)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # lewy przycisk
                        mx, my = event.pos
                        # przenieś obiekt natychmiast i zapisz pozycję
                        self.player.set_pos(mx, my)
                        self.player.clamp_to_rect(self.width, self.height)
                        self.path.push(self.player.pos)
            except Exception as e:
                # Bardzo ogólne zabezpieczenie przed crash
                print("Błąd podczas obsługi zdarzenia:", e)

    def draw_hud(self):
        lines = [
            "Sterowanie: strzałki - ruch | klik lewym - teleport | SPACJA - odtwarzanie trasy",
            "R/G/B - kolor | ESC - wyjscie | C - wyczysc trase (pomocnicze)",
            f"Pozycji w stosie: {len(self.path.stack)}",
            f"Tryb odtwarzania: {'TAK' if self.playing_back else 'NIE'}",
        ]
        y = 5
        for l in lines:
            surf = self.font.render(l, True, BLACK)
            self.screen.blit(surf, (5, y))
            y += 18

    def quit(self):
        pygame.quit()
        sys.exit(0)

    def run(self):
        try:
            while True:
                dt = self.clock.tick(FPS) / 1000.0  # sekundy
                # handle events + ruch klawiatury
                self.handle_events(dt)
                # playback (jeśli aktywne)
                self.update_playback()

                # rysowanie
                self.screen.fill(WHITE)
                # rysuj trase (pod spodem)
                self.path.draw_path(self.screen)
                # rysuj gracza
                self.player.draw(self.screen)
                # HUD
                self.draw_hud()

                pygame.display.flip()
        except SystemExit:
            raise
        except Exception as e:
            # Zabezpieczenie przed nieoczekiwanym crashem: zamknij pygame i wypisz info
            print("Wystąpił nieobsłużony błąd:", e)
            try:
                pygame.quit()
            except Exception:
                pass


if __name__ == '__main__':
    app = GameApp()
    app.run()