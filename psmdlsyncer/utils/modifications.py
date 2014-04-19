class ModificationStatement:

    def __init__(self, left, right, status, param):
        self.left = left
        self.right = right
        self.status = status
        self.param = param

    def __repr__(self):
        return "{0.__class__.__name__} -- status:'{0.status}' param:'{0.param}' left:'{0.left}' right:'{0.right}'".format(  self)
