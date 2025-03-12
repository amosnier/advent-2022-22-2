# Advent of Code, 2022, day 22, part two: walking on a flattened cube

## The problem

The problem we want to solve is [Advent of Code 2022, day 22, part
two](https://adventofcode.com/2022/day/22).

## Representing a flattened cube as a matrix of characters

The simple example given by Advent of Code in this case is:

            1111
            1111
            1111
            1111
    222233334444
    222233334444
    222233334444
    222233334444
            55556666
            55556666
            55556666
            55556666

The problem really is about walking on the flattened cube as if it was not flattened. For instance,
walking out from face 1 upwards, we end up on face 2, downwards. But the flattening above is just one
possible flattening, there are many others, and our walking algorithm needs to work for any flattening!

More generally we are given $M$, a matrix like the above and:

- $a$, the face size ($4$ in the example above),
- $(x, y)$ a position in the matrix above. In the case above, $0 <= x < 4a$ and $0 <= y < 3a$,
- $\alpha$ the direction we are facing. $\alpha = 0$, $\alpha = \pi/2$, $\alpha = \pi$ or $\alpha =
  3\pi/2$. $\alpha = 0$ means we are facing right, $\alpha = \pi/2$ means we are facing up, etc.

$a$ can in fact be computed from $M$, among others because at least one line or one column of $M$ will be
occupied by a single face (we will not prove that here, we will just assume it).

We want to implement a function $f$ (the next step function) where $f(M, x, y, \alpha) = (x', y',
\alpha')$, and:

- $(x', y')$ is the next position in the same direction,
- $\alpha'$ is the new direction, which may or may no be equal to $\alpha$.

## Moving out rightward

One possible way to implement $f$ is to enumerate all the ways there are to transition between two faces.

For instance, we could consider all the transitions between faces while walking rightward. Once we have
solved that, the other cases are obtained by rotation. Also, given one way to transition between two faces
walking rightward, we know that the symmetry of that transition with respect to the horizontal axis that
passes though the middle of the start face also is a transition. In some cases, that symmetry gives back
the same transition, but most often, it gives a different transition (going up instead for down, for
instance).

The following diagram depicts the simplest such transition:

    12

In this case, as soon as we leave face 1 facing right, we enter face 2. That transition's vertical
symmetry is itself.

It is tempting to hope that we would be able to find the target face by just checking whether or not a
certain candidate target face exists. But unfortunately, things are not quite that easy. For instance, the
arguably second most obvious transition would be:

    1┐
    x2

By just checking the presence of face 2 on the picture above, we could hope to know whether or not that
transition applies. But consider:

    13
     2

That's a perfectly valid part of a flattened cube, and face 2 is where expected, but in this case, the
target face is obviously 3, not 2. I.e. this is in fact the first case, not the second one. So it seems
that we at least have to consider candidates in a certain order to avoid the risk of drawing an incorrect
conclusion. Also, in case one, the direction is unchanged, while in the second case, it goes from $0$ to
$-\pi/2$.

## Finding the target faces

Based on the previous analysis, here comes a hopefully comprehensive list of all the possible transitions
when moving rightward, in an order that would hopefully allow us to stop the search as soon as a candidate
target face is present.

### Case 1

See above, $\alpha' = 0$:

    12

### Cases 2 and 3

See above, $\alpha' = \pm \pi / 2$:

    1┐
    x2

### Cases 4 and 5

$\alpha' = \pi$:

    1─┐
    x │
    x2┘

### Cases 6 and 7

These are like the previous cases, but in the opposite direction. $\alpha' = \pi$:

    x1┐
    x │
    2─┘

### Cases 8 and 9

$\alpha' = \pm \pi / 2$:

    1─┐
    x │
    x │
    x2│
     └┘
### Case 10 and 11

These are like the previous cases, but in the opposite direction. $\alpha' = \pm \pi / 2$:

    ┌───┐
    │  1┘
    2xxx

### Case 12

$\alpha' = 0$:

    ┌2xx1┐
    └────┘

### Cases 13 and 14

$\alpha' = 0$:

       1┐
      xx│
     xx │
    ┌2  │
    └───┘

### Cases 15 and 16

$\alpha' = 0$:

      1┐
      x│
     xx│
     x │
    ┌2 │
    └──┘

## Implementation

For an optimal implementation, we probably want to divide the calculation into two fairly independent
steps:
- Step one: perform the calculation at $a = 1$ i.e. the canonical case where every face in the cube has a
  size of one.
- Step two: perform the calculation for the actual face size, based on the result from step one.

Step one implements all the cases listed above, and represents the flattened cube's topology. It is non
trivial, and could potentially be memoized, for performance. Step one will also motivate fairly extensive
unit testing, which will be much easier when the face size is one.

Step two is really just a scaling step.
