from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.http import Http404, JsonResponse
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views import View
from django.views.generic import TemplateView

from .forms import FeedbackForm
from .models import Feedback, Parcel, RemittanceQueue, RemittanceTicket


PLACES = [
    {"name": "臺北北門郵局", "area": "臺北市中正區", "type": "郵局", "address": "臺北市中正區忠孝西路一段 120 號", "hours": "08:30–17:00", "services": ["郵務", "儲匯"]},
    {"name": "臺北大安郵局", "area": "臺北市大安區", "type": "郵局", "address": "臺北市大安區信義路三段 89 號", "hours": "08:30–17:00", "services": ["郵務", "儲匯"]},
    {"name": "臺北車站 i 郵箱", "area": "臺北市中正區", "type": "i 郵箱", "address": "臺北車站大廳層東側", "hours": "24 小時", "services": ["i 郵箱", "24 小時"]},
    {"name": "新北板橋郵局", "area": "新北市板橋區", "type": "郵局", "address": "新北市板橋區文化路一段 395 號", "hours": "08:30–17:00", "services": ["郵務", "儲匯"]},
    {"name": "臺中民權路郵局", "area": "臺中市西區", "type": "郵局", "address": "臺中市西區民權路 86 號", "hours": "08:30–17:00", "services": ["郵務", "儲匯"]},
]

# 起重 0.5 公斤 + 每續重 0.5 公斤；資料依中華郵政國際航空包裹常用資費表。
INTERNATIONAL_AIR_RATES = {
    "hong_kong": ("香港", 240, 35, 30),
    "macau": ("澳門", 260, 45, 30),
    "japan": ("日本", 425, 55, 30),
    "singapore": ("新加坡", 220, 55, 30),
    "indonesia": ("印尼", 340, 90, 30),
    "malaysia": ("馬來西亞", 170, 55, 30),
    "thailand": ("泰國", 240, 55, 30),
    "philippines": ("菲律賓", 230, 45, 20),
    "south_korea": ("大韓民國", 220, 40, 20),
    "vietnam": ("越南", 360, 100, 30),
    "india": ("印度", 290, 80, 20),
    "australia": ("澳大利亞", 310, 105, 20),
    "new_zealand": ("紐西蘭", 340, 100, 30),
    "united_states": ("美國", 500, 105, 30),
    "hawaii": ("夏威夷", 180, 120, 30),
    "canada": ("加拿大", 230, 155, 30),
    "france": ("法國", 480, 125, 30),
    "germany": ("德國", 300, 105, 30),
    "switzerland": ("瑞士", 280, 115, 30),
    "netherlands": ("荷蘭", 280, 105, 20),
    "united_kingdom": ("英國", 380, 115, 30),
    "italy": ("義大利", 480, 105, 30),
    "spain": ("西班牙", 320, 120, 30),
}


