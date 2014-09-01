from psmdlsyncer.settings import config,  config_get_section_attribute

from psmdlsyncer.models.datastores.autosend import AutoSendTree

if __name__ == "__main__":

		autosend = AutoSendTree()
		autosend.process()
		autosend.build_automagic_emails()