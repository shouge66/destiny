import json
from urllib import error as urllib_error
from urllib import request as urllib_request

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import permissions
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AnnualGoal
from .models import AnnualPlan
from .models import AnonymousAggregate
from .models import Assessment
from .models import CollaborationFeedback
from .models import CollaborationInvite
from .models import DataExportLog
from .models import DeleteRequest
from .models import Gift
from .models import MonthlyAction
from .models import MonthlyReview
from .models import MysticInput
from .models import PrivacyConsent
from .models import ProfileEdit
from .models import TalentProfile
from .models import WeightingConfig
from .serializers import AnnualGoalSerializer
from .serializers import AnnualPlanSerializer
from .serializers import AnonymousAggregateSerializer
from .serializers import AssessmentSerializer
from .serializers import CollaborationFeedbackSerializer
from .serializers import CollaborationInviteSerializer
from .serializers import DataExportLogSerializer
from .serializers import DeleteRequestSerializer
from .serializers import GiftSerializer
from .serializers import MonthlyActionSerializer
from .serializers import MonthlyReviewSerializer
from .serializers import MysticInputSerializer
from .serializers import PrivacyConsentSerializer
from .serializers import ProfileEditSerializer
from .serializers import TalentProfileSerializer
from .serializers import WeightingConfigSerializer


def build_token_payload(user):
	refresh = RefreshToken.for_user(user)
	return {
		"refresh": str(refresh),
		"access": str(refresh.access_token),
	}


def ensure_demo_user():
	User = get_user_model()
	username = settings.DEMO_USERNAME
	password = settings.DEMO_PASSWORD
	email = settings.DEMO_EMAIL
	user, _created = User.objects.get_or_create(username=username, defaults={"email": email})
	if email and user.email != email:
		user.email = email
	user.set_password(password)
	user.is_active = True
	user.save(update_fields=["email", "password", "is_active"])
	return user


class ApiRootView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response(
			{
				"name": "gift_tracker API",
				"api_root": "/api/",
				"health": "/api/health/",
				"admin": "/admin/",
				"auth": {
					"token": "POST /api/auth/token/",
					"refresh": "POST /api/auth/token/refresh/",
				},
				"resources": {
					"gifts": "/api/gifts/",
					"assessments": "/api/assessments/",
					"mystic_analysis": "/api/mystic-analysis/",
					"mystic_inputs": "/api/mystic-inputs/",
					"weighting_configs": "/api/weighting-configs/",
					"talent_profiles": "/api/talent-profiles/",
					"profile_edits": "/api/profile-edits/",
					"annual_plans": "/api/annual-plans/",
					"annual_goals": "/api/annual-goals/",
					"monthly_actions": "/api/monthly-actions/",
					"monthly_reviews": "/api/monthly-reviews/",
					"collaboration_invites": "/api/collaboration-invites/",
					"collaboration_feedbacks": "/api/collaboration-feedbacks/",
					"privacy_consents": "/api/privacy-consents/",
					"data_export_logs": "/api/data-export-logs/",
					"delete_requests": "/api/delete-requests/",
					"anonymous_aggregates": "/api/anonymous-aggregates/",
				},
				"workflows": {
					"generate_profile": "POST /api/assessments/{id}/generate-profile/",
					"submit_review": "POST /api/monthly-reviews/submit/",
					"delete_personal_data": "POST /api/delete-requests/execute/",
				},
			}
		)


class HealthCheckView(APIView):
	permission_classes = [permissions.AllowAny]

	def get(self, request):
		return Response({"status": "ok", "project": "gift_tracker"})


class RegisterView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		User = get_user_model()
		username = str(request.data.get("username") or "").strip()
		password = str(request.data.get("password") or "")
		email = str(request.data.get("email") or "").strip()

		if len(username) < 3:
			return Response({"detail": "用户名至少 3 个字符。"}, status=status.HTTP_400_BAD_REQUEST)
		if len(password) < 8:
			return Response({"detail": "密码至少 8 个字符。"}, status=status.HTTP_400_BAD_REQUEST)
		if User.objects.filter(username=username).exists():
			return Response({"detail": "用户名已存在，请更换。"}, status=status.HTTP_400_BAD_REQUEST)

		user = User.objects.create_user(username=username, email=email, password=password)
		return Response(
			{
				"user": {"id": user.id, "username": user.username, "email": user.email},
				**build_token_payload(user),
			},
			status=status.HTTP_201_CREATED,
		)


class GuestLoginView(APIView):
	permission_classes = [permissions.AllowAny]

	def post(self, request):
		user = ensure_demo_user()
		return Response(
			{
				"user": {"id": user.id, "username": user.username, "email": user.email},
				"guest": True,
				**build_token_payload(user),
			},
			status=status.HTTP_200_OK,
		)


