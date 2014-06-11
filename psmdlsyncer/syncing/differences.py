from psmdlsyncer.settings import logging
from psmdlsyncer.utils.modifications import ModificationStatement
from psmdlsyncer.utils import NS2
from psmdlsyncer.syncing.templates import DefaultTemplate

class DetermineChanges:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, template_klass=None, **kwargs):
        self.left = left
        self.right = right

        self.left.process()
        self.right.process()

        if True:
            print('Inside DetermineChange __init__')
            from IPython import embed
            embed()

        if not template_klass:
            self.template = DefaultTemplate()
        else:
            self.template = template_klass()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.default_logger = self.logger.debug   # change this to debug for verbosity
        self.default_logger("Inside FindDifferences")
        self.default_logger("Left: {}".format(self.left))
        self.default_logger("Right: {}".format(self.right))
        self._re_process = False
        self.go()
        if self._re_process: #self._re_process:
            self.logger.info('REPROCESSING')
            self.left.re_process()
            # You don't need to re_process self.right
            # because that's the stuff you "need", and that hasn't changed
            self.go()

    def go(self, **kwargs):
        for item in self.subtract():
            if self.template and hasattr(item, 'status'):
                if item.status in ['new_teacher', 'new_student']:
                    self._repeat = True
                dispatch = self.template.get(item.status)
            else:
                dispatch = None
            if dispatch:
                dispatch(item)
            else:
                #TODO: Handle unrecognized statuses here
                self.logger.warning("This item wasn't handled, because a handler ({}) wasn't defined!".format(item.status))

    def get_subbranch(self, tree, subbranch):
        """
        Returns the subbranch of tree
        TODO: Check and throw KeyError exception if key is missing
        """
        return tree.__class__._store[tree.__class__.qual_name_format.format(
                branch=tree.__class__.__name__,
                delim=tree.__class__.qual_name_delimiter,
                subbranch=subbranch)]

    def subtract(self):
        """
        Yields ModificationStatements, which get fed back into the go method, which in turn
        dispatches the message to lower-level routines
        The ModfiicationStatements represent the changes that have occured.
        This method inspects meta data and passes on further inspections to the model itself
        """

        # First, process the meta data about the model, which
        # is basically just checking the keys for additions
        # then looking for differences between each item
        # then we check the keys for subtractions

        assert(len(self.left.get_subbranches()) == len(self.right.get_subbranches()))

        subbranches = [
        'cohorts', 'course_metadatas', 'courses', 'teachers', 'students',
        'groups', 'parents', 'parent_links', 'timetable_datas', 'custom_profile_fields', 'online_portfolios'
        ] # self.left.get_subbranches()

        for subbranch in subbranches:
            self.default_logger("Subbranch: {}".format(subbranch))

            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)
            self.default_logger("There are {} items in {}'s left branch".format(len(right_branch), subbranch))
            self.default_logger("There are {} items in {}'s right branch".format(len(right_branch), subbranch))

            self.default_logger("Looking for new {}:".format(subbranch))

            if subbranch == 'timetable_datas':   # for debugging
                from IPython import embed
                embed()

            # Loop through missing stuff and do with it what we must
            for key in right_branch.keys() - left_branch.keys():
                yield ModificationStatement(
                    left = left_branch.get(key),
                    right = right_branch.get(key),
                    status = NS2.string("new_{term}", term=subbranch[:-1]),
                    param = key
                    )

        # Now go through the model and inspect the individual items
        for subbranch in subbranches:
            self.default_logger("Individual items: {}".format(subbranch))
            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)

            for item_key in left_branch:
                item_left = left_branch.get(item_key)
                item_right = right_branch.get(item_key)
                if item_left and item_right:
                    for left_minus_right in item_left - item_right:
                        yield ModificationStatement(
                            left = left_minus_right.left,
                            right = left_minus_right.right,
                            status = left_minus_right.status,
                            param = left_minus_right.param
                            )

        for subbranch in subbranches:
            self.default_logger("Looking for old {}".format(subbranch))
            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)

            for key in left_branch.keys() - right_branch.keys():
                yield ModificationStatement(
                    left = left_branch.get(key),
                    right = right_branch.get(key),
                    status = NS2.string("old_{term}", term=subbranch[:-1]),
                    param = key
                    )



if __name__ == "__main__":

    pass
