"""
DATABASEACTIVITYEXTENDER

SOME CLASSES THAT ARE USEFUL FOR EXTENDING MOODLE'S DATABASE MODULE

"""

from psmdlsyncer.sql import MoodleDBConnection

class FieldObject(MoodleDBConnection):
    """

    """

    def __init__(self, database_name, field_name, samples=None):
        super().__init__()
        self.use_samples = samples
        if not self.use_samples:
            self.database_name = database_name
            self.database_id = self.call_sql("select id from ssismdl_data where name = '{}'".format(self.database_name))[0][0]
            self.field_name = field_name

    def all_values(self):
        if self.use_samples:
            return self.use_samples
        values = self.call_sql("select param1 from ssismdl_data_fields where name = '{}' and dataid = {}".format(self.field_name, self.database_id))[0][0]
        values = values.split('\r\n')
        return values

    def default_value(self):
        return self.all_values()[0]

class UpdateField(MoodleDBConnection):
    """
    Class that is used to update a field in a database module
    """

    def __init__(self, database_name, field_name):
        super().__init__()
        self.field_name = field_name
        self.target = self.sql(
            "select ssismdl_data_fields.id from ssismdl_data join ssismdl_data_fields on (ssismdl_data.name = '{}' and ssismdl_data.id = ssismdl_data_fields.dataid and ssismdl_data_fields.name = '{}')"
            .format(database_name, field_name)
            )

        self.target_id = self.target()[0][0]

    def update_menu(self, value):
        """
        
        """
        if self.target_id is None:
            return
        if isinstance(value, list):
            value = "\r\n".join(value)
        command = "update ssismdl_data_fields set param1 = '{}' where id = {}".format(value, self.target_id)
        try:
            self.call_sql(command)
        except:
            print("I was unable to issue the following sql command: {}".format(command))


class ProfileUpdater(MoodleDBConnection):

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

