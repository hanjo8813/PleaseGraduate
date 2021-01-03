from django.db import models

# DB 테이블의 구조를 파이썬 클래스로 보여주고, 수정가능

class TestTable(models.Model):
    num = models.IntegerField(primary_key=True)
    text = models.CharField(max_length=45)

    class Meta:
        managed = False
        db_table = 'test_table'


class AllLecture(models.Model):
    subject_num = models.IntegerField(primary_key=True)
    subject_name = models.CharField(max_length=70)
    classification = models.CharField(max_length=45)
    selection = models.CharField(max_length=45, blank=True, null=True)
    grade = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'all_lecture'

class NewLecture(models.Model):
    subject_num = models.OneToOneField(AllLecture, models.DO_NOTHING, db_column='subject_num', primary_key=True)

    class Meta:
        managed = False
        db_table = 'new_lecture'


class Basic(models.Model):
    ind = models.OneToOneField('IndCombi', models.DO_NOTHING, db_column='ind', primary_key=True)
    subject_num_list = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'basic'


class CoreEssential(models.Model):
    ind = models.OneToOneField('IndCombi', models.DO_NOTHING, db_column='ind', primary_key=True)
    subject_num_list = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'core_essential'


class CoreSelection(models.Model):
    ind = models.OneToOneField('IndCombi', models.DO_NOTHING, db_column='ind', primary_key=True)
    subject_num_list = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'core_selection'


class GraduateScore(models.Model):
    ind = models.OneToOneField('IndCombi', models.DO_NOTHING, db_column='ind', primary_key=True)
    sum_score = models.IntegerField()
    major_essential = models.IntegerField()
    major_selection = models.IntegerField()
    core_essential = models.IntegerField()
    core_selection = models.IntegerField()
    basic = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'graduate_score'


class IndCombi(models.Model):
    ind = models.AutoField(primary_key=True)
    major = models.CharField(max_length=45)
    year = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'ind_combi'


class SubjectGroup(models.Model):
    subject_num = models.OneToOneField(AllLecture, models.DO_NOTHING, db_column='subject_num', primary_key=True)
    group_num = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'subject_group'


