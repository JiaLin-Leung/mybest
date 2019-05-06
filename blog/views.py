import time

from myblog.libs.utils import render_template, db


def hello(request):
    context = {}
    # data = db.default.mobile_subject_detail_hn.filter(subject_id=2)
    sql_cycle_info = '''
        select id,cycle_max_id,main_cycle_num,add_time,sql_cycle_num from sql_cycle_info;
    '''  # 查询记录sql每次循环的最大id值，和目前的循环次数
    data = db.yd.fetchone_dict(sql_cycle_info)
    if data:
        timeArray = time.localtime(data.add_time)
        data.add_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        context["data"] = data
        context["compare_num"] = data.sql_cycle_num * 500
        return render_template(request, 'login.html',context)
