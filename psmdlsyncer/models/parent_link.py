"""
A bit odd to have this as a part of the 'model'
but when you consider that the model in his package represents anything that can be different
from each other,
and how those differences are handeld changes, it does actually make sense
"""
from psmdlsyncer.utils import NS, weak_reference
from psmdlsyncer.models.base import BaseModel

class ParentLink(BaseModel):
    def __init__(self, idnumber, parent, child):
        self.idnumber = self.ID = idnumber
        self.parent = weak_reference(parent)
        self.child = weak_reference(child)

    def differences(self, other):
        if self.parent != other.parent:
            # wrong parent!
            pass
        if self.child != other.child:
            # wrong!
            pass

    __sub__ = differences
