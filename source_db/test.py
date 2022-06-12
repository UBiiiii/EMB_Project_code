import pyrebase

firebaseConfig = {
    'use your config'
}

firebase = pyrebase.initialize_app(firebaseConfig)

db = firebase.database()

room = db.child('3/302/redirect').get()
print(room.val())
