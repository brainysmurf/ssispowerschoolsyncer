"""
A bit odd to have this as a part of the 'model'
but when you consider that the model in his package represents anything that can be different
from each other,
and how those differences are handeld changes, it does actually make sense
"""
from psmdlsyncer.utils import NS, weak_reference
from psmdlsyncer.models.base import BaseModel

class ParentLink(BaseModel):
    def __init__(self, parent_idnumber, child_idnumber=None):
        self.parent_idnumber = self.ID = self.idnumber = parent_idnumber
        self.children = []

    def add_child(self, child_idnumber):
        self.children.append(child_idnumber)

    def __sub__(self, other):
        if self.children != other.children:
            for to_add in set(other.children) - set(self.children):
                ns = NS()
                ns.status = 'associate_child_to_parent'
                ns.left = self
                ns.right = other
                ns.param = NS()
                ns.param.child = to_add
                ns.param.parent = self.parent_idnumber
                yield ns

            for to_remove in set(self.children) - set(other.children):
                ns = NS()
                ns.status = 'deassociate_child_from_parent'
                ns.left = self
                ns.right = other
                ns.param = NS()
                ns.param.child = to_remove
                ns.param.parent = self.parent_idnumber
                yield ns
