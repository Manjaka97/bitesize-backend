from django.test import TestCase, Client
from datetime import date
from app.views import *

# Create your tests here.
class ModelTest(TestCase):
    def setUp(self):
        # Populating the database with test data
        User.objects.create(id='testid', username='testuser', email='testemail@test.com', firstname='testfirstname', lastname='testlastname', gender='N', birthday='1969-01-01', picture='testpicture')
        Category.objects.create(id=1, name='testcategory')
        Goal.objects.create(user_id=User.objects.get(id='testid'), name='testgoal', description='testdescription', deadline='1969-01-01', picture='testpicture')
        Step.objects.create(goal_id=Goal.objects.get(name='testgoal'), user_id=User.objects.get(id='testid'), name='teststep', description='testdescription', deadline='1969-01-01')

    def test_user(self):
        self.u = User.objects.get(id='testid')
        self.assertEqual(self.u.email, 'testemail@test.com')
        self.assertEqual(self.u.firstname, 'testfirstname')
        self.assertEqual(self.u.lastname, 'testlastname')
        self.assertEqual(self.u.gender, 'N')
        self.assertEqual(self.u.birthday, date(1969, 1, 1))
        self.assertEqual(self.u.picture, 'testpicture')

    def test_goal(self):
        self.g = Goal.objects.get(name='testgoal')
        self.assertEqual(self.g.user_id, User.objects.get(id='testid'))
        self.assertEqual(self.g.description, 'testdescription')
        self.assertEqual(self.g.deadline, date(1969, 1, 1))
        self.assertEqual(self.g.picture, 'testpicture')
        self.assertFalse(self.g.complete)

    def test_step(self):
        self.s = Step.objects.get(name='teststep')
        self.assertEqual(self.s.goal_id, Goal.objects.get(name='testgoal'))
        self.assertEqual(self.s.user_id, User.objects.get(id='testid'))
        self.assertEqual(self.s.description, 'testdescription')
        self.assertEqual(self.s.deadline, date(1969, 1, 1))
        self.assertFalse(self.s.complete)

class ViewTest(TestCase):
    def setUp(self):
        # Populating the database with test data
        User.objects.create(id='testid', username='testuser', email='testemail@test.com', firstname='testfirstname', lastname='testlastname', gender='N', birthday='1969-01-01', picture='testpicture')
        Category.objects.create(id=1, name='testcategory')
        # Step.objects.create(goal_id=Goal.objects.get(name='testgoal'), user_id=User.objects.get(id='testid'), name='teststep', description='testdescription', deadline='1969-01-01')

        # Obtaining an Auth0 token
        get_token = GetToken(os.getenv("AUTH_DOMAIN"))
        token = get_token.client_credentials(os.getenv("BITESIZE_CLIENT"), os.getenv("BITESIZE_SECRET"), os.getenv('AUTH_AUDIENCE'))
        self.api_token = token['access_token']

        # Creating test clients
        self.unauthorized_client = Client()
        self.authorized_client= Client(HTTP_AUTHORIZATION='Bearer ' + self.api_token)
    
    def test_user(self):
        response = self.unauthorized_client.post('/sync_and_fetch_user/testid')
        self.assertEqual(response.status_code, 401)
        
        response = self.authorized_client.post('/sync_and_fetch_user/testid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['id'], 'testid')
        self.assertEqual(response.json()['username'], 'testuser')
        self.assertEqual(response.json()['email'], 'testemail@test.com')
        self.assertEqual(response.json()['firstname'], 'testfirstname')
        self.assertEqual(response.json()['lastname'], 'testlastname')
        self.assertEqual(response.json()['gender'], 'N')
        self.assertEqual(response.json()['birthday'], '1969-01-01')
        self.assertEqual(response.json()['picture'], 'testpicture')
        self.assertEqual(response.json()['encouragement'], 'Perseverance, secret of all triumphs - Victor Hugo (Edit this to be anything you want in Profile -> Motivation)')
        self.assertEqual(response.json()['subscribed'], True)

        response = self.unauthorized_client.post('/update_profile/testid')
        self.assertEqual(response.status_code, 401)

        # We use null and lowercase booleans to simulate the data sent by the frontend in javascript
        response = self.authorized_client.post('/update_profile/testid', {'firstname': 'newfirstname', 'lastname': 'newlastname', 'gender':'N', 'birthday': 'null', 'encouragement': 'new encouragement', 'subscribed':'false'})
        self.assertEqual(response.status_code, 200)

        response = self.authorized_client.get('/get_profile/testid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['firstname'], 'newfirstname')
        self.assertEqual(response.json()['lastname'], 'newlastname')
        self.assertIsNone(response.json()['birthday'])
        self.assertFalse(response.json()['subscribed'])

    def test_goal(self):
        response = self.unauthorized_client.post('/create_goal/testid')
        self.assertEqual(response.status_code, 401)

        response = self.authorized_client.post('/create_goal/testid', {'name': 'testgoal', 'description':'testdescription', 'category': 1, 'deadline': '1969-01-01'})
        self.assertEqual(response.status_code, 201)

        response = self.authorized_client.get('/get_goal/testid/'+str(Goal.objects.get(name='testgoal').id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user_id'], 'testid')
        self.assertEqual(response.json()['name'], 'testgoal')
        self.assertEqual(response.json()['deadline'], '1969-01-01')

    def test_step(self):
        Goal.objects.create(user_id=User.objects.get(id='testid'), name='testgoal', description='testdescription', deadline='1969-01-01')
        g = Goal.objects.get(name='testgoal')

        response = self.unauthorized_client.post('/create_step/testid/1')
        self.assertEqual(response.status_code, 401)

        response = self.authorized_client.post('/create_step/testid/'+str(g.id), {'name': 'teststep', 'description': 'testdescription', 'deadline': '1969-01-01'})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Step.objects.get(id=response.json()['id']).goal_id.id, g.id)

        response = self.authorized_client.get('/get_user_steps/testid')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]['name'], 'teststep')
        self.assertEqual(response.json()[0]['description'], 'testdescription')
        self.assertEqual(response.json()[0]['deadline'], '1969-01-01')
        self.assertEqual(response.json()[0]['goal_id'], g.id)