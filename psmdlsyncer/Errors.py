import datetime

class DocumentErrors():

      def __init__(self, path):
          self.path = path
          self.tracking = {}  # simple dict of writes

      def document_errors(self, kind, content):
          if not kind in list(self.tracking.keys()):
              write_date = True
              self.tracking[kind] = True
          else:
              write_date = False

          with open(self.path + '/' + kind + '.txt', 'a') as f:
              if write_date:
                  f.write(str(datetime.date.today()) + '\n')
              f.write(str(content) + '\n')
