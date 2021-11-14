class Unit:
    is_imaginary = True
    def __init__(self, value):
        self._value = complex(0, value) if self.is_imaginary else complex(value, 0)

    @property
    def value(self):
        return self._value.imag if self.is_imaginary else self._value.real

    @classmethod
    def set_real(cls):
        if cls.is_imaginary:
            cls.is_imaginary = False

    @classmethod
    def _set_rules(cls, instances: dict, rules: dict):
        '''Get subclass instances of these class and set rules of multiplication between them'''
        cls._rules = {}
        for (A, B), (C, D) in rules.items():
            cls._rules[(instances[A], instances[B])] = (-1 if C == '-' else 1), instances[D]
        print('Set new multiplication rules')

    def __mul__(self, other):
        assert hasattr(self, '_rules'), 'Rules between Units must be define!'
        if isinstance(other, (float, int)):  #default linear rule: const * Unit(k) = Unit(const * K)
            return other * self.value
        sign, unit = self._rules[(self.__class__, other.__class__)]
        return unit(sign * self.value * other.value)

    def __neg__(self):
        self._value = -self._value
        return self

    def __str__(self):
        return f'{self.value}{type(self).__name__}'

    def __call__(self, new_value):
        self._value = complex(0, new_value) if self.is_imaginary else complex(new_value, 0)
        return self

class UnitRules:
    def __init__(self, unit_names, rules):
        self.unit_names = unit_names
        self.units = {name: type(name, (Unit,), {}) for name in unit_names}
        self.unit_index = {self.units[u]: index for index, u in enumerate(self.unit_names)}
        Unit._set_rules(self.units, rules)