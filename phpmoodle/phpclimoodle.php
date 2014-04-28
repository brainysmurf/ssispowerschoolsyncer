<?php

error_reporting(1);
define(CLI_SCRIPT,1);
require_once( '../../config.php');
require_once('../../cohort/lib.php');
require_once('../../enrol/locallib.php');
require_once('../../group/lib.php');
require_once('../../lib/grouplib.php');

class moodlephp
{
    private $ADMIN_USER_ID = 2;
    private $DEFAULT_PASSWORD = "changeme";

    function __construct($args)
    {
      global $DB;

      $s = $DB->get_record_select( 'role', 'name = ?', array("Student") );
      $this->STUDENT_ROLE_ID = $s->id;
      $s = $DB->get_record_select( 'role', 'name = ?', array('Parent') );
      $this->PARENT_ROLE_ID = $s->id;
      $s = $DB->get_record_select( 'role', 'name = ?', array('Teacher') );
      $this->TEACHER_ROLE_ID = $s->id;

      $which_function = $args[0];
      array_shift($args);
      $r = $this->$which_function($args);
      echo $r;
    }

    private function create_cohort($idnumber, $name, $description)
    {
      $new_cohort = new stdClass;
      $new_cohort->idnumber = $idnumber;
      $new_cohort->name = $name;
      $new_cohort->description = $description;

      $cohortID = cohort_add_cohort($new_cohort);
      echo "Added new cohort ".$name;
      return $cohortID;
    }

    private function add_user_to_cohort($args)
    {
      $idnumber = $args[0];
      $cohortidnumber = $args[1];

      global $DB;
      if( !$user = $this->getUserByIDNumber($idnumber) ) {
        return "-1 Could not find user $idnumber while adding cohort $cohortidnumber";
      }

      if( ! ($cohort = $DB->get_record_select( 'cohort', "idnumber = ?", array($cohortidnumber) )) ) {
        //$cohortID = $this->create_cohort($idnumber, $cohortidnumber, '');
        return "-1 Cohort $cohortidnumber does not exist";
      }

      $cohortID= $cohort->id;
      $userID = $user->id;
      // workaround, instead of using cohort_existing_selector, due to bug
      $cohort_membership = $DB->get_record_select('cohort_members', 'cohortid = ? and userid = ?', array('cohortid'=>$cohortID,'userid'=>$userID));
      if( $cohort_membership ) {
        return "0 $idnumber is already a member of this cohort $cohortidnumber !";
      }

      $r = cohort_add_member($cohortID, $userID);
      echo "Added $idnumber to cohort $cohortidnumber" ;
      return $r;
    }

    private function remove_user_from_cohort($args) {
      $idnumber = $args[0];
      $cohortidnumber = $args[1];

      global $DB;
      if( !$user = $this->getUserByIDNumber($idnumber) ) {
    	  return "-1 Could not find user $idnumber while adding cohort $cohortidnumber";
      }

      if ( $cohort = $DB->get_record_select( 'cohort', 'idnumber = ?', array($cohortidnumber) )) {
        $cohortID= $cohort->id;
        $userID = $user->id;
        // workaround, instead of using cohort_existing_selector, due to bug
        $cohort_membership = $DB->get_record_select('cohort_members', 'cohortid = ? and userid = ?', array('cohortid'=>$cohortID,'userid'=>$userID));
        if ( !($cohort_membership) ) {
          return "0 $idnumber  is not a member of the cohort $cohortidnumber";
        }
      } else {
        return "-1 Could not find cohort $cohortidnumber";
    }

      $r = cohort_remove_member($cohortID, $userID);
      echo "Removed $idnumber from cohort $cohortidnumber";
      return $r;
    }

    private function create_account( $args )
    {
      $username = $args[0];
      $email = $args[1];
      $firstname = $args[2];
      $lastname = $args[3];
      $idnumber = $args[4];

      if ( $this->user_does_exist(array($username)) ) {
        return "0 This username is already taken: $username";
      }

      global $DB, $CFG;

      try {
	        $user = create_user_record( $username, "changeme" );  // changeme forces password reset
      }

      catch( Exception $e ) {
          var_dump($e);
          return "-1 Could not create account for $username";
      }

      $user->email = trim($email);
      $user->firstname = trim($firstname);
      $user->lastname = trim($lastname);
      $user->idnumber = trim($idnumber);
      $user->maildigest = 1;  // All my users should use digest, for the love of god
      $user->city = 'Suzhou';
      $user->country = 'CN';

      $DB->update_record( 'user' , $user );

      return "0";
    }

