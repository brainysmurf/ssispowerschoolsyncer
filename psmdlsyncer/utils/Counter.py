"""
Counter class that remembers the order in which keys were added
"""

from collections import OrderedDict

class Counter:
    """
    Remembers the order in which it counted something
    """
    def __init__(self, startat=0):
        self._ordered = OrderedDict()
        self.startat = startat

    def add(self, key, step=1):
        if not key in self._ordered:
            self._ordered[key] = self.startat
        self._ordered[key] += step

    @property
    def maximum_in_order_added(self):
        """
        Returns a list of the highest-frequency items
        in the order in which they were added
        """
        if self._ordered.values():
            maximum = max(self._ordered.values())
        else:
            return []
        r = []
        for item in self._ordered:
            if self._ordered[item] == maximum and item not in r:
                r.append(item)
        return r

if __name__ == "__main__":

    c = Counter()
    c.add('fgh')
    c.add('abc')
    c.add('lskdjfals;dkfj')
    c.add('fgh')
    c.add('abc')
    print(c.result)
