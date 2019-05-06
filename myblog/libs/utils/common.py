import datetime
import hashlib
import time
import json
import logging
import re
import traceback
import pypinyin
import urllib3
import os
import requests
from django.http import HttpResponse
from django.template import loader
from django.conf import settings
from django.views.generic import TemplateView

from . import ajax
log = logging.getLogger(__name__)
RE_CHINA_MOBILE = re.compile(r"^1(([3][456789])|([5][012789])|([8][23478])|([4][7])|([7][8]))[0-9]{8}$")


class Struct(dict):
    """
    为字典加上点语法. 例如:
    >>> o = Struct({'a':1})
    >>> o.a
    >>> 1
    >>> o.b
    >>> None
    """

    def __init__(self, *e, **f):
        if e:
            self.update(e[0])
        if f:
            self.update(f)

    def __getattr__(self, name):
        # Pickle is trying to get state from your object, and dict doesn't implement it.
        # Your __getattr__ is being called with "__getstate__" to find that magic method,
        # and returning None instead of raising AttributeError as it should.
        if name.startswith('__'):
            raise AttributeError
        return self.get(name)

    def __setattr__(self, name, val):
        self[name] = val

    def __delattr__(self, name):
        self.pop(name, None)

    def __hash__(self):
        return id(self)


def is_chinamobile(phone):
    """
    功能说明：       判断是否为移动手机号
    ----------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------
    王晨光                2016-10-10
    """
    if not isinstance(phone, str):
        return False
    return RE_CHINA_MOBILE.match(phone)


def from_unixtime(stamp):
    """
    时间戳转Datetime
    :param stamp: 时间
    :return: datatime
    """
    if not isinstance(stamp, int):
        return stamp
    st = time.localtime(stamp)
    return datetime.datetime(*st[:6])


def casts(self, **kw):
    """
    功能说明：       批量转换url参数类型
    用法:
    >>> request.GET.__class__ = casts
    >>> args = request.GET.casts(keyword=str, page=int, a="(\d+)")
    >>> print args
    >>> {'keyword': '', 'page':0, 'a':''}
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-6-26
    """
    args = Struct()
    for k, typ in kw.items():
        v = self.get(k)
        if isinstance(typ, str):
            if typ == 'json':
                try:
                    v = json.loads(v) if v else {}
                except Exception as e:
                    print(e)
                    pass
            elif typ == 'datetime':
                if v:
                    if v.endswith('24:00:00'):
                        v = v.split()[0] + ' 23:59:59'
                        v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = time.localtime(time.mktime(v) + 1)
                        v = datetime.datetime(*v[:6])
                    else:
                        t = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = datetime.datetime(*t[:6])
                else:
                    v = None
            elif typ == 'timestamp':
                if v:
                    if v.endswith('24:00:00'):
                        v = v.split()[0] + ' 23:59:59'
                        v = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = int(time.mktime(v) + 1)
                    else:
                        t = time.strptime(v, "%Y-%m-%d %H:%M:%S")
                        v = int(time.mktime(t))
            else:
                m = re.match(typ, v or '')
                groups = m.groups() if m else ()
                groups = [g for g in groups if g is not None]
                v = groups[0] if groups else ''
        else:
            defv = type_default_value(typ)
            try:
                v = v if defv == [] else (typ(v) if v is not None else defv)
                # 添加原生数组数据传递解决办法
                if isinstance(defv, list):
                    if isinstance(v, str):
                        v = json.loads(v.strip('"'))
            except:
                v = defv
        if v is not None:
            args[k] = v
    return args


def strxor(s, key):
    """
    功能:异或加密
    返回:一个bytearray类型
    """
    try:
        key = key & 0xff
        a = bytearray(s)
        b = bytearray(len(a))
        for i, c in enumerate(a):
            b[i] = c ^ key
        return b
    except Exception as e:
        print(e)


def type_default_value(typ):
    """返回基本类型默认值, 没有识别的类型返回None"""
    tab = {str: "", list: [], int: 0}
    return tab.get(typ)


def loads(self):
    """
    功能说明：      解析json格式参数
    用法:
    >>> request.__class__ = loads
    >>> args = request.loads()
    >>> print args
    >>> {}
    """
    try:
        o = json.loads(self.body)
    except Exception as e:
        print(e)
        o = {}
    return Struct(o)


def not_found(request):
    """
    404 response
    :param request: 
    :return: 
    """
    return ajax.jsonp_fail(request)


def get_absurl(url):
    """
    将相对路径转换为绝对路径
    :param url: 
    :return: 
    """
    if not url:
        return ""
    if "http" in url:
        return url
    return "%s/upload_media/%s" % (settings.FILE_CDN_URLROOT, url)


