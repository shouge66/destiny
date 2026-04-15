from django.db import models


class Gift(models.Model):
	name = models.CharField(max_length=120)
	category = models.CharField(max_length=80, blank=True)
	price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
	gift_date = models.DateField(null=True, blank=True)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


class Assessment(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="assessments")
	version = models.CharField(max_length=30, default="v1")
	questionnaire_data = models.JSONField(default=dict)
	behavior_data = models.JSONField(default=dict)
	external_import_data = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Assessment {self.id} - {self.user.username}"


class MysticInput(models.Model):
	user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="mystic_input")
	birth_date = models.DateField(null=True, blank=True)
	birth_time = models.TimeField(null=True, blank=True)
	latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
	longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
	timezone_name = models.CharField(max_length=64, blank=True)
	consent_flag = models.BooleanField(default=False)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"MysticInput - {self.user.username}"


class WeightingConfig(models.Model):
	user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="weighting_config")
	mystic_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.20)
	questionnaire_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.50)
	behavior_weight = models.DecimalField(max_digits=4, decimal_places=2, default=0.30)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Weighting - {self.user.username}"


class TalentProfile(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="talent_profiles")
	assessment = models.ForeignKey(Assessment, on_delete=models.SET_NULL, null=True, blank=True)
	profile_data = models.JSONField(default=dict)
	strengths_rank_data = models.JSONField(default=list)
	explanation_data = models.JSONField(default=dict)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"TalentProfile {self.id} - {self.user.username}"


class ProfileEdit(models.Model):
	profile = models.ForeignKey(TalentProfile, on_delete=models.CASCADE, related_name="edits")
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="profile_edits")
	edit_text = models.TextField(blank=True)
	edited_fields = models.JSONField(default=list)
	regenerated_profile_data = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"ProfileEdit {self.id} - {self.user.username}"


class AnnualPlanStatus(models.TextChoices):
	DRAFT = "draft", "Draft"
	ACTIVE = "active", "Active"
	ARCHIVED = "archived", "Archived"


class AnnualPlan(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="annual_plans")
	year = models.PositiveIntegerField()
	direction_text = models.TextField()
	evidence_chain_data = models.JSONField(default=dict)
	status = models.CharField(max_length=20, choices=AnnualPlanStatus.choices, default=AnnualPlanStatus.DRAFT)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["user", "year"], name="unique_annual_plan_per_user_year"),
		]

	def __str__(self):
		return f"AnnualPlan {self.year} - {self.user.username}"


class GoalStatus(models.TextChoices):
	TODO = "todo", "Todo"
	IN_PROGRESS = "in_progress", "In Progress"
	DONE = "done", "Done"


class AnnualGoal(models.Model):
	plan = models.ForeignKey(AnnualPlan, on_delete=models.CASCADE, related_name="goals")
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="annual_goals")
	goal_text = models.TextField()
	priority = models.PositiveSmallIntegerField(default=3)
	status = models.CharField(max_length=20, choices=GoalStatus.choices, default=GoalStatus.TODO)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"AnnualGoal {self.id} - {self.user.username}"


class MonthlyAction(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="monthly_actions")
	plan = models.ForeignKey(AnnualPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name="monthly_actions")
	month_key = models.CharField(max_length=7, help_text="Format: YYYY-MM")
	action_text = models.TextField()
	est_minutes = models.PositiveIntegerField(null=True, blank=True)
	due_date = models.DateField(null=True, blank=True)
	is_done = models.BooleanField(default=False)
	done_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"MonthlyAction {self.id} - {self.user.username}"


class ReviewTemplateType(models.TextChoices):
	OUTCOME = "outcome", "Outcome"
	EMOTION = "emotion", "Emotion"
	HABIT = "habit", "Habit"
	DECISION = "decision", "Decision"


class MonthlyReview(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="monthly_reviews")
	month_key = models.CharField(max_length=7, help_text="Format: YYYY-MM")
	template_type = models.CharField(max_length=20, choices=ReviewTemplateType.choices)
	review_data = models.JSONField(default=dict)
	confidence_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"MonthlyReview {self.month_key} - {self.user.username}"


class InviteType(models.TextChoices):
	FRIEND = "friend", "Friend"
	MENTOR = "mentor", "Mentor"


class InviteStatus(models.TextChoices):
	PENDING = "pending", "Pending"
	SENT = "sent", "Sent"
	ACCEPTED = "accepted", "Accepted"
	COMPLETED = "completed", "Completed"
	DECLINED = "declined", "Declined"


class CollaborationInvite(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="collaboration_invites")
	invite_type = models.CharField(max_length=20, choices=InviteType.choices)
	target_name = models.CharField(max_length=120, blank=True)
	target_contact = models.CharField(max_length=255)
	status = models.CharField(max_length=20, choices=InviteStatus.choices, default=InviteStatus.PENDING)
	sent_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Invite {self.id} - {self.user.username}"


class CollaborationFeedback(models.Model):
	invite = models.ForeignKey(CollaborationInvite, on_delete=models.CASCADE, related_name="feedbacks")
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="collaboration_feedbacks")
	feedback_tags = models.JSONField(default=list)
	feedback_text = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Feedback {self.id} - {self.user.username}"


class PrivacyConsentType(models.TextChoices):
	PERSONALIZATION = "personalization", "Personalization"
	AGGREGATION = "aggregation", "Anonymous Aggregation"
	COLLABORATION = "collaboration", "Collaboration"
	MYSTIC = "mystic", "Mystic Input"


class PrivacyConsent(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="privacy_consents")
	consent_type = models.CharField(max_length=30, choices=PrivacyConsentType.choices)
	is_granted = models.BooleanField(default=False)
	granted_at = models.DateTimeField(null=True, blank=True)
	revoked_at = models.DateTimeField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Consent {self.consent_type} - {self.user.username}"


class DataExportLog(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="data_export_logs")
	export_scope_data = models.JSONField(default=dict)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"DataExportLog {self.id} - {self.user.username}"


class DeleteRequestStatus(models.TextChoices):
	PENDING = "pending", "Pending"
	COMPLETED = "completed", "Completed"
	FAILED = "failed", "Failed"


class DeleteRequest(models.Model):
	user = models.ForeignKey("auth.User", on_delete=models.CASCADE, related_name="delete_requests")
	status = models.CharField(max_length=20, choices=DeleteRequestStatus.choices, default=DeleteRequestStatus.PENDING)
	requested_at = models.DateTimeField(auto_now_add=True)
	completed_at = models.DateTimeField(null=True, blank=True)

	def __str__(self):
		return f"DeleteRequest {self.id} - {self.user.username}"


class AnonymousAggregate(models.Model):
	stat_date = models.DateField()
	goal_type = models.CharField(max_length=80)
	metric_key = models.CharField(max_length=80)
	metric_value = models.DecimalField(max_digits=10, decimal_places=2)
	sample_size = models.PositiveIntegerField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Aggregate {self.goal_type} - {self.metric_key} ({self.stat_date})"
