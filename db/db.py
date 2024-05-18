from peewee import IntegerField, BigIntegerField, TextField, FloatField
from peewee import Model
from peewee import SqliteDatabase

db = SqliteDatabase("./db/db.db")


class Admins(Model):
    user_id = BigIntegerField(primary_key=True)

    class Meta:
        database = db


class Users(Model):
    user_id = BigIntegerField(primary_key=True)
    state = IntegerField(default=0)
    phone = TextField(default='None')
    password = TextField(default='None')
    USDT = FloatField(default=0.0)
    TON = FloatField(default=0.0)
    BTC = FloatField(default=0.0)
    LTC = FloatField(default=0.0)
    ETH = FloatField(default=0.0)
    BNB = FloatField(default=0.0)
    TRX = FloatField(default=0.0)
    USDC = FloatField(default=0.0)

    class Meta:
        database = db


class Sponsors(Model):
    channel_id = BigIntegerField(primary_key=True)
    link = TextField()
    name = TextField(default='Подпишись')

    class Meta:
        database = db


if __name__ == '__main__':
    Users.create_table()
    Sponsors.create_table()
    Admins.create_table()
