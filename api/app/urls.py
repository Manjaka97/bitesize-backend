from django.urls import path
from . import views

urlpatterns = [
    path('sync_and_fetch_user/<str:id>', views.sync_and_fetch_user),
    path('create_goal/<str:id>', views.create_goal),
    path('get_goals/<str:id>', views.get_goals),
    path('get_goal/<str:id>/<str:goal_id>', views.get_goal),
    path('get_completed_goals/<str:id>', views.get_completed_goals),
    path('get_completed_goals_paginated/<str:id>/<int:page>/<int:num_per_page>', views.get_completed_goals_paginated),
    path('update_goal/<str:id>/<str:goal_id>', views.update_goal),
    path('delete_goal/<str:id>/<str:goal_id>', views.delete_goal),
    path('complete_goal/<str:id>/<str:goal_id>', views.complete_goal),
    path('upload_picture/<str:id>/<str:goal_id>', views.upload_picture),
    path('upload_profile_picture/<str:id>', views.upload_profile_picture),
    path('create_step/<str:id>/<str:goal_id>', views.create_step),
    path('get_steps/<str:id>/<str:goal_id>', views.get_steps),
    path('get_completed_steps/<str:id>/<str:goal_id>', views.get_completed_steps),
    path('get_user_steps/<str:id>', views.get_user_steps),
    path('complete_step/<str:id>/<str:goal_id>/<str:step_id>', views.complete_step),
    path('get_profile/<str:id>', views.get_profile),
    path('get_profile_picture/<str:id>', views.get_profile_picture),
    path('update_profile/<str:id>', views.update_profile),
    path('delete_profile/<str:id>', views.delete_profile),
    # path('api/users', views.UserList.as_view(), name='user-list'),
    # path('api/goals', views.GoalList.as_view(), name='goal-list'),
    # path('api/steps', views.StepList.as_view(), name='step-list'),
    path('api/categories', views.CategoryList.as_view(), name='category-list'),
    # path('celery', views.send_test_email)
]