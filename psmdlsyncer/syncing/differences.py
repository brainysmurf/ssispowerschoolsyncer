import logging
from psmdlsyncer.utils.modifications import ModificationStatement
from psmdlsyncer.utils import NS2
from psmdlsyncer.syncing.templates import DefaultTemplate
from psmdlsyncer.settings import config_get_section_attribute

class DetermineChanges:
    """
    BOILERPLATE STUFF FOR MAKING THE WHEEL TURN
    LEFT IS "HAVE"
    RIGHT IS "NEED"
    """
    def __init__(self, left, right, template_klass=None, **kwargs):

        self.left = left
        self.right = right

        if not self.left._processed:
            self.left.process()
        if not self.right._processed:
            self.right.process()

        if config_get_section_attribute('DEBUGGING', 'inspect_datastores'):
             print('Inside DetermineChange __init__')
             from IPython import embed
             embed()
             exit()

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
        # if self._re_process: #self._re_process:
        #     self.logger.info('REPROCESSING')
        #     self.left.re_process()
        #     # You don't need to re_process self.right
        #     # because that's the stuff you "need", and that hasn't changed
        #     self.go()

    def go(self, **kwargs):
        debug = config_get_section_attribute('DEBUGGING', 'print_dispatches')
        for item in self.subtract():
            if self.template and hasattr(item, 'status'):
                if item.status in ['new_teacher', 'new_student']:
                    self._repeat = True
                dispatch = self.template.get(item.status)
            else:
                dispatch = None
            if dispatch:
                debug and print(item)
                dispatch(item)
            else:
                #TODO: Handle unrecognized statuses here
                self.logger.warning("This item wasn't handled, because a handler ({}) wasn't defined!".format(item.status))

            #input('::')


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

        # NOTE, removed custom_profile_fields and timetable_datas

        subbranches = [
        'cohorts', 'courses', 'teachers', 'students',
        'groups', 'parents', 'parent_links', 'online_portfolios'
        ] # self.left.get_subbranches()

        for subbranch in subbranches:
            self.default_logger("Subbranch: {}".format(subbranch))

            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)
            self.default_logger("There are {} items in {}'s left branch".format(len(right_branch), subbranch))
            self.default_logger("There are {} items in {}'s right branch".format(len(right_branch), subbranch))

            self.default_logger("Looking for new {}:".format(subbranch))

            # Loop through missing stuff and do with it what we must
            for key in right_branch.keys() - left_branch.keys():
                yield ModificationStatement(
                    left = left_branch.get(key),
                    right = right_branch.get(key),
                    status = NS2.string("new_{term}", term=subbranch[:-1]),
                    param = key
                    )

        # Now go through the model and inspect the individual items
        # We have to go through each key on the left side, and on the right

        for subbranch in subbranches:
            self.default_logger("Individual items: {}".format(subbranch))
            left_branch = self.get_subbranch(self.left, subbranch)
            right_branch = self.get_subbranch(self.right, subbranch)

            # Left side:
            for item_key in left_branch:
                item_left = left_branch.get(item_key)
                item_right = right_branch.get(item_key)
                if item_left and item_right:

                    # The model itself defines how to look at each item with __sub__
                    # And we just yield that result
                    for left_minus_right in item_left - item_right:
                        yield ModificationStatement(
                            left = left_minus_right.left,
                            right = left_minus_right.right,
                            status = left_minus_right.status,
                            param = left_minus_right.param
                            )

            # short circuit out of this

            if subbranch in ["parent_links", "online_portfolios"]:
                # not compatible with the below, especially with make, because it wants the child
                continue

            # Right side:
            for item_key in right_branch:
                item_left = left_branch.get(item_key)
                item_right = right_branch.get(item_key)

                # Same principal as with the left side, but
                # there is a special case where, there is something on the right
                # but nothing on the left
                # The modification statement for "new_" will be spit out by the above
                # so we can just make a proxy object in order to manufacture the yield statements
                if item_right and not item_left and item_right.idnumber:

                    # Makes an empty, default one
                    fake = getattr(self.left, subbranch).\
                            make(item_right.idnumber)

                    # Notice fake - item_right
                    for right_minus_left in fake - item_right:
                        yield ModificationStatement(
                            left = right_minus_left.left,
                            right = right_minus_left.right,
                            status = right_minus_left.status,
                            param = right_minus_left.param
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
