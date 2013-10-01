
class Entry:

    def update(self, key, value):
        self.key = value

    def compare_kwargs(self, **kwargs):
        if set(list(kwargs.keys())).issubset(list(self.__dict__)):
            for key in kwargs:
                if not str(self.__dict__[key]) == str(kwargs[key]):
                    return False
        else:
            return False
        return True

    def database_new(self, new):
        """
        Called whenever this is a new object
        """
        pass

    def database_compare(self, prev):
        """
        Copy of the previous object under the same key repre by prev
        Called when both keys exist in database
        TODO: ????
        """
        pass

    def format_string(self, s, **kwargs):
        d = self.__dict__.copy()
        for key in kwargs.keys():
            # replace anything sent in, this is on purpose
            # because as it turns out you might have a method with the same name
            d[key] = kwargs[key]
        return s.format(**d)

    def get_extra_profile_fields(self):
        return [(key.split('profile_extra_')[1], self.__dict__[key]) for key in self.__dict__ if key.startswith('profile_extra_')]
