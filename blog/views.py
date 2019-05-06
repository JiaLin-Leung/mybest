from myblog.libs.utils import render_template, db


def hello(request):
    context = {}
    data = db.default.mobile_subject_detail_hn.filter(subject_id=2)
    context["aa"] = data
    return render_template(request, 'login.html',context)
