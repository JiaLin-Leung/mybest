# coding: utf-8
import time
import logging
import traceback
import simplejson as json
from django.conf import settings
from django.http.request import QueryDict
from django.http import HttpRequest, HttpResponse, Http404, HttpResponseRedirect
from libs.utils import auth_token, casts, loads
from com import com_user
from libs.utils.auth_token import login_response
from libs.utils.validate import argument
log = logging.getLogger(__name__)

# 给request.GET, request.POST, request.QUERY注入新方法
QueryDict.casts = casts
QueryDict.argument = argument
HttpRequest.loads = loads

write_list = ["/apidoc/", "site_media", "login", "pro_service",
              "about", "contact", "privacy", "company_news", "company_news/detail", "logout"]


class Redirect(Exception):
    """
    - 用异常来实现随时重定向, 需要结合中间件process_exception. 用法:
    >>> raise Redirect('/login')
    """

    def __init__(self, url):
        Exception.__init__(self, 'Redirect to: %s' % url)
        self.url = url


def get_user_id(self):
    """
    从cookie中获取user_id, 失败返回None
    """
    token = get_token(self)
    r = auth_token.decode_token(token)
    account_id = r['account_id'] if r else None
    user_id = r['user_id'] if r else None
    self._expire = expire = r['expire'] if r else None
    # 如果token过期时间到一半就续签
    if expire and time.time() >= expire - settings.SESSION_COOKIE_AGE / 2:
        self._newtoken = auth_token.create_token(account_id, user_id)
    return user_id


def get_user_info(self):
    """
    远程调用获取user, 失败返回None
    """
    if not hasattr(self, '_user'):
        user_id = get_user_id(self)
        self._user = com_user.get_user(self) if user_id else None
    return self._user


def get_token(request):
    token = request.GET.get("tbkt_token") \
        or request.META.get('HTTP_TBKT_TOKEN') \
        or request.COOKIES.get('tbkt_token')
    return token


# 添加user_id属性,保存角色ID信息
HttpRequest.user_id = property(get_user_id)
# 添加User属性,保存用户信息
HttpRequest.user = property(get_user_info)


class AuthenticationMiddleware():
    def process_request(self, request):
        return self._process_request(request)

    @staticmethod
    def _process_request(request):

        try:
            # REQUEST过期, 使用QUERY代替
            query = request.GET.copy()
            query.update(request.POST)

            try:
                if request.body and not isinstance(request.body, bytes):
                    body = json.loads(request.body)
                    query.update(body)
            except Exception as e:
                log.error(e)

            # 把body参数合并到QUERY
            request.QUERY = query

            path = str(request.path)
            for i in write_list:
                # 允许白名单访问
                if i in path:
                    return

            if not request.user_id:
                return HttpResponseRedirect('/login')
            user = request.user
            units = user.units

            if not units and "class" not in path:
                # 如果没有班级 重定向至加入班级
                return HttpResponseRedirect('/class/join/')
            if user.user_type == 1:
                # 学生身份跳转学生端
                r = HttpResponseRedirect(settings.STU_WEB_URL)
                r.delete_cookie("tbkt_token")
                return r
            return
        except:
            pass

    @staticmethod
    def cross_domain(request, response=None):
        """
        添加跨域头
        """
        if request.method == 'OPTIONS' and not response:
            response = HttpResponse()
        if not response:
            return
        return response

    def process_response(self, request, response):
        try:
            cookies_token = request.COOKIES.get("tbkt_token")
            args_token = get_token(request)
            if not cookies_token and args_token:
                login_response(response, args_token)

            # 更新token
            if getattr(request, '_newtoken', None):
                login_response(response, request._newtoken)
                auth_token.login_response(response, request._newtoken)
            token = request.GET.get("tbkt_token")
            if token and token != request.COOKIES.get('tbkt_token'):
                auth_token.login_response(response, token)
            # 添加跨域头
            self.cross_domain(request, response)
            return response
        except Exception as e:
            log.error(e)

    @staticmethod
    def process_exception(request, exception):
        """
        功能说明:view函数抛出异常处理
        -------------------------------
        修改人     修改时间
        --------------------------------
        徐威      2013-07-17
        """
        if isinstance(exception, Http404):
            return

        exc = traceback.format_exc()
        log.error(exc)
        if request.is_ajax():
            return HttpResponse("error", status=500)
        if request.method == "POST":
            return HttpResponse("error", status=500)
        return HttpResponse("系统错误,请联系客服!", status=500)
