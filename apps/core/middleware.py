import logging

from .models import UserOperationLog


logger = logging.getLogger(__name__)

OPERATION_LABELS = {
    "home": "查看首頁",
    "tracking": "查詢包裹",
    "postage": "使用郵資試算",
    "compare": "比較寄件方案",
    "locations": "查詢郵局據點",
    "map": "查看據點地圖",
    "location_detail": "查看據點詳情",
    "remittance": "查看取號服務",
    "remittance_form": "選擇取號業務",
    "ticket": "查看號碼牌",
    "feedback_submit": "提交意見回饋",
}


class UserOperationLogMiddleware:
    """Record successful, authenticated visits and submissions to user features."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        match = getattr(request, "resolver_match", None)
        operation = (
            OPERATION_LABELS.get(match.url_name)
            if match is not None and match.namespace == "core"
            else None
        )
        if request.method == "POST" and match is not None:
            if match.url_name == "ticket":
                operation = "申請數位號碼牌"
            elif match.url_name == "remittance_form":
                operation = "申請取號"
        request.user_operation_name = operation or ""
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if (
            response.status_code < 400
            and user is not None
            and user.is_authenticated
            and user.account != "Manager"
            and match is not None
            and match.namespace == "core"
            and request.method in {"GET", "POST"}
        ):
            if operation:
                try:
                    UserOperationLog.objects.create(
                        user=user,
                        account_name=user.account,
                        operation=operation,
                        foreground_seconds=0,
                    )
                except Exception:
                    logger.exception("Could not save user operation log.")
        return response
