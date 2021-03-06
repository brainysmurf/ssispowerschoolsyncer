import os, json

from psmdlsyncer.files import clear_folder
import gns

class BulkEmailManager:
    path = gns('{config.directories.path_to_postfix}') or '/tmp/bulkemail/results'
    email_lists = {}

    parentsALL = 'usebccparentsALL'
    parentsELEM = 'usebccparentsELEM'
    parentsSEC = 'usebccparentsSEC'
    parentsGRADE = lambda cls, g: 'usebccparentsGRADE'+ str(g)
    parentsHROOM = lambda cls, hr: 'usebccparentsHROOM'+str(hr)
    parentsCHINESE = 'usebccparentsCHINESE'
    parentsCHINESESEC = 'usebccparentsCHINESESEC'
    parentsCHINESEELEM = 'usebccparentsCHINESEELEM'
    parentsCHINESEGRADE = lambda cls, g: 'usebccparentsCHINESEGRADE' + str(g)
    parentsKOREAN = 'usebccparentsKOREAN'
    parentsKOREANSEC = 'usebccparentsKOREANSEC'
    parentsKOREANELEM = 'usebccparentsKOREANELEM'
    parentsKOREANGRADE = lambda cls, g: 'usebccparentsKOREANGRADE' + str(g)
    parentsJAPANESE = 'usebccparentsJAPANESE'
    parentsJAPANESESEC = 'usebccparentsJAPANESESEC'
    parentsJAPANESEELEM = 'usebccparentsJAPANESEELEM'
    parentsJAPANESEGRADE = lambda cls, g: 'usebccparentsJAPANESEGRADE' + str(g)
    parentsGERMAN = 'usebccparentsGERMAN'
    parentsGERMANSEC = 'usebccparentsGERMANSEC'
    parentsGERMANELEM = 'usebccparentsGERMANELEM'
    parentsGERMANGRADE = lambda cls, g: 'usebccparentsGERMANGRADE' + str(g)
    parentsNOTGERMAN = 'usebccparentsNOTGERMAN'
    parentsSWA = 'usebccparentsSWA'
    parentsSWASEC = 'usebccparentsSWASEC'
    parentsSWAELEM = 'usebccparentsSWAELEM'
    parentsSWAGRADE = lambda cls, g: 'usebccparentsSWAGRADE' + str(g)
    parentsNOTSWA = 'usebccparentsNOTSWA'

    teachersGRADE = lambda cls, g: 'usebccteachers' + str(g)

    studentsSEC = 'usebccstudentsSEC'
    studentsGRADE = lambda cls, g: 'usebccstudentsGRADE'+ str(g)
    studentsHOMEROOM = lambda cls, hr: 'usebccstudentsHROOM' + hr

    groups = lambda cls, g: 'usebcc' + g
    groupsPARENTS = lambda cls, g: 'usebcc' + g+'PARENTS'

    parentlink = lambda cls, s: s + 'PARENTS'
    teacherlink = lambda cls, s: s + 'TEACHERS'
    hrlink = lambda cls, s: s + 'HROOM'


    def __init__(self):
        exclude_db_files = lambda x: x.endswith('.db')
        clear_folder(self.path, exclude=exclude_db_files)
        self.cat = type('names', (), {})
        self.add_name('global')
        self.cat.global_ = 'global'
        self.add_name('grades')
        self.cat.grades = 'grades'
        self.add_name('homerooms')
        self.cat.homerooms = 'homerooms'
        self.add_name('classes')
        self.cat.classes = 'classes'
        self.add_name('parentlink')
        self.cat.parentlink = 'parentlink'
        self.add_name('teacherlink')
        self.cat.teacherlink = 'teacherlink'
        self.add_name('homeroomlink')
        self.cat.homeroomlink = 'homeroomlink'
        self.add_name('departments')
        self.cat.departments = 'departments'
        self.add_name('activities')
        self.cat.activities = 'activities'

    def add_name(self, name):
        self.email_lists[name] = BulkEmailName(self.path, name)

    def add_category_to_name(self, category, name):
        self.email_lists[name].add_category(category)

    def add_emails(self, emails, name, category):
        for email in emails:
            self.add_email(email, name, category)

    def add_email(self, email, name, category):
        """
        Adds subcat to a category, also sets up alias information
        """
        if not name in self.email_lists:
            self.email_lists[name] = BulkEmailName(self.path, name)
        self.email_lists[name].add_email(email, category)

    def output_all_aliases(self):
        for name in self.email_lists:
            self.email_lists[name].output_aliases()

    def output_json(self):
        path = gns.config.directories.path_to_bulk_mail_output
        user_id = gns.config.email.wwwdatauserid
        group_id = gns.config.email.wwwdatagroupid
        with open(path, 'w') as f:
            f.write(json.dumps(self.email_lists, default=lambda o: o.categories, sort_keys=True, indent=4))
        os.chown(path, int(user_id), int(group_id))

class BulkEmailName:
    """
    self.name is the name of the directory in which subcategories appear
    """
    ext = '.txt'
    
    def __init__(self, path, name):
        self.path = '{path}/{name}'.format(path=path, name=name)
        self.name = name
        self.categories = {}
        clear_folder(self.path)

    def output_aliases(self):
        with open(self.path_to_alias_definitions, 'w') as f:
            for category in self.categories:
                f.write(self.include_statement(category)+'\n')

        for category in self.categories:
            this_path = self.path_to_category(category)
            with open(this_path, 'w') as f:
                f.write('\n'.join(self.category_emails(category)))

    @property
    def path_to_alias_definitions(self):
        return "{path}{ext}".format(path=self.path, ext=self.ext)

    def path_to_category(self, category):
        return "{path}/{category}{ext}".format(path=self.path, ext=self.ext, category=category)

    def include_statement(self, category):
        return gns('{category}{COLON}{SPACE}{include}{path}{SLASH}{category}{ext}', 
                path=self.path, name=self.name, 
                category=category, ext=self.ext, include=":include:")

    def category_emails(self, category):
        return self.categories[category]

    def add_category(self, category, prefixed=True):
        self.categories[category] = []

    def add_email(self, email, category):
        if email is None:
            return
        if not category in self.categories:
            self.add_category(category)
        if not email in self.categories[category]:
            self.categories[category].append(email)

if __name__ == '__main__':

    bm = BulkEmailManager()
    
    bm.add_emails(['here@example.com', 'there@example.com'], bm.cat.global_, bm.parentsELEM)
    bm.add_emails(['here@example.com', 'there@example.com'], bm.cat.parentlink, bm.parentlink('jiyunpark16'))
    bm.add_emails(['here@example.com', 'there@example.com'], bm.cat.teacherlink, bm.teacherlink('jiyunpark16'))
    bm.add_emails(['here@example.com', 'there@example.com'], bm.cat.homeroomlink, bm.hrlink('jiyunpark16'))

    bm.output_all_aliases()
    bm.output_json()

