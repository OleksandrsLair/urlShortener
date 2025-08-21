# Generated manually for initial migration
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Link",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.CharField(db_index=True, max_length=32, unique=True)),
                ("target_url", models.URLField()),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("expires_at", models.DateTimeField(blank=True, null=True, db_index=True)),
                ("hit_count", models.PositiveIntegerField(default=0)),
            ],
            options={},
        ),
        migrations.AddIndex(
            model_name="link",
            index=models.Index(fields=["code"], name="shortener_code_idx"),
        ),
        migrations.AddIndex(
            model_name="link",
            index=models.Index(fields=["expires_at"], name="shortener_expires_idx"),
        ),
    ]
