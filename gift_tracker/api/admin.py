from django.contrib import admin
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


@admin.register(Gift)
class GiftAdmin(admin.ModelAdmin):
	list_display = ("id", "name", "category", "price", "gift_date", "created_at")
	search_fields = ("name", "category", "note")
	list_filter = ("category", "gift_date", "created_at")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "version", "created_at")
	search_fields = ("user__username", "version")
	list_filter = ("version", "created_at")


@admin.register(MysticInput)
class MysticInputAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "birth_date", "timezone_name", "consent_flag", "updated_at")
	search_fields = ("user__username", "timezone_name")
	list_filter = ("consent_flag", "updated_at")


@admin.register(WeightingConfig)
class WeightingConfigAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "mystic_weight", "questionnaire_weight", "behavior_weight", "updated_at")
	search_fields = ("user__username",)


@admin.register(TalentProfile)
class TalentProfileAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "assessment", "is_active", "created_at")
	search_fields = ("user__username",)
	list_filter = ("is_active", "created_at")


@admin.register(ProfileEdit)
class ProfileEditAdmin(admin.ModelAdmin):
	list_display = ("id", "profile", "user", "created_at")
	search_fields = ("user__username", "profile__id")
	list_filter = ("created_at",)


@admin.register(AnnualPlan)
class AnnualPlanAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "year", "status", "created_at", "updated_at")
	search_fields = ("user__username", "year")
	list_filter = ("status", "year", "created_at")


@admin.register(AnnualGoal)
class AnnualGoalAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "plan", "priority", "status", "created_at")
	search_fields = ("user__username", "goal_text")
	list_filter = ("status", "priority", "created_at")


@admin.register(MonthlyAction)
class MonthlyActionAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "month_key", "is_done", "due_date", "created_at")
	search_fields = ("user__username", "month_key", "action_text")
	list_filter = ("is_done", "month_key", "created_at")


@admin.register(MonthlyReview)
class MonthlyReviewAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "month_key", "template_type", "confidence_score", "created_at")
	search_fields = ("user__username", "month_key", "template_type")
	list_filter = ("template_type", "month_key", "created_at")


@admin.register(CollaborationInvite)
class CollaborationInviteAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "invite_type", "target_contact", "status", "sent_at", "created_at")
	search_fields = ("user__username", "target_contact", "target_name")
	list_filter = ("invite_type", "status", "created_at")


@admin.register(CollaborationFeedback)
class CollaborationFeedbackAdmin(admin.ModelAdmin):
	list_display = ("id", "invite", "user", "created_at")
	search_fields = ("user__username", "invite__id", "feedback_text")
	list_filter = ("created_at",)


@admin.register(PrivacyConsent)
class PrivacyConsentAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "consent_type", "is_granted", "granted_at", "revoked_at")
	search_fields = ("user__username", "consent_type")
	list_filter = ("consent_type", "is_granted", "created_at")


@admin.register(DataExportLog)
class DataExportLogAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "created_at")
	search_fields = ("user__username",)
	list_filter = ("created_at",)


@admin.register(DeleteRequest)
class DeleteRequestAdmin(admin.ModelAdmin):
	list_display = ("id", "user", "status", "requested_at", "completed_at")
	search_fields = ("user__username",)
	list_filter = ("status", "requested_at")


@admin.register(AnonymousAggregate)
class AnonymousAggregateAdmin(admin.ModelAdmin):
	list_display = ("id", "goal_type", "metric_key", "metric_value", "sample_size", "stat_date")
	search_fields = ("goal_type", "metric_key")
	list_filter = ("goal_type", "stat_date")
