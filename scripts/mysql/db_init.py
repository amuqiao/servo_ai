"""
MySQL数据库初始化脚本
功能：自动创建表结构并插入测试数据
用法：python3 db_init.py （需先启动MySQL服务）
"""

import os
import pymysql
from typing import List
from pymysql import Error as MySQLError
from pymysql.connections import Connection


class DBConfig:
    """从环境变量加载数据库配置"""
    def __init__(self, config_dict):
        self.host = config_dict.get('host', '127.0.0.1')
        self.port = int(config_dict.get('port', 3306))
        self.user = config_dict.get('user', 'root')
        self.password = config_dict.get('password', 'Luffy2025@')
        self.database = config_dict.get('database', 'iot_platform')

def create_connection(config: DBConfig, retries=3) -> Connection:
    """创建数据库连接（带重试机制）"""
    attempt = 0
    while attempt < retries:
        try:
            conn = pymysql.connect(
                host=config.host,
                port=config.port,
                user=config.user,
                password=config.password,
                database=config.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("数据库连接成功")
            return conn
        except MySQLError as e:
            attempt += 1
            print(f"连接失败，第{attempt}次重试... 错误: {e}")
    raise ConnectionError(f"无法连接到数据库，已重试{retries}次")

def execute_sql_file(conn: Connection, file_path: str):
    """执行SQL文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')
            
        with conn.cursor() as cursor:
            for command in sql_commands:
                command = command.strip()
                if command:
                    try:
                        cursor.execute(command)
                        print(f"执行成功: {command[:50]}...")
                    except MySQLError as e:
                        print(f"执行失败: {command[:50]}...\n错误: {e}")
                        conn.rollback()
                        raise
            conn.commit()
            print(f"文件 {os.path.basename(file_path)} 执行完成")
    except Exception as e:
        conn.rollback()
        print(f"事务回滚，错误: {e}")
        raise

def main():
    config_dict = {
        "host": "127.0.0.1",
        "port": 3306,
        "user": "root",
        "password": "Luffy2025@",
        "database": "iot_platform"
    }
    config = DBConfig(config_dict)
    sql_files = [
        '/Users/wangqiao/NutstoreFiles/code/ai/servo_ai_project/servo_ai/scripts/mysql/create_tables.sql',  # 建表文件
        '/Users/wangqiao/NutstoreFiles/code/ai/servo_ai_project/servo_ai/scripts/mysql/insert_data.sql'   # 数据文件
    ]
    
    try:
        conn = create_connection(config)
        with conn:
            for sql_file in sql_files:
                if not os.path.exists(sql_file):
                    raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
                execute_sql_file(conn, sql_file)
    except Exception as e:
        print(f"执行失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
    
# 预测输出
# (.venv) (base) ➜  mysql git:(main) ✗ python db_init.py
# 数据库连接成功
# 执行成功: -- auto-generated definition
# create table t_gec_fi...
# 文件 create_tables.sql 执行完成
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 执行成功: INSERT INTO iot_platform.t_gec_file_ocr_record (id...
# 文件 insert_data.sql 执行完成