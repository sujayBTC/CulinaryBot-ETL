# trigger.py

from celery_task.recipe_task import recipe_task

task = recipe_task.delay()

print(task.id)