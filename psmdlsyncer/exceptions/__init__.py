class BasicException(Exception):
    def __init__(self, it):
        self.it = it

    def __str__(self):
        return repr(self.it)

class NoSuchStudent(BasicException): pass
class CannotPassMeNone(BasicException): pass
class UnknownGrade(BasicException): pass
class NoHomeroom(BasicException): pass
class StudentChangedName(Exception): pass
class NoStudentInMoodle(Exception): pass
class NoEmailAddress(Exception): pass
class NoParentAccount(Exception): pass
class ParentAccountNotAssociated(Exception): pass
class ParentNotInGroup(Exception): pass
class GroupDoesNotExist(Exception): pass
class StudentNotInGroup(Exception): pass
class MustExit(Exception): pass

__all__ = [NoSuchStudent, CannotPassMeNone, BasicException, UnknownGrade, NoHomeroom,
           StudentChangedName, NoStudentInMoodle, NoEmailAddress, NoParentAccount,
           ParentAccountNotAssociated, ParentNotInGroup, GroupDoesNotExist, StudentNotInGroup,
           MustExit]
