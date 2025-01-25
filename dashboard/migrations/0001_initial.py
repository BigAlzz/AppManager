# Generated by Django 5.1.5 on 2025-01-25 15:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="App",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                ("path", models.CharField(max_length=255)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("executable", "Executable"),
                            ("script", "Script"),
                            ("web", "Web Tool"),
                        ],
                        max_length=20,
                    ),
                ),
                ("status", models.CharField(default="Stopped", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="AppLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("action", models.CharField(max_length=50)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                ("details", models.TextField()),
                (
                    "app",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs",
                        to="dashboard.app",
                    ),
                ),
            ],
        ),
    ]