    private function user_does_exist($args)
    {
      $username = $args[0];

      global $DB, $CFG;
      $s = $DB->get_record_select( 'user' , 'username = ?', array($username) );
      return $s;
    }

    private function associate_child_to_parent($args) {
      $parent_idnumber = $args[0];
      $child_idnumber = $args[1];

      try {
        if( $parent = $this->getUserByIDNumber( $parent_idnumber ) and $child = $this->getUserByIDNumber($child_idnumber) ) {
  	      $context = get_context_instance( CONTEXT_USER , $child->id );
          role_assign( $this->PARENT_ROLE_ID, $parent->id, $context->id );
        } else {
          return "-1 Either could not find parent $parent_idnumber or couldn't find child $child_idnumber";
        }
      } catch( Exception $e ) {
        var_dump($e);
        return "-1 Could not associate child $child_idnumber to parent $parent_idnumber";
      }

      return "0";
    }

    private function get_group_from_name($group_name) {
      // this only works properly because in draognnet group names are guaranteed to be unique
      // ( teacher username + course idnumber )
      global $DB;
      return $DB->get_record('groups', array('name'=>$group_name), '*');
    }

    private function add_user_to_group($args)
    {
      $user_idnum = $args[0];
      $group_name = $args[1];

      $user = $this->getUserByIDNumber($user_idnum);
      $group = $this->get_group_from_name($group_name);

      if (!$group) {
        return "-1 Group $group_name does not exist! Cannot add user $user_idnum";
      }

      if (!$user) {
        return "-1 User $user_idnum does not exist! Cannot add him to group $group_name";
      }

      groups_add_member($group, $user);
    }

    private function remove_user_from_group($args) {
      $user_idnum = $args[0];
      $group_name = $args[1];

      global $DB;

      $user = $this->getUserByIDNumber($user_idnum);
      $group = $this->get_group_from_name($group_name);

      if (!$group) {
        return "-1 Group $group_name does not exist! Cannot remove user $user_idnum";
      }

      if (!$user) {
        return "-1 User $user_idnum does not exist! Cannot remove him to group $group_name";
      }

      groups_remove_member($group, $user);
    }

    private function delete_group_for_course($args) {
      $group_name = $args[1];

      if ( !$group = $this->get_group_from_name($group_name) ) {
        return "-1 Cannot get group, may because course does not exist?... ".$course_idnumber;
      }

      if (groups_delete_group($group)) {
        echo "PHP says deleted group ";
      } else {
        return "-1 Cannot delete group... ";
      }
    }

    private function create_group_for_course($args)
    {
      $course_idnumber = $args[0];
      $group_name = $args[1];
      global $DB;

      if ( !$course = $DB->get_record('course', array('idnumber'=>$course_idnumber), '*') ) {
        return "-1 Course does not exist!... ".$course_idnumber;
      }

      // check to see if there's one already there
      if ( $group = $this->get_group_from_name($group_name)) {
        return "-1 Group $group_name already there!";
      }

      $group_data = new stdClass;
      $group_data->courseid = $course->id;
      $group_data->name = $group_name;

      if (groups_create_group($group_data)) {
        echo "PHP says Created group ".$group_name;
      } else {
        return "-1 Cannot create group, OH NO!";
      }
    }

