"""
A bit odd to have this as a part of the 'model'
but when you consider that the model in his package represents anything that can be different
from each other,
and how those differences are handeld changes, it does actually make sense
"""
from psmdlsyncer.utils import NS
from psmdlsyncer.models.base import BaseModel

class Cohort(BaseModel):
    def __init__(self, idnumber):
        """
        Doesn't do much!
        """
        self.idnumber = idnumber   # the name of the field

    def __sub__(self, other):
        return ()

