from psmdlsyncer.sql import MoodleDBSession
from psmdlsyncer.models.datastores.autosend import AutoSendTree
from psmdlsyncer.php import ModUserEnrollments

dry_run = True

if __name__ == "__main__":
	dnet = MoodleDBSession()
	mod = ModUserEnrollments()


	not_students = []
	cohorts = ['parentsALL', 'teachersALL']
	for cohort in cohorts:
		users = dnet.users_enrolled_in_this_cohort(cohort)
		not_students.extend( [u.idnumber for u in users] )

	dnet = MoodleDBSession()
	enrollments = dnet.bell_schedule()

	count = 0

	for enrollment in enrollments:
		if enrollment.rolename == 'student' and enrollment.userID in not_students:
			count = count + 1
			dry_run and print(enrollment)
			role = "parent" if enrollment.userID.endswith('P') else "teacher"
			not dry_run and mod.unenrol_user_from_course(enrollment.userID, enrollment.courseID)
			not dry_run and mod.enrol_user_into_course(enrollment.userID, enrollment.courseID, enrollment.groupName, enrollment.groupIdNumber, role)

	print("Total {}".format(count))