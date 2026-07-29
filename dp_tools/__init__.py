"""
Набор функций для загрузки данных в базу DP Non-KA и обработки Excel файлов.

Основные модули:
- functions: содержит функции загрузки в ClickHouse.
- utils: вспомогательные утилиты для работы с данными.

Автор: Dmitry Romanov
"""

from .utils import report_nan, create_df_from_folder,rebuild_loss_data, iqr_flag_series
#from .functions import create_and_insert_df

__all__ = ['create_df_from_folder', 'report_nan', 'rebuild_loss_data','iqr_flag_series']
__version__ = "0.2.8"