def join(o):
    """
    把数组用逗号连接成字符串

    例如:
    >>> join([1, 2])
    >>> '1,2'
    """
    if isinstance(o, (list, tuple, set)):
        return ','.join(str(i) for i in o)
    return str(o)


def pinyin_abb(name):
    """
    功能说明：       将姓名转换为拼音首字母缩写
    >>> pinyin_abb(u'王晨光')
    >>> wcg
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016-10-10
    """
    if not isinstance(name, str):
        name = name.decode('utf-8')
    rows = pypinyin.pinyin(name, style=pypinyin.NORMAL)
    return ''.join(row[0][0] for row in rows if len(row)>0)


def num_to_ch(num):
    """
    功能说明：讲阿拉伯数字转换成中文数字（转换[0, 10000)之间的阿拉伯数字 ）
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    陈龙                2012.2.9
    """
    num = int(num)
    _MAPPING = ('零', '一', '二', '三', '四', '五', '六', '七', '八', '九',)
    _P0 = ('', '十', '百', '千',)
    _S4 = 10 ** 4

    if _S4 <= num < 0:
        return None
    if num < 10:
        return _MAPPING[num]
    else:
        lst = []
        while num >= 10:
            lst.append(num % 10)
            num = num / 10
        lst.append(num)
        c = len(lst)  # 位数
        result = u''
        for idx, val in enumerate(lst):
            if val != 0:
                result += _P0[idx] + _MAPPING[int(val)]
            if idx < c - 1 and lst[idx + 1] == 0:
                result += '零'
        return result[::-1].replace('一十', '十')


def stamp_format(stamp, fmt="%m-%d %H:%M"):
    """
    时间戳转换
    :param stamp:
    :param fmt:
    :return:
    """
    return time.strftime(fmt, time.localtime(stamp))


def check_response(data_dict):
    """
    功能:检测返回数据结果
    :param data_dict:
    :return: 成功返回data_dict的data和True,失败或者错误返回message和False
    """
    # 返回结果的response可能为ok, fail, error
    if data_dict.response == "error" or data_dict.response == "fail":
        return data_dict.data, data_dict.message, False
    else:
        if isinstance(data_dict.data, dict):
            data = Struct(data_dict.data)
        else:
            data = data_dict.data
        return data, data_dict.message, True


def date_to_unix(obj_value, add=0):
    """
    功能: 把时间字符串转换为时间戳并返回
    ---------------------------------
    接收参数类型: '20180326', '2018-03-26', '2018-03-26 18:00:00', datetime.datetime格式
    ---------------------------------------------------------------------------------
    修改:宋国洋   添加多参数类型的转换,且非datetime格式的数据只精确到天,datetime格式精确到秒
    """

    if isinstance(obj_value, datetime.datetime) or isinstance(obj_value, str):
        if isinstance(obj_value, datetime.datetime):
            if add > 0:
                obj_value += datetime.timedelta(days=add)
            time_stamp = int(time.mktime(obj_value.timetuple()))
        else:
            # 只获取字符串中的数字
            string_obj = ""
            for st in re.findall(r'\d', obj_value):
                string_obj += st
            if len(string_obj) < 8:
                raise ValueError("illegal param")
            y, m, d = string_obj[:4], string_obj[4:6], string_obj[6:8]
            t_date = datetime.date(int(y), int(m), int(d))
            if add > 0:
                t_date += datetime.timedelta(days=add)
            time_stamp = int(time.mktime(t_date.timetuple()))
        return time_stamp
    else:
        raise ValueError("param type must be str or datetime.datetime")


def render_template_data(request, template_path, context):
    t = loader.get_template(template_path)

    context['user'] = request.user                         # base_api profile属性
    context['settings'] = settings                         # 返回settings配置属性
    context["token"] = request.COOKIES.get("tbkt_token")   # 用户token
    context["now"] = datetime.datetime.today()             # 服务器时间
    context["time_stamp"] = int(time.time())               # 服务器时间戳
    path = request.get_full_path()
    context['path'] = path
    s = t.render(context, request)
    return s


def render_template(request, template_path, context={}):
    s = render_template_data(request, template_path, context)
    return HttpResponse(s)


def list_to_str(data_list):
    """
    功能:将列表元素转换成字符串返回
    """
    ret_str = ""
    for obj in data_list:
        if ret_str:
            ret_str += ",%s" % obj
        else:
            ret_str = "%s" % obj
    return ret_str


