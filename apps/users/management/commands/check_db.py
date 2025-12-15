from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = '检查数据库连接'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]
                self.stdout.write(
                    self.style.SUCCESS(f'✓ 数据库连接成功！')
                )
                self.stdout.write(f'PostgreSQL版本: {version}')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ 数据库连接失败: {str(e)}')
            )
