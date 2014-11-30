from psmdlsyncer.settings import config, config_get_section_attribute

from psmdlsyncer.models.datastores.autosend import AutoSendTree

from psmdlsyncer.utils import NS

from psmdlsyncer.sql import MoodleDBSession

database = MoodleDBSession()

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

if __name__ == "__main__":

	autosend = AutoSendTree()
	autosend.process()

	html_start = """
<table class="userinfotable">
<tbody>"""

	feedback_row = """
<tr>
<td>{course_name}</td>
<td><a href="{url}">View (if available)</a></td>
</tr>"""

	email_row = """
<tr>
<td>{course_name}</td>
<td><a href="mailto:{email}">{name}</a></td>
</tr>"""

	html_end = """</tbody>
</table>"""


	for student_key in autosend.students.get_keys():
		student = autosend.students.get_key(student_key)
		user = database.get_user_from_idnumber(student.num)
		database_id = str(user.id)  #FIXME: Should do this from within the model!

		ns = NS()

		feedback_rows = [
			feedback_row.format(**dict(
				course_name="Forums (All Classes)",
				url="https://dragonnet.ssis-suzhou.net/mod/forum/user.php?id=" + database_id))
		]

		if student.homeroom_teacher:
			email_rows = [
				email_row.format(**dict(
					course_name="Homeroom Teacher",
					email=student.homeroom_teacher.email,
					name=student.homeroom_teacher.lastfirst
					))
			]

		for group in student.groups:

			course = group.course
			course_obj = database.get_course_from_idnumber(course.ID)
			if not course_obj:
				continue
			course_id = str(course_obj.id)

			feedback_rows.append(feedback_row.format(**dict(
				course_name=course.name,
				url="https://dragonnet.ssis-suzhou.net/course/user.php?mode=grade&id=" + course_id + "&user="+ database_id
				)))

			if 'HROOM' in course.ID:
				continue

			for teacher in group.teachers:
				email_rows.append(email_row.format(**dict(
					course_name=course.name,
					email=teacher.email,
					name=teacher.lastfirst
					)))

		feedback_html = html_start + "".join(feedback_rows) + html_end
		email_html = html_start + "".join(email_rows) + html_end

		try:
			database.update_table('user_info_datum', where={'userid':database_id, 'fieldid':2},
				data=email_html)
		except NoResultFound:
			database.insert_table('user_info_datum',
					fieldid=2,
					dataformat=1,
					userid=database_id,
					data=email_html
				)
		except MultipleResultsFound:
			print("Multiple entries for contacts user_data_info for {}".format(student))
	
		try:
			database.update_table('user_info_datum', where={'userid':database_id, 'fieldid':3},
				data=feedback_html)
		except NoResultFound:
			database.insert_table('user_info_datum',
					fieldid=3,
					dataformat=1,
					userid=database_id,
					data=email_html
				)
		except MultipleResultsFound:
			print("Multiple entries for feedback user_data_info for {}".format(student))




