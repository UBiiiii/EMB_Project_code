import pyrebase

firebaseConfig = {
    'use your config'
}

<<<<<<< HEAD
firebase = pyrebase.initialize_app(firebaseConfig)
=======
# firebase_admin.initialize_app(cred,{
#     #insert your firebase config
# })
>>>>>>> 4db7ce627212f0041a6fb5b303bf66199b8cb20d

db = firebase.database()

<<<<<<< HEAD
room = db.child('3/302/redirect').get()
print(room.val())
=======
# ref = db.reference('이름')
# print(ref.get())

# firebase_admin.initialize_app(cred,{
#     'projectId': 'proj2022-3cd0d'
# })
# db = firestore.client()

# # doc_ref = db.collection('users').document('user02')
# # doc_ref.set({
# #     'level': 30,
# #     'money': 700,
# #     'job': "knight"
# # })

# users_ref = db.collection('asdf')
# docs = users_ref.stream()

# for doc in docs:
#     print('{}=>{}'.format(doc.id, doc.to_dict()))

app = firebase_admin.initialize_app(cred, {
        #insert your firebase config
})


bucket = storage.bucket()

storage.child('').download("","download.jpg")
>>>>>>> 4db7ce627212f0041a6fb5b303bf66199b8cb20d
