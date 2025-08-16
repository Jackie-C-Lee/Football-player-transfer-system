import sqlite3
import os
from contextlib import contextmanager


class DatabaseConfig:
    DB_PATH = 'football_transfer_enhanced.db'

    @staticmethod
    def get_connection():
        """获取数据库连接"""
        try:
            conn = sqlite3.connect(DatabaseConfig.DB_PATH)
            conn.row_factory = sqlite3.Row  # 使结果可以像字典一样访问
            return conn
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            return None

    @staticmethod
    @contextmanager
    def get_db_cursor():
        """上下文管理器，自动处理连接的打开和关闭"""
        conn = DatabaseConfig.get_connection()
        if conn:
            try:
                cursor = conn.cursor()
                yield cursor, conn
                conn.commit()
            except sqlite3.Error as e:
                conn.rollback()
                print(f"数据库操作错误: {e}")
                raise
            finally:
                conn.close()
        else:
            raise Exception("无法连接到数据库")

    @staticmethod
    def execute_query(query, params=None):
        """执行查询并返回结果"""
        try:
            with DatabaseConfig.get_db_cursor() as (cursor, conn):
                cursor.execute(query, params or ())

                if query.strip().upper().startswith('SELECT'):
                    # 对于查询操作，返回结果
                    rows = cursor.fetchall()
                    return [dict(row) for row in rows]  # 转换为字典列表
                else:
                    # 对于插入/更新/删除操作，返回影响的行数
                    return cursor.rowcount
        except Exception as e:
            print(f"查询执行错误: {e}")
            return None

    @staticmethod
    def execute_many(query, params_list):
        """批量执行操作"""
        try:
            with DatabaseConfig.get_db_cursor() as (cursor, conn):
                cursor.executemany(query, params_list)
                return cursor.rowcount
        except Exception as e:
            print(f"批量操作错误: {e}")
            return None