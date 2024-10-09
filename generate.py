import sys
from crossword import *

class CrosswordGenerator:

    def __init__(self, crossword):
        """
        Initialize the crossword generator with a given crossword structure.
        """
        self.crossword = crossword
        self.domains = {var: self.crossword.words.copy() for var in self.crossword.variables}

    def create_letter_grid(self, assignment):
        """
        Generate a 2D grid representation based on the current assignment.
        """
        grid = [[None for _ in range(self.crossword.width)] for _ in range(self.crossword.height)]
        for var, word in assignment.items():
            direction = var.direction
            for index in range(len(word)):
                row = var.i + (index if direction == Variable.DOWN else 0)
                col = var.j + (index if direction == Variable.ACROSS else 0)
                grid[row][col] = word[index]
        return grid

    def display(self, assignment):
        """
        Output the crossword assignment to the console.
        """
        grid = self.create_letter_grid(assignment)
        for row in range(self.crossword.height):
            for col in range(self.crossword.width):
                if self.crossword.structure[row][col]:
                    print(grid[row][col] or " ", end="")
                else:
                    print("█", end="")
            print()

    def export(self, assignment, filename):
        """
        Save the crossword layout to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        grid = self.create_letter_grid(assignment)

        # Create a blank image canvas
        img = Image.new("RGBA", (self.crossword.width * cell_size, self.crossword.height * cell_size), "black")
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for row in range(self.crossword.height):
            for col in range(self.crossword.width):
                rect = [
                    (col * cell_size + cell_border, row * cell_size + cell_border),
                    ((col + 1) * cell_size - cell_border, (row + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[row][col]:
                    draw.rectangle(rect, fill="white")
                    if grid[row][col]:
                        w, h = draw.textsize(grid[row][col], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2), rect[0][1] + ((interior_size - h) / 2) - 10),
                            grid[row][col], fill="black", font=font
                        )

        img.save(filename)

    def find_solution(self):
        """
        Apply node and arc consistency methods, then solve the crossword puzzle.
        """
        self.ensure_node_consistency()
        self.apply_ac3()
        return self.perform_backtracking(dict())

    def ensure_node_consistency(self):
        """
        Adjust `self.domains` so that each variable is node-consistent.
        This involves removing any words that do not fit the variable's length constraint.
        """
        for var in self.domains:
            for word in set(self.domains[var]):
                if len(word) != var.length:
                    self.domains[var].remove(word)

    def revise_domains(self, x, y):
        """
        Ensure that variable `x` is arc consistent with respect to variable `y`.
        Remove any values from `self.domains[x]` that cannot match with values in `self.domains[y]`.
        
        Return True if any revisions were made to the domain of `x`; otherwise, return False.
        """
        revised = False
        i, j = self.crossword.overlaps[x, y]

        for x_word in set(self.domains[x]):
            remove = True
            for y_word in self.domains[y]:
                if x_word[i] == y_word[j]:
                    remove = False
            if remove:
                self.domains[x].remove(x_word)
                revised = True

        return revised

    def apply_ac3(self, arcs=None):
        """
        Enforce arc consistency across the crossword variables.
        If `arcs` is not specified, initialize it with all arcs in the problem.

        Return True if arc consistency is achieved and all domains are non-empty; otherwise, return False.
        """
        if arcs is None:
            arcs = [(x, y) for x in self.domains for y in self.crossword.neighbors(x)]

        while arcs:
            x, y = arcs.pop()
            if self.revise_domains(x, y):
                if not self.domains[x]:
                    return False
                for z in self.crossword.neighbors(x) - {y}:
                    arcs.append((z, x))

        return True

    def is_assignment_complete(self, assignment):
        """
        Check if the current assignment is complete, meaning every variable has an assigned value.
        """
        return len(self.crossword.variables) == len(assignment)

    def is_consistent(self, assignment):
        """
        Verify if the current assignment is consistent with the constraints of the crossword puzzle.
        """
        used_words = set()

        for var in assignment:
            if assignment[var] in used_words:
                return False
            used_words.add(assignment[var])

            if len(assignment[var]) != var.length:
                return False

            for neighbor in self.crossword.neighbors(var):
                if neighbor in assignment:
                    i, j = self.crossword.overlaps[var, neighbor]
                    if assignment[var][i] != assignment[neighbor][j]:
                        return False

        return True

    def order_values(self, var, assignment):
        """
        List the values in the domain of `var`, sorted by how many values they eliminate for neighboring variables.
        The first value should eliminate the least number of values in its neighbors' domains.
        """
        n = {value: 0 for value in self.domains[var]}
        for value in self.domains[var]:
            for neighbor in self.crossword.neighbors(var) - set(assignment):
                if value in self.domains[neighbor]:
                    n[value] += 1
        return sorted(n, key=n.get)

    def select_variable(self, assignment):
        """
        Choose an unassigned variable, preferring the one with the least remaining values in its domain.
        In case of a tie, select the variable with the highest degree.
        """
        best = None
        for var in self.crossword.variables - set(assignment):
            if (best is None or
                len(self.domains[var]) < len(self.domains[best]) or
                len(self.crossword.neighbors(var)) > len(self.crossword.neighbors(best))):
                best = var
        return best

    def perform_backtracking(self, assignment):
        """
        Implement Backtracking Search to find a complete assignment for the crossword puzzle.
        If successful, return the completed assignment; otherwise, return None.
        """
        if self.is_assignment_complete(assignment):
            return assignment

        var = self.select_variable(assignment)

        for value in self.domains[var]:
            assignment[var] = value

            if self.is_consistent(assignment):
                result = self.perform_backtracking(assignment)
                if result is not None:
                    return result

            assignment.pop(var)

        return None


def main():
    # Validate command-line usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Extract command-line arguments
    structure_file = sys.argv[1]
    words_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) == 4 else None

    # Create crossword puzzle
    crossword = Crossword(structure_file, words_file)
    generator = CrosswordGenerator(crossword)
    solution = generator.find_solution()

    # Output result
    if solution is None:
        print("No solution found.")
    else:
        generator.display(solution)
        if output_file:
            generator.export(solution, output_file)


if __name__ == "__main__":
    main()
