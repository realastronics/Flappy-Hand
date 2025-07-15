import cv2
import mediapipe as mp
import pygame
import sys
import threading
import time
import config 

# Jump Detector Class using finger motion
class HandDetector:
    def __init__(self, detection_confidence=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=detection_confidence
        )
        self.cap = cv2.VideoCapture(0)
        self.fist_closed = False
        self.running = True

    def start(self):
        threading.Thread(target=self._capture, daemon=True).start()

    def _capture(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            self.fist_closed = False

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    index_tip = hand_landmarks.landmark[8]
                    thumb_tip = hand_landmarks.landmark[4]

                    h, w, _ = frame.shape
                    index_x, index_y = int(index_tip.x * w), int(index_tip.y * h)
                    thumb_x, thumb_y = int(thumb_tip.x * w), int(thumb_tip.y * h)

                    distance = ((index_x - thumb_x)**2 + (index_y - thumb_y)**2) ** 0.5
                    if distance < 50:  # Less strict threshold
                        self.fist_closed = True

            # Show window for debug; comment out for faster detection
            cv2.imshow("Hand Detection - Press ESC to Quit", frame)
            if cv2.waitKey(1) & 0xFF == 27:
                self.running = False
                break

        self.cap.release()
        cv2.destroyAllWindows()


# Game Constants are to be taken from conig ;)

# Main Game Function
def run_game(detector):
    pygame.init()
    screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 32)
# Load ACM Logo
    import os 
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))  # This script's folder
        logo_path = os.path.join(script_dir, "acm_logo.png")     # Path inside same folder

        logo_image = pygame.image.load(logo_path).convert_alpha()
        logo_image = pygame.transform.scale(logo_image, (150, 150))
        logo_image.set_alpha(120)  # More visible
        print("Logo image loaded successfully from:", logo_path)
    except Exception as e:
        print("Error loading ACM logo:", e)
        logo_image = None

    bird_y = config.HEIGHT // 2
    bird_vel = 0
    score = 0

    pipes = [{'x': config.WIDTH + 100, 'height': 200}]
    pipe_speed = config.PIPE_SPEED

    running = True
    game_started = False
    game_over = False

    while running and detector.running:
        # Handle events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
                detector.running = False

        # Intro screen
        if not game_started:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    game_started = True
                    start_time = time.time()

            screen.fill((50,50,50))
            if logo_image:
                screen.blit(logo_image, (config.WIDTH//2 - logo_image.get_width()//2, config.HEIGHT//3 - 80))
            title = font.render("Flappy Bird Hand Control", True, (255,255,255))
            prompt = small_font.render("Press Space to Start", True, (200,200,200))
            screen.blit(title, (config.WIDTH//2 - title.get_width()//2, config.HEIGHT//2))
            screen.blit(prompt, (config.WIDTH//2 - prompt.get_width()//2, config.HEIGHT//2 + 40))
            pygame.display.flip()
            clock.tick(60)
            continue

        # Countdown before starting
        if time.time() - start_time < 3 and not game_over:
            screen.fill((50,50,50))
            countdown = font.render(f"Starting in {3 - int(time.time()-start_time)}", True, (255,255,255))
            screen.blit(countdown, (config.WIDTH//2 - countdown.get_width()//2, config.HEIGHT//2))
            pygame.display.flip()
            clock.tick(60)
            continue

        # If game over
        if game_over:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                    # Reset game state
                    bird_y = config.HEIGHT // 2
                    bird_vel = 0
                    score = 0
                    pipes = [{'x': config.WIDTH + 100, 'height': 200}]
                    game_over = False
                    # Skip countdown
                    start_time = time.time() - 3

            screen.fill((50,50,50))
            over_text = font.render("Game Over", True, (200,0,0))
            score_text = small_font.render(f"Score: {score//30}", True, (255,255,255))
            prompt = small_font.render("Press Space to Restart", True, (200,200,200))
            screen.blit(over_text, (config.WIDTH//2 - over_text.get_width()//2, config.HEIGHT//3))
            screen.blit(score_text, (config.WIDTH//2 - score_text.get_width()//2, config.HEIGHT//2))
            screen.blit(prompt, (config.WIDTH//2 - prompt.get_width()//2, config.HEIGHT//2 + 40))
            pygame.display.flip()
            clock.tick(60)
            continue

        # Bird physics
        bird_vel += config.GRAVITY
        bird_y += bird_vel

        if detector.fist_closed:
            bird_vel = config.JUMP_STRENGTH

        # Move pipes
        for pipe in pipes:
            pipe['x'] -= pipe_speed

        # Add new pipes
        if pipes[-1]['x'] < config.WIDTH - 200:
            from random import randint
            pipes.append({'x': config.WIDTH, 'height': randint(100, 400)})

        # Remove off-screen pipes
        pipes = [pipe for pipe in pipes if pipe['x'] > -config.PIPE_WIDTH]

        # Collision detection
        for pipe in pipes:
            if pipe['x'] < 50 < pipe['x'] + config.PIPE_WIDTH:
                if bird_y < pipe['height'] or bird_y > pipe['height'] + config.PIPE_GAP:
                    game_over = True

        if bird_y > config.HEIGHT or bird_y < 0:
            game_over = True

        # Draw everything
        screen.fill((50,50,50))

        if logo_image:
            screen.blit(logo_image, (config.WIDTH - logo_image.get_width() - 10, config.HEIGHT - logo_image.get_height() -10))

        for pipe in pipes:
            pygame.draw.rect(screen, (102,0,153), (pipe['x'], 0, config.PIPE_WIDTH, pipe['height']))
            pygame.draw.rect(screen, (153,50,204), (pipe['x'], pipe['height'] + config.PIPE_GAP, config.PIPE_WIDTH, config.HEIGHT))

        pygame.draw.circle(screen, (255,255,0), (50, int(bird_y)), 15)

        score += 1
        score_text = font.render(str(score//30), True, (255,255,255))
        screen.blit(score_text, (config.WIDTH//2 - score_text.get_width()//2, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


# Main Entry
if __name__ == "__main__":
    detector = HandDetector()
    detector.start()
    run_game(detector)
