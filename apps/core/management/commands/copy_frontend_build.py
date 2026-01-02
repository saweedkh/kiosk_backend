"""
Management command برای کپی کردن فایل‌های build فرانت به staticfiles/frontend
"""
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'کپی کردن فایل‌های build فرانت به staticfiles/frontend'

    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            help='مسیر build فرانت (مثلاً ../frontend/out یا ../frontend/.next)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='حذف پوشه مقصد قبل از کپی (اگر وجود داشته باشد)',
        )

    def handle(self, *args, **options):
        # تعیین مسیر source
        if options['source']:
            source_path = Path(options['source']).resolve()
            if not source_path.is_absolute():
                source_path = Path(settings.BASE_DIR).parent / options['source']
        else:
            # استفاده از FRONTEND_BUILD_PATH از settings
            source_path = getattr(settings, 'FRONTEND_BUILD_PATH', None)
            if not source_path:
                # پیش‌فرض: پوشه frontend در همان سطح پروژه
                source_path = Path(settings.BASE_DIR).parent / 'frontend' / 'out'
                if not source_path.exists():
                    source_path = Path(settings.BASE_DIR).parent / 'frontend' / '.next'

        # تعیین مسیر destination
        dest_path = Path(settings.BASE_DIR) / 'staticfiles' / 'frontend'

        # بررسی وجود source
        if not source_path.exists():
            self.stdout.write(
                self.style.ERROR(
                    f'❌ پوشه build فرانت پیدا نشد: {source_path}\n'
                    f'لطفاً مسیر build فرانت را با --source مشخص کنید.'
                )
            )
            return

        # نمایش اطلاعات
        self.stdout.write(
            self.style.SUCCESS(f'📦 Source: {source_path}')
        )
        self.stdout.write(
            self.style.SUCCESS(f'📁 Destination: {dest_path}')
        )

        # حذف destination اگر force=True
        if options['force'] and dest_path.exists():
            self.stdout.write(
                self.style.WARNING(f'🗑️  حذف پوشه قبلی: {dest_path}')
            )
            shutil.rmtree(dest_path)

        # ایجاد پوشه destination
        dest_path.mkdir(parents=True, exist_ok=True)

        # کپی فایل‌ها
        try:
            self.stdout.write('🔄 در حال کپی کردن فایل‌ها...')
            
            # کپی کردن تمام محتویات
            if source_path.is_dir():
                # اگر source یک پوشه است، محتویات آن را کپی کن
                for item in source_path.iterdir():
                    dest_item = dest_path / item.name
                    if item.is_dir():
                        shutil.copytree(item, dest_item, dirs_exist_ok=True)
                        self.stdout.write(f'  ✓ {item.name}/')
                    else:
                        shutil.copy2(item, dest_item)
                        self.stdout.write(f'  ✓ {item.name}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ مسیر source باید یک پوشه باشد: {source_path}')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ فایل‌های build فرانت با موفقیت کپی شدند!\n'
                    f'📂 مسیر: {dest_path}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا در کپی کردن فایل‌ها: {str(e)}')
            )
            raise

