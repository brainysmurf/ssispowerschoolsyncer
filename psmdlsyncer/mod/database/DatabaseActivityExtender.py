"""
DATABASEACTIVITYEXTENDER

SOME CLASSES THAT ARE USEFUL FOR EXTENDING MOODLE'S DATABASE MODULE

"""

from psmdlsyncer.sql import MoodleDBSession

class FieldObject(MoodleDBSession):
    """

    """

    def __init__(self, database_name, field_name):
        super().__init__()
        self.database_name = database_name
        self.database_id = self.get_column_from_row('data', 'id', name=self.database_name)
        self.field_name = field_name

    def all_values(self):
        sections = self.get_column_from_row('data_fields', 'param1', name=self.field_name, dataid=self.database_id)
        return sections.split('\r\n')

    def default_value(self):
        return self.all_values()[0]

class UpdateField(MoodleDBSession):
    """
    Class that is used to update a field in a database module
    """

    def __init__(self, database_name, field_name):
        super().__init__()
        self.field_name = field_name

        with self.DBSession() as session:
            DataFields = self.table_string_to_class('data_fields')
            Data = self.table_string_to_class('data')

            statement = session.query(DataFields).select_from(Data).\
                join(DataFields, self.and_(
                    Data.name==database_name,
                    Data.id == DataFields.dataid,
                    DataFields.name == field_name
                    )
                )

        self.target = statement.one()
        self.target_id = self.target.id

    def update_menu(self, value):
        """
        
        """
        if self.target_id is None:
            return
        if isinstance(value, list):
            value = "\r\n".join(value)

        self.update_table('data_fields', where=dict(id=self.target_id), param1=value)

class ProfileUpdater(MoodleDBSession):

    def update_profile_fields_for_user(user):
        """
        Takes any variables in user that begins with "profile_extra"
        and adds them to the right database area so that it registers in Moodle
        Boolean only, if you need text areas use one of the randome ID things
        """
        
        for key, value in [item for itme in luser.__dict__.items() if item[0].startswith('profile_extra_')]:
             results = self.get_table('ssismdl_user_profile_field',
                               shortname = key)
             if not results:
                #TODO: Inform admin that you need to create it
                #TODO? Create it for them???
                continue

             fieldid = results[0][0]

             if hasattr(user, 'database_id') and user.database_id:
                 where = {'userid':user.database_id, 'fieldid':fieldid}
                 self.update_or_insert('ssismdl_user_profile_data',
                                      where=where,
                                      userid=user.database_id,
                                      fieldid=fieldid,
                                      data='1',
                                      dataformat='0')

