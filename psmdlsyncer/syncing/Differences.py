from psmdlsyncer.importing import InfoController, Moodle, AutoSend, PostFix
from psmdlsyncer.php import ModUserEnrollments
from psmdlsyncer.settings import config_get_section_attribute

class Differences:
    """
    PROCESSES DIFFERENCES BETWEEN TWO OBJECTS AND RELAYS TO THE RIGHT PLACE
    """

if __name__ == "__main__":
    moodle = Moodle()
    autosend = AutoSend()
    postfix = PostFix()
    mod = ModUserEnrollments()

    sync_moodle = config_get_section_attribute('MOODLE', 'sync')
    check_email = config_get_section_attribute('EMAIL', 'check_accounts')
    dispatcher = {}
    
    if check_email:
        dispatcher['new_student'] = mod.no_email
        dispatcher['departed_student'] = None

        for item in autosend - postfix:
            dispatch = dispatcher.get(item.status)
            if dispatch:
                if hasattr(item, 'param') and item.param:
                    if not isinstance(item.param, list):
                        item.param = [item.param]
                    dispatch(*item.param)

    if sync_moodle:
        dispatcher['new_student'] = mod.new_student
        dispatcher['departed_student'] = None

    for item in autosend - moodle:
        dispatch = dispatcher.get(item.status)
        if dispatch:
            if hasattr(item, 'param') and item.param:
                if not isinstance(item.param, list):
                    item.param = [item.param]
                dispatch(*item.param)

