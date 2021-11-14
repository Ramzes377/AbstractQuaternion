import numpy as np
from unit import UnitRules

Unit_names = ('r', 'i', 'j', 'k') #use only one-letter unit name

class Quaternion:
    properties = {}  # Temporary declaration of properties during startup
    unit_index = {}
    rules = None

    @staticmethod
    def _make_property(props, name, init_value=None, doc=None):
        """Creates a property which can be assigned to a variable, with getter, setter, and deleter methods"""
        props[name] = init_value
        def getter1(self):
            return Quaternion(**{name: self.properties.get(name).value})
        def setter1(self, value):
            self.properties[name](value)
        def deleter1(self):
            self.properties[name] = None
        return property(getter1, setter1, deleter1, doc)

    for unit in Unit_names:
        exec("{attr:} = _make_property.__func__(properties, '{attr:}')".format(attr=unit))

    @classmethod
    def set_rules(cls, rules: UnitRules):
        assert type(rules) is UnitRules
        cls.rules = rules

    def __init__(self, a=0, b=0, c=0, d=0, *args, **kwargs):
        self.as_vector = np.array([a, b, c, d, *args], dtype=float)

        self.__call__() #link properties

        for unit_name, value in kwargs.items():         #set kwargs
            unit = Quaternion.rules.units[unit_name]
            self.as_vector[Quaternion.rules.unit_index[unit]] = value

    @property
    def real_part(self):
        return self.as_vector[0]

    @property
    def vector_part(self):
        return self.as_vector[1:]

    @property
    def norm(self):
        return np.linalg.norm(self.as_vector)

    @property
    def conjugate(self):
        return Quaternion(self.real_part, *(-self.vector_part))

    def scalar_product(self, other):
        assert isinstance(other, Quaternion)
        return (self.conjugate.custom_multiply(other) + other.conjugate.custom_multiply(self)) * 0.5

    def outer_product(self, other):
        assert isinstance(other, Quaternion)
        return (self.conjugate.custom_multiply(other) - other.conjugate.custom_multiply(self)) * 0.5

    def vector_product(self, other):
        return (self.custom_multiply(other) - other.custom_multiply(self)) * 0.5

    def custom_multiply(self, other):
        '''
        Multiply by use non-standart method of quaternion multiplication.
        These operations should be described in Unit class instance
        '''
        q = Quaternion()
        for x in self:
            for y in other:
                q += x*y
        return q()

    def _calculate_coeffs_of_product_with_quaternion(self, b):
        '''Standart quaternion multiplication. Other ways can be described in rules of multiplication'''
        a = self.as_vector
        tmp = np.zeros(4)
        tmp[0] = a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]
        tmp[1] = a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2]
        tmp[2] = a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1]
        tmp[3] = a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]
        return tmp

    def __call__(self):
        #Alias to relink properties values
        self.properties = self.properties.copy()
        for unit_name, value in zip(Quaternion.rules.unit_names, self.as_vector):
            self.properties[unit_name] = Quaternion.rules.units[unit_name](value)
        return self

    def __mul__(self, other):
        if isinstance(other, Quaternion):
            new_coeffs = self._calculate_coeffs_of_product_with_quaternion(other.as_vector)
            return Quaternion(*new_coeffs)
        elif isinstance(other, float):
            coeffs = other * self.as_vector
            return Quaternion(*coeffs)

    def __imul__(self, other):
        if isinstance(other, Quaternion):
            self.as_vector = self._calculate_coeffs_of_product_with_quaternion(other.as_vector)
        elif isinstance(other, float):
            self.as_vector = other * self.as_vector
        return self

    def __add__(self, other):
        assert isinstance(other, (Quaternion, int, float)) or type(other) in self.rules.units.values()
        if isinstance(other, Quaternion):
            return Quaternion(*(self.as_vector + other.as_vector))
        elif isinstance(other, (int, float)):
            v = self.as_vector.copy()
            v[0] += other
            return Quaternion(*v)
        elif type(other) in self.rules.units.values():
            self.as_vector[self.rules.unit_index[type(other)]] += other.value

    def __iadd__(self, other):
        assert isinstance(other, (Quaternion, float, int)) or type(other) in Quaternion.rules.units.values()
        if isinstance(other, Quaternion):
            self.as_vector += other.as_vector
        elif isinstance(other, (float, int)):
            self.as_vector[0] += other
        elif type(other) in Quaternion.rules.units.values():
            self.as_vector[Quaternion.rules.unit_index[type(other)]] += other.value
        return self

    def __sub__(self, other):
        assert isinstance(other, Quaternion)
        return Quaternion(*(self.as_vector - other.as_vector))

    def __isub__(self, other):
        assert isinstance(other, Quaternion)
        self.as_vector -= other.as_vector
        return self

    def __str__(self):
        coeffs_as_str = []
        for unit, y in zip(self.rules.unit_names, self.as_vector.round(6)):
            if y != 0:
                if y >= 0:
                    coeffs_as_str.append(f' + {y}{unit}')
                else:
                    coeffs_as_str.append(f' - {abs(y)}{unit}')
        out = ''.join(coeffs_as_str).strip()
        return out[1:] if out.startswith('+') else out

    def __invert__(self):
        norm = self.norm
        return self.conjugate * (1/(norm * norm))

    def __iter__(self):
        yield from (Quaternion.rules.units[name](v) for name, v in zip(Quaternion.rules.unit_names, self.as_vector))

    def __eq__(self, other):
        if isinstance(other, Quaternion):
            return (self.as_vector.round(6) == other.as_vector.round(6)).all()
        elif isinstance(other, (float, int)):
            return round(self.as_vector[0], 6) == other


