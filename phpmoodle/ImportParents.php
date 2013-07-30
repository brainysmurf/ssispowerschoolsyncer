<?php

	error_reporting(1);
	define(CLI_SCRIPT,1);
		
	//Change this to the path to the moodle config file
	require_once( '../../config.php' );

	class parentImporter
	{
		private $STUDENT_DATA_FILENAME = 'studenttest.txt';
		//private $STUDENT_DATA_FILENAME = '/home/powerschool/ssis_studentinfodumpsec'; //Name of the file that contains the output from powerschool
		private $ADMIN_USER_ID = 2; //User ID of the admin user - the person who will saved as having creating the parents' user accounts
		private $PARENT_ROLE_ID = 12;
		private $DEFAULT_PASSWORD = 'changeme';
		private $NEW_PARENT_FILE = "new_parents.txt";
		
		function __construct()
		{
			echo "Import Users\n";
			//Run automatically when creating a new instnance of this class...
		
			//Parse the text file and get an array of parent/student pairings
			$parents = $this->loadData();
			//Save those in the database
			$this->importParents($parents);
		}
		
		
		private function getUserByIDNumber($idnumber)
		{
			global $DB, $CFG;
			$s = $DB->get_record_select( 'user' , 'idnumber = ?', array($idnumber) );
			return $s;
		}
		
		
		private function getUserByEmail($email)
		{
			global $DB, $CFG;
			$s = $DB->get_record_select( 'user' , 'email = ?', array($email) );
			return $s;
		}
		
		
		private function getUserByUsername($username)
		{
			global $DB, $CFG;
			$s = $DB->get_record_select( 'user' , 'username = ?', array($username) );
			return $s;
		}
		
		
		//Create an account with the username the same as the email address and the password as 'changeme'
		private function createAccount( $username , $email , $firstname=false , $lastname=false , $idnumber=false , $department=false )
		{
			global $DB, $CFG;
			
			//Update additional user details
			try
			{
				$user = create_user_record( $username, $this->DEFAULT_PASSWORD );
			
				//Save additional information
				$user->email = trim($email);
				$user->firstname = trim($firstname);
				$user->lastname = trim($lastname);
				$user->idnumber = trim($idnumber);
				$user->department = $department;
				$user->city = 'Suzhou';
				$user->country = 'CN';
				
				$DB->update_record( 'user' , $user );
				return $user;
			}
			catch( Exception $e )
			{
				var_dump($e);
				//return 0;
				die();
			}
			
			return $user->id;
		}
		
		
		//Read the text file and return an array of student/parent data
		private function loadData()
		{
			$parents = array();
			
			//Load the CSV file	
			$students = file_get_contents($this->STUDENT_DATA_FILENAME);
	
			//Break it up by line
			$students = explode( "\n",$students );
			
			// Zero out the new_parents one
			//$fh = fopen($this->NEW_PARENT_FILE, 'w') or die("Could not open file");
			//fclose($fh);

			//For each line (each student)...
			foreach ( $students as $student )
			{
				//Break it up by tabs
				$student = explode("\t",$student );
				
				$studentID = $student[0];
				
				$homeroom = $student[1];
				$year = intval($student[1]);
				
				$studentName = explode(",",$student[2]);
				$studentFirstName = $studentName[1];
				$studentLastName = $studentName[0];
				
				//Split the parent email addresses by commas or semicolons in case more than one is listed
				$parentEmails = preg_split( "/[\,\;]/", $student[3] );
				$parentEmail = $parentEmails[0];

				echo "\n";
				echo 'Student ID: '.$studentID.'   ';
				echo 'Parent Email: '.$parentEmail.'   ';
				echo 'Homeroom: '.$homeroom;
				
				if ( !$parentEmail )
				{
					//If no parent email is listed we can't do anything. Stop here but continue to iterate over the other students.
					continue;
				}

				$student = $this->getUserByIDNumber($studentID);
				
				//In production uncomment this line to skip to the next student here if the current student does not have an account in moodle
				#if ( !$student ) { continue; }

				$studentUserID = $student->id;
				$studentUsername = $student->username;
				$parentEmail = strtolower($parentEmail);
				$parentUsername = $parentEmail;
				
				//Check if the parent already has an account - that is, an account exists with the parent's email as the username
				
				if ( $parentUser = $this->getUserByUsername( $parentEmail ) )
				{
					//Parent has an account already
					echo "\nParent does have an account, no need to create...";
					$parentUserID = $parentUser->id;
				}
				else
				{
					echo "\nParent does not have account, creating...";
					
					//Need to make a new user for this parent
					$parentUser = $this->createAccount( $parentEmail , $parentEmail , 'Parent', $parentEmail );
					$parentUserID = $parentUser->id;

					$fh = fopen($this->NEW_PARENT_FILE, 'a') or die("Could not open file");
					fwrite($fh, $parentEmail . "\n");
					fclose($fh);
				}

				//Add to our array of parents
				$parents[] = array(
					'parent_userid' => $parentUserID,
					'parent_username' => $parentUsername,
					'child_userid' => $studentUserID,
					'child_username' => $studentUsername
				);
				
			}
			
			return $parents;
		}
	
		
		//Take the array of students/parents returned from the previous function and insert into the database	
		private function importParents( $parents )
		{
			//For each of the students' parents, add it to the table (run the prepared statement from above)
			foreach ( $parents as $parent )
			{	
				echo $parent['child_userid']."\n";
				$context = get_context_instance( CONTEXT_USER , $parent['child_userid'] );
				try {
					role_assign( $this->PARENT_ROLE_ID, $parent['parent_userid'], $context->id );
				}
				catch( Exception $e ) {
					echo "What the hell! ".$parent['parent_userid']."\n";
				}
			}
		}
		
				
	}		
	
	//Run automatically when this script is loaded
	$pi = new parentImporter();
	
	echo "\n";
	
