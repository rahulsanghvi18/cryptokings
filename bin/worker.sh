#!/bin/bash
celery -A cryptokings.celery_app.app worker -l INFO