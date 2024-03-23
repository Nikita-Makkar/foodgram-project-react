import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("filename", nargs="+", type=str)

    def handle(self, *args, **options):
        for filename in options["filename"]:
            path = os.path.join(settings.BASE_DIR, "data", filename)
            if not os.path.exists(path):
                self.stdout.write(self.style.ERROR(
                    f"Файл '{filename}' не найден."))
                continue
            with open(path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                next(reader)
                handler = self.get_handler(filename)
                if handler:
                    self.process_file(reader, handler)
                else:
                    self.stdout.write(self.style.ERROR(
                        f"Файл '{filename}' не найден."))

    def get_handler(self, filename):
        handlers = {
            "ingredients.csv": self.process_ingredients,
        }
        return handlers.get(filename)

    def process_file(self, reader, handler):
        for row in reader:
            handler(row)

    def process_ingredients(self, row):
        name, measurement_unit = row[:2]
        Ingredient.objects.get_or_create(
            name=name,
            measurement_unit=measurement_unit,
        )
