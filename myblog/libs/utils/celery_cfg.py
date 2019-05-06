# @File  : celery_cfg.py
# @Author: 王世成
# @Date  : 2018/12/12
# @Desc  :
from celery import Celery
from kombu import Exchange
from django.conf import settings


class SyncQueue(object):
    def __init__(self, remote_folder='tasks', prefix='tbkt.sync'):
        """
        :param remote_folder: celery项目要执行函数所在文件夹
        :param prefix: celery项目处理异步任务的模块目录
        """
        self.prefix = prefix
        self.remote_folder = remote_folder

    def _callable(self, item):
        remote_dir = f"{self.prefix}.{self.remote_folder}.{item}"
        return Invoking(remote_dir)

    def __getitem__(self, item):
        return self._callable(item)

    def __getattr__(self, item):
        return self._callable(item)


class Invoking(object):
    """发送异步任务请求
    暂时实现比较简单
    没有研究过业务如何扩展
    """
    def __init__(self, func_path):
        self.func_path = func_path

    @staticmethod
    def instance():
        app = Celery()
        app.conf.update(
            task_serializer='json',  # 任务序列化和反序列化 json
            result_serializer='json',  # 结果序列化
            timezone='Asia/Shanghai',  # 指定时区，不指定默认为 'UTC'
            broker_url='amqp://{}:{}@{}:{}'.format(*settings.RABBIT_MQ.values())  # broker地址
        )
        return app

    @staticmethod
    def sync_exchange():
        return Exchange('stage_sync')

    def send(self, routing_key='tbkt.stage_sync.call', eta=None, args=None, kwargs=None):
        """发送异步任务
        routing_key = '路由key 保证符合worker启动队列匹配规则一致'
        eta = '多长时间后执行 暂时没有去验证 接受的整形秒数吧'
        args = 参数列表
        kwargs = 参数字典
        """
        print('amqp://{}:{}@{}:{}'.format(*settings.RABBIT_MQ.values()))
        print(self.func_path)
        print(routing_key)
        print(routing_key)
        self.instance().send_task(
                      self.func_path,
                      exchange=self.sync_exchange(),
                      routing_key=routing_key,
                      args=args,
                      kwargs=kwargs,
                      eta=eta)


if __name__ == "__main__":
    # sync = SyncQueue().test.send(kwargs={"message_id": ar, "url": "11111"})
    sync = SyncQueue().web_send_score.send(kwargs={"message_id": 1, "user": 1, "unit_id": 1})
