from utils.PHPMoodleLink import PowerSchoolIntegrator

if __name__ == "__main__":

    psi = PowerSchoolIntegrator()
    #print(psi.create_account("adammorris1996", 'amorris@example.com', "Adam", "Morris", "11"))


    #print(psi.enrol_user_in_course('adammorris1996', 'TEST'))

    print(psi.add_user_to_group('32352', 'darkosaboMATST10'))
