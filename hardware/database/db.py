from peewee import *
from playhouse.sqlite_ext import JSONField
import os


path = os.path.dirname(os.path.abspath(__file__))
dbpath = os.path.join(path, '/home/toby/database.sqlite')

db = SqliteDatabase(dbpath)

class Home(Model):
    class Meta:
        database = db
        table_name = 'homes'
    id = AutoField()
    name = CharField()
    council = CharField()
    council_data = JSONField()
    active = BooleanField()
    timeout = IntegerField()

    @classmethod
    def get_active(cls):
        return cls.get_or_none(cls.active == True)


class Bin(Model):
    class Meta:
        database = db
        table_name = 'bins'

    id = AutoField()
    council_name = CharField()
    name = CharField()
    position = IntegerField()
    home_id = ForeignKeyField(Home, backref='bins')

class Schedule(Model):
    class Meta:
        database = db
        table_name = 'schedules'

    id = AutoField()
    start = DateField()
    end = DateField(null=True)
    repeat_weeks = IntegerField()
    home_id = ForeignKeyField(Home, backref='schedules')

class BinSchedule(Model):
    class Meta:
        database = db
        table_name = 'bin_schedules'

    id = AutoField()
    bin_id = ForeignKeyField(Bin, backref='bin_schedules')
    schedule_id = ForeignKeyField(Schedule, backref='bin_schedules')

class BinDay(Model):
    class Meta:
        database = db
        table_name = 'bin_days'

    id = AutoField()
    bin_id = ForeignKeyField(Bin, backref='bin_days')
    date = DateField()
    home_id = ForeignKeyField(Home, backref='bin_days')
    schedule_id = ForeignKeyField(Schedule, backref='bin_days')