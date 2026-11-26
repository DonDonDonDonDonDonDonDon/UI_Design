from django.conf import settings
from django.db import models


class Parcel(models.Model):
    class PackageType(models.TextChoices):
        LETTER = "letter", "信件 / 小包"
        REGISTERED = "registered", "掛號郵件"
        BOX = "box", "便利箱"
        BAG = "bag", "便利袋"
        INTERNATIONAL = "international", "國際包裹"

    class Status(models.TextChoices):
        ACCEPTED = "accepted", "已收寄"
        IN_TRANSIT = "in_transit", "運送中"
        OUT_FOR_DELIVERY = "out_for_delivery", "配送中"
        DELIVERED = "delivered", "已送達"
        EXCEPTION = "exception", "配送異常"

    tracking_number = models.CharField("郵件單號", max_length=32, unique=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_parcels",
        verbose_name="寄件人",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="received_parcels",
        verbose_name="收件人",
    )
    package_type = models.CharField("包裹種類", max_length=20, choices=PackageType.choices)
    origin_office = models.CharField("寄件郵局", max_length=120, default="臺北北門郵局")
    destination_office = models.CharField("收件郵局", max_length=120, default="臺北大安郵局")
    current_status = models.CharField(
        "目前狀態", max_length=24, choices=Status.choices, default=Status.ACCEPTED
    )
    current_location = models.CharField("目前位置", max_length=120, default="郵局收寄")
    route_stops = models.JSONField("運送站點", default=list, blank=True)
    sent_at = models.DateTimeField("寄件時間", auto_now_add=True)
    updated_at = models.DateTimeField("進度更新時間", auto_now=True)

    class Meta:
        db_table = "parcel"
        ordering = ("-updated_at",)
        verbose_name = "包裹"
        verbose_name_plural = "包裹"

    def __str__(self):
        return self.tracking_number

    def get_route_steps(self):
        stations = self.route_stops or [
            self.origin_office,
            "臺北郵件處理中心",
            self.destination_office,
        ]
        if self.current_location in stations:
            current_index = stations.index(self.current_location)
        elif self.current_status == self.Status.ACCEPTED:
            current_index = 0
        elif self.current_status in (self.Status.OUT_FOR_DELIVERY, self.Status.DELIVERED):
            current_index = len(stations) - 1
        else:
            current_index = min(1, len(stations) - 1)
        return [
            {
                "role": (
                    "寄件郵局" if index == 0
                    else "收件郵局" if index == len(stations) - 1
                    else "轉運／查驗站"
                ),
                "name": station,
                "current": index == current_index,
                "passed": index < current_index,
                "connector_passed": index < current_index,
            }
            for index, station in enumerate(stations)
        ]


class RemittanceQueue(models.Model):
    office_name = models.CharField("郵局", max_length=120, unique=True)
    waiting_people = models.PositiveIntegerField("目前等候人數", default=0)
    last_ticket_number = models.PositiveIntegerField("最後號碼牌序號", default=0)
    updated_at = models.DateTimeField("更新時間", auto_now=True)

    class Meta:
        db_table = "remittancequeue"
        ordering = ("office_name",)
        verbose_name = "儲匯等候狀況"
        verbose_name_plural = "儲匯等候狀況"

    @property
    def estimated_wait_minutes(self):
        return self.waiting_people * 2

    def __str__(self):
        return f"{self.office_name}（等候 {self.waiting_people} 人）"


class RemittanceTicket(models.Model):
    BUSINESS_TYPES = [
        ("remittance", "匯款"),
        ("deposit_withdrawal", "存提"),
        ("account_opening", "開戶"),
        ("seal_change", "換印鑑"),
        ("postal", "郵務業務"),
    ]
    GENERAL_BUSINESS_TYPES = BUSINESS_TYPES[:4]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="remittance_tickets",
        verbose_name="會員帳號",
    )
    office_name = models.CharField("郵局", max_length=120)
    business_type = models.CharField(
        "業務類別", max_length=24, choices=BUSINESS_TYPES, default="remittance"
    )
    ticket_number = models.CharField("號碼牌", max_length=20)
    people_ahead = models.PositiveIntegerField("取號時前方等候人數", default=0)
    issued_at = models.DateTimeField("取號時間", auto_now_add=True)

    class Meta:
        db_table = "remittanceticket"
        ordering = ("-issued_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "office_name", "business_type"),
                name="unique_user_ticket_per_office_business",
            ),
            models.UniqueConstraint(
                fields=("office_name", "ticket_number"),
                name="unique_remittance_ticket_number_per_office",
            ),
        ]
        verbose_name = "儲匯號碼牌"
        verbose_name_plural = "儲匯號碼牌"

    @property
    def estimated_wait_minutes(self):
        return self.people_ahead * 2

    def __str__(self):
        return f"{self.office_name} {self.ticket_number}"


class Feedback(models.Model):
    class FeedbackType(models.TextChoices):
        LIKE = "like", "按讚"
        DISLIKE = "dislike", "倒讚"
        FORM = "form", "意見表單"

    class Category(models.TextChoices):
        SUGGESTION = "suggestion", "功能建議"
        ISSUE = "issue", "問題回報"
        EXPERIENCE = "experience", "使用體驗"
        OTHER = "other", "其他"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback_entries",
        verbose_name="提交會員",
    )
    account_name = models.CharField("提交時帳號", max_length=150)
    feedback_type = models.CharField(
        "回饋方式", max_length=12, choices=FeedbackType.choices
    )
    category = models.CharField(
        "回饋類型", max_length=20, choices=Category.choices, blank=True
    )
    message = models.TextField("回饋內容", max_length=1000, blank=True)
    contact = models.CharField("聯絡方式", max_length=120, blank=True)
    created_at = models.DateTimeField("提交時間", auto_now_add=True)

    class Meta:
        db_table = "userfeedback"
        ordering = ("-created_at",)
        verbose_name = "意見回饋"
        verbose_name_plural = "意見回饋"

    def __str__(self):
        return f"{self.account_name} · {self.get_feedback_type_display()} · {self.created_at:%Y-%m-%d %H:%M}"


class UserOperationLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operation_logs",
        verbose_name="操作會員",
    )
    account_name = models.CharField("操作時帳號", max_length=150)
    operation = models.CharField("操作", max_length=120)
    foreground_seconds = models.PositiveIntegerField("頁面前景停留秒數", default=0)
    operated_at = models.DateTimeField("操作時間", auto_now_add=True)

    class Meta:
        db_table = "useroperationlog"
        ordering = ("-operated_at",)
        verbose_name = "使用者操作紀錄"
        verbose_name_plural = "使用者操作紀錄"

    def __str__(self):
        return f"{self.account_name} · {self.operation} · {self.operated_at:%Y-%m-%d %H:%M}"
