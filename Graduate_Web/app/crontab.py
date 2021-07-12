import datetime
from .models import *


# 매일 00:00 마다 실행됨
# visitor_count 테이블에 해당 날짜 row을 생성
def insert_today():
    print('hello world')

    new_tt = TestTable()
    new_tt.text = 'test'
    new_tt.save()

    '''
    new_vc = VisitorCount()
    new_vc.visit_date = datetime.datetime.now().strftime('%Y-%m-%d')
    new_vc.visit_count = 1
    new_vc.save()
    '''