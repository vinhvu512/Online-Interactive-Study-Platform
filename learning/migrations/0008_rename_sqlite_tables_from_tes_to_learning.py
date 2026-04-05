# After the app label moved from `tes` to `learning`, Django expects
# `learning_*` table names. Existing SQLite DBs still had `tes_*` rows.

from django.db import migrations


def rename_sqlite_tables(apps, schema_editor):
    conn = schema_editor.connection
    if conn.vendor != "sqlite":
        return
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='tes_video'"
        )
        if not cursor.fetchone():
            return
    # SQLite updates FK references when renaming parent tables (3.26+).
    with conn.cursor() as cursor:
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute('ALTER TABLE "tes_video" RENAME TO "learning_video"')
        cursor.execute('ALTER TABLE "tes_pdf" RENAME TO "learning_pdf"')
        cursor.execute(
            'ALTER TABLE "tes_generatedcontent" RENAME TO "learning_generatedcontent"'
        )
        cursor.execute("PRAGMA foreign_keys = ON")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("learning", "0007_video_video_url"),
    ]

    operations = [
        migrations.RunPython(rename_sqlite_tables, migrations.RunPython.noop),
    ]
