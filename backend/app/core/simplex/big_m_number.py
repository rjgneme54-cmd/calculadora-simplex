from __future__ import annotations

from fractions import Fraction


class BigMNumber:
    """Representa a + b*M de forma simbolica y exacta (a, b son Fraction)."""

    __slots__ = ("const", "m_coeff")

    def __init__(self, const: Fraction | int = 0, m_coeff: Fraction | int = 0):
        self.const = const if isinstance(const, Fraction) else Fraction(const)
        self.m_coeff = m_coeff if isinstance(m_coeff, Fraction) else Fraction(m_coeff)

    @staticmethod
    def of(value) -> BigMNumber:
        if isinstance(value, BigMNumber):
            return value
        return BigMNumber(Fraction(value))

    def __add__(self, other) -> BigMNumber:
        o = BigMNumber.of(other)
        return BigMNumber(self.const + o.const, self.m_coeff + o.m_coeff)

    __radd__ = __add__

    def __sub__(self, other) -> BigMNumber:
        o = BigMNumber.of(other)
        return BigMNumber(self.const - o.const, self.m_coeff - o.m_coeff)

    def __rsub__(self, other) -> BigMNumber:
        return BigMNumber.of(other) - self

    def __neg__(self) -> BigMNumber:
        return BigMNumber(-self.const, -self.m_coeff)

    def __mul__(self, scalar) -> BigMNumber:
        if isinstance(scalar, BigMNumber):
            raise TypeError("No se puede multiplicar dos expresiones que contienen M")
        f = scalar if isinstance(scalar, Fraction) else Fraction(scalar)
        return BigMNumber(self.const * f, self.m_coeff * f)

    __rmul__ = __mul__

    def __truediv__(self, scalar) -> BigMNumber:
        if isinstance(scalar, BigMNumber):
            raise TypeError("No se puede dividir por una expresión que contiene M")
        f = scalar if isinstance(scalar, Fraction) else Fraction(scalar)
        return BigMNumber(self.const / f, self.m_coeff / f)

    def __eq__(self, other) -> bool:
        o = BigMNumber.of(other)
        return self.const == o.const and self.m_coeff == o.m_coeff

    def __lt__(self, other) -> bool:
        o = BigMNumber.of(other)
        if self.m_coeff != o.m_coeff:
            return self.m_coeff < o.m_coeff
        return self.const < o.const

    def __le__(self, other) -> bool:
        return self < other or self == other

    def __gt__(self, other) -> bool:
        return not (self <= other)

    def __ge__(self, other) -> bool:
        return not (self < other)

    def is_zero(self) -> bool:
        return self.m_coeff == 0 and self.const == 0

    def __repr__(self) -> str:
        return f"BigMNumber({self.const}, {self.m_coeff})"

    def __str__(self) -> str:
        if self.m_coeff == 0:
            return str(self.const)
        if self.const == 0:
            return f"{self.m_coeff}M"
        return f"{self.const} + ({self.m_coeff})M"
