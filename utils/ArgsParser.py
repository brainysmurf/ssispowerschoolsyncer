class HoldPassedArugments:
    """
    Class that uses the argsparse module and puts data into the passed object
    """

    def __init__(self, *switches, **strings):
        """
        switches are used for boolean values
        strings are usef for passed values
        """
        import argparse
        import sys

        parser = argparse.ArgumentParser()
        for switch in switches:
            parser.add_argument('--' + switch, action='store_true')
        for string in strings.keys():
            parser.add_argument('-' + string, action='store', dest=string, default=strings[string])
        self.arguments = parser.parse_args(sys.argv[1:])
        #for key, value in vars(parser.parse_args(sys.argv[1:])).items():
        #    setattr(self.arguments, key, value)

class O:
    pass

if __name__ == "__main__":


    hello = O()
    Me(hello)
    print(hello.automagic_emails)
