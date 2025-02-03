import pygame
import random
import time

pygame.init()

# Основные цвета
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)
background_color = (135, 206, 235)  # цвет фона

# Размеры окна
dis_width = 800
dis_height = 600
dis = pygame.display.set_mode((dis_width, dis_height))
pygame.display.set_caption('Змейка')
clock = pygame.time.Clock()

# Размер блока змейки
snake_block = 10
initial_snake_speed = 9

# Шрифт для текста
font_style = pygame.font.SysFont("LucidaConsole", 18)


# Вывод сообщения на экран
def message(msg, color):
    mesg = font_style.render(msg, True, color)
    dis.blit(mesg, [dis_width / 6, dis_height / 3])


# Функция для отображения инструкций с кнопкой "понял продолжить"
def show_controls_message():
    dis.fill(white)
    message("Управление: Стрелки или WASD; P - пауза; Q - выход из игры", black)

    # Отрисовка кнопи под инструкцией
    ok_button_rect = pygame.Rect(dis_width / 2 - 100, dis_height / 2 + 100, 200, 30)
    pygame.draw.rect(dis, background_color, ok_button_rect)

    # Вывод текста для кнопки для закрытия инструкции и начала игры
    ok_text = font_style.render("Понял, продолжить", True, black)
    text_rect = ok_text.get_rect(center=ok_button_rect.center)  # Центрируем текст на кнопке
    dis.blit(ok_text, text_rect)

    pygame.display.update()

    waiting_for_ok = True
    while waiting_for_ok:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button_rect.collidepoint(event.pos):
                    waiting_for_ok = False


# Отрисовка змейки
def draw_snake(snake_block, snake_list):
    for x in snake_list:
        pygame.draw.rect(dis, black, [x[0], x[1], snake_block, snake_block])


# Класс для еды
class Food:
    def __init__(self):
        self.x = round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0
        self.y = round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
        self.type = random.choice(['normal', 'speed', 'slow'])


# Основная логика игры
def gameLoop():
    show_controls_message()  # Показ инструкции при запуске игры

    game_over = False
    game_close = False
    game_paused = False

    # Позиция змейки при старте
    x1 = dis_width / 2
    y1 = dis_height / 2
    x1_change = 0
    y1_change = 0

    # Хранение частей змейки
    snake_List = []
    Length_of_snake = 1

    # Позиция еды при старте
    food_list = [Food()]

    # Время генерации еды
    last_food_generation_time = time.time()

    # Блоки препятствий
    obstacles = []
    for _ in range(10):
        obs_x = round(random.randrange(0, dis_width - snake_block) / 10.0) * 10.0
        obs_y = round(random.randrange(0, dis_height - snake_block) / 10.0) * 10.0
        obstacles.append((obs_x, obs_y))

    # Счётчики
    score = 0
    snake_speed = initial_snake_speed

    # Игровой цикл
    while not game_over:

        while game_close:
            dis.fill(white)
            message("Вы проиграли! Нажмите Q для выхода или C для новой игры", red)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        gameLoop()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    x1_change = -snake_block
                    y1_change = 0
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    x1_change = snake_block
                    y1_change = 0
                elif event.key == pygame.K_UP or event.key == pygame.K_w:
                    y1_change = -snake_block
                    x1_change = 0
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    y1_change = snake_block
                    x1_change = 0

                # Возможность выхода из игры по нажатию Q
                if event.key == pygame.K_q:
                    game_over = True

                if event.key == pygame.K_p:
                    game_paused = not game_paused

        if not game_paused:
            if x1 >= dis_width or x1 < 0 or y1 >= dis_height or y1 < 0:
                game_close = True

            x1 += x1_change
            y1 += y1_change

            dis.fill(background_color)

            # Генерация новой еды каждые 5 секунд
            current_time = time.time()
            if current_time - last_food_generation_time > 5:
                food_list.append(Food())
                last_food_generation_time += 5

            # Отображение еды на экране и проверка на столкновение со змейкой.
            for food in food_list:
                if food.type == 'normal':
                    pygame.draw.rect(dis, green, [food.x, food.y, snake_block, snake_block])
                elif food.type == 'speed':
                    pygame.draw.rect(dis, blue, [food.x, food.y, snake_block, snake_block])
                elif food.type == 'slow':
                    pygame.draw.rect(dis, yellow, [food.x, food.y, snake_block, snake_block])

                # Проверка на столкновение со змеей.
                if x1 == food.x and y1 == food.y:
                    if food.type == 'normal':
                        Length_of_snake += 1
                        score += 10
                    elif food.type == 'speed':
                        snake_speed += 2
                        score += 20
                    elif food.type == 'slow':
                        snake_speed -= 1
                        if snake_speed < 1:
                            snake_speed = 1
                        score += 5

                    food_list.remove(food)  # Удаление съеденной еды

            for obs in obstacles:
                pygame.draw.rect(dis, red, [obs[0], obs[1], snake_block, snake_block])

            snake_Head = []
            snake_Head.append(x1)
            snake_Head.append(y1)
            snake_List.append(snake_Head)

            if len(snake_List) > Length_of_snake:
                del snake_List[0]

            for x in snake_List[:-1]:
                if x == snake_Head:
                    game_close = True

            for obs in obstacles:
                if x1 == obs[0] and y1 == obs[1]:
                    game_close = True

            draw_snake(snake_block, snake_List)

            score_text = font_style.render(f"Счет: {score}, Длина: {Length_of_snake}", True, black)
            dis.blit(score_text, [10, 10])

        else:
            message("Игра на паузе! Нажмите P для продолжения", yellow)

        pygame.display.update()
        clock.tick(snake_speed)

    pygame.quit()
    quit()


gameLoop()
