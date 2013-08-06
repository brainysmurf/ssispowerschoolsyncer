from psmdlsyncer.utils.DB import DragonNetDBConnection
from psmdlsyncer.settings import config

mdl = config['MOODLE']

db = DragonNetDBConnection(mdl.get('db_username'), mdl.get('db_password'), mdl.get('db_host'), mdl.get('db_name'))
this = db.get_teaching_learning_categories()
from IPython import embed
embed()
