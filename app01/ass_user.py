from app01 import models
import redis
conn = redis.Redis(host='192.168.20.17',port=6379,)


class Ass:
    @classmethod
    def fetch_users(cls):
        sale_id_list = []
        sales1 = models.Balance.objects.all().order_by('-weight')
        sales2 = models.Balance.objects.all().order_by('-num').first()
        for i in range(sales2.num):
            for obj in sales1:
                if obj.num > i:
                    sale_id_list.append(obj.user_id)
        print(sale_id_list)
        if sale_id_list:
            conn.rpush('sale_id_list',*sale_id_list)
            conn.rpush('sale_id_list_origin',*sale_id_list)   #数据备份
            return True
        return False

    @classmethod
    def get_sale_id(cls):
        #查看是否有原数据
        is_len = conn.llen('sale_id_list_origin')
        if not is_len:
            bol = cls.fetch_users()
            if not bol:
                return None
        else:
            sale_id = conn.lpop('sale_id_list')
            if sale_id:
                return sale_id
            else:
                reset = conn.get('reset_status')
                if reset:
                    conn.delete('sale_id_list')
                    conn.delete('sale_id_list_origin')
                    status = cls.fetch_users()
                    if not status:
                        return None
                    conn.delete('reset_status')
                for i in range(is_len):
                    sale_id_origin = conn.lindex('sale_id_list_origin',i)
                    conn.rpush('sale_id_list',sale_id_origin)
        cls.get_sale_id()



    @classmethod
    def reset(cls):
        conn.set('reset_status','1')

    @classmethod
    def rollback(cls,nid):
        conn.lpush('sale_id_list',nid)

