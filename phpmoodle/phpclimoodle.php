<?php

error_reporting(1);
define(CLI_SCRIPT,1);
require_once( '../../config.php');
require_once('../../cohort/lib.php');
require_once('../../enrol/locallib.php');
require_once('../../group/lib.php');

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

      $which_function = $args[0];
      array_shift($args);
      $r = $this->$which_function($args);
      echo $r;
    }

    private function add_user_to_cohort($args) 
    {
      $idnumber = $args[0];
      $cohortName = $args[1];

      global $DB;
      if( !$user = $this->getUserByIDNumber($idnumber) )
	{
	  return "-1 Could not find user ".$idnumber;
	}

      if( $cohort = $DB->get_record_select( 'cohort', 'name = ?', array($cohortName) ) )
	{
	  $cohortID= $cohort->id;
	  $userID = $user->id;
	  // workaround, instead of using cohort_existing_selector, due to bug
	  $cohort_membership = $DB->get_record_select('cohort_members', 'cohortid = ? and userid = ?', array('cohortid'=>$cohortID,'userid'=>$userID));
	  if( $cohort_membership )
	    {
	      return "0";
	    }
	}
      else
	{
	  return "-1 Could not find cohort ".$cohortName;
	}
     
      $r = cohort_add_member($cohortID, $userID);
      echo "Added ".$idnumber." to cohort ".$cohortName ;
      return $r;

      global $DB;
    }

    private function create_account( $args )
    {
      var_dump($args);
      $username = $args[0];
      $email = $args[1];
      $firstname = $args[2];
      $lastname = $args[3];
      $idnumber = $args[4];
      

      if( $this->user_does_exist(array($username)) )
	{
	  return "0 This username is already taken: ".$username;
	}

      global $DB, $CFG;

      try
	{
	  $user = create_user_record( $username, "changeme" );

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

      catch( Exception $e )
	{
	  var_dump($e);
	  return "-1 Could not create account for ".$username;
        }

      return $user->id;
    }

    private function user_does_exist($args)
    {
      $username = $args[0];

      global $DB, $CFG;
      $s = $DB->get_record_select( 'user' , 'username = ?', array($username) );
      return $s;
    }

    private function associate_child_to_parent($args)
    {
      $parent_idnumber = $args[0];
      $child_idnumber = $args[1];

      try
	{
	  if( $parent = $this->getUserByIDNumber( $parent_idnumber ) and $child = $this->getUserByIDNumber($child_idnumber) )
	    {
	      $context = get_context_instance( CONTEXT_USER , $child->id );
	      role_assign( $this->PARENT_ROLE_ID, $parent->id, $context->id );
	    }
	  else
	    {
	      return "-1 Could not find parent ".$parent_idnumber;
	    }
	}

      catch( Exception $e ) 
	{
	  var_dump($e);
	  return "-1 Could not associate child".$child_idnumber." to parent ".$parent_idnumber;
	}
    }

    private function add_user_to_group($args)
    {
      $user_idnum = $args[0];
      $group_name = $args[1];

      global $DB;

      $user = $this->getUserByIDNumber($user_idnum);
      $group = $DB->get_record('groups', array('name'=>$group_name), '*', MUST_EXIST);

      groups_add_member($group, $user);
    }

    private function enrol_user_in_course($args)
    {
      $useridnumber = $args[0];
      $short_name = $args[1];
      $group_name = $args[2];
      $role = $args[3];

      if ($role = 'Student') {
	$roleid = $this->STUDENT_ROLE_ID;
      }
      else if( $role = 'Parent') {
	$roleid = $this->PARENT_ROLE_ID;
      }
      else {
	return "-1 No viable role ID was passed ".$role;
      }

      global $DB, $PAGE;

      if( !$user = $this->getUserByIDnumber($useridnumber) )
	{
	  return "-1 Could not find user".$useridnumber;
	}

      $course = $DB->get_record('course', array('shortname'=>$short_name), '*');
      $context = get_context_instance(CONTEXT_COURSE, $course->id, MUST_EXIST);
      $manager = new course_enrolment_manager($PAGE, $course);

      if( !is_enrolled($context, $user->id) )
	{
	  $enrolMethod = $DB->get_record('enrol', array('enrol'=>'manual', 'courseid'=>$course->id), '*', MUST_EXIST);
	  $enrolid = $enrolMethod->id;

	  $instances = $manager->get_enrolment_instances();
	  $plugins = $manager->get_enrolment_plugins();

	  if (!array_key_exists($enrolid, $instances))
	    {
	      throw new enrol_ajax_exception('invalidenrolinstance');
	    }
	  
	  $instance = $instances[$enrolid];
	  $plugin = $plugins[$instance->enrol];

	  $today = time();

	  $today = make_timestamp(date('Y', $today), date('m', $today), date('d', $today), 0, 0, 0);
	  $timestart = $today;
	  $timeend = 0;

	  $plugin->enrol_user($instance, $user->id, $roleid, $timestart, $timeend);
	  echo "Enrolled ".$useridnumber." into class ".$short_name.".";
	}

      $groups = $manager->get_all_groups();
      if( array_key_exists($group_name, $groups) )
        {
          $manager->add_user_to_group( $user, $groups[$group_name]->id );
          echo "Added user ".$useridnumber." into group ".$group_name.".";
        }

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