class PostageView(TemplateView):
    template_name = "core/postage.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request
        context.update(
            weight=request.GET.get("weight", ""),
            kind=request.GET.get("kind", "parcel"),
            international_country=request.GET.get("international_country", "japan"),
            region=request.GET.get("region", "across"),
            delivery=request.GET.get("delivery", "home"),
            box_size=request.GET.get("box_size", "box5"),
            reused=request.GET.get("reused") == "yes",
            length=request.GET.get("length", ""),
            width=request.GET.get("width", ""),
            height=request.GET.get("height", ""),
            result=None,
            error=None,
            regions=[
                ("local", "本島同縣市／北北基互寄／外島島內"),
                ("across", "臺灣本島不同縣市"),
                ("island", "臺灣本島與外島互寄"),
            ],
            delivery_options=[("home", "宅配到府"), ("locker", "i 郵箱取件／自郵領件")],
            box_options=[
                ("box1", "長型便利箱", "31 × 22.8 × 10.3 cm", 80, 7),
                ("box2", "方型便利箱", "23 × 18 × 19 cm", 80, 7),
                ("box3", "90 公分便利箱", "39.5 × 27.5 × 23 cm", 110, 12),
                ("box4", "長柱型便利箱", "10 × 10 × 62.5 cm", 80, 7),
                ("box5", "小型便利箱", "23 × 14 × 13 cm", 65, 3),
                ("bag1", "一般便利袋", "31 × 23 × 3 cm", 65, 0),
                ("bag2", "寶貝便利袋（氣泡布）", "29.5 × 22 cm", 70, 0),
            ],
            international_countries=[
                (code, data[0], data[3])
                for code, data in INTERNATIONAL_AIR_RATES.items()
            ],
        )
        selected_country = INTERNATIONAL_AIR_RATES.get(context["international_country"])
        context["weight_max"] = (
            selected_country[3] * 1000
            if context["kind"] == "international" and selected_country
            else 30000 if context["kind"] == "international" else 20000
        )
        context["weight_limit_kg"] = (
            selected_country[3]
            if context["kind"] == "international" and selected_country
            else 30 if context["kind"] == "international" else 20
        )

        if "calculate" not in request.GET:
            return context

        if context["kind"] not in ("parcel", "box", "international"):
            context["error"] = "請選擇有效的寄件方式。"
            return context

        try:
            weight = int(context["weight"])
            max_weight = 30000 if context["kind"] == "international" else 20000
            if weight < 1 or weight > max_weight:
                raise ValueError
        except (ValueError, TypeError):
            limit = "30,000" if context["kind"] == "international" else "20,000"
            context["error"] = f"請輸入 1 至 {limit} 公克的有效重量。"
            return context

        if context["kind"] == "international":
            tariff = INTERNATIONAL_AIR_RATES.get(context["international_country"])
            if tariff is None:
                context["error"] = "目前尚無此目的地的線上估價，請使用官方資費查詢。"
                return context
            country, starting_price, half_kilo_price, country_limit = tariff
            if weight > country_limit * 1000:
                context["error"] = f"{country}國際航空包裹限重 {country_limit} 公斤。"
                return context
            try:
                dimensions = [int(context[key]) for key in ("length", "width", "height")]
                if any(value < 1 for value in dimensions):
                    raise ValueError
            except (ValueError, TypeError):
                context["error"] = "國際包裹請填寫完整且大於 0 的長、寬、高。"
                return context
            volumetric_grams = (dimensions[0] * dimensions[1] * dimensions[2] + 5) // 6
            chargeable_grams = max(weight, volumetric_grams)
            billable_half_kilos = (chargeable_grams + 499) // 500
            chargeable_kg = billable_half_kilos / 2
            if chargeable_kg > country_limit:
                context["error"] = f"{country}計費重量上限為 {country_limit} 公斤（實重與材積重取較重者）。"
                return context
            price = starting_price + (billable_half_kilos - 1) * half_kilo_price
            context["result"] = {
                "name": "國際航空包裹",
                "price": price,
                "weight_label": f"{weight:,} 公克",
                "billing_label": f"{chargeable_kg:g} 公斤",
                "destination_label": country,
                "dimensions": " × ".join(str(value) for value in dimensions) + " 公分",
                "note": "材積重量以長 × 寬 × 高 ÷ 6,000 計算，取實重與材積重量較重者，再以每 0.5 公斤級距計價。急難航空附加費與附加服務未包含。",
            }
            return context

        if context["kind"] == "box":
            box = next(
                (item for item in context["box_options"] if item[0] == context["box_size"]),
                None,
            )
            if box is None:
                context["error"] = "請選擇有效的便利箱或便利袋款式。"
                return context
            _, name, dimensions, base_price, reuse_discount = box
            discount = reuse_discount if context["reused"] else 0
            context["result"] = {
                "name": name,
                "price": base_price - discount,
                "base_price": base_price,
                "discount": discount,
                "dimensions": dimensions,
                "note": "便利箱（袋）國內單一價格；重複使用折抵依款式計算。",
            }
            return context

        region = context["region"]
        delivery = context["delivery"]
        rates = {
            "local": {"home": [70, 90, 110, 135], "locker": [48, 68, 88, 113]},
            "across": {"home": [80, 100, 120, 145], "locker": [58, 78, 98, 123]},
            "island": {"home": [100, 125, 150, 180], "locker": [78, 103, 128, 158]},
        }
        if region not in rates or delivery not in rates[region]:
            context["error"] = "請重新選擇有效的寄送區域與投遞方式。"
            return context

        dimensions = None
        if delivery == "locker":
            try:
                dimensions = [int(context[key]) for key in ("length", "width", "height")]
                if any(value < 1 for value in dimensions):
                    raise ValueError
            except (ValueError, TypeError):
                context["error"] = "i 郵箱取件請填寫完整且大於 0 的長、寬、高。"
                return context
            sorted_dimensions = sorted(dimensions, reverse=True)
            if (
                sorted_dimensions[0] > 45
                or sorted_dimensions[1] > 34
                or sorted_dimensions[2] > 27
                or sum(sorted_dimensions) > 105
            ):
                context["error"] = "包裹尺寸超出 i 郵箱限制，請改選宅配或縮小包裝。"
                return context

        tier = next(index for index, limit in enumerate((5000, 10000, 15000, 20000)) if weight <= limit)
        price = rates[region][delivery][tier]
        context["result"] = {
            "name": "國內普通包裹",
            "price": price,
            "weight_label": f"{weight:,} 公克",
            "tier_label": ("不逾 5 公斤", "逾 5 公斤不逾 10 公斤", "逾 10 公斤不逾 15 公斤", "逾 15 公斤不逾 20 公斤")[tier],
            "delivery_label": dict(context["delivery_options"])[delivery],
            "region_label": dict(context["regions"])[region],
            "note": "依國內包裹窗口普通資費估算。",
        }
        return context


