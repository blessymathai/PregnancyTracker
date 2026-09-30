from django.core.management.base import BaseCommand
from User.models import tbl_Nutrition


class Command(BaseCommand):

    help = "Create automatic nutrition recommendations for pregnancy weeks 1-40"

    def handle(self, *args, **kwargs):

        nutrition_data = [

            # Week 1-4
            {
                "week_start": 1,
                "week_end": 4,
                "foods": [
                    ("Spinach", "Vegetables", 23, 2.9, 2.7, 99, 2.2,
                     "Rich in folate and iron. Include leafy vegetables regularly."),

                    ("Egg", "Protein", 155, 13, 1.2, 50, 0,
                     "Good source of protein and essential nutrients."),

                    ("Orange", "Fruit", 47, 0.9, 0.1, 40, 2.4,
                     "Provides vitamin C and supports iron absorption."),

                    ("Milk", "Dairy", 61, 3.2, 0.0, 120, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 5-8
            {
                "week_start": 5,
                "week_end": 8,
                "foods": [
                    ("Banana", "Fruit", 89, 1.1, 0.3, 5, 2.6,
                     "Provides potassium and energy."),

                    ("Lentils", "Protein", 116, 9.0, 3.3, 19, 7.9,
                     "Good source of protein, iron and fiber."),

                    ("Avocado", "Fruit", 160, 2.0, 0.6, 12, 6.7,
                     "Provides healthy fats and fiber."),

                    ("Curd", "Dairy", 61, 3.5, 0.0, 121, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 9-12
            {
                "week_start": 9,
                "week_end": 12,
                "foods": [
                    ("Broccoli", "Vegetables", 34, 2.8, 0.7, 47, 2.6,
                     "Provides folate, fiber and vitamin C."),

                    ("Chickpeas", "Protein", 164, 8.9, 2.9, 49, 7.6,
                     "Provides plant protein, iron and fiber."),

                    ("Apple", "Fruit", 52, 0.3, 0.1, 6, 2.4,
                     "Provides fiber and useful vitamins."),

                    ("Milk", "Dairy", 61, 3.2, 0.0, 120, 0,
                     "Supports calcium and protein intake.")
                ]
            },

            # Week 13-16
            {
                "week_start": 13,
                "week_end": 16,
                "foods": [
                    ("Sweet Potato", "Vegetables", 86, 1.6, 0.6, 30, 3.0,
                     "Provides energy, fiber and beta-carotene."),

                    ("Egg", "Protein", 155, 13, 1.2, 50, 0,
                     "Good source of high-quality protein."),

                    ("Guava", "Fruit", 68, 2.6, 0.3, 18, 5.4,
                     "Rich in vitamin C and fiber."),

                    ("Almonds", "Nuts", 579, 21, 3.7, 269, 12.5,
                     "Provides protein, healthy fats and calcium.")
                ]
            },

            # Week 17-20
            {
                "week_start": 17,
                "week_end": 20,
                "foods": [
                    ("Spinach", "Vegetables", 23, 2.9, 2.7, 99, 2.2,
                     "Supports iron and folate intake."),

                    ("Salmon", "Protein", 208, 20, 0.5, 9, 0,
                     "Provides protein and healthy fats."),

                    ("Orange", "Fruit", 47, 0.9, 0.1, 40, 2.4,
                     "Provides vitamin C."),

                    ("Yogurt", "Dairy", 59, 10, 0.1, 110, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 21-24
            {
                "week_start": 21,
                "week_end": 24,
                "foods": [
                    ("Broccoli", "Vegetables", 34, 2.8, 0.7, 47, 2.6,
                     "Provides fiber, folate and vitamin C."),

                    ("Beans", "Protein", 127, 8.7, 2.9, 28, 6.4,
                     "Provides protein, iron and fiber."),

                    ("Papaya", "Fruit", 43, 0.5, 0.3, 20, 1.7,
                     "Provides vitamin C and fiber."),

                    ("Milk", "Dairy", 61, 3.2, 0.0, 120, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 25-28
            {
                "week_start": 25,
                "week_end": 28,
                "foods": [
                    ("Carrot", "Vegetables", 41, 0.9, 0.3, 33, 2.8,
                     "Provides beta-carotene and fiber."),

                    ("Chicken", "Protein", 165, 31, 1.3, 15, 0,
                     "Provides high-quality protein."),

                    ("Pear", "Fruit", 57, 0.4, 0.2, 9, 3.1,
                     "Provides fiber and hydration."),

                    ("Almonds", "Nuts", 579, 21, 3.7, 269, 12.5,
                     "Provides healthy fats, protein and calcium.")
                ]
            },

            # Week 29-32
            {
                "week_start": 29,
                "week_end": 32,
                "foods": [
                    ("Oats", "Grains", 389, 16.9, 4.7, 54, 10.6,
                     "Provides fiber and sustained energy."),

                    ("Lentils", "Protein", 116, 9.0, 3.3, 19, 7.9,
                     "Good source of iron, protein and fiber."),

                    ("Banana", "Fruit", 89, 1.1, 0.3, 5, 2.6,
                     "Provides potassium and energy."),

                    ("Yogurt", "Dairy", 59, 10, 0.1, 110, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 33-36
            {
                "week_start": 33,
                "week_end": 36,
                "foods": [
                    ("Spinach", "Vegetables", 23, 2.9, 2.7, 99, 2.2,
                     "Provides iron and folate."),

                    ("Egg", "Protein", 155, 13, 1.2, 50, 0,
                     "Provides high-quality protein."),

                    ("Orange", "Fruit", 47, 0.9, 0.1, 40, 2.4,
                     "Provides vitamin C and fiber."),

                    ("Milk", "Dairy", 61, 3.2, 0.0, 120, 0,
                     "Provides calcium and protein.")
                ]
            },

            # Week 37-40
            {
                "week_start": 37,
                "week_end": 40,
                "foods": [
                    ("Sweet Potato", "Vegetables", 86, 1.6, 0.6, 30, 3.0,
                     "Provides energy, fiber and beta-carotene."),

                    ("Chicken", "Protein", 165, 31, 1.3, 15, 0,
                     "Provides protein needed for maternal nutrition."),

                    ("Banana", "Fruit", 89, 1.1, 0.3, 5, 2.6,
                     "Provides potassium and energy."),

                    ("Yogurt", "Dairy", 59, 10, 0.1, 110, 0,
                     "Provides calcium and protein.")
                ]
            }
        ]

        # Clear old data
        tbl_Nutrition.objects.all().delete()

        count = 0

        for period in nutrition_data:

            for food in period["foods"]:

                tbl_Nutrition.objects.create(
                    week_start=period["week_start"],
                    week_end=period["week_end"],
                    name=food[0],
                    category=food[1],
                    calories=food[2],
                    protein=food[3],
                    iron=food[4],
                    calcium=food[5],
                    fiber=food[6],
                    recommendation=food[7]
                )

                count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{count} nutrition records created successfully."
            )
        )