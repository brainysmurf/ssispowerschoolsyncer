import shelve

db = {}
raw = open('moodle_users.txt').readlines()
raw.pop(0)
for line in raw:
    split = line.split(',')
    username = split[0]
    password = split[3]
    db[username] = password

shelve = shelve.open('password_database.shelve')
for key in db.keys():
    print(key)
    shelve[key] = db[key]
    print(shelve[key])

print()
print(shelve['jihwanpark14'])

