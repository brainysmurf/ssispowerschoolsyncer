from psmdlsyncer.utils import NS2

class BaseModel:
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

    def format_string(self, s, **kwargs):
        d = self.__dict__.copy()
        for key in kwargs.keys():
            # replace anything sent in, this is on purpose
            # because as it turns out you might have a method with the same name
            d[key] = kwargs[key]
        return s.format(**d)

    def plain_name_of_custom_field(self, custom_field):
        return custom_field.split('custom_profile_')[1]

    def get_custom_field_keys(self):
        """
        Return all the custom_profile instance and class variables
        If a custom_profile is set to None, don't return it
        That way someone else can set it None for more manual control
        """
        keys = [key for key in self.__dict__ if key.startswith('custom_profile_')]
        keys.extend([key for key in self.__class__.__dict__ if key.startswith('custom_profile_')])
        return [key for key in keys if getattr(self, key) is not None]

    def get_custom_field(self, name, default=None):
        return getattr(self, 'custom_profile_'+name, default)

    def set_custom_field(self, name, value):
        return setattr(self, 'custom_profile_'+name, value)

    def differences(self, other):

        for to_add in set(other.get_custom_field_keys()) - set(self.get_custom_field_keys()):
            ns = NS()
            ns.status = 'add_custom_profile_field_to_user'
            ns.left = self
            ns.right = other
            ns.param = to_add
            yield ns

        for to_remove in set(self.cohort_idnumbers) - set(other.cohort_idnumbers):
            ns = NS()
            ns.status = 'remove_custom_profile_field_to_user'
            ns.left = self
            ns.right = other
            ns.param = to_remove
            yield ns

        for field in self.get_custom_field_keys():
            left = self.get_custom_field(field)
            right = self.get_custom_field(field)

            if left != right:
                ns = NS()
                ns.status = 'custom_profile_value_changed'
                ns.left = self
                ns.right = other
                param = NS()
                param.value = other.value
                param.field = self.name
                ns.param = param
                yield ns


