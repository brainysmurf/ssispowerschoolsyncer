from collections import defaultdict

class Comparer:

    def __init__(self):
        self._left = defaultdict(list)
        self._right = defaultdict(list)

    def left(self, key, value):
        self._left[key].append(value)

    def right(self, key, value):
        self._right[key].append(value)

    def generate_differences(self):
        """
        Generator that produces output that explains the differences between the data
        """
        # First figure out which keys are in left, and not in right, and vice versa
        left_keys = set(list(self._left.keys()))
        right_keys = set(list(self._right.keys()))
        if left_keys != right_keys:
            for extra_left_key in left_keys - right_keys:
                yield ("ADD", extra_left_key, self._left[extra_left_key], None)
            for extra_right_key in right_keys - left_keys:
                yield ("DELETE", extra_right_key, None, self._right[extra_right_key])
        for shared_key in left_keys & right_keys:
            left = self._left[shared_key]
            right = self._right[shared_key]
            if left != right:
                yield ("CHANGE", shared_key, left, right)

if __name__ == "__main__":

    c = Comparer()
    c.left('hi', 'there')
    c.left('hi', 'ho')
    c.left('yo', 'bro')

    c.right('nope', 'nothing')
    c.right('noone', 'knows')
    c.right('hi', 'there')

    for item in c.generate_differences():
        print(item)
        