class CompareView(TemplateView):
    template_name = "core/compare.html"


class LocationsView(TemplateView):
    template_name = "core/locations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = self.request.GET.get("city", "")
        district = self.request.GET.get("district", "")
        # Keep links using the older `area` query parameter working.
        area = self.request.GET.get("area", "")
        if area and not city:
            if area.endswith(("市", "縣")):
                city = area
            else:
                city, district = area[:3], area[3:]
        service = self.request.GET.get("service", "全部服務")
        places = [dict(place, place_id=index) for index, place in enumerate(PLACES)]
        cities = sorted({p["area"][:3] for p in PLACES})
        districts = sorted({p["area"][3:] for p in PLACES if p["area"].startswith(city)}) if city else []
        if city:
            places = [p for p in places if p["area"].startswith(city)]
        if district:
            places = [p for p in places if p["area"] == f"{city}{district}"]
        if service != "全部服務":
            places = [p for p in places if service in p["services"]]
        context.update(places=places, city=city, district=district, cities=cities, districts=districts,
                       service=service, services=["全部服務", "郵務", "儲匯", "i 郵箱", "24 小時"])
        return context


class LocationMapView(TemplateView):
    template_name = "core/map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["places"] = PLACES
        return context


class LocationDetailView(TemplateView):
    template_name = "core/location_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        place_id = kwargs.get("place_id")
        if place_id is None or place_id < 0 or place_id >= len(PLACES):
            raise Http404("找不到這個據點")
        context["place"] = PLACES[place_id]
        return context


@method_decorator(never_cache, name="dispatch")
class RemittanceView(LoginRequiredMixin, TemplateView):
    template_name = "core/remittance.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        city = self.request.GET.get("city", "")
        district = self.request.GET.get("district", "")
        offices = [dict(place, place_id=index) for index, place in enumerate(PLACES)
                   if "儲匯" in place["services"]]
        cities = sorted({place["area"][:3] for place in offices})
        districts = sorted({place["area"][3:] for place in offices
                            if place["area"].startswith(city)}) if city else []
        if city:
            offices = [place for place in offices if place["area"].startswith(city)]
        if district:
            offices = [place for place in offices if place["area"] == f"{city}{district}"]

        queue_data = {
            queue.office_name: queue
            for queue in RemittanceQueue.objects.filter(
                office_name__in=[office["name"] for office in offices]
            )
        }
        for office in offices:
            queue = queue_data.get(office["name"])
            office["waiting"] = queue.waiting_people if queue else 0
            office["minutes"] = queue.estimated_wait_minutes if queue else 0
        context.update(offices=offices, city=city, district=district,
                       cities=cities, districts=districts)
        return context


def get_remittance_office(office_id):
    try:
        place = PLACES[int(office_id)]
    except (ValueError, TypeError, IndexError):
        return PLACES[0]
    return place if "儲匯" in place["services"] else PLACES[0]