class MysticAnalysisView(APIView):
	permission_classes = [permissions.IsAuthenticated]

	def post(self, request):
		api_url = settings.WENMO_TIANJI_API_URL
		api_key = settings.WENMO_TIANJI_API_KEY

		if not api_url or not api_key:
			return Response(
				{"detail": "Wenmo Tianji API is not configured."},
				status=status.HTTP_503_SERVICE_UNAVAILABLE,
			)

		payload = {
			"birth_date": request.data.get("birth_date"),
			"birth_time": request.data.get("birth_time"),
			"talent_summary": request.data.get("talent_summary", ""),
			"top_strengths": request.data.get("top_strengths", []),
		}

		body = json.dumps(payload).encode("utf-8")
		proxy_request = urllib_request.Request(
			api_url,
			data=body,
			headers={
				"Content-Type": "application/json",
				"Authorization": f"Bearer {api_key}",
			},
			method="POST",
		)

		try:
			with urllib_request.urlopen(proxy_request, timeout=20) as response:
				response_data = json.loads(response.read().decode("utf-8"))
				return Response(response_data, status=status.HTTP_200_OK)
		except urllib_error.HTTPError as exc:
			message = exc.read().decode("utf-8", errors="ignore")
			return Response(
				{"detail": "Wenmo Tianji API request failed.", "error": message},
				status=exc.code,
			)
		except Exception as exc:
			return Response(
				{"detail": "Wenmo Tianji API request failed.", "error": str(exc)},
				status=status.HTTP_502_BAD_GATEWAY,
			)


class UserOwnedModelViewSet(viewsets.ModelViewSet):
	permission_classes = [permissions.IsAuthenticated]
	user_field_name = "user"

	def get_queryset(self):
		queryset = self.queryset
		return queryset.filter(**{self.user_field_name: self.request.user})

	def perform_create(self, serializer):
		serializer.save(**{self.user_field_name: self.request.user})


class GiftViewSet(viewsets.ModelViewSet):
	queryset = Gift.objects.all().order_by("-created_at")
	serializer_class = GiftSerializer
	permission_classes = [permissions.IsAuthenticated]


class AssessmentViewSet(UserOwnedModelViewSet):
	queryset = Assessment.objects.all().order_by("-created_at")
	serializer_class = AssessmentSerializer

	def _numeric_dict(self, data):
		if not isinstance(data, dict):
			return {}
		result = {}
		for key, value in data.items():
			if isinstance(value, (int, float)):
				result[key] = float(value)
		return result

	@action(detail=True, methods=["post"], url_path="generate-profile")
	def generate_profile(self, request, pk=None):
		assessment = self.get_object()
		weighting, _ = WeightingConfig.objects.get_or_create(user=request.user)

		questionnaire = self._numeric_dict(assessment.questionnaire_data)
		behavior = self._numeric_dict(assessment.behavior_data)
		external_import = self._numeric_dict(assessment.external_import_data)

		combined_scores = {}
		all_keys = set(questionnaire) | set(behavior) | set(external_import)
		for key in all_keys:
			combined_scores[key] = round(
				(questionnaire.get(key, 0.0) * float(weighting.questionnaire_weight))
				+ (behavior.get(key, 0.0) * float(weighting.behavior_weight))
				+ (external_import.get(key, 0.0) * float(weighting.mystic_weight)),
				2,
			)

		sorted_strengths = sorted(combined_scores.items(), key=lambda item: item[1], reverse=True)
		top_strengths = [name for name, _score in sorted_strengths[:3]]

		TalentProfile.objects.filter(user=request.user, is_active=True).update(is_active=False)
		profile = TalentProfile.objects.create(
			user=request.user,
			assessment=assessment,
			profile_data={
				"summary": "已基于问卷、行为和补充输入生成天赋画像。",
				"top_strengths": top_strengths,
			},
			strengths_rank_data=sorted_strengths,
			explanation_data={
				"conflict_rule": "问卷与行为数据优先，其他来源用于补充解释。",
				"weights": {
					"questionnaire": float(weighting.questionnaire_weight),
					"behavior": float(weighting.behavior_weight),
					"mystic": float(weighting.mystic_weight),
				},
			},
			is_active=True,
		)

		serializer = TalentProfileSerializer(profile)
		return Response(serializer.data, status=status.HTTP_201_CREATED)


class MysticInputViewSet(UserOwnedModelViewSet):
	queryset = MysticInput.objects.all().order_by("-updated_at")
	serializer_class = MysticInputSerializer


class WeightingConfigViewSet(UserOwnedModelViewSet):
	queryset = WeightingConfig.objects.all().order_by("-updated_at")
	serializer_class = WeightingConfigSerializer


class TalentProfileViewSet(UserOwnedModelViewSet):
	queryset = TalentProfile.objects.all().order_by("-created_at")
	serializer_class = TalentProfileSerializer


class ProfileEditViewSet(UserOwnedModelViewSet):
	queryset = ProfileEdit.objects.all().order_by("-created_at")
	serializer_class = ProfileEditSerializer


