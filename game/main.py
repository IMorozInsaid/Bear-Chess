import pygame
from pygame import *
import math
import sys
import asyncio
import random
import pyjs  # Для JS в pygbag, если не работает - удалите и используйте только оффлайн

try:
    import android
except ImportError:
    android = None

pygame.init()
pygame.mixer.init()
move_sound = pygame.mixer.Sound('move.wav')
capture_sound = pygame.mixer.Sound('capture.wav')

if android:
    android.init()
    android.map_key(android.KEYCODE_BACK, pygame.K_ESCAPE)

is_mobile = android is not None

if is_mobile:
    wind = display.set_mode((0, 0), FULLSCREEN)
    screen_width, screen_height = wind.get_size()
    menu_height = 60
    cell_size = min(screen_width // 10, (screen_height - menu_height) // 10)
    board_size = cell_size * 10
    board_x = (screen_width - board_size) // 2
    board_y = 0
    menu_y = board_y + board_size
    button_width = (board_size - 3 * (cell_size // 8)) // 4
    button_height = menu_height - 10
    button_spacing = cell_size // 8
    piece_size = int(cell_size * 0.875)
    small_size = int(cell_size * 0.375)
    font_size = int(cell_size / 2.5)
    circle_radius = cell_size // 8
    promo_spacing = cell_size + 10
    surrender_rect = pygame.Rect(board_x + 3 * (button_width + button_spacing), menu_y, button_width, button_height)
    restart_rect = pygame.Rect(board_x + 2 * (button_width + button_spacing), menu_y, button_width, button_height)
    start_rect = pygame.Rect(board_x + button_width + button_spacing, menu_y, button_width, button_height)
    sound_rect = pygame.Rect(board_x, menu_y, button_width, button_height)
    captured_y = menu_y + (menu_height - small_size) // 2
    small_spacing = small_size + (cell_size // 20)
    captured_left_x = 10
    # Для лобби на мобильных
    lobby_local_rect = pygame.Rect(board_x + board_size // 4, board_y + board_size // 2 - button_height * 2, board_size // 2, button_height)
    lobby_bot_rect = pygame.Rect(board_x + board_size // 4, board_y + board_size // 2 - button_height // 2, board_size // 2, button_height)
    lobby_online_rect = pygame.Rect(board_x + board_size // 4, board_y + board_size // 2 + button_height, board_size // 2, button_height)
else:
    board_x = 200
    wind = display.set_mode((1400, 800))
    display.set_caption('Bear Chess')
    cell_size = 80
    board_size = 800
    board_y = 0
    piece_size = 70
    small_size = 30
    font_size = 35
    circle_radius = 10
    promo_spacing = 100
    surrender_rect = pygame.Rect(1120, 700, 200, 50)
    restart_rect = pygame.Rect(1120, 600, 200, 50)
    start_rect = pygame.Rect(1120, 500, 200, 50)
    sound_rect = pygame.Rect(1120, 400, 200, 50)
    captured_left_x = 10  # Для captured white
    captured_bottom_y = 750  # Для captured black
    captured_top_y = 10
    # Для лобби на ПК, центрировано
    lobby_local_rect = pygame.Rect(600, 300, 200, 50)
    lobby_bot_rect = pygame.Rect(600, 360, 200, 50)
    lobby_online_rect = pygame.Rect(600, 420, 200, 50)

clock = time.Clock()

RectList = []
for i in range(10):
    for n in range(5):
        RectList.append(pygame.Rect((n * cell_size * 2 + (i % 2) * cell_size, i * cell_size, cell_size, cell_size)))


def DrawBg(surf):
    pygame.draw.rect(surf, (181, 136, 99), (0, 0, board_size, board_size))
    for R in RectList:
        pygame.draw.rect(surf, (240, 217, 181), R)


Board = [['.' for _ in range(10)] for _ in range(10)]
Board[0] = ['R1', 'N1', 'B1', 'M1', 'Q1', 'K1', 'M1', 'B1', 'N1', 'R1']
Board[1] = ['P1'] * 10
Board[8] = ['P0'] * 10
Board[9] = ['R0', 'N0', 'B0', 'M0', 'Q0', 'K0', 'M0', 'B0', 'N0', 'R0']

AttackDict = {
    'R': [[0, 1], [1, 0], [0, -1], [-1, 0], 1],
    'B': [[1, 1], [-1, -1], [1, -1], [-1, 1], 1],
    'Q': [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [1, 0], [0, -1], [-1, 0], 1],
    'N': [[1, 2], [2, 1], [-1, -2], [-2, -1], [-1, 2], [-2, 1], [1, -2], [2, -1], 0],
    'K': [[1, 1], [-1, -1], [1, -1], [-1, 1], [0, 1], [1, 0], [0, -1], [-1, 0], 0],
    'M': [[1, 2], [2, 1], [-1, -2], [-2, -1], [-1, 2], [-2, 1], [1, -2], [2, -1], [0, 2], [0, -2], [2, 0], [-2, 0],
          [2, 2], [2, -2], [-2, 2], [-2, -2], 0]
}


def get_piece_image(piece):
    if piece != '.':
        color = 'w' if piece[1] == '0' else 'b'
        ptype = piece[0]
        if ptype == 'M':
            img_name = color + 'Bear.png'
        else:
            img_name = color + ptype.lower() + '.png'
        img = transform.scale(pygame.image.load(img_name), (piece_size, piece_size))
        return img
    return None


def get_small_piece_image(piece):
    if piece != '.':
        color = 'w' if piece[1] == '0' else 'b'
        ptype = piece[0]
        if ptype == 'M':
            img_name = color + 'Bear.png'
        else:
            img_name = color + ptype.lower() + '.png'
        img = transform.scale(pygame.image.load(img_name), (small_size, small_size))
        return img
    return None


def DrawPieces(surf):
    if flip_view:
        board_rows = reversed(Board)
    else:
        board_rows = Board
    y = 0
    for row in board_rows:
        x = 0
        for piece in row:
            img = get_piece_image(piece)
            if img:
                surf.blit(img, ((cell_size - piece_size) // 2 + x * cell_size,
                                (cell_size - piece_size) // 2 + y * cell_size))
            x += 1
        y += 1


def CheckShah(B_W):
    for y in range(10):
        for x in range(10):
            B = Board[y][x]
            if B != '.' and B[1] != B_W:
                if B[0] == 'P':
                    dir = 1 if B[1] == '1' else -1
                    shifts = [[-1, dir], [1, dir]]
                    long_range = 0
                else:
                    shifts = AttackDict[B[0]][:-1]
                    long_range = AttackDict[B[0]][-1]
                for shift in shifts:
                    pos_x = x
                    pos_y = y
                    while True:
                        pos_x += shift[0]
                        pos_y += shift[1]
                        if not (0 <= pos_x < 10 and 0 <= pos_y < 10):
                            break
                        if Board[pos_y][pos_x] != '.':
                            if Board[pos_y][pos_x] == 'K' + B_W:
                                return True
                            break
                        if not long_range:
                            break

    return False


Variants = []


def ShowVariants(x, y):
    global Variants
    Variants = []
    B = Board[y][x]
    if B == '.':
        return
    if B[0] == 'P':
        dir = 1 if B[1] == '1' else -1
        shifts = [[-1, dir], [1, dir]]
        long_range = 0
        pos_x = x
        pos_y = y
        start_row = 1 if B[1] == '1' else 8
        steps = 3 if y == start_row else 1
        for i in range(1, steps + 1):
            ny = pos_y + i * dir
            if not (0 <= ny < 10) or Board[ny][pos_x] != '.':
                break
            Variants.append([pos_x, ny])
        for shift in shifts:
            pos_x = x + shift[0]
            pos_y = y + shift[1]
            if 0 <= pos_x < 10 and 0 <= pos_y < 10:
                target = Board[pos_y][pos_x]
                if target != '.' and target[1] != B[1]:
                    Variants.append([pos_x, pos_y])
        for dx in [-1, 1]:
            nx = x + dx
            ny = y + dir
            if 0 <= nx < 10 and 0 <= ny < 10 and Board[ny][nx] == '.':
                for entry in en_passant:
                    if entry[0] == nx and entry[1] == ny:
                        Variants.append([nx, ny])
                        break
    else:
        shifts = AttackDict[B[0]][:-1]
        long_range = AttackDict[B[0]][-1]
        for shift in shifts:
            pos_x = x
            pos_y = y
            for _ in range(9 if long_range else 1):
                pos_x += shift[0]
                pos_y += shift[1]
                if not (0 <= pos_x < 10 and 0 <= pos_y < 10):
                    break
                target = Board[pos_y][pos_x]
                if target == '.':
                    Variants.append([pos_x, pos_y])
                else:
                    if target[1] != B[1]:
                        Variants.append([pos_x, pos_y])
                    if long_range:
                        break

    if B[0] == 'K' and not CheckShah(B[1]):
        if castlingL[int(B[1])]:
            path_free = all(Board[y][k] == '.' for k in range(1, 5))
            if path_free:
                safe = True
                Board[y][x] = '.'
                for pos in [2, 3, 4]:
                    Board[y][pos] = B
                    if CheckShah(B[1]):
                        safe = False
                    Board[y][pos] = '.'
                    if not safe:
                        break
                Board[y][x] = B
                if safe:
                    Variants.append([2, y])
        if castlingR[int(B[1])]:
            path_free = all(Board[y][k] == '.' for k in range(6, 9))
            if path_free:
                safe = True
                Board[y][x] = '.'
                for pos in [6, 7]:
                    Board[y][pos] = B
                    if CheckShah(B[1]):
                        safe = False
                    Board[y][pos] = '.'
                    if not safe:
                        break
                Board[y][x] = B
                if safe:
                    Variants.append([7, y])

    ForDeletion = []
    remember = Board[y][x]
    Board[y][x] = '.'
    for v in Variants:
        remember_target = Board[v[1]][v[0]]
        Board[v[1]][v[0]] = B
        if CheckShah(B[1]):
            ForDeletion.append(v)
        Board[v[1]][v[0]] = remember_target
    Board[y][x] = remember
    for del_v in ForDeletion:
        if del_v in Variants:
            Variants.remove(del_v)


def CheckCheckMate(B_W):
    for y in range(10):
        for x in range(10):
            if Board[y][x] != '.' and Board[y][x][1] == B_W:
                ShowVariants(x, y)
                if Variants:
                    return 0
    if CheckShah(B_W):
        return 1
    return 2


castlingL = [True, True]
castlingR = [True, True]

en_passant = []

Turn = 0
promotion = None
selected = None
promotion_choices = ['Q', 'R', 'B', 'N', 'M']
check = 0
animating_move = False
move_start = None
move_end = None
move_piece = None
move_progress = 0
animating_capture = False
capture_pos = None
capture_piece = None
capture_progress = 0
pending_turn_switch = False
captured_white = []
captured_black = []
moves = []
sound_on = True
started = False
game_over = False
winner_message = None
in_lobby = True # Новый флаг для лобби
game_mode = None # 'local' , 'bot' или 'online'
player_color = None # Цвет игрока в режиме bot или online: 0 - белые, 1 - черные
flip_view = False # Флаг для переворота доски
input_mode = False
input_ip = ''
waiting_connection = False
ip = ''
conn = None
host = False
def col_to_letter(col):
    return chr(97 + col)
# Функция для получения всех возможных ходов для текущего Turn
def get_all_possible_moves(turn):
    all_moves = []
    for y in range(10):
        for x in range(10):
            if Board[y][x] != '.' and Board[y][x][1] == str(turn):
                ShowVariants(x, y)
                for v in Variants:
                    all_moves.append(((x, y), (v[0], v[1])))
    return all_moves
# Функция для выполнения хода (для бота и игрока)
def perform_move(from_pos, to_pos):
    global animating_move, move_start, move_end, move_piece, move_progress, animating_capture, capture_pos, capture_piece, capture_progress, en_passant, promotion, pending_turn_switch, captured_white, captured_black, moves, castlingL, castlingR
    cx, cy = to_pos
    sx, sy = from_pos
    remember_target = Board[cy][cx]
    is_capture = remember_target != '.'
    if remember_target != '.':
        animating_capture = True
        capture_pos = (cx, cy)
        capture_piece = remember_target
        capture_progress = 0
        if Turn == 0:
            captured_black.append(remember_target)
        else:
            captured_white.append(remember_target)
    move_start = from_pos
    move_end = to_pos
    move_piece = Board[sy][sx]
    Board[sy][sx] = '.'
    animating_move = True
    move_progress = 0
    from_col = col_to_letter(sx)
    from_row = 10 - sy
    to_col = col_to_letter(cx)
    to_row = 10 - cy
    moves.append(f"{move_piece[0]}{from_col}{from_row}{to_col}{to_row}")
    moves = moves[-10:]
    if move_piece[0] == 'P' and remember_target == '.' and abs(cx - sx) == 1:
        for entry in en_passant:
            if entry[0] == cx and entry[1] == cy:
                Board[entry[3]][entry[2]] = '.'
                is_capture = True
                capture_piece_en = 'P' + str(1 - Turn)
                animating_capture = True
                capture_pos = (entry[2], entry[3])
                capture_progress = 0
                if Turn == 0:
                    captured_black.append(capture_piece_en)
                else:
                    captured_white.append(capture_piece_en)
                break
    if is_capture and sound_on:
        capture_sound.play()
    else:
        if sound_on:
            move_sound.play()
    if move_piece[0] == 'K':
        if cx == 2:
            rook = Board[sy][0]
            Board[sy][3] = rook
            Board[sy][0] = '.'
        elif cx == 7:
            rook = Board[sy][9]
            Board[sy][6] = rook
            Board[sy][9] = '.'
        castlingL[Turn] = False
        castlingR[Turn] = False
    if move_piece[0] == 'K':
        castlingL[Turn] = False
        castlingR[Turn] = False
    if move_piece[0] == 'R':
        if sx == 0:
            castlingL[Turn] = False
        elif sx == 9:
            castlingR[Turn] = False
    if move_piece[0] == 'P' and abs(cy - sy) > 1:
        dir = 1 if move_piece[1] == '1' else -1
        steps = abs(cy - sy)
        en_passant = [(cx, sy + i * dir, cx, cy) for i in range(1, steps)]
    else:
        en_passant = []
    if move_piece[0] == 'P' and ((move_piece[1] == '0' and cy == 0) or (move_piece[1] == '1' and cy == 9)):
        promotion = (cx, cy, move_piece[1])
    else:
        pending_turn_switch = True
async def main():
    global Turn, promotion, selected, game, check, animating_move, move_start, move_end, move_piece, move_progress, animating_capture, capture_pos, capture_piece, capture_progress, pending_turn_switch, captured_white, captured_black, moves, sound_on, started, game_over, winner_message, in_lobby, game_mode, player_color, flip_view, input_mode, input_ip, waiting_connection, ip, conn, host
    game = True
    while game:
        if is_mobile and android:
            if android.check_pause():
                android.wait_for_resume()
        for e in event.get():
            if e.type == QUIT:
                game = False
            if e.type == KEYDOWN:
                if input_mode:
                    if e.key == K_BACKSPACE:
                        input_ip = input_ip[:-1]
                    elif e.key == K_RETURN:
                        input_mode = False
                    else:
                        input_ip += e.unicode
            if e.type == MOUSEBUTTONUP and e.button == 1:
                mx, my = e.pos
                if in_lobby:
                    if lobby_local_rect.collidepoint(mx, my):
                        game_mode = 'local'
                        player_color = None # Не нужно для local
                        flip_view = False
                        in_lobby = False
                        started = True
                    elif lobby_bot_rect.collidepoint(mx, my):
                        game_mode = 'bot'
                        player_color = random.choice([0, 1])
                        flip_view = (player_color == 1)
                        in_lobby = False
                        started = True
                    elif lobby_online_rect.collidepoint(mx, my):
                        game_mode = 'online'
                        player_color = random.choice([0, 1])
                        flip_view = (player_color == 1)
                        host = player_color == 0
                        if host:
                            # Для host - создайте комнату на сервере через WS
                            try:
                                ws = pyjs.js.WebSocket('wss://2dc91583-3517-478c-890b-2a8859db2ca5-00-279ww8v7879bc.kirk.replit.dev/')
                                ws.onopen = lambda: ws.send('create_room') # Отправьте команду на сервер
                                ws.onmessage = lambda evt: print('Room: ' + evt.data) # Обработайте ответ
                            except:
                                winner_message = 'Connection failed'
                        else:
                            input_mode = True # Для join - ввод кода комнаты
                        in_lobby = False
                        started = True
                else:
                    # Button handling always available
                    if surrender_rect.collidepoint(mx, my):
                        game_over = True
                        if game_mode == 'online':
                            try:
                                ws = pyjs.js.WebSocket('wss://2dc91583-3517-478c-890b-2a8859db2ca5-00-279ww8v7879bc.kirk.replit.dev/')
                                ws.onopen = lambda: ws.send('surrender')
                            except:
                                winner_message = 'Connection failed'
                        else:
                            if Turn == 0:
                                winner_message = 'Black wins!'
                            else:
                                winner_message = 'White wins!'
                    elif restart_rect.collidepoint(mx, my):
                        # Restart
                        Board[:] = [['.' for _ in range(10)] for _ in range(10)]
                        Board[0] = ['R1', 'N1', 'B1', 'M1', 'Q1', 'K1', 'M1', 'B1', 'N1', 'R1']
                        Board[1] = ['P1'] * 10
                        Board[8] = ['P0'] * 10
                        Board[9] = ['R0', 'N0', 'B0', 'M0', 'Q0', 'K0', 'M0', 'B0', 'N0', 'R0']
                        Turn = 0
                        selected = None
                        promotion = None
                        captured_white = []
                        captured_black = []
                        moves = []
                        en_passant = []
                        castlingL = [True, True]
                        castlingR = [True, True]
                        check = 0
                        game_over = False
                        winner_message = None
                        started = True
                        in_lobby = True # Возврат в лобби при рестарте
                        game_mode = None
                        player_color = None
                        flip_view = False
                        input_mode = False
                        waiting_connection = False
                        if conn:
                            conn.close()
                            conn = None
                    elif sound_rect.collidepoint(mx, my):
                        sound_on = not sound_on
                    if not animating_move and not animating_capture and not input_mode and not waiting_connection:
                        board_left = board_x if is_mobile else board_x
                        board_top = board_y
                        if board_left <= mx < board_left + board_size and board_top <= my < board_top + board_size and started and not game_over:
                            cx = math.floor((mx - board_left) / cell_size)
                            cy = math.floor((my - board_top) / cell_size)
                            if flip_view:
                                cy = 9 - cy
                            if 0 <= cx < 10 and 0 <= cy < 10:
                                if promotion is None and (game_mode == 'local' or Turn == player_color):
                                    if selected is None:
                                        if Board[cy][cx] != '.' and Board[cy][cx][1] == str(Turn):
                                            ShowVariants(cx, cy)
                                            selected = (cx, cy)
                                    else:
                                        if [cx, cy] in Variants:
                                            perform_move(selected, (cx, cy))
                                            if game_mode == 'online':
                                                ws.send(f"{selected[0]} {selected[1]} {cx} {cy}")
                                            selected = None
                                        elif Board[cy][cx] != '.' and Board[cy][cx][1] == str(Turn):
                                            ShowVariants(cx, cy)
                                            selected = (cx, cy)
                                        else:
                                            selected = None
                if promotion is not None and (game_mode == 'local' or Turn == player_color):
                    px, py, color = promotion
                    if is_mobile:
                        promo_x = cell_size // 2
                        promo_y = board_size // 2 - (cell_size * 2) // 2
                    else:
                        promo_x = 200
                        promo_y = 360
                    for i, choice in enumerate(promotion_choices):
                        rect = pygame.Rect(board_x + promo_x + i * promo_spacing, promo_y, cell_size, cell_size)
                        if rect.collidepoint(mx, my):
                            Board[py][px] = choice + color
                            promotion = None
                            pending_turn_switch = True
                            if game_mode == 'online':
                                ws.send(choice)
                            break
        if animating_move:
            move_progress += 0.1
            if move_progress >= 1:
                Board[move_end[1]][move_end[0]] = move_piece
                animating_move = False
        if animating_capture:
            capture_progress += 0.1
            if capture_progress >= 1:
                animating_capture = False
        if not animating_move and not animating_capture and pending_turn_switch:
            pending_turn_switch = False
            Turn = 1 - Turn
            check = CheckCheckMate(str(Turn))
            if check == 1:
                game_over = True
                winner_message = "White wins!" if Turn == 1 else "Black wins!"
            elif check == 2:
                game_over = True
                winner_message = 'STALEMATE!'
        # Логика бота
        if game_mode == 'bot' and Turn != player_color and not animating_move and not animating_capture and not pending_turn_switch and not game_over and started and promotion is None:
            possible_moves = get_all_possible_moves(Turn)
            if possible_moves:
                from_pos, to_pos = random.choice(possible_moves)
                perform_move(from_pos, to_pos)
        # Логика онлайн
        if game_mode == 'online' and Turn != player_color and not animating_move and not animating_capture and not pending_turn_switch and not game_over and started and promotion is None:
            # Получайте сообщения от WS
            # ws.onmessage = lambda evt: perform_move_from_data(evt.data)  # Адаптируйте
            await asyncio.sleep(0)  # Для WASM
        # Обработка промоушена для бота
        if promotion is not None and game_mode == 'bot' and Turn != player_color:
            px, py, color = promotion
            choice = random.choice(promotion_choices)
            Board[py][px] = choice + color
            promotion = None
            pending_turn_switch = True
        # Обработка промоушена для онлайн
        if promotion is not None and game_mode == 'online' and Turn != player_color:
            # Ждите выбора от WS
            await asyncio.sleep(0)
        wind.fill((128, 128, 128))
        if in_lobby:
            # Рисуем лобби
            font = pygame.font.SysFont(None, font_size)
            pygame.draw.rect(wind, (200, 200, 200), lobby_local_rect)
            local_text = font.render('Play Local', True, (0, 0, 0))
            wind.blit(local_text, (lobby_local_rect.centerx - local_text.get_width() // 2, lobby_local_rect.centery - local_text.get_height() // 2))
            pygame.draw.rect(wind, (200, 200, 200), lobby_bot_rect)
            bot_text = font.render('Play vs Bot', True, (0, 0, 0))
            wind.blit(bot_text, (lobby_bot_rect.centerx - bot_text.get_width() // 2, lobby_bot_rect.centery - bot_text.get_height() // 2))
            pygame.draw.rect(wind, (200, 200, 200), lobby_online_rect)
            online_text = font.render('Play Online', True, (0, 0, 0))
            wind.blit(online_text, (lobby_online_rect.centerx - online_text.get_width() // 2, lobby_online_rect.centery - online_text.get_height() // 2))
        else:
            board_surf = Surface((board_size, board_size))
            DrawBg(board_surf)
            DrawPieces(board_surf)
            if selected is not None:
                for v in Variants:
                    v_draw = (9 - v[1]) if flip_view else v[1]
                    pygame.draw.circle(board_surf, (0, 255, 0),
                                       (v[0] * cell_size + cell_size // 2, v_draw * cell_size + cell_size // 2),
                                       circle_radius)
            if animating_move:
                img = get_piece_image(move_piece)
                if img:
                    start_x = move_start[0] * cell_size + (cell_size - piece_size) // 2
                    start_y = ((9 - move_start[1]) if flip_view else move_start[1]) * cell_size + (cell_size - piece_size) // 2
                    end_x = move_end[0] * cell_size + (cell_size - piece_size) // 2
                    end_y = ((9 - move_end[1]) if flip_view else move_end[1]) * cell_size + (cell_size - piece_size) // 2
                    pos_x = start_x + (end_x - start_x) * move_progress
                    pos_y = start_y + (end_y - start_y) * move_progress
                    board_surf.blit(img, (pos_x, pos_y))
            if animating_capture:
                img = get_piece_image(capture_piece)
                if img:
                    scale = 1 - capture_progress
                    img = transform.scale(img, (int(piece_size * scale), int(piece_size * scale)))
                    pos_x = capture_pos[0] * cell_size + (cell_size - piece_size) // 2 + (piece_size // 2) * (1 - scale)
                    pos_y = ((9 - capture_pos[1]) if flip_view else capture_pos[1]) * cell_size + (cell_size - piece_size) // 2 + (piece_size // 2) * (1 - scale)
                    board_surf.blit(img, (pos_x, pos_y))
            if promotion is not None and (game_mode == 'local' or Turn == player_color):
                if is_mobile:
                    promo_x = cell_size // 2
                    promo_y = board_size // 2 - (cell_size * 2) // 2
                    pygame.draw.rect(board_surf, (200, 200, 200),
                                     (promo_x - 10, promo_y - 10, 5 * promo_spacing, cell_size + 20))
                else:
                    promo_x = 200
                    promo_y = 360
                    pygame.draw.rect(board_surf, (200, 200, 200), (promo_x - 20, promo_y - 20, 500, 120))
                px, py, color = promotion
                for i, choice in enumerate(promotion_choices):
                    img_name = ('w' if color == '0' else 'b') + choice.lower() + '.png'
                    if choice == 'M':
                        img_name = ('w' if color == '0' else 'b') + 'Bear.png'
                    img = transform.scale(pygame.image.load(img_name), (piece_size, piece_size))
                    board_surf.blit(img, (promo_x + i * promo_spacing + (cell_size - piece_size) // 2,
                                          promo_y + (cell_size - piece_size) // 2))
            if game_over and winner_message:
                font = pygame.font.SysFont(None, cell_size if is_mobile else 50)
                text = font.render(winner_message, True, (255, 0, 0))
                board_surf.blit(text, (board_size // 2 - text.get_width() // 2, board_size // 2 - text.get_height() // 2))
            wind.blit(board_surf, (board_x, board_y))
            if is_mobile:
                # Captured pieces
                if flip_view:
                    left_captured = captured_black
                    right_captured = captured_white
                else:
                    left_captured = captured_white
                    right_captured = captured_black
                x = captured_left_x
                y = captured_y
                for piece in left_captured[:5]:
                    img = get_small_piece_image(piece)
                    if img:
                        wind.blit(img, (x, y))
                    x += small_spacing
                captured_right_x = wind.get_width() - (min(len(right_captured), 5) * small_spacing) - 10
                x = captured_right_x
                for piece in right_captured[:5]:
                    img = get_small_piece_image(piece)
                    if img:
                        wind.blit(img, (x, y))
                    x += small_spacing
            else:
                # Captured pieces
                if flip_view:
                    captured_bottom_list = captured_white
                    captured_top_list = captured_black
                else:
                    captured_bottom_list = captured_black
                    captured_top_list = captured_white
                # bottom
                x = 10
                y = captured_bottom_y
                for piece in captured_bottom_list:
                    img = get_small_piece_image(piece)
                    if img:
                        wind.blit(img, (x, y))
                    x += 40
                    if x > 180:
                        x = 10
                        y -= 40
                # top
                x = 10
                y = captured_top_y
                for piece in captured_top_list:
                    img = get_small_piece_image(piece)
                    if img:
                        wind.blit(img, (x, y))
                    x += 40
                    if x > 180:
                        x = 10
                        y += 40
                # Move history on PC
                history_surf = Surface((350, 800))
                history_surf.fill((255, 255, 200))
                y = 0
                for move in moves:
                    text = pygame.font.SysFont(None, 25).render(move, True, (0, 0, 0))
                    history_surf.blit(text, (10, y * 30 + 10))
                    y += 1
                wind.blit(history_surf, (1050, 0))
            # Buttons
            font = pygame.font.SysFont(None, font_size)
            pygame.draw.rect(wind, (200, 200, 200), sound_rect)
            sound_text = font.render('Sound ' + ('On' if sound_on else 'Off'), True, (0, 0, 0))
            wind.blit(sound_text,
                      (sound_rect.centerx - sound_text.get_width() // 2, sound_rect.centery - sound_text.get_height() // 2))
            pygame.draw.rect(wind, (200, 200, 200), restart_rect)
            restart_text = font.render('Restart', True, (0, 0, 0))
            wind.blit(restart_text, (restart_rect.centerx - restart_text.get_width() // 2,
                                     restart_rect.centery - restart_text.get_height() // 2))
            pygame.draw.rect(wind, (200, 200, 200), surrender_rect)
            surrender_text = font.render('Surrender' if not is_mobile else 'Surr.', True, (0, 0, 0))
            wind.blit(surrender_text, (surrender_rect.centerx - surrender_text.get_width() // 2,
                                       surrender_rect.centery - surrender_text.get_height() // 2))
        await asyncio.sleep(0)  # Критично для WASM
asyncio.run(main())
