"""
Interface between Python structures and the database
"""

import os

from psmdlsyncer.files import clear_folder

class Controller():
    """
    A generic controller class for a dictionary of dictionary of objects
    """

    def __init__(self, klass):
        self._db = {}
        self.klass = klass

    def get(self, key):
        try:
            return self._db[key]
        except KeyError:
            return None

    def get_kwargs(self, **kwargs):
        result = []
        for key in self.keys():
            this = self.get(key)
            if this.compare_kwargs(**kwargs):
                result.append(this)
        return result

    def keys(self):
        return self._db.keys()

    def add(self, *args, **kwargs):
        key = str(args[0])
        self._db[key] = self.klass(*args,
                                   **kwargs)
        return self._db[key]

    def update(self, id, key, value):
        """
        Adds information to the database
        """
        if id is None:
            raise CannotPassMeNone('Controller.update')
        item = self.get(id)
        if not item:
            raise NoSuchStudent(id)
        # If the object defines a method with the same name as
        # update_$key, use that method
        call = "update_{}".format(key)
        if hasattr(item, call):
            getattr(item, call)(value)
        else:
            item.update(key, value)

    def objects(self):
        """
        Return a generator that builds the objects in the database
        """
        raise NotImplemented
        
    def output(self, file=None):
        if not file:
            keys = list(self._db.keys())
            keys.sort()
            for key in self._db.keys():
                print(self._db[key])
        else:
            pass

    def output_filter(self, filter):
        for key in self._db.keys():
            this = self.get(key)
            if filter(this):
                print(this)
