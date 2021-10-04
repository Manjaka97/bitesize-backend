from django.shortcuts import render
from functools import wraps
import jwt
from auth0.v3.authentication import GetToken, get_token
from auth0.v3.management import Auth0
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from .models import *
from .serializers import *
from rest_framework import generics
from django.core.paginator import Paginator
import cloudinary
from cloudinary.uploader import upload
from cloudinary.api import delete_all_resources, delete_folder, delete_resources
from datetime import datetime
from .tasks import send_weekly_email
import http.client
import json
import os
from dotenv import load_dotenv
load_dotenv()

cloudinary.config(
    cloud_name = "elvnosix",
    api_key = os.getenv('CLOUDINARY_API_KEY'),
    api_secret = os.getenv('CLOUDINARY_API_SECRET')
)

# Create your views here.

def get_token_auth_header(request):
    """Obtains the access token from the Authorization Header
    """
    auth = request.META.get("HTTP_AUTHORIZATION", None)
    parts = auth.split()
    token = parts[1]
    return token

def requires_scope(required_scope):
    """Determines if the required scope is present in the access token
    Args:
        required_scope (str): The scope required to access the resource
    """
    def require_scope(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_auth_header(args[0])
            decoded = jwt.decode(token, audience=os.getenv('AUTH_AUDIENCE'), algorithms='RS256', verify=False)
            if decoded.get("scope"):
                token_scopes = decoded["scope"].split()
                for token_scope in token_scopes:
                    if token_scope == required_scope:
                        return f(*args, **kwargs)
            response = JsonResponse({'message': 'You don\'t have access to this resource'})
            response.status_code = 403
            return response
        return decorated
    return require_scope

# Views for testing
class UserList(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

class GoalList(generics.ListCreateAPIView):
    queryset = Goal.objects.all()
    serializer_class = GoalSerializer
    permission_classes = (AllowAny,)

class StepList(generics.ListCreateAPIView):
    queryset = Step.objects.all()
    serializer_class = StepSerializer
    permission_classes = (AllowAny,)

class CategoryList(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (AllowAny,)


# Create or update a user profile in the local database
@api_view(["POST"])
@requires_scope('update:current_user')
def sync_and_fetch_user(request, id):
    data = request.POST
    user_query = User.objects.filter(id=id)
    # If the user exists, check if email and picture have been updated
    if len(user_query) > 0:
        user = user_query[0]
        if 'email' in data and data['email'] != user.email:
            user.email = data['email']
            user.save()
        # Only update picture if user has not uploaded one
        if 'picture' in data and user.picture == '':
            user.picture = data['picture']
            user.save()
        return Response(UserSerializer(user).data, status=200)
    # If the user does not exist, create a new user
    else:
        if 'email' in data and 'name' in data and 'picture' in data:
            user = User(id=id, email=data['email'], username=data['name'], picture=data['picture'])
            user.save()
            return Response(UserSerializer(user).data, status=201)
        else:
            return Response({'message': 'Email and/or username missing'}, status=400)

# Fetch a user profile
@api_view(["GET"])
@requires_scope('read:current_user')
def get_profile(request, id):
    user = User.objects.filter(id=id)
    if len(user) > 0:
        return Response(UserSerializer(user[0]).data, status=200)
    return Response({'message':'user not found'}, status=404)

# Fetch user profile picture
@api_view(["GET"])
@requires_scope('read:current_user')
def get_profile_picture(request, id):
    user = get_object_or_404(User, id=id)
    if user.picture != '':
        return Response(user.picture, status=200)
    return Response({'message':'user picture not found'}, status=404)

# Update a user profile
@api_view(["POST"])
@requires_scope('update:current_user')
def update_profile(request, id):
    data = request.POST
    user = get_object_or_404(User, id=id)
    user.firstname = data['firstname']
    user.lastname = data['lastname']
    user.gender = data['gender']
    if data['birthday'] == '' or data['birthday'] == 'null':
        user.birthday = None
    else:
        user.birthday = data['birthday']
    user.encouragement = data['encouragement']
    if data['subscribed'] == 'false':
        user.subscribed = False
    else:
        user.subscribed = True
    user.save()
    # Return the updated user profile
    return Response(UserSerializer(user).data, status=200)

# Delete a user account
@api_view(["DELETE"])
@requires_scope('update:current_user')
def delete_profile(request, id):
    # First we need to obtain an access token and create auth0 object with the token
    get_token = GetToken(os.getenv("AUTH_DOMAIN"))
    token = get_token.client_credentials(os.getenv("AUTH_CLIENT"), os.getenv("AUTH_SECRET"), f"https://{os.getenv('AUTH_DOMAIN')}/api/v2/")
    mgmt_api_token = token['access_token']
    auth0 = Auth0(os.getenv("AUTH_DOMAIN"), mgmt_api_token)
    # Using the token, we call the auth0 management api to delete the user
    auth0.users.delete(id)
    User.objects.filter(id=id).delete()
    return Response({'deleted': True}, status=204)

# Create a new goal
@api_view(["POST"])
@requires_scope('update:current_user')
def create_goal(request, id):
    data = request.POST
    user = get_object_or_404(User, id=id)
    category = Category.objects.get(id=data['category'])
    # Null type from Reactjs becomes a string
    if data['deadline'] == 'null' or data['deadline'] == '':
        deadline = None
    else:
        deadline = data['deadline']
    goal = Goal(user_id=user, name=data['name'], description=data['description'], deadline=deadline, category_id=category)
    goal.save()
    return Response({'id': goal.id}, status=201)

# Fetch all user goals that are not completed
@api_view(["GET"])
@requires_scope('read:current_user')
def get_goals(request, id):
    get_object_or_404(User, id=id)
    goals = Goal.objects.filter(user_id=id, complete=False)
    return Response(GoalSerializer(goals, many=True).data, status=200)

# Fetch a specific goal
@api_view(["GET"])
@requires_scope('read:current_user')
def get_goal(request, id, goal_id):
    goals = Goal.objects.filter(id=goal_id)
    if len(goals) > 0:
        goal = goals[0]
        if goal.user_id.id == id:
            return Response(GoalSerializer(goal).data, status=200)
        return Response({'message': 'Unauthorized'}, status=403)
    return Response({'message': 'Goal does not exist'}, status=404)

# Fetch all completed goals
@api_view(["GET"])
@requires_scope('read:current_user')
def get_completed_goals(request, id):
    get_object_or_404(User, id=id)
    goals = Goal.objects.filter(user_id=id, complete=True)
    return Response(GoalSerializer(goals, many=True).data, status=200)

# Fetch paginated completed goals
@api_view(["GET"])
@requires_scope('read:current_user')
def get_completed_goals_paginated(request, id, page, num_per_page):
    get_object_or_404(User, id=id)
    goals = Paginator(Goal.objects.filter(user_id=id, complete=True).order_by('completion_date'), num_per_page)
    if page > goals.num_pages:
        return Response({'message': 'Page does not exist'}, status=404)
    return Response(GoalSerializer(goals.page(page), many=True).data, status=200)

# Update a goal
@api_view(["POST"])
@requires_scope('update:current_user')
def update_goal(request, id, goal_id):
    user = get_object_or_404(User, id=id)
    data = request.POST
    category = Category.objects.get(id=data['category'])
    # Null type from Reactjs becomes a string
    if data['deadline'] == 'null' or data['deadline'] == '':
        deadline = None
    else:
        deadline = data['deadline']
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.user_id.id == user.id:
        goal.name = data['name']
        goal.description = data['description']
        goal.deadline = deadline
        goal.category_id = category
        goal.save()
        return Response({'id': goal.id}, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

# Delete a goal
@api_view(["DELETE"])
@requires_scope('update:current_user')
def delete_goal(request, id, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.user_id.id == id:
        delete_picture(id, goal_id)
        goal.delete()
        return Response({'message': 'Goal deleted'}, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

# Complete a goal
@api_view(["POST"])
@requires_scope('update:current_user')
def complete_goal(request, id, goal_id):
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.user_id.id == id:
        # Mark all steps as complete
        steps = Step.objects.filter(goal_id=goal_id)
        for step in steps:
            step.complete = True
            step.completion_date = datetime.now()
            step.save()
        goal.complete = True
        goal.completion_date = datetime.now()
        goal.save()
        return Response({'message': 'Goal completed'}, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

# Fetch all categories
@api_view(["GET"])
@permission_classes((AllowAny,))
def get_categories(request):
    categories = Category.objects.all()
    return Response(CategorySerializer(categories, many=True).data, status=200)

# Upload a picture on cloudinary
@api_view(["POST"])
@requires_scope('update:current_user')
def upload_picture(request, id, goal_id):
    get_object_or_404(User, id=id)
    if 'picture' not in request.FILES:
        return Response({'message': 'No picture uploaded'}, status=400)
    uploaded = upload(request.FILES['picture'], public_id='bitesize/'+id+'/goals/'+goal_id)
    goal = get_object_or_404(Goal, id=int(goal_id))
    goal.picture = uploaded['secure_url']
    goal.save()
    return Response({'url': uploaded['secure_url']}, status=201)

# Upload profile picture on cloudinary
@api_view(["POST"])
@requires_scope('update:current_user')
def upload_profile_picture(request, id):
    if 'picture' not in request.FILES:
        return Response({'message': 'No picture uploaded'}, status=400)
    uploaded = upload(request.FILES['picture'], public_id='bitesize/'+id+'/profile')
    user = get_object_or_404(User, id=id)
    user.picture = uploaded['secure_url']
    user.save()
    return Response({'url': uploaded['secure_url']}, status=201)

# Delete a picture on cloudinary
def delete_picture(id, goal_id):
    get_object_or_404(User, id=id)
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.user_id.id == id:
        picture_url = goal.picture
        if picture_url != '':
            delete_resources('bitesize/'+id+'/goals/'+goal_id)

# Create a new step and returns the id
@api_view(["POST"])
@requires_scope('update:current_user')
def create_step(request, id, goal_id):
    data = request.POST
    goal = get_object_or_404(Goal, id=goal_id)
    user = get_object_or_404(User, id=id)
    if goal.user_id == user:
        if data['deadline'] == 'null' or data['deadline'] == '':
            deadline = None
        else:
            deadline = data['deadline']
        # if data['recurring'] == 'true':
        #     recurring = True
        # else:
        #     recurring = False
        step = Step(goal_id=goal, user_id=user, name=data['name'], description=data['description'], deadline=deadline)#, recurring=recurring)
        step.save()
        goal.current_steps_count += 1
        goal.total_steps_count += 1
        goal.save()
        return Response({'id': step.id}, status=201)
    return Response({'message': 'Unauthorized'}, status=403)

# Fetch all non-completed steps of a user
@api_view(["GET"])
@requires_scope('read:current_user')
def get_user_steps(request, id):
    get_object_or_404(User, id=id)
    steps = Step.objects.filter(user_id=id, complete=False)
    return Response(StepSerializer(steps, many=True).data, status=200)

# Fetch all steps of a goal that are not completed
@api_view(["GET"])
@requires_scope('read:current_user')
def get_steps(request, id, goal_id):
    get_object_or_404(User, id=id)
    steps = Step.objects.filter(goal_id=goal_id, complete=False)
    goal = get_object_or_404(Goal, id=goal_id)
    if goal.user_id.id == id:
        return Response(StepSerializer(steps, many=True).data, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

# Fetch completed steps of a goal
@api_view(["GET"])
@requires_scope('read:current_user')
def get_completed_steps(request, id, goal_id):
    get_object_or_404(User, id=id)
    steps = Step.objects.filter(goal_id=goal_id, complete=True)
    goal = get_object_or_404(Goal, id=goal_id)
    if not goal:
        return Response({'message':'goal not found'}, status=404)
    if goal.user_id.id == id:
        return Response(StepSerializer(steps, many=True).data, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

# Complete a step
@api_view(["POST"])
@requires_scope('update:current_user')
def complete_step(request, id, goal_id, step_id):
    get_object_or_404(User, id=id)
    goal = get_object_or_404(Goal, id=goal_id)
    step = get_object_or_404(Step, id=step_id)
    if step.goal_id.user_id.id == id:
        step.complete = True
        step.completion_date = datetime.now()
        step.save()
        goal.current_steps_count -= 1
        goal.save()
        return Response({'message': 'Step completed'}, status=200)
    return Response({'message': 'Unauthorized'}, status=403)

@api_view(["GET"])
@permission_classes((AllowAny,))
def send_test_email(request):
    send_weekly_email()
    return Response({'message': 'Email scheduled'}, status=200)