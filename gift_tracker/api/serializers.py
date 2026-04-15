from rest_framework import serializers

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


class GiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gift
        fields = "__all__"
        read_only_fields = ("id", "created_at")


class AssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assessment
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class MysticInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = MysticInput
        fields = "__all__"
        read_only_fields = ("id", "user", "updated_at")


class WeightingConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeightingConfig
        fields = "__all__"
        read_only_fields = ("id", "user", "updated_at")


class TalentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentProfile
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class ProfileEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileEdit
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class AnnualPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualPlan
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


class AnnualGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnnualGoal
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")

    def validate_plan(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError("plan must belong to current user")
        return value


class MonthlyActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyAction
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")

    def validate_plan(self, value):
        request = self.context.get("request")
        if value and request and value.user_id != request.user.id:
            raise serializers.ValidationError("plan must belong to current user")
        return value


class MonthlyReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyReview
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class CollaborationInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborationInvite
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class CollaborationFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollaborationFeedback
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")

    def validate_invite(self, value):
        request = self.context.get("request")
        if request and value.user_id != request.user.id:
            raise serializers.ValidationError("invite must belong to current user")
        return value


class PrivacyConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivacyConsent
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class DataExportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataExportLog
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at")


class DeleteRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeleteRequest
        fields = "__all__"
        read_only_fields = ("id", "user", "requested_at")


class AnonymousAggregateSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnonymousAggregate
        fields = "__all__"
        read_only_fields = ("id", "created_at")
