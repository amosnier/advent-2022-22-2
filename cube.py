CUBE_1 = """
xxx
 x
 x
 x
"""


def trim(cube: str) -> str:
    return "\n".join(matrix(cube))


def matrix(cube: str) -> list[str]:
    return cube.split("\n")[1:-1]


def test1() -> None:
    print(matrix(CUBE_1))
    print(trim(CUBE_1))


if __name__ == "__main__":
    test1()
