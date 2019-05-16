import time

from blog.common.views import yd_information_common, error_info
from myblog.libs.utils import render_template, db, Struct
import math

from myblog.libs.utils.page import api_page


def main_page(request):
    """
    main/ 主入口页面
    :param request:
    :return:
    """
    return render_template(request, 'main.html')


def yd_information(request):
    """
    info/ 移动对比数据信息页面
    :param request:
    :return:
    """
    offset = 20  # 每页现实的信息条数
    out = Struct()
    if request.method == 'GET':
        page = int(request.GET.get('page', 1))
        cycle_num = int(request.GET.get('cycle_num', 1))
        sql_cycle_info = '''
            select id,cycle_max_id,main_cycle_num,add_time,sql_cycle_num from sql_cycle_info;
        '''  # 查询记录sql每次循环的最大id值，和目前的循环次数
        data = db.yd.fetchone_dict(sql_cycle_info)
        if data:
            timeArray = time.localtime(data.add_time)
            data.add_time = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
            out.data_info = data
            out.compare_num = data.sql_cycle_num * 500
        total = yd_information_common()  # 返回总页数
        num_total = math.ceil(total / 10)
        data = error_info(page, offset, cycle_num)
        data, page_range = api_page(data, page, total)
        out.data = data
        out.page_range = page_range
        out.cycle_num = cycle_num
        out.page = page
        out.allpage = num_total
        return render_template(request, 'info/info.html', out)


def yd_information_error(request):
    """
    error/ 错误数据重新跑的结果
    :param request:
    :return:
    """
    return render_template(request, 'info/info_error.html')
