# Generated by Django 5.1.2 on 2024-11-06 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education', '0002_content_contentcompletion_content_completed_by_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Path',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('difficulty', models.CharField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], max_length=30)),
                ('type', models.CharField(max_length=30)),
                ('lessons', models.PositiveIntegerField()),
                ('duration', models.CharField(max_length=50)),
                ('points', models.PositiveIntegerField()),
                ('image', models.ImageField(blank=True, null=True, upload_to='static/paths')),
            ],
        ),
    ]