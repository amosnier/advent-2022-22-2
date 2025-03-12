import typing
from enum import Enum

from instructions import pop_direction, pop_number

# WARNING: errors in the input, like invalid cube data, are not handled.
# Garbage in, garbage out, basically. On the other hand, we should be able to
# handle any valid input. Unit tests are provided in test_xxx.py.


# In this implementation, (0, 1, 2, 3) represent the angles obtained by
# multiplying each number by π/2, which is implicit in the code. But (0, 1, 2,
# 3) also represent the directions right, up, left, down, respectively. There
# is an obvious connection between those uses, and they are even composed to
# calculate the transition index, but in an attempt to maximize clarity, we use
# an enumeration for directions.
class _Direction(Enum):
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3


class _MoveDownRef:
    """
    Reference for a move down from one face row to the next while
    parsing the input. When moving to the next row in the input data,
    in order to unambiguously identify where we are, we will always
    start from the leftmost face that has a face just above it.

    This class stores the information we need about the face we are
    moving down from: its column, its face index and its rotation.
    """

    def __init__(self, col_index: int, face_index: int, rotation: int) -> None:
        self.col_index = col_index
        self.face_index = face_index
        self.rotation = rotation


_Face = list[str]
_Rows = list[str]

# ((row index, column index), rotation)
_FaceInfo = tuple[tuple[int, int], int]

_CanonFace = tuple[_Face, _FaceInfo]

_Pos = tuple[int, int]

_NextPos = tuple[
    tuple[_Pos, _Pos, _Pos, _Pos],  # rotation-dependent face transition
    bool,  # condition for face transition
    _Pos,  # position when there is no face transition
]


