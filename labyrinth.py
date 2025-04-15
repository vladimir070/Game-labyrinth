import tkinter as tk
from tkinter import messagebox
import random
import heapq
import time

class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = self.create_grid()
        self.generate_maze()

    def create_grid(self):
        return [[{'walls': {'N': True, 'E': True, 'S': True, 'W': True}, 'visited': False}
                 for _ in range(self.width)]
                for _ in range(self.height)]

    def generate_maze(self):
        start_row, start_col = random.randint(0, self.height - 1), random.randint(0, self.width - 1)
        self.iterative_backtracker(start_row, start_col)

    def iterative_backtracker(self, start_row, start_col):
        stack = [(start_row, start_col)]
        self.grid[start_row][start_col]['visited'] = True

        while stack:
            row, col = stack[-1]
            directions = [(0, 1, 'E', 'W'), (1, 0, 'S', 'N'), (0, -1, 'W', 'E'), (-1, 0, 'N', 'S')]
            random.shuffle(directions)

            unvisited_neighbor_found = False
            for dr, dc, wall, opposite_wall in directions:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < self.height and 0 <= new_col < self.width and not self.grid[new_row][new_col]['visited']:
                    self.grid[row][col]['walls'][wall] = False
                    self.grid[new_row][new_col]['walls'][opposite_wall] = False
                    self.grid[new_row][new_col]['visited'] = True
                    stack.append((new_row, new_col))
                    unvisited_neighbor_found = True
                    break

            if not unvisited_neighbor_found:
                stack.pop()


class MazeSolver:
    def __init__(self, maze_generator):
        self.maze = maze_generator.grid
        self.width = maze_generator.width
        self.height = maze_generator.height
        self.start = (0, 0)
        self.end = (self.height - 1, self.width - 1)

    def is_valid(self, row, col):
        return 0 <= row < self.height and 0 <= col < self.width

    def get_neighbors(self, row, col):
        neighbors = []
        if self.is_valid(row, col):
            if not self.maze[row][col]['walls']['N'] and self.is_valid(row - 1, col):
                neighbors.append(((row - 1, col), 1))
            if not self.maze[row][col]['walls']['E'] and self.is_valid(row, col + 1):
                neighbors.append(((row, col + 1), 1))
            if not self.maze[row][col]['walls']['S'] and self.is_valid(row + 1, col):
                neighbors.append(((row + 1, col), 1))
            if not self.maze[row][col]['walls']['W'] and self.is_valid(row, col - 1):
                neighbors.append(((row, col - 1), 1))
        return neighbors

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def solve_a_star(self):
        open_set = []
        heapq.heappush(open_set, (0, self.start))
        came_from = {}
        g_score = {(row, col): float('inf') for row in range(self.height) for col in range(self.width)}
        g_score[self.start] = 0
        f_score = {(row, col): float('inf') for row in range(self.height) for col in range(self.width)}
        f_score[self.start] = self.heuristic(self.start, self.end)

        while open_set:
            current_f_score, current_node = heapq.heappop(open_set)
            current_row, current_col = current_node

            if (current_row, current_col) == self.end:
                return self.reconstruct_path(came_from)

            for neighbor, cost in self.get_neighbors(current_row, current_col):
                neighbor_row, neighbor_col = neighbor
                tentative_g_score = g_score[(current_row, current_col)] + cost

                if tentative_g_score < g_score[(neighbor_row, neighbor_col)]:
                    came_from[(neighbor_row, neighbor_col)] = (current_row, current_col)
                    g_score[(neighbor_row, neighbor_col)] = tentative_g_score
                    f_score[(neighbor_row, neighbor_col)] = tentative_g_score + self.heuristic((neighbor_row, neighbor_col), self.end)
                    if neighbor not in [node for _, node in open_set]:
                        heapq.heappush(open_set, (f_score[(neighbor_row, neighbor_col)], neighbor))

        return None

    def reconstruct_path(self, came_from):
        path = []
        current = self.end
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.append(self.start)
        return path[::-1]


