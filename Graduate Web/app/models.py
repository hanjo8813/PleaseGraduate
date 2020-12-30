from django.db import models

# objects = models.Manager() -> vscode 오류때문에 추가해줌.

# DB 테이블의 구조를 보여주고, 수정가능
class TestTable(models.Model):
    objects = models.Manager()
    num = models.AutoField(primary_key=True)
    text = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'test_table'

# 테이블 userinfo
class Userinfo(models.Model):
    objects = models.Manager()
    # id가 PK라서 노랑색임
    id = models.CharField(primary_key=True, max_length=50)
    pw = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'userinfo'