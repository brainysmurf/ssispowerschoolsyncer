
import re
import datetime

class Result:

    def __init__(self, rows):
        self.email_pattern = r'[0-9A-Za-z\.-]+@[0-9A-Za-z\.-]+'
        self.rows = rows

    def count(self):
        return len(self.rows)

    def __str__(self):
        #for row in self.rows:
        #    print(row)
        #    print()
        return "{} hits".format(self.count())

class Date(Result):
    def __init__(self, rows, date):
        super().__init__(rows)
        self.date = date
        self.init()
        search_key = self.date.strftime(self.date_format)
        if date.day < 10:
            search_key = search_key.replace('0', ' ')
        self.search_key = search_key
        self.rows = [r for r in rows if r.startswith(self.search_key)]

    def init(self):
        self.date_format = '%b %d'
        self.one_day = datetime.timedelta(days=1)

    def __str__(self):
        return "{} hits on {}".format(self.count(),
                                      self.date.strftime(self.date_format))

class Today(Date):
    def __init__(self, rows):
        super().__init__(rows, datetime.datetime.today())

class Yesterday(Date):
    def __init__(self, rows):
        self.init()
        super().__init__(rows, datetime.datetime.today() - self.one_day)

class Tomorrow(Date):
    def __init__(self, rows):
        self.init()
        super().__init__(rows, datetime.datetime.today() + self.one_day)

class Domains:
    def __init__(self):
        self.domains = {}

    def add(self, domain, email):
        if not domain in list(self.domains.keys()):
            self.domains[domain] = []
        if not email in self.domains[domain]:
            self.domains[domain].append(email)

    def keys(self):
        return list(self.domains.keys())

    def count_domains(self):
        return len(list(self.domains.keys()))

    def count_emails(self):
        count = 0
        for domain in self.domains.keys():
            count += len(self.domains[domain])
        return count

    def __getitem__(self, item):
        return self.domains[item]

class Results:
    """
    Takes a look at things.
    """

    def __init__(self):
        self.domains = Domains()

    def domain(self, email):
        """ Get the domain of this email """
        return email[ email.index('@')+1: ]

    def add(self, _list):
        """
        Looks at length of _list and updates the counts and info accordingly
        """
        if _list:
            if len(_list) == 2:
                _to, _orig_to = _list
            elif len(_list) == 1:
                _to = _list[0]
            elif len(_list) == 3:
                _to, _orig_to, _ = _list
            else:
                input("WHAT HAPPENED")
                return

            self.domains.add(self.domain(_to), _to)

    def __str__(self):
        return '\n' + "-" * 50 + "\nThere are {} domains bouncing with {} total emails\n{}".format(
            self.domains.count_domains(),
            self.domains.count_emails(),
            "\n".join( ["{}:\t{} emails\n{}\n".format(d, len(self.domains[d]),
                                                      ", ".join(self.domains[d]) if len(self.domains[d]) < 5 else "...") for d in self.domains.keys()] )
            )
 
class Bounced(Today):
    def __init__(self, rows):
        super().__init__(rows)
        for row in self.rows:
        self.rows = [r for r in self.rows if 'status=deferred' in r or 'status=bounced' in r]
        self.results = Results()
        for row in self.rows:
            self.results.add( re.findall(self.email_pattern, row) )

    def __str__(self):
        return str(self.results)
            
class MailLogReader(Bounced):

    def __init__(self, path):
        self.path = path
        self.raw = [l.strip('\n') for l in open(path).readlines() if l.strip('\n')]

    def filter_bounces(self):
        return Bounced(self.raw)

if __name__ == "__main__":

    mail = MailLogReader('../mail.log')
    print( mail.filter_bounces() )
    
