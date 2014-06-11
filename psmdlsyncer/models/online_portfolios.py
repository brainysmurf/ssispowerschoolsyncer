from psmdlsyncer.models.base import BaseModel

class OnlinePortfolio(BaseModel):

    def __init__(self, idnumber):
        self.idnumber = idnumber
