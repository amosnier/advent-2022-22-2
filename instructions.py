from itertools import takewhile


def pop_number(instructions: str) -> tuple[int, str]:
    number = "".join(takewhile(lambda c: c.isnumeric(), instructions))
    return int(number), instructions[len(number) :]


def pop_direction(instructions: str) -> tuple[str, str]:
    return instructions[0], instructions[1:]
