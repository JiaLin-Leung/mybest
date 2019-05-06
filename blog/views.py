from django.http import HttpResponse
from django.shortcuts import render

from myblog.libs.utils import render_template, db


def hello(request):
    gifts = db.gift.score_gift.filter(app_id=7, status=1, is_indexed=1).select(
        'id', 'name', 'img_url', 'score voucher').group_by('name').order_by('-add_date')[:6]
    print("111111",gifts)
    out = dict(
        today=gifts
    )
    return render_template(request, 'login.html',out)
