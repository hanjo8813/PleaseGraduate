from django.db import models

# objects = models.Manager() -> vscode 오류때문에 추가해줌.

# DB 테이블의 구조를 보여주고, 수정가능
class TestTable(models.Model):
    num = models.AutoField(primary_key=True)
    text = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'test_table'

# 테이블 userinfo
class Userinfo(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    pw = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'userinfo'

# --------------------------------------------------

# case별 이수학점 기준표
class Graduatescore(models.Model):
    ind = models.AutoField(primary_key=True)
    major = models.CharField(max_length=50)
    startyear = models.IntegerField()
    sum = models.IntegerField()
    major_essential = models.IntegerField()
    major_selection = models.IntegerField()
    core_essential = models.IntegerField()
    core_selection = models.IntegerField()
    liberal = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'graduatescore'


class Dicon16CoreEssential(models.Model):
    subject_num = models.IntegerField(primary_key=True)
    subjec_name = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()
    kind = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'dicon_16_core_essential'


class Dicon16CoreSelection(models.Model):
    subject_num = models.IntegerField(primary_key=True)
    isessential = models.IntegerField()
    subjec_name = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()
    kind = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'dicon_16_core_selection'


class Dicon16Liberal(models.Model):
    subject_num = models.IntegerField(primary_key=True)
    subjec_name = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()
    kind = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'dicon_16_liberal'