class MazeGUI:
    def __init__(self, master):
        self.master = master
        master.title("Лабиринт")

        self.difficulty = "Профессионал"
        self.width, self.height = self.get_maze_dimensions(self.difficulty)
        self.maze_generator = MazeGenerator(self.width, self.height)
        self.maze_solver = MazeSolver(self.maze_generator)

        menubar = tk.Menu(master)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Новый лабиринт", command=self.regenerate_maze)
        filemenu.add_command(label="Новичок (10x10)", command=lambda: self.set_difficulty("Новичок"))
        filemenu.add_command(label="Средний (20x20)", command=lambda: self.set_difficulty("Средний"))
        filemenu.add_command(label="Профессионал (30x30)", command=lambda: self.set_difficulty("Профессионал"))
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=master.quit)
        menubar.add_cascade(label="Файл", menu=filemenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label="Подсказка", command=self.solve_maze)
        menubar.add_cascade(label="Помощь", menu=helpmenu)

        master.config(menu=menubar)

        self.canvas = tk.Canvas(master, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.focus_set()

        self.time_label = tk.Label(master, text="Время: 0.00")
        self.time_label.pack()
        self.start_time = 0.0
        self.running = False
        self.time_started = False
        self.game_over = False

        self.player_x = 0
        self.player_y = 0
        self.player_size = 0
        self.player_color = "yellow"

        self.cell_size = 20
        self.solution_path = None

        master.bind("<Configure>", self.on_resize)
        self.canvas.bind("<KeyPress>", self.move_player)

        self.draw_maze()

    def get_maze_dimensions(self, difficulty):
        if difficulty == "Новичок":
            return 10, 10
        elif difficulty == "Средний":
            return 20, 20
        else:
            return 30, 30

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.width, self.height = self.get_maze_dimensions(self.difficulty)
        self.regenerate_maze()

    def draw_maze(self):
        self.canvas.delete("all")
        if not self.maze_generator: return

        self.cell_size = min(self.canvas.winfo_width() // self.maze_generator.width,
                             self.canvas.winfo_height() // self.maze_generator.height)
        self.player_size = self.cell_size // 2

        for row in range(self.maze_generator.height):
            for col in range(self.maze_generator.width):
                x1 = col * self.cell_size
                y1 = row * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                if self.maze_generator.grid[row][col]['walls']['N']:
                    self.canvas.create_line(x1, y1, x2, y1, width=2, fill="black")
                if self.maze_generator.grid[row][col]['walls']['E']:
                    self.canvas.create_line(x2, y1, x2, y2, width=2, fill="black")
                if self.maze_generator.grid[row][col]['walls']['S']:
                    self.canvas.create_line(x1, y2, x2, y2, width=2, fill="black")
                if self.maze_generator.grid[row][col]['walls']['W']:
                    self.canvas.create_line(x1, y1, x1, y2, width=2, fill="black")

        start_x1, start_y1 = 0, 0
        start_x2, start_y2 = self.cell_size, self.cell_size
        self.canvas.create_rectangle(start_x1, start_y1, start_x2, start_y2, fill="green")

        end_x1 = (self.maze_generator.width - 1) * self.cell_size
        end_y1 = (self.maze_generator.height - 1) * self.cell_size
        end_x2 = end_x1 + self.cell_size
        end_y2 = end_y1 + self.cell_size
        self.canvas.create_rectangle(end_x1, end_y1, end_x2, end_y2, fill="red")

        self.draw_player()
        self.draw_solution()

    def solve_maze(self):
        if not self.maze_generator: return
        self.solution_path = self.maze_solver.solve_a_star()
        self.draw_solution()

    def draw_solution(self):
        self.canvas.delete("solution")
        if self.solution_path:
            for row, col in self.solution_path[1:-1]:
                x1 = col * self.cell_size + self.cell_size // 4
                y1 = row * self.cell_size + self.cell_size // 4
                x2 = x1 + self.cell_size // 2
                y2 = y1 + self.cell_size // 2
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="blue", outline="blue", tags="solution")

    def regenerate_maze(self):
        self.running = False
        self.time_started = False
        self.game_over = False
        self.maze_generator = MazeGenerator(self.width, self.height)
        self.maze_solver = MazeSolver(self.maze_generator)
        self.player_x = 0
        self.player_y = 0
        self.solution_path = None
        self.draw_maze()
        self.time_label.config(text="Время: 0.00")
        self.canvas.focus_set()

    def on_resize(self, event):
        self.draw_maze()

    def update_time(self):
        if self.running and self.time_started:
            elapsed_time = time.time() - self.start_time
            self.time_label.config(text="Время: {:.2f}".format(elapsed_time))
        self.master.after(50, self.update_time)

    def draw_player(self):
        if self.maze_generator:
            x = self.player_x * self.cell_size + self.cell_size // 4
            y = self.player_y * self.cell_size + self.cell_size // 4
            self.canvas.create_oval(x, y, x + self.player_size, y + self.player_size, fill=self.player_color, tags="player")

    def move_player(self, event):
        if not self.maze_generator or self.game_over: return

        if not self.time_started:
            self.start_time = time.time()
            self.running = True
            self.time_started = True
            self.update_time()

        new_x = self.player_x
        new_y = self.player_y

        #  Проверка клавиш с использованием event.keysym
        if event.keysym == "Up":
            if not self.maze_generator.grid[self.player_y][self.player_x]['walls']['N']:
                new_y -= 1
        elif event.keysym == "Down":
            if not self.maze_generator.grid[self.player_y][self.player_x]['walls']['S']:
                new_y += 1
        elif event.keysym == "Left":
            if not self.maze_generator.grid[self.player_y][self.player_x]['walls']['W']:
                new_x -= 1
        elif event.keysym == "Right":
            if not self.maze_generator.grid[self.player_y][self.player_x]['walls']['E']:
                new_x += 1

        if self.is_valid_move(new_x, new_y):
            self.player_x = new_x
            self.player_y = new_y
            self.canvas.delete("player")
            self.draw_player()

            if (self.player_y, self.player_x) == (self.maze_generator.height - 1, self.maze_generator.width - 1):
                self.running = False
                self.game_over = True
                elapsed_time = time.time() - self.start_time
                messagebox.showinfo("Поздравляем!", "Вы прошли лабиринт за {:.2f} секунд!".format(elapsed_time))

    def is_valid_move(self, x, y):
        if not self.maze_generator: return False
        return 0 <= x < self.maze_generator.width and 0 <= y < self.maze_generator.height

root = tk.Tk()
gui = MazeGUI(root)
root.mainloop()