if __name__ == '__main__':
    default_quaternion_rule = UnitRules(unit_names=Unit_names,
                                        rules={'ij': ' k', 'jk': ' i', 'ki': ' j', 'ik': '-j', 'kj': '-i', 'ji': '-k',
                                               'ri': ' i', 'ir': ' i', 'jr': ' j', 'rj': ' j', 'kr': ' k', 'rk': ' k',
                                               'ii': '-r', 'jj': '-r', 'kk': '-r', 'rr': ' r'})
    default_quaternion_rule.units['r'].set_real()
    Quaternion.set_rules(default_quaternion_rule) #change multiplication rule

    n = Quaternion(5)

    q1 = Quaternion(1, 2, 3, 4)
    q2 = Quaternion(5, 6, 7, 8)
    print("Q1: ", q1)
    print("Q2: ", q2)
    q3 = q1 * q2
    print('Q1 * Q2: ', q3)
    q4 = q1.custom_multiply(q2) # standart quaternion multiplication
    assert q3 == q4


    print('Scalar product: ', q1.scalar_product(q2))
    print('Vector product: ', q1.vector_product(q2))
    print('Outer product: ', q1.outer_product(q2))


    print('Invert q1: ', ~q1)
    q5 = q1 * ~q1
    assert q5 == Quaternion(1) == 1

    print('Conjugate q1: ', q1.conjugate)

    del q1, q2, q3, q4
    del Quaternion.rules

    print('\n')

    custom_quaternion_rule = UnitRules(unit_names=Unit_names,  # simillar to default but i^2 = j; j^2 = k; k^2 = i
                                       rules={'ij': ' k', 'jk': ' i', 'ki': ' j', 'ik': '-j', 'kj': '-i', 'ji': '-k',
                                              'ri': ' i', 'ir': ' i', 'jr': ' j', 'rj': ' j', 'kr': ' k', 'rk': ' k',
                                              'ii': ' j', 'jj': ' k', 'kk': ' i', 'rr': ' r'})
    Quaternion.set_rules(custom_quaternion_rule) #change multiplication rules

    q1 = Quaternion(1, 2, 3, 4)
    q2 = Quaternion(5, 6, 7, 8)
    print("Q1: ", q1)
    print("Q2: ", q2)
    q3 = q1 * q2
    q4 = q1.custom_multiply(q2) # trying custom quaternion multiplication
    print("Q1 * Q2 (Default product):\t", q3) #comapare
    print("Custom_product(q1, q2):\t\t",  q4)

    print('Scalar product: ', q1.scalar_product(q2))
    print('Vector product: ', q1.vector_product(q2))
    print('Outer product: ', q1.outer_product(q2))

    number = Quaternion(3)
    number += q3.j
    print(number)
    number -= q4.i
    print(number)