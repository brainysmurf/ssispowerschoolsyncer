"""
A bit odd to have this as a part of the 'model'
but when you consider that the model in his package represents anything that can be different
from each other,
and how those differences are handeld changes, it does actually make sense
"""
from psmdlsyncer.utils import NS, weak_reference
from psmdlsyncer.models.base import BaseModel

class MRBSEditor(BaseModel):
    def __init__(self, idnumber, userid=None):
        self.idnumber = self.ID = idnumber
        self.userid = userid
