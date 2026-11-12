# Online Course — Django assessment feature

IBM Skills Network final project, implemented with AI assistance from the official starter. Adds Question, Choice and Submission models, inline admin editing, an enrolled learner's exam form and detailed results.

## Run locally

Create a Python virtual environment, install requirements.txt, run `python manage.py migrate`, create an administrator with `python manage.py createsuperuser`, then run `python manage.py runserver`. Open `/admin/` to create instructors, courses, lessons, questions and choices. Open `/onlinecourse/` to enroll and take a mock exam.

Run `python manage.py test onlinecourse` for the evaluation and access checks. An answer must match the complete correct set; selecting every checkbox does not earn credit. Submitted choices must belong to the current course, and results are accessible only to the submitting learner.

This is a local educational application. Screenshots show the application's own mock exam, not a Coursera grade. Use persistent deployment secrets, HTTPS and production settings before any public deployment.
