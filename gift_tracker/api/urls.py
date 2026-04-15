from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AnnualGoalViewSet
from .views import AnnualPlanViewSet
from .views import AnonymousAggregateViewSet
from .views import ApiRootView
from .views import AssessmentViewSet
from .views import CollaborationFeedbackViewSet
from .views import CollaborationInviteViewSet
from .views import DataExportLogViewSet
from .views import DeleteRequestViewSet
from .views import GiftViewSet
from .views import GuestLoginView
from .views import HealthCheckView
from .views import MonthlyActionViewSet
from .views import MonthlyReviewViewSet
from .views import MysticAnalysisView
from .views import MysticInputViewSet
from .views import PrivacyConsentViewSet
from .views import ProfileEditViewSet
from .views import RegisterView
from .views import TalentProfileViewSet
from .views import WeightingConfigViewSet

router = DefaultRouter()
router.register("gifts", GiftViewSet, basename="gift")
router.register("assessments", AssessmentViewSet, basename="assessment")
router.register("mystic-inputs", MysticInputViewSet, basename="mystic-input")
router.register("weighting-configs", WeightingConfigViewSet, basename="weighting-config")
router.register("talent-profiles", TalentProfileViewSet, basename="talent-profile")
router.register("profile-edits", ProfileEditViewSet, basename="profile-edit")
router.register("annual-plans", AnnualPlanViewSet, basename="annual-plan")
router.register("annual-goals", AnnualGoalViewSet, basename="annual-goal")
router.register("monthly-actions", MonthlyActionViewSet, basename="monthly-action")
router.register("monthly-reviews", MonthlyReviewViewSet, basename="monthly-review")
router.register("collaboration-invites", CollaborationInviteViewSet, basename="collaboration-invite")
router.register("collaboration-feedbacks", CollaborationFeedbackViewSet, basename="collaboration-feedback")
router.register("privacy-consents", PrivacyConsentViewSet, basename="privacy-consent")
router.register("data-export-logs", DataExportLogViewSet, basename="data-export-log")
router.register("delete-requests", DeleteRequestViewSet, basename="delete-request")
router.register("anonymous-aggregates", AnonymousAggregateViewSet, basename="anonymous-aggregate")

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("health/", HealthCheckView.as_view(), name="health-check"),
    path("mystic-analysis/", MysticAnalysisView.as_view(), name="mystic-analysis"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path("auth/guest/", GuestLoginView.as_view(), name="guest-login"),
    path("auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(router.urls)),
]
