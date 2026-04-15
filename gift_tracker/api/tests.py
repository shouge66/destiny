from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import AnnualGoal
from .models import AnnualPlan
from .models import AnonymousAggregate
from .models import Assessment
from .models import DeleteRequest
from .models import MonthlyAction
from .models import MonthlyReview
from .models import TalentProfile


class ApiBaseTestCase(APITestCase):
	def setUp(self):
		user_model = get_user_model()
		self.user_a = user_model.objects.create_user(username="user_a", password="Pass@1234")
		self.user_b = user_model.objects.create_user(username="user_b", password="Pass@1234")

	def login_as_a(self):
		self.client.force_authenticate(user=self.user_a)

	def login_as_b(self):
		self.client.force_authenticate(user=self.user_b)


class ApiRootAndPermissionTests(ApiBaseTestCase):
	def test_api_root_and_health_available(self):
		api_root = self.client.get("/api/")
		health = self.client.get("/api/health/")

		self.assertEqual(api_root.status_code, status.HTTP_200_OK)
		self.assertEqual(health.status_code, status.HTTP_200_OK)
		self.assertIn("workflows", api_root.json())

	def test_protected_endpoint_requires_auth(self):
		response = self.client.get("/api/assessments/")
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ResourceIsolationTests(ApiBaseTestCase):
	def test_assessment_list_is_user_scoped(self):
		Assessment.objects.create(user=self.user_a, questionnaire_data={"analysis": 80})
		Assessment.objects.create(user=self.user_b, questionnaire_data={"analysis": 20})

		self.login_as_a()
		response = self.client.get("/api/assessments/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.json()), 1)
		self.assertEqual(response.json()[0]["user"], self.user_a.id)

	def test_cannot_create_goal_with_other_users_plan(self):
		other_plan = AnnualPlan.objects.create(
			user=self.user_b,
			year=2026,
			direction_text="B direction",
			evidence_chain_data={},
			status="draft",
		)
		self.login_as_a()

		response = self.client.post(
			"/api/annual-goals/",
			{"plan": other_plan.id, "goal_text": "invalid", "priority": 3, "status": "todo"},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("plan", response.json())


class WorkflowActionTests(ApiBaseTestCase):
	def test_generate_profile_creates_new_active_profile(self):
		assessment = Assessment.objects.create(
			user=self.user_a,
			questionnaire_data={"analysis": 80, "communication": 60},
			behavior_data={"analysis": 70, "communication": 75},
			external_import_data={"analysis": 60, "communication": 85},
		)
		TalentProfile.objects.create(
			user=self.user_a,
			assessment=assessment,
			profile_data={"summary": "old"},
			strengths_rank_data=[],
			explanation_data={},
			is_active=True,
		)

		self.login_as_a()
		url = reverse("assessment-generate-profile", args=[assessment.id])
		response = self.client.post(url, format="json")

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(TalentProfile.objects.filter(user=self.user_a).count(), 2)
		self.assertEqual(TalentProfile.objects.filter(user=self.user_a, is_active=True).count(), 1)
		self.assertIn("weights", response.json()["explanation_data"])

	def test_submit_monthly_review_auto_calculates_confidence(self):
		self.login_as_a()
		MonthlyAction.objects.create(user=self.user_a, month_key="2026-04", action_text="A1", is_done=True)
		MonthlyAction.objects.create(user=self.user_a, month_key="2026-04", action_text="A2", is_done=False)

		url = reverse("monthly-review-submit")
		response = self.client.post(
			url,
			{
				"month_key": "2026-04",
				"template_type": "outcome",
				"review_data": {"wins": ["done something"]},
			},
			format="json",
		)

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(float(response.json()["review"]["confidence_score"]), 50.0)
		self.assertEqual(MonthlyReview.objects.filter(user=self.user_a).count(), 1)

	def test_execute_delete_request_clears_personal_data_but_keeps_aggregate(self):
		self.login_as_a()
		assessment = Assessment.objects.create(user=self.user_a, questionnaire_data={"analysis": 80})
		TalentProfile.objects.create(
			user=self.user_a,
			assessment=assessment,
			profile_data={"summary": "temp"},
			strengths_rank_data=[],
			explanation_data={},
			is_active=True,
		)
		AnonymousAggregate.objects.create(
			stat_date="2026-04-01",
			goal_type="career_growth",
			metric_key="completion_rate",
			metric_value=72.5,
			sample_size=120,
		)

		url = reverse("delete-request-execute")
		response = self.client.post(url, format="json")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(Assessment.objects.filter(user=self.user_a).count(), 0)
		self.assertEqual(TalentProfile.objects.filter(user=self.user_a).count(), 0)
		self.assertEqual(AnonymousAggregate.objects.count(), 1)

		delete_request_id = response.json()["delete_request_id"]
		delete_request = DeleteRequest.objects.get(id=delete_request_id)
		self.assertEqual(delete_request.status, "completed")
