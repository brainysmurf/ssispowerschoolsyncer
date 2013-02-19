<?php

/* * This script allows you to reset any local user password to changeme

Forces reset password

Adam Morris, slightly modified from moodle original

 */

define('CLI_SCRIPT', true);

//$path = "/home/lcssisadmin/database_password_reset/dragonnet_reset_password.txt";

require(dirname(dirname(dirname(__FILE__))).'/config.php');
require_once($CFG->libdir.'/clilib.php');      // cli only functions

cli_heading('Password reset'); // TODO: localize

//$usernames = file_get_contents($path);
//$usernames = explode( "\n",$usernames );

$password = 'changeme';
$hashedpassword = hash_internal_user_password($password);
array_shift($argv);

foreach ( $argv as $useridnumber ) {
	if (!$user = $DB->get_record('user', array('auth'=>'manual', 'idnumber'=>$useridnumber, 'mnethostid'=>$CFG->mnet_localhost_id))) {
	    cli_error("Can not find user " . $useridnumber);
	}

	$DB->set_field('user', 'password', $hashedpassword, array('id'=>$user->id));

	echo "Dragonnet2 password for user with idnumber " . $useridnumber . " reset\n";

}

exit(0); // 0 means success