    private function enrol_user_in_course($args)
    {
      $useridnumber = $args[0];
      $course_idnumber = $args[1];
      $group_name = $args[2];
      $role = $args[3];

      switch (strtolower($role)) {
        case "student":
          $roleid = $this->STUDENT_ROLE_ID;
          break;
        case "parent":
          $roleid = $this->PARENT_ROLE_ID;
          break;
        case "teacher":
          $roleid = $this->TEACHER_ROLE_ID;
          break;
        default :
          return "-1 No viable role ID was passed ".$role;
      }

      global $DB, $PAGE;

      if( !$user = $this->getUserByIDnumber($useridnumber) ) {
        return "-1 Could not find user $useridnumber when enrolling in course $course_idnumber";
      }

      if ( !$course = $DB->get_record('course', array('idnumber'=>$course_idnumber), '*') ) {
        return "-1 Course does not exist!... $course_idnumber";
      }

      if( !$context = get_context_instance(CONTEXT_COURSE, $course->id, MUST_EXIST) ) {
        return "-1 Could not get context for course $course_idnumber with ID $course->id";
      }

      $manager = new course_enrolment_manager($PAGE, $course);

      if( !is_enrolled($context, $user->id) ) {
    	  $enrolMethod = $DB->get_record('enrol', array('enrol'=>'manual', 'courseid'=>$course->id), '*', MUST_EXIST);
    	  $enrolid = $enrolMethod->id;

    	  $instances = $manager->get_enrolment_instances();
    	  $plugins = $manager->get_enrolment_plugins();

    	  if (!array_key_exists($enrolid, $instances)) {
    	      throw new enrol_ajax_exception('invalidenrolinstance');
        }

    	  $instance = $instances[$enrolid];
    	  $plugin = $plugins[$instance->enrol];

    	  $today = time();

    	  $today = make_timestamp(date('Y', $today), date('m', $today), date('d', $today), 0, 0, 0);
    	  $timestart = $today;
    	  $timeend = 0;

    	  $plugin->enrol_user($instance, $user->id, $roleid, $timestart, $timeend);
    	  echo "PHP says Enrolled $useridnumber into class $course_idnumber as a $roleid";
    	} else {
        echo "Seems like this person was already enrolled!";
      }

      if ( !($group = $this->get_group_from_name($group_name)) ) {
	      //create the group first
        $group_data = new stdClass;
        $group_data->courseid = $course->id;
        $group_data->name = $group_name;

        if (groups_create_group($group_data)) {
    	    echo "PHP says Created group $group_name";
        } else {
          return "-1 Cannot create group, OH NO!";
        }
      }

      if ( !($group) ) {
        $group = $this->get_group_from_name($group_name);
      }

       if( groups_add_member($group, $user) ) {
         echo "PHP says Added (or was already a member) user $useridnumber into group $group_name for course $course_idnumber";
       } else {
         echo "-1 Couldn't add user $useridnumber to group $group_name";
       }
    }

    private function deenrol_user_from_course($args) {
      $useridnumber = $args[0];
      $course_idnumber = $args[1];

      global $DB, $PAGE;

      if( !$user = $this->getUserByIDnumber($useridnumber) ) {
        return "-1 Could not find user $useridnumber when deenrolling from course $course_idnumber";
      }

      if( !$course = $DB->get_record('course', array('idnumber'=>$course_idnumber), '*') ) {
	       return "-1 Course does not exist!... $course_idnumber";
      }

      if( !$context = get_context_instance(CONTEXT_COURSE, $course->id, MUST_EXIST) ) {
	       return "-1 Could not get context for course $course_idnumber with ID $course->id";
      }

      $manager = new course_enrolment_manager($PAGE, $course);

      if( !is_enrolled($context, $user->id) ) {
    	  return "-1 Already not enrolled";
	    }

      $enrolMethod = $DB->get_record('enrol', array('enrol'=>'manual', 'courseid'=>$course->id), '*', MUST_EXIST);
      $enrolid = $enrolMethod->id;

      $instances = $manager->get_enrolment_instances();
      $plugins = $manager->get_enrolment_plugins();

      if (!array_key_exists($enrolid, $instances)) {
	      throw new enrol_ajax_exception('invalidenrolinstance');
      }

      $instance = $instances[$enrolid];
      $plugin = $plugins[$instance->enrol];

      $plugin->unenrol_user($instance, $user->id);

      echo "PHP says de-enrolled {$user->id} from class $course_idnumber";
    }

    private function change_username($args)
    {
      $idnumber = $args[0];
      $new_username = $args[1];
      global $DB;

      $user = $this->getUserByIDNumber($idnumber);
      $user->username = $new_username;

      $DB->update_record($user);
    }

    private function getUserByIDNumber($idnumber)
    {
      global $DB;
      $s = $DB->get_record_select( 'user' , 'idnumber = ?', array($idnumber) );
      return $s;
    }

   private function getUserByUsername($username)
   {
     global $DB;
     $s = $DB->get_record_select( 'user', 'username = ?', array($username) );
     return $s;
   }
}

array_shift($argv);
$newclassmoodle = new moodlephp( $argv );