@transaction.atomic
def issue_remittance_ticket(user, office, business_type):
    queue = RemittanceQueue.objects.select_for_update().get(office_name=office["name"])
    existing_ticket = RemittanceTicket.objects.filter(
        user=user,
        office_name=office["name"],
        business_type=business_type,
    ).first()
    if existing_ticket:
        return existing_ticket

    queue.waiting_people += 1
    queue.last_ticket_number += 1
    queue.save(update_fields=("waiting_people", "last_ticket_number", "updated_at"))
    return RemittanceTicket.objects.create(
        user=user,
        office_name=office["name"],
        business_type=business_type,
        ticket_number=f"A{queue.last_ticket_number:03d}",
        people_ahead=queue.waiting_people - 1,
    )


@method_decorator(never_cache, name="dispatch")
class RemittanceFormView(LoginRequiredMixin, TemplateView):
    template_name = "core/remittance_form.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        office_id = self.request.GET.get("office", self.request.session.get("remittance_office", 0))
        service = self.request.GET.get("service", "general")
        if service not in {"general", "postal"}:
            service = "general"
        context["office_id"] = office_id
        context["office"] = get_remittance_office(office_id)
        context["service"] = service
        context["business_types"] = (
            [("postal", "郵務業務")]
            if service == "postal"
            else RemittanceTicket.GENERAL_BUSINESS_TYPES
        )
        return context

    def post(self, request, *args, **kwargs):
        office = get_remittance_office(request.POST.get("office"))
        service = request.POST.get("service", "general")
        if service not in {"general", "postal"}:
            service = "general"
        allowed_types = dict(
            [("postal", "郵務業務")]
            if service == "postal"
            else RemittanceTicket.GENERAL_BUSINESS_TYPES
        )
        business_type = request.POST.get("business_type", "")
        if business_type not in allowed_types:
            return redirect(
                f"{reverse('core:remittance_form')}?office={PLACES.index(office)}&service={service}"
            )
        request.session["remittance_office"] = PLACES.index(office)
        ticket = issue_remittance_ticket(request.user, office, business_type)
        return redirect(f"{reverse('core:ticket')}?ticket={ticket.pk}")


@method_decorator(never_cache, name="dispatch")
class TicketView(LoginRequiredMixin, TemplateView):
    template_name = "core/ticket.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tickets = RemittanceTicket.objects.filter(user=self.request.user)
        ticket_id = self.request.GET.get("ticket")
        selected_ticket = (
            tickets.filter(pk=int(ticket_id)).first()
            if ticket_id and ticket_id.isdigit()
            else tickets.first()
        )
        context["my_tickets"] = tickets
        context["selected_ticket"] = selected_ticket
        return context

    def post(self, request, *args, **kwargs):
        office = get_remittance_office(request.POST.get("office"))
        business_type = request.POST.get("business_type", "")
        if business_type not in dict(RemittanceTicket.BUSINESS_TYPES):
            return redirect("core:remittance")
        ticket = issue_remittance_ticket(request.user, office, business_type)
        return redirect(f"{reverse('core:ticket')}?ticket={ticket.pk}")


class TrackingView(LoginRequiredMixin, TemplateView):
    template_name = "core/tracking.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sent = list(Parcel.objects.filter(sender=self.request.user).select_related("recipient"))
        received = list(Parcel.objects.filter(recipient=self.request.user).select_related("sender"))
        for parcel in sent:
            parcel.route_stations = parcel.get_route_steps()
        for parcel in received:
            parcel.route_stations = parcel.get_route_steps()
        context.update(
            sent_parcels=sent,
            received_parcels=received,
        )
        return context


class HomeView(TemplateView):
    template_name = "home.html"


class FeedbackSubmitView(LoginRequiredMixin, View):
    login_url = "accounts:login"

    def post(self, request, *args, **kwargs):
        form = FeedbackForm(request.POST)
        next_url = request.POST.get("next", "")
        if not url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            next_url = reverse("core:home")

        if form.is_valid():
            Feedback.objects.create(
                user=request.user,
                account_name=request.user.account,
                **form.cleaned_data,
            )
            messages.success(request, "意見回饋已記錄，謝謝你的建議。")
        else:
            messages.error(request, "請確認回饋內容並重新送出。")
        return redirect(next_url)


@ensure_csrf_cookie
@never_cache
def refresh_csrf_token(request):
    return JsonResponse({"csrfToken": get_token(request)})