class AnnualPlanViewSet(UserOwnedModelViewSet):
	queryset = AnnualPlan.objects.all().order_by("-year", "-updated_at")
	serializer_class = AnnualPlanSerializer


class AnnualGoalViewSet(UserOwnedModelViewSet):
	queryset = AnnualGoal.objects.all().order_by("-created_at")
	serializer_class = AnnualGoalSerializer


class MonthlyActionViewSet(UserOwnedModelViewSet):
	queryset = MonthlyAction.objects.all().order_by("-created_at")
	serializer_class = MonthlyActionSerializer


class MonthlyReviewViewSet(UserOwnedModelViewSet):
	queryset = MonthlyReview.objects.all().order_by("-created_at")
	serializer_class = MonthlyReviewSerializer

	@action(detail=False, methods=["post"], url_path="submit")
	def submit(self, request):
		month_key = request.data.get("month_key")
		template_type = request.data.get("template_type")
		review_data = request.data.get("review_data", {})
		confidence_score = request.data.get("confidence_score")

		if not month_key or not template_type:
			return Response(
				{"detail": "month_key and template_type are required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		planned_count = MonthlyAction.objects.filter(user=request.user, month_key=month_key).count()
		done_count = MonthlyAction.objects.filter(user=request.user, month_key=month_key, is_done=True).count()

		if confidence_score is None:
			if planned_count == 0:
				confidence_score = 60.0
			else:
				confidence_score = round((done_count / planned_count) * 100, 2)

		review = MonthlyReview.objects.create(
			user=request.user,
			month_key=month_key,
			template_type=template_type,
			review_data=review_data,
			confidence_score=confidence_score,
		)

		serializer = self.get_serializer(review)
		return Response(
			{
				"review": serializer.data,
				"action_stats": {
					"planned_count": planned_count,
					"done_count": done_count,
				},
			},
			status=status.HTTP_201_CREATED,
		)


class CollaborationInviteViewSet(UserOwnedModelViewSet):
	queryset = CollaborationInvite.objects.all().order_by("-created_at")
	serializer_class = CollaborationInviteSerializer


class CollaborationFeedbackViewSet(UserOwnedModelViewSet):
	queryset = CollaborationFeedback.objects.all().order_by("-created_at")
	serializer_class = CollaborationFeedbackSerializer


class PrivacyConsentViewSet(UserOwnedModelViewSet):
	queryset = PrivacyConsent.objects.all().order_by("-created_at")
	serializer_class = PrivacyConsentSerializer


class DataExportLogViewSet(UserOwnedModelViewSet):
	queryset = DataExportLog.objects.all().order_by("-created_at")
	serializer_class = DataExportLogSerializer


class DeleteRequestViewSet(UserOwnedModelViewSet):
	queryset = DeleteRequest.objects.all().order_by("-requested_at")
	serializer_class = DeleteRequestSerializer

	@action(detail=False, methods=["post"], url_path="execute")
	def execute(self, request):
		user = request.user
		delete_request = DeleteRequest.objects.create(user=user, status="pending")

		with transaction.atomic():
			delete_counts = {
				"profile_edits": ProfileEdit.objects.filter(user=user).delete()[0],
				"talent_profiles": TalentProfile.objects.filter(user=user).delete()[0],
				"assessments": Assessment.objects.filter(user=user).delete()[0],
				"monthly_reviews": MonthlyReview.objects.filter(user=user).delete()[0],
				"monthly_actions": MonthlyAction.objects.filter(user=user).delete()[0],
				"annual_goals": AnnualGoal.objects.filter(user=user).delete()[0],
				"annual_plans": AnnualPlan.objects.filter(user=user).delete()[0],
				"collaboration_feedbacks": CollaborationFeedback.objects.filter(user=user).delete()[0],
				"collaboration_invites": CollaborationInvite.objects.filter(user=user).delete()[0],
				"privacy_consents": PrivacyConsent.objects.filter(user=user).delete()[0],
				"mystic_inputs": MysticInput.objects.filter(user=user).delete()[0],
				"weighting_configs": WeightingConfig.objects.filter(user=user).delete()[0],
				"data_export_logs": DataExportLog.objects.filter(user=user).delete()[0],
			}

			delete_request.status = "completed"
			delete_request.completed_at = timezone.now()
			delete_request.save(update_fields=["status", "completed_at"])

		return Response(
			{
				"message": "Personal data deletion completed.",
				"delete_request_id": delete_request.id,
				"deleted_records": delete_counts,
				"notes": [
					"Anonymous aggregates are preserved as non-identifiable statistics.",
					"User account is kept for future re-onboarding.",
				],
			},
			status=status.HTTP_200_OK,
		)


class AnonymousAggregateViewSet(viewsets.ReadOnlyModelViewSet):
	queryset = AnonymousAggregate.objects.all().order_by("-stat_date", "goal_type", "metric_key")
	serializer_class = AnonymousAggregateSerializer
	permission_classes = [permissions.IsAuthenticated]
