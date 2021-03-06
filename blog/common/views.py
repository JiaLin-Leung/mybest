from myblog.libs.utils import db


def yd_information_common():
    sql = """
        select count(*) as total from tbkt_base.mobile_cycle_exception
    """
    data = db.yd.fetchone_dict(sql)
    return data.total if data else 0


def error_info(page, page_size, cycle_num):
    error_info_sql = '''
        select id,phone_num,code,ecid,subject_id,after_status,cycle_num from tbkt_base.mobile_cycle_exception where cycle_num = %s limit %s,%s;
    ''' % (cycle_num, (page - 1) * page_size, page_size)
    data = db.yd.fetchall_dict(error_info_sql)
    return data