def safe(path):
    """
    功能说明：       安全修饰器, path: 模板路径
    如果页面报错, 至少给用户返回一个无数据的模板页面
    ----------------------------------------------------------------------------
    修改人                修改时间                修改原因
    ----------------------------------------------------------------------------
    王晨光                2016.5.27
    """
    def _safe(f):
        def wrap(request, *args, **kw):
            try:
                o = f(request, *args, **kw)
                if o is None:
                    o = {}
                if isinstance(o, dict):
                    return render_template(request, path, o)
                else:
                    return o
            except:
                exc = traceback.format_exc()
                log.error(exc)
                if settings.DEBUG:
                    print(exc)
                r = render_template(request, path, {})
                r.status_code = 500
                return r
        return wrap
    return _safe


def upload_static_sever(file, type):
    """
    功能: 上传文件并返回服务器文件保存的路径
    --------------------
    编辑: 王建彬
    --------------------
    日期: 2018-08-06
    --------------------
    """
    # 拼装上传服务器地址
    upload_domain = settings.FILE_UPLOAD_URLROOT
    if type == 1:
        upload_folder = 'portrait'
    if type == 2:
        upload_folder = 'message'
    key = upload_key()
    upload_url = f'{upload_domain}/swf_upload/?upcheck={key}&upType={upload_folder}'
    # 上传文件
    http = urllib3.PoolManager()
    r = http.request(
        'POST',
        upload_url,
        body=file,
        headers={'Content-Type': 'image/jpeg'},
    )
    # 解析响应
    raw = r.data.decode('utf-8')
    raw = re.sub('\'', '\"', raw)
    body = json.loads(raw)
    path = body[0].get('file_url', '')
    return path


def upload_key():
    """
    功能: 上传资源密匙
    --------------------
    编辑: 王建彬
    --------------------
    日期: 2018-08-04
    --------------------
    """
    now = datetime.datetime.now()
    date_now = now.strftime("%Y%m%d")
    sever_key = settings.FILE_UPLOAD_KEY
    m = hashlib.md5()
    m.update(f'{sever_key}{date_now}'.encode('utf-8'))
    key = m.hexdigest()
    return key


class SimpleRender(TemplateView):
    def get(self, request, *args, **kwargs):
        kwargs["settings"] = settings
        kwargs['path'] = request.get_full_path()
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)


def rename(filename, prefix=''):
    """
    功能:返回以日期命名的文件名
    -----------------------------
    添加人:宋国洋
    -----------------------------
    添加时间:2017-12-06
    """
    x = filename.rindex('.') + 1
    y = len(filename)
    ext_name = filename[x:y]
    now_time = datetime.datetime.now()
    ret_val = '%s'% (now_time.strftime("%Y/%m/%d/"))+'%s.%s' % (now_time.strftime("%Y%m%d%H%M%S") + str(now_time.microsecond), ext_name)
    if prefix:
        ret_val = prefix + ret_val
    return ret_val


def getfilename(filename, subdir=''):
    """
    返回路径字符串
    """
    if subdir:
        return os.path.join(settings.MEDIA_ROOT, subdir, filename)
    else:
        return os.path.join(settings.MEDIA_ROOT, filename)


def upload_sever1(file, type):
    """
    功能: 上传文件并返回服务器文件保存的路径
    --------------------
    编辑: 王建彬
    --------------------
    日期: 2018-08-06
    --------------------
    """
    sever_domain = settings.FILE_UPLOAD_URLROOT
    # url = "https://upload.m.xueceping.cn/swf_upload/?upcheck=" + upload_key() + "&upType=score"
    url = sever_domain+"/swf_upload/?upcheck=" + upload_key() + "&upType=score"
    if type == 1:
        files = {"field1": file}
    if type == 2:
        files = {"field1": open(file, 'rb')}
    response = requests.post(url, files=files)
    raw = response.content.decode('utf-8')
    raw = re.sub('\'', '\"', raw)
    body = json.loads(raw)
    path = body[0].get('file_url', '')

    file_url = f'{sever_domain}/upload_media/{path}'
    return file_url


def upload_service(new_url):
    """文件上传服务器"""
    sever_domain = settings.FILE_UPLOAD_URLROOT
    url = sever_domain + "/swf_upload/?upcheck=" + upload_key() + "&upType=score"
    # url = "https://upload.m.xueceping.cn/swf_upload/?upcheck=" + upload_key() + "&upType=score"
    files = {"field1": open(new_url, 'rb')}
    response = requests.post(url, files=files)
    raw = response.content.decode('utf-8')
    raw = re.sub('\'', '\"', raw)
    body = json.loads(raw)
    path = body[0].get('file_url', '')
    sever_domain = settings.FILE_UPLOAD_URLROOT
    file_url = f'{sever_domain}/upload_media/{path}'
    return file_url

