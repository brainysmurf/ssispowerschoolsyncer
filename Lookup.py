from utils.DB import DragonNetDBConnection
import re
import os

class LookUp(DragonNetDBConnection):

    def __init__(self):
        super().__init__()
        if not self.on_server:
            print("Not on server, using ../postfix files")
        self.domain = "@student.ssis-suzhou.net"
        self.prepare_id_username_map()
        self.prepare_files()

    def read_in_raw(self, path):
        return [l.strip('\n') for l in open(path).readlines() if l.strip('\n')]

    def list_files(self, path):
        """
        Only list files we care about
        """
        return [f for f in os.listdir(path) if not f.startswith('.')]

ls    def prepare_files(self):
        d = {}
        d['space'] = " "
        wittle_patterns = {
            'classes':     (r'[^a-z]', ''),
            'teacherlink': (r'(^[a-z])(.*)$',  '\\1'),
            'homerooms':   (r'[a-z]', ''),
            'parentlink':  (r'(^[a-z])(.*)$', '\\1'),
            }
        wittle_sort = {
            'homerooms':  (r'[^0-9A-Z]', ''),
            }
        for kind in ['classes', 'homerooms', 'grades', 'parentlink', 'teacherlink', 'departments']:
            d['kind'] = kind
            d['kindpath'] = '../postfix/{kind}'.format(**d)
            happy_headers = []
            pattern = wittle_patterns.get(kind)
            with open('../output/lookup/{kind}.txt'.format(**d), 'w') as output_file:
                files = self.list_files('{kindpath}'.format(**d))

                sort_pattern = wittle_sort.get(kind)
                if sort_pattern:
                    sort_files = [(re.sub(sort_pattern[0], sort_pattern[1], f), f) for f in files]
                    sort_files.sort(key=lambda x: x[0])
                    files = [f[1] for f in sort_files]
                
                for h in files:
                    header = h[:-4]
                    if pattern:
                        header = re.sub(pattern[0], pattern[1], header)
                    if not header in happy_headers:
                        happy_headers.append(header)
                if len(happy_headers) > 10:
                    do_jumps = True
                    output_file.write('Here are some shortcuts to the areas:<br/>')
                    for header in happy_headers:
                        d['header'] = header
                        output_file.write( '<a href="#{header}">{header}</a>'.format(**d) )
                        if len(header) > 5:
                            output_file.write("<br/>")
                        else:
                            output_file.write(", ")
                else:
                    do_jumps = False

                output_file.write('<br/>')

                for this_file in files:
                    d['header'] = this_file[:-4]  #strip extention
                    usernames = self.read_in_raw('{kindpath}/{header}.txt'.format(**d))
                    output_file.write('\n<br />')
                    if do_jumps:
                        if pattern:
                            happy = re.sub(pattern[0], pattern[1], '{header}'.format(**d))
                        else:
                            happy = "{header}".format(**d)
                        if happy in happy_headers:
                            output_file.write('<a name="{}"></a>'.format(happy))
                            happy_headers.pop(happy_headers.index(happy))
                    output_file.write('<strong><a href="mailto:{header}@student.ssis-suzhou.net">{header}@student.ssis-suzhou.net</a></strong> goes to ...<br />\n'.format(**d))
                    for username in usernames:
                        d['username'] = username
                        d['preusername'] = '<a href="mailto:{username}">'.format(**d)
                        d['postusername'] = '</a>'
                        user_info = self.id_username.get(username, "")

                        if user_info:
                            d['idnum'] = user_info['idnum']
                            d['prename'] = '<a href="http://dragonnet.ssis-suzhou.net/user/profile.php?id={idnum}">'.format(**d)
                            d['name'] = user_info['name']
                            d['postname'] = '</a>'
                            output_file.write( "{prename}{name}{postname} {preusername}(email){postusername}{space}<br />\n".format(**d) )
                        else:
                            output_file.write( "{preusername}{username}{postusername}<br />\n".format(**d) )

if __name__ == "__main__":

    lookup = LookUp()
