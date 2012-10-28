old_code = """
class Controller():
    'TODO: Recycle this code if needed, otherwise, delete'

    def __init__(self, path_to_database, klass):
        self.path = path_to_database
        self.klass = klass
        prevdb = path_to_database + '.db'
        if os.path.exists(prevdb):
            if not debug:
                # This allows me to test that it works
                os.rename(prevdb, path_to_database + ".prevdb.db")
            self._prevdb = path_to_database + ".prevdb.db"  # don't open until later
        else:
            self._prevdb = None
        self._db = shelve.open(path_to_database, writeback=True)
        self.errors = DocumentErrors(k_path_to_errors)

    def document_error(self, kind, content):
        self.errors.document_errors(kind, content)

    def get(self, key):
        try:
            return self._db[key]
        except KeyError:
            return None

    def get_kwargs(self, **kwargs):
        result = []
        for key in self.keys():
            this = self.get(key)
            if this.compare_kwargs(**kwargs):
                result.append(this)
        return result

    def keys(self):
        return self._db.keys()

    def add(self, *args, **kwargs):
        key = str(args[0])
        self._db[key] = self.klass(*args, **kwargs)

    def update(self, id, key, value):
        'Adds information to the database'

        if not id:
            raise CannotPassMeNone('Controller.update')
        item = self.get(id)
        if not item:
            raise NoSuchStudent(id)
        # If the object defines a method with the same name as
        # update_$key, use that method
        call = "update_{}".format(key)
        if hasattr(item, call):
            getattr(item, call)(value)
        else:
            item.update(key, value)

    def objects(self):
        'Return a generator that builds the objects in the database'
        raise NotImplemented
        
    def output(self, file=None):
        if not file:
            keys = list(self._db.keys())
            keys.sort()
            for key in self._db.keys():
                print(self._db[key])
        else:
            pass

    def output_filter(self, filter):
        for key in self._db.keys():
            this = self.get(key)
            if filter(this):
                print(this)

    def compare_databases(self):
        'Compares previous database with current one'
        if self._prevdb:
            self._prevdb = self._prevdb[:-3]
            self._prevdb = shelve.open(self._prevdb)
            for key in self.keys():
                new = self._db[key]
                try:
                    old = self._prevdb[key]
                except KeyError:
                    new.database_new(new)
                    continue
                new.database_compare(old)

            newkeys = list(self.keys())
            for key in self._prevdb.keys():
                if not key in newkeys:
                    print(self._prevdb[key])
                    print("Old student has gone away!")"""