class Cube:
    """Class to parse the cube input, compute the canonical flattened cube, and
    move on the cube.

    Definitions:
    - Tile: the sub-parts of faces. If the face size is s, there are s² tiles
      per face.
    - Face row as opposed to just "row", in a flattened cube: if there are n
      rows in a flattened cube (16 in the canonical case below), there are n /
      s face rows, where s is the face size (4 in the canonical example below).
      In the canonical flattened cube below, for instance, there are 4 face
      rows.
    - Face column: same principle as face row, but for columns (there are 3
      face columns in the canonical flattened cube below).

    In our algorithms, we will naturally have to manipulate both tile
    coordinates and face coordinates in parallel. There is a scaling factor
    between them, which is the face size.
    """

    # Canonical flattened cube:

    #     2222
    #     2222
    #     2222
    #     2222
    # 333300001111
    # 333300001111
    # 333300001111
    # 333300001111
    #     4444
    #     4444
    #     4444
    #     4444
    #     5555
    #     5555
    #     5555
    #     5555

    # Transitions on the canonical cube. For every face, target face and
    # rotation, for the directions right, up, left, down.
    _transitions = (
        ((1, 0), (2, 0), (3, 0), (4, 0)),
        ((5, 2), (2, 1), (0, 0), (4, 3)),
        ((1, 3), (5, 0), (3, 1), (0, 0)),
        ((0, 0), (2, 3), (5, 2), (4, 1)),
        ((1, 1), (0, 0), (3, 3), (5, 0)),
        ((1, 2), (4, 0), (3, 2), (2, 0)),
    )

    def __init__(self, rows: str | _Rows) -> None:
        if isinstance(rows, str):
            # Read every line as a string, removing the newline.
            with open(rows) as f:
                rows = [line.rstrip() for line in f]
        self._num_cols = max(len(row) for row in rows)
        # Prolong all rows to max row size, padding with space.
        self._rows = [row + (self._num_cols - len(row)) * " " for row in rows]
        self._num_rows = len(rows)
        # Calculate the common number of tiles per row and column of every
        # face. At least one row or column will have exactly that number of
        # non-space symbols, and hence when stripped, it will be the shortest
        # of all the stripped rows and columns.
        self._size = min(len(row.strip()) for row in (rows + self._transpose()))
        self._num_face_rows = self._num_rows // self._size
        self._num_face_cols = self._num_cols // self._size
        self._calc_canonical()

    def __str__(self) -> str:
        return (
            f"{self._size}, {self._num_rows} x {self._num_cols}, "
            + f"{self._num_face_rows} x {self._num_face_cols}\n"
            + f"{self._canon}"
        )

    def _transpose(self) -> _Rows:
        # Return the transposed rows.
        return ["".join(row[i] for row in self._rows) for i in range(self._num_cols)]

    def _has_face(self, face_row: int, face_col: int) -> bool:
        # Check whether the cube has a face at the given face row and face column.
        return self._rows[face_row * self._size][face_col * self._size] != " "

    def _set_canon_face(
        self, face_index: int, face_row_index: int, face_col_index: int, rotation: int
    ) -> None:
        """Set a canonical flattened cube face.

        Keyword arguments:
        face_index     -- The face index: 0 to 5
        face_row_index -- The face row index in the input data
        face_col_index -- The face column index in the input data
        rotation       -- Input cube face data rotation angle: 0-3. Times π/2.
        """
        size = self._size
        start_row = face_row_index * size
        start_col = face_col_index * size
        info: _FaceInfo = ((face_row_index, face_col_index), rotation)
        match rotation:
            case 0 | 2:
                step = 1 - rotation
                self._canon[face_index] = (
                    [
                        row[start_col : start_col + size][::step]
                        for row in self._rows[start_row : start_row + size][::step]
                    ],
                    info,
                )

            case 1 | 3:
                step = 2 - rotation
                self._canon[face_index] = (
                    [
                        "".join(
                            row[i]
                            for row in self._rows[start_row : start_row + size][::step]
                        )
                        for i in range(start_col, start_col + size)[::-step]
                    ],
                    info,
                )
            case _:
                raise ValueError(f"{rotation} not a supported rotation")

    def _is_last_face_row(self, row: int) -> bool:
        return row == self._num_face_rows - 1

    def _handle_input_cols(
        self,
        row_index: int,
        start_col: int,
        stop_col: int,
        face_index: int,
        rotation: int,
        next_move_down_ref: None | _MoveDownRef,
        direction: _Direction,
    ) -> tuple[int, int, None | _MoveDownRef]:
        """Handle columns in the input for a move down, right or left

        As it happens, the logic to handle the move to the next face
        row, and the moves right and left on that row, is mostly the
        same. Hence, we are able to use this common function for those
        three cases.

        Keyword arguments
        row_index          -- current row index
        start_col          -- start column index
        stop_col           -- stop column index
        face_index         -- index of the face we are coming from
        rotation           -- rotation of the face we are coming from
        next_move_down_ref -- current next_move_down_ref (could be None)
        direction          -- direction of the transition from the previous face

        Return the updated values of: face_index, rotation, next_move_down_ref
        """

        # For the move down, we shall only handle one column. Assert that.
        assert direction != _Direction.DOWN or stop_col == start_col + 1

        found_one = False
        for col_index in range(start_col, stop_col, 1 if start_col < stop_col else -1):
            if self._has_face(row_index, col_index):
                transition = self._transitions[face_index][
                    (direction.value + rotation) % 4
                ]
                face_index = transition[0]
                assert not self._canon[face_index]
                rotation = (rotation + transition[1]) % 4
                self._set_canon_face(face_index, row_index, col_index, rotation)
                # We want to select the leftmost move down candidate.
                # Only update the candidate if we do not really have a
                # better one.
                if (
                    (next_move_down_ref is None or direction == _Direction.LEFT)
                    and not self._is_last_face_row(row_index)
                    and self._has_face(row_index + 1, col_index)
                ):
                    next_move_down_ref = _MoveDownRef(col_index, face_index, rotation)
                found_one = True
            elif found_one:
                # Immediately exit if there are no more faces in this direction.
                break
        return face_index, rotation, next_move_down_ref

    def _calc_canonical(self) -> None:
        """
        Calculate the canonical cube. That will be enough the move around in
        the cube later on, but it will not quite be enough to solve the
        problem, which requires us to know where we are and our orientation *on
        the original map*. Hence, for every face, also store original face
        coordinates and rotation.
        """
        # The canonical faces
        self._canon: list[None | _CanonFace] = [None for i in range(6)]

        # Find the face column of the first face.
        for col_index in range(self._num_face_cols):
            if self._has_face(0, col_index):
                break

        # For initialization, emulate coming down from non-rotated face 2.
        # Since face 2 is just above face 0 in the canonical representation,
        # our regular algorithm will then automatically interpret the first
        # face we find when parsing the input as face 0. This avoids having to
        # implement specific logic for the initialization.
        move_down_ref = _MoveDownRef(col_index, 2, 0)

        for row_index in range(self._num_face_rows):
            # Handle the move down from the previous face row.
            face_index, rotation, next_move_down_ref = self._handle_input_cols(
                row_index,
                move_down_ref.col_index,
                move_down_ref.col_index + 1,
                move_down_ref.face_index,
                move_down_ref.rotation,
                None,
                _Direction.DOWN,
            )
            # Handle faces to the right
            _, _, next_move_down_ref = self._handle_input_cols(
                row_index,
                move_down_ref.col_index + 1,
                self._num_face_cols,
                face_index,
                rotation,
                next_move_down_ref,
                _Direction.RIGHT,
            )
            # Handle faces to the left
            _, _, next_move_down_ref = self._handle_input_cols(
                row_index,
                move_down_ref.col_index - 1,
                -1,
                face_index,
                rotation,
                next_move_down_ref,
                _Direction.LEFT,
            )

            if not self._is_last_face_row(row_index):
                assert next_move_down_ref is not None
                move_down_ref = next_move_down_ref

    def _next_pos(
        self, i: int, j: int
    ) -> tuple[_NextPos, _NextPos, _NextPos, _NextPos]:
        """
        Return the next position table, indexed by direction. For every
        direction, the first value is a table indexed by rotation, which is
        used in case of face transition. The second value is the condition for
        transition, and the third value is the position when there is no
        transition.

        Keyword arguments:
        i -- Line
        j -- Column
        """
        ij_max = self._size - 1
        return (
            (  # right
                ((i, 0), (ij_max, i), (ij_max - i, ij_max), (0, ij_max - i)),
                j == ij_max,
                (i, j + 1),
            ),
            (  # up
                ((ij_max, j), (ij_max - j, ij_max), (0, ij_max - j), (j, 0)),
                i == 0,
                (i - 1, j),
            ),
            (  # left
                ((i, ij_max), (0, i), (ij_max - i, 0), (ij_max, ij_max - i)),
                j == 0,
                (i, j - 1),
            ),
            (  # down
                ((0, j), (ij_max - j, 0), (ij_max, ij_max - j), (j, ij_max)),
                i == ij_max,
                (i + 1, j),
            ),
        )

    def walk(self, instructions: str) -> int:
        """
        Execute movement instructions and return the problem's solution.
        """
        face, i, j, direction = 0, 0, 0, _Direction.RIGHT
        while instructions:
            number, instructions = pop_number(instructions)
            while number:
                transition = self._transitions[face][direction.value]
                rotation = transition[1]
                next_pos = self._next_pos(i, j)[direction.value]
                next_i, next_j = next_pos[0][rotation] if next_pos[1] else next_pos[2]
                next_face, next_dir = (
                    (transition[0], _Direction((direction.value + transition[1]) % 4))
                    if next_pos[1]
                    else (face, direction)
                )

                canon_face = typing.cast(_CanonFace, self._canon[next_face])
                if canon_face[0][next_i][next_j] == ".":
                    face, i, j, direction = (
                        next_face,
                        next_i,
                        next_j,
                        next_dir,
                    )
                number -= 1
            if instructions:
                d, instructions = pop_direction(instructions)
                match d:
                    case "L":
                        direction = _Direction((direction.value + 1) % 4)
                    case "R":
                        direction = _Direction((direction.value - 1) % 4)
                    case _:
                        raise ValueError(f"{d} not a supported direction")
        # To retrieve the original position, we start by applying the rotation.
        ij_max = self._size - 1
        face_info = typing.cast(_CanonFace, self._canon[face])[1]
        i, j = ((i, j), (j, ij_max - i), (ij_max - i, ij_max - j), (ij_max - j, i))[
            face_info[1]
        ]
        # We then apply the translation into the original map, including
        # scaling.
        i += face_info[0][0] * self._size
        j += face_info[0][1] * self._size
        # We then apply the rotation to the direction.
        direction = _Direction((direction.value - face_info[1]) % 4)
        # Apply Advent Of Code's magic formula, including adaptation for
        # indexing and direction conventions.
        return (
            (i + 1) * 1000
            + (j + 1) * 4
            + (
                1
                if direction == _Direction.DOWN
                else 3
                if direction == _Direction.UP
                else direction.value
            )
        )


def main() -> None:
    for i in range(2):
        with open(f"./instructions{i+1}.txt") as f:
            instructions = f.read().strip()
        print(Cube(f"./map{i+1}.txt").walk(instructions))


if __name__ == "__main__":
    main()
