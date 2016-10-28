import requests

print ''

term = 1
info = [('asdfw', 'awefrw'), ('find', 'aweroisdufi'), ('fiw33', '089dfklw2')]

for item in info:
    print 'Test Case ' + str(term)

    r = requests.post('http://127.0.0.1:8000/add', data={'name': item[0], 'message': item[1]})
    print "User %s add message %s to the database" % (item[0], item[0])

    r = requests.get('http://127.0.0.1:8000/record')
    if item[0] in r.text and item[1] in r.text:
        print "Find information in the database"
    else:
        print "Information is not in the database"
        raise Exception

    r = requests.post('http://127.0.0.1:8000/delete', data={'name': item[0], 'message': item[1]})
    print r.text
    print ''

    r = requests.get('http://127.0.0.1:8000/submit', data={'quantity': 500})
    print r.text
    print ''

    term += 1

print "End of the test!"
