from django.db import models


class Instrument(models.Model):
    symbol = models.CharField(max_length=100, unique=True)
    volume = models.FloatField(default=0)
    cprsystem = models.JSONField(default=dict)