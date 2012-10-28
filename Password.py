from Controller import Controller
import shelve

class Password(Controller):
      
      def __init__(self, path_to_database):
      	  self._db = shelve.open(path_to_database)

      def check(self):
          pass

    

if __name__ == "__main__":

      passwords = Password('password_database.shelve')
      for key in passwords.keys():
            print(key)
            print(passwords.get(key))
      print('\n')
      print(passwords.get('jihwanpark14'))
