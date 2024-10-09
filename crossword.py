class Variable:
    """A variable representing a word in the crossword puzzle."""

    ACROSS = "across"
    DOWN = "down"

    def __init__(self, i: int, j: int, direction: str, length: int):
        """
        Create a new variable with starting point, direction, and length.

        Args:
            i (int): Row index of the starting point.
            j (int): Column index of the starting point.
            direction (str): Direction of the word, either 'across' or 'down'.
            length (int): Length of the word.
        """
        self.i = i
        self.j = j
        self.direction = direction
        self.length = length
        self.cells = [(self.i + (k if self.direction == Variable.DOWN else 0),
                       self.j + (k if self.direction == Variable.ACROSS else 0)) for k in range(self.length)]

    def __hash__(self) -> int:
        """Return a hash of the variable."""
        return hash((self.i, self.j, self.direction, self.length))

    def __eq__(self, other: 'Variable') -> bool:
        """Check equality with another variable."""
        return (self.i == other.i and
                self.j == other.j and
                self.direction == other.direction and
                self.length == other.length)

    def __str__(self) -> str:
        """Return a string representation of the variable."""
        return f"({self.i}, {self.j}) {self.direction} : {self.length}"

    def __repr__(self) -> str:
        """Return a detailed representation of the variable."""
        direction = repr(self.direction)
        return f"Variable({self.i}, {self.j}, {direction}, {self.length})"


class Crossword:
    """A crossword puzzle defined by its structure and words."""

    def __init__(self, structure_file: str, words_file: str):
        """
        Initialize the crossword with a structure and words.

        Args:
            structure_file (str): Path to the file defining the crossword structure.
            words_file (str): Path to the file containing the words.
        """
        # Determine structure of crossword
        with open(structure_file) as f:
            contents = f.read().splitlines()
            self.height = len(contents)
            self.width = max(len(line) for line in contents)

            self.structure = []
            for i in range(self.height):
                row = [j < len(contents[i]) and contents[i][j] == "_" for j in range(self.width)]
                self.structure.append(row)

        # Save vocabulary list
        with open(words_file) as f:
            self.words = set(f.read().upper().splitlines())

        # Determine variable set
        self.variables = set()
        for i in range(self.height):
            for j in range(self.width):
                # Vertical words
                if self.structure[i][j] and (i == 0 or not self.structure[i - 1][j]):
                    length = 1
                    for k in range(i + 1, self.height):
                        if self.structure[k][j]:
                            length += 1
                        else:
                            break
                    if length > 1:
                        self.variables.add(Variable(i=i, j=j, direction=Variable.DOWN, length=length))

                # Horizontal words
                if self.structure[i][j] and (j == 0 or not self.structure[i][j - 1]):
                    length = 1
                    for k in range(j + 1, self.width):
                        if self.structure[i][k]:
                            length += 1
                        else:
                            break
                    if length > 1:
                        self.variables.add(Variable(i=i, j=j, direction=Variable.ACROSS, length=length))

        # Compute overlaps for each word
        self.overlaps = {}
        for v1 in self.variables:
            for v2 in self.variables:
                if v1 == v2:
                    continue
                intersection = set(v1.cells).intersection(v2.cells)
                if not intersection:
                    self.overlaps[v1, v2] = None
                else:
                    intersection = intersection.pop()
                    self.overlaps[v1, v2] = (v1.cells.index(intersection), v2.cells.index(intersection))

    def neighbors(self, var: Variable) -> set:
        """
        Given a variable, return a set of overlapping variables.

        Args:
            var (Variable): The variable for which to find neighbors.

        Returns:
            set: A set of overlapping variables.
        """
        return {v for v in self.variables if v != var and self.overlaps.get((v, var)) is not None}
