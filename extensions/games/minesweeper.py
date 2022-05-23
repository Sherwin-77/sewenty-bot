from itertools import repeat
import random
from queue import SimpleQueue
from typing import Optional

FLAG_VALUE = -69
MINE_VALUE = -420
MINE_AND_FLAG_VALUE = -727


class Minesweeper:
    def __init__(self, row: int, column: int, mine_number: Optional[int] = None):
        """
        Create minesweeper game

        Parameters
        ----------
        row : int
        column : int
        """
        if not isinstance(row, int) or not isinstance(column, int):
            raise TypeError("Row and Column must be int")
        if row < 1 or column < 1:
            raise ValueError("Field must be at reasonable size (at least 2x2)")
        self.max_row = row
        self.max_column = column
        self.size = self.max_row * self.max_column

        self.data = [[n for n in repeat(0, self.max_row)] for _ in repeat(None, self.max_column)]
        self.visited = [[n for n in repeat(False, self.max_row)] for _ in repeat(None, self.max_column)]

        self.bomb_count = self.size // 5

    def _find_neighbours(self, row: int, col: int):
        if not isinstance(row, int) or not isinstance(col, int):
            raise TypeError("Row and Column must be int")

        if row >= self.max_row or row < 0:
            raise ValueError("Row position must be between max created row - 1 and 0 (0-indexed)")
        if col >= self.max_column or col < 0:
            raise ValueError("Column position must be between max created column -1 and 0 (0-indexed)")
        # BFS bois
        q = SimpleQueue()
        q.put((row, col))
        self.visited[col][row] = True
        while not q.empty():
            r, c = q.get()
            self.visited[c][r] = True
            if self.data[c][r] == 0:
                # another spaghetti code
                if r > 0 and not self.visited[c][r-1]:
                    q.put((r-1, c))
                if r < self.max_row-1 and not self.visited[c][r+1]:
                    q.put((r+1, c))
                if c > 0 and not self.visited[c-1][r]:
                    q.put((r, c-1))
                if c < self.max_column-1 and not self.visited[c+1][r]:
                    q.put((r, c+1))

                if r > 0 and col > 0 and not self.visited[c-1][r-1]:
                    q.put((r-1, c-1))
                if r > 0 and c < self.max_column-1 and not self.visited[c+1][r-1]:
                    q.put((r-1, c+1))
                if r < self.max_row-1 and c > 0 and not self.visited[c-1][r+1]:
                    q.put((r+1, c-1))
                if r < self.max_row-1 and c < self.max_column-1 and not self.visited[c+1][r+1]:
                    q.put((r+1, c+1))

    def start(self, row_position: int, column_position: int):
        """
        Start filling mines when first move created. position is 0-indexed

        Parameters
        ----------
        row_position : int
        column_position : int

        Returns
        -------
        None
        """
        if row_position >= self.max_row or row_position < 0:
            raise ValueError("Row position must be between max created row - 1 and 0 (0-indexed)")
        if column_position >= self.max_column or column_position < 0:
            raise ValueError("Column position must be between max created column -1 and 0 (0-indexed)")

        for _ in repeat(None, self.bomb_count):   # replace this with any number you want
            row = random.choice(list(range(0, row_position)) + list(range(row_position+1, self.max_row)))
            col = random.choice(list(range(0, column_position)) + list(range(column_position+1, self.max_column)))
            if self.data[col][row] == MINE_VALUE:  # bonus
                continue
            self.data[col][row] = MINE_VALUE
            # here goes spaghetti code
            if row > 0 and self.data[col][row-1] != MINE_VALUE:
                self.data[col][row-1] += 1  # right
            if row < self.max_row-1 and self.data[col][row+1] != MINE_VALUE:
                self.data[col][row+1] += 1  # left
            if col > 0 and self.data[col-1][row] != MINE_VALUE:
                self.data[col-1][row] += 1  # up
            if col < self.max_column-1 and self.data[col+1][row] != MINE_VALUE:
                self.data[col+1][row] += 1  # down

            # border time
            if row > 0 and col > 0 and self.data[col-1][row-1] != MINE_VALUE:
                self.data[col-1][row-1] += 1  # top right
            if row < self.max_row-1 and col > 0 and self.data[col-1][row+1] != MINE_VALUE:
                self.data[col-1][row+1] += 1  # top left
            if row > 0 and col < self.max_column-1 and self.data[col+1][row-1] != MINE_VALUE:
                self.data[col+1][row-1] += 1  # bottom right
            if row < self.max_row-1 and col < self.max_column-1 and self.data[col+1][row+1] != MINE_VALUE:
                self.data[col+1][row+1] += 1  # bottom left

        # at the end reveal the starting cell
        self.open(row_position=row_position, column_position=column_position)

    def flag(self, row_position: int, column_position: int):
        """
        User puts flag on cell in field

        Parameters
        ----------
        row_position : int
        column_position : int

        Returns
        -------
        None
        """
        pass
        # if row_position >= self.max_row or row_position < 0:
        #     raise ValueError("Row position must be between max created row - 1 and 0 (0-indexed)")
        # if column_position >= self.max_column or column_position < 0:
        #     raise ValueError("Column position must be between max created column -1 and 0 (0-indexed)")
        # if self.data[column_position][row_position] == MINE_VALUE:
        #     self.data[column_position][row_position] = MINE_AND_FLAG_VALUE
        # else:
        #     self.data[column_position][row_position] = FLAG_VALUE

    def open(self, row_position: int, column_position: int):
        """
        User opens the cell in field

        Parameters
        ----------
        row_position : int
        column_position : int

        Returns
        -------
        bool
            indicating user open bomb cell or no
        """
        if row_position >= self.max_row or row_position < 0:
            raise ValueError("Row position must be between max created row - 1 and 0 (0-indexed)")
        if column_position >= self.max_column or column_position < 0:
            raise ValueError("Column position must be between max created column -1 and 0 (0-indexed)")

        if self.data[column_position][row_position] == 0 or self.data[column_position][row_position] == FLAG_VALUE:
            self.visited[column_position][row_position] = True
            self._find_neighbours(row=row_position, col=column_position)
            return False
        if self.data[column_position][row_position] > 0:  # non-zero cell but not bomb
            self.visited[column_position][row_position] = True
            return False
        if self.data[column_position][row_position] <= MINE_VALUE:  # bomb cell
            return True

    def is_win(self):
        """
        Indicating user win the game or no

        Returns
        -------
        bool
        """
        count = 0
        for i, col in enumerate(self.visited):
            for j, visited in enumerate(col):
                if visited and self.data[i][j] >= 0:
                    count += 1
        return count == self.size - self.bomb_count
