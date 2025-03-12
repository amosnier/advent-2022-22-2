from instructions import pop_direction, pop_number


def main() -> None:
    instructions = "10R4L756L16"
    n, instructions = pop_number(instructions)
    assert n == 10
    d, instructions = pop_direction(instructions)
    assert d == "R"
    n, instructions = pop_number(instructions)
    assert n == 4
    d, instructions = pop_direction(instructions)
    assert d == "L"
    n, instructions = pop_number(instructions)
    assert n == 756
    d, instructions = pop_direction(instructions)
    assert d == "L"
    n, instructions = pop_number(instructions)
    assert n == 16
    assert not instructions


if __name__ == "__main__":
    main()
