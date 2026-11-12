from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Course, Enrollment, Question, Choice, Submission


class ExamTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user('learner', password='Synthetic-test-only-123')
        cls.other = User.objects.create_user('other', password='Synthetic-test-only-456')
        cls.course = Course.objects.create(name='Learning Django', description='Test course')
        cls.enrollment = Enrollment.objects.create(user=cls.user, course=cls.course)
        cls.question = Question.objects.create(course=cls.course, content='Which are Django features?', grade=100)
        cls.a = Choice.objects.create(question=cls.question, content='ORM', is_correct=True)
        cls.b = Choice.objects.create(question=cls.question, content='Templates', is_correct=True)
        cls.c = Choice.objects.create(question=cls.question, content='A web browser', is_correct=False)
        cls.other_course = Course.objects.create(name='Other course')
        q = Question.objects.create(course=cls.other_course, content='Other question')
        cls.foreign_choice = Choice.objects.create(question=q, content='Foreign', is_correct=True)

    def setUp(self):
        self.client.force_login(self.user)
        self.submit_url = reverse('onlinecourse:submit', args=[self.course.pk])

    def test_exact_answers_pass_and_render_details(self):
        response = self.client.post(self.submit_url, {f'choice_{self.a.pk}': self.a.pk, f'choice_{self.b.pk}': self.b.pk}, follow=True)
        self.assertContains(response, 'Congratulations')
        self.assertContains(response, 'Score: 100/100')
        self.assertEqual(Submission.objects.count(), 1)
        self.assertContains(response, 'Correct answer')

    def test_selecting_every_answer_or_partial_answers_does_not_pass(self):
        for ids in [[self.a.pk, self.b.pk, self.c.pk], [self.a.pk], []]:
            response = self.client.post(self.submit_url, {f'choice_{i}': i for i in ids}, follow=True)
            self.assertContains(response, 'Score: 0/100')
            self.assertNotContains(response, 'Congratulations')

    def test_reject_foreign_and_malformed_choices_without_saving(self):
        for value in [self.foreign_choice.pk, 999999, 'invalid']:
            response = self.client.post(self.submit_url, {'choice_1': value})
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Submission.objects.count(), 0)

    def test_result_ownership_and_course_are_enforced(self):
        submission = Submission.objects.create(enrollment=self.enrollment)
        result = reverse('onlinecourse:exam_result', args=[self.course.pk, submission.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(result).status_code, 404)
        self.assertEqual(self.client.post(self.submit_url, {}).status_code, 404)
        self.client.force_login(self.user)
        wrong_course = reverse('onlinecourse:exam_result', args=[self.other_course.pk, submission.pk])
        self.assertEqual(self.client.get(wrong_course).status_code, 404)

    def test_login_and_post_required(self):
        self.assertEqual(self.client.get(self.submit_url).status_code, 405)
        self.client.logout()
        self.assertEqual(self.client.post(self.submit_url, {}).status_code, 302)
        self.assertEqual(Submission.objects.count(), 0)

    def test_repeated_enrollment_does_not_inflate_count(self):
        self.client.force_login(self.other)
        url = reverse('onlinecourse:enroll', args=[self.course.pk])
        self.client.post(url)
        self.client.post(url)
        self.course.refresh_from_db()
        self.assertEqual(self.course.total_enrollment, 1)
        self.assertEqual(Enrollment.objects.filter(user=self.other, course=self.course).count(), 1)
