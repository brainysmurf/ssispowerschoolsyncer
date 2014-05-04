"""
A bit odd to have this as a part of the 'model'
but when you consider that the model in his package represents anything that can be different
from each other,
and how those differences are handeld changes, it does actually make sense
"""
from psmdlsyncer.utils import NS
from psmdlsyncer.models.base import BaseModel

class CustomProfile(BaseModel):
    def __init__(self, idnumber, name, value, useridnumber):
        """
        Here, idnumber has to be unique, so it takes the useridnumber plus the name of the field
        """
        self.idnumber = idnumber
        self.useridnumber = useridnumber
        self.name = name
        self.value = value

    def differences(self, other):
        if not self.value == other.value:
            # Make NS with information about changes
            ns = NS()
            ns.status = 'custom_profile_value_changed'
            ns.left = self
            ns.right = other
            param = NS()
            param.value = other.value
            param.field = self.name
            ns.param = param
            yield ns

    __sub__ = differences
