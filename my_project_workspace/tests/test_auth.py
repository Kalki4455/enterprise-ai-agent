from services.auth import register_user
def test_registration():
    u = register_user('Arjun')
    assert u.username == 'Arjun'