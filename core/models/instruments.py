from django.db import models


class InstrumentType(models.Model):
    type = models.CharField(max_length=100)


class Instrument(models.Model):
    symbol = models.CharField(max_length=100)
    volume = models.FloatField(default=0)
    cprsystem = models.JSONField(default=dict)
    type = models.ForeignKey(InstrumentType, on_delete=models.CASCADE)