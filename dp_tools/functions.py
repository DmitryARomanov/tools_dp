import pandas as pd


def create_and_insert_df(
    client, df: pd.DataFrame, table_name: str, order_by_cols: list | None = None
):
    """
    Подготавливает и вставляет DataFrame в таблицу базы данных.
    Если таблица существует, происходит очистка таблицы и вставка данных.
    Если таблица не существует, то исходя из типов данных в DataFrame создается таблица.

    Параметры
    ---------
    client : объект клиента БД
        Клиент для подключения к базе данных.
    df : pd.DataFrame
        DataFrame с данными для вставки.
    table_name : str
        Имя целевой таблицы. Можно с схемой: SCHEMA.tbl_name.
    order_by_cols : list | None
        Список колонок для ORDER BY в ClickHouse. Если не передан, используется пустой кортеж.

    Возвращает
    ----------
    bool
        True, если вставка прошла успешно, иначе False.
    """
    if order_by_cols is None:
        order_by_cols = ["tuple()"]

    # 1. Проверяем, существует ли таблица в базе данных
    check_query = f"EXISTS TABLE {table_name}"
    result = client.command(check_query)
    table_exists = result and result[0] == 1

    if table_exists:
        print("🧹 Выполняем очистку таблицы...")
        client.command(f"TRUNCATE TABLE {table_name}")
        print("✅ Таблица очищена.")
    else:
        print(f"❌ Таблица '{table_name}' отсутствует. Генерируем DDL… 📜🗜️")
        columns_ddl = []
        for col_name, dtype in df.dtypes.items():
            ch_type = "String"
            if pd.api.types.is_integer_dtype(dtype):
                non_null = df[col_name].dropna()
                if non_null.empty:
                    base_type = "UInt64"
                else:
                    min_val = non_null.min()
                    base_type = "UInt64" if min_val >= 0 else "Int64"
                ch_type = base_type
            elif pd.api.types.is_float_dtype(dtype):
                ch_type = "Float64"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                s = df[col_name]
                if (s.dt.microsecond > 0).any():
                    ch_type = "DateTime64(3)"
                else:
                    ch_type = "DateTime"

            elif pd.api.types.is_object_dtype(dtype) or dtype == "string":
                non_empty = df[col_name].dropna()
                if not non_empty.empty:
                    first_val = non_empty.iloc[0]
                    if isinstance(first_val, pd.Timestamp):
                        if (
                            first_val.hour == 0
                            and first_val.minute == 0
                            and first_val.second == 0
                        ):
                            ch_type = "Date"
                        else:
                            ch_type = "DateTime"
                    elif hasattr(first_val, "year") and not hasattr(first_val, "hour"):
                        ch_type = "Date"
                    else:
                        ch_type = "String"
                else:
                    ch_type = "String"
            else:
                ch_type = "String"

            has_nulls = df[col_name].isna().any()
            make_nullable = has_nulls or (col_name not in order_by_cols)

            if make_nullable and ch_type not in ("Date", "DateTime", "DateTime64(3)"):
                ch_type = f"Nullable({ch_type})"
            elif (
                has_nulls
                and col_name not in order_by_cols
                and ch_type in ("Date", "DateTime", "DateTime64(3)")
            ):
                ch_type = f"Nullable({ch_type})"

            columns_ddl.append(f"    `{col_name}` {ch_type}")

        if order_by_cols:
            order_by_str = ", ".join(f"`{c}`" for c in order_by_cols if c in df.columns)
            order_by_clause = f"ORDER BY ({order_by_str})"

        sql_script = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
        {",\n".join(columns_ddl)}
        )
        ENGINE = MergeTree()
        {order_by_clause};
        """
        client.command(sql_script)
        print(f"✅ Таблица '{table_name}' успешно создана! 🏗️\n")

    try:
        client.insert_df(table_name, df)
        print(f"🎉 Данные успешно записаны в '{table_name}'! Готово. 👍\n")
        return True
    except Exception as e:
        print(f"❌ Ошибка при вставке данных: {e}\n")
        return False
