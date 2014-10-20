from psmdlsyncer.utils import NS2
from collections import OrderedDict
import json

class BaseModel:

    def output(self, **kwargs):
        """
        Can send an 'add' kwarg to add metadata to the result
        """ 
        d = OrderedDict()
        if 'add' in kwargs:
            add = kwargs['add']
            d.update(add)
            del kwargs['add']
        d['data'] = OrderedDict()

        data = d['data']
        data['name'] = self.lastfirst
        data['username'] = self.username
        data['idnumber'] = self.idnumber
        if hasattr(self, 'grade'):
            data['grade'] = self.grade
        if hasattr(self, 'homeroom'):
            data['homeroom'] = self.homeroom

        if hasattr(self, 'courses'):
            data['courses'] = []
            for course in self.courses:
                data['courses'].append(course.name + ' => ' + course.idnumber)

        if hasattr(self, 'cohorts'):
            data['cohorts'] = []
            for cohort in self.cohorts:
                data['cohorts'].append(cohort)

        return json.dumps(d, **kwargs)

    def to_json(self, **kwargs):
        return json.dumps(self.__dict__, **kwargs)

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
        return [key for key in keys if getattr(self, key, None) is not None]

    def get_custom_field(self, name, default=None):
        return getattr(self, 'custom_profile_'+name, default)

    def set_custom_field(self, name, value):
        return setattr(self, 'custom_profile_'+name, value)

    def __sub__(self, other):

        for to_add in set(other.get_custom_field_keys()) - set(self.get_custom_field_keys()):
            ns = NS2()
            ns.status = 'add_custom_profile_field_to_user'
            ns.left = self
            ns.right = other
            param = NS2()
            plain = self.plain_name_of_custom_field(to_add)
            param.value = other.get_custom_field(plain)
            param.field = plain
            ns.param = param
            yield ns

        for to_remove in set(self.get_custom_field_keys()) - set(other.get_custom_field_keys()):
            ns = NS2()
            ns.status = 'remove_custom_profile_field_to_user'
            ns.left = self
            ns.right = other
            param = NS2()
            plain = self.plain_name_of_custom_field(to_remove)
            param.value = self.get_custom_field(plain)
            param.field = plain
            ns.param = param
            yield ns

        for field in self.get_custom_field_keys():
            left = self.get_custom_field(field)
            right = self.get_custom_field(field)

            if left != right:
                ns = NS2()
                ns.status = 'custom_profile_value_changed'
                ns.left = self
                ns.right = other
                param = NS2()
                param.value = other.value
                param.field = self.name
                ns.param = param
                yield ns


