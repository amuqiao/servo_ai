"""
MySQL数据库初始化脚本
功能：自动创建表结构并插入测试数据
用法：python3 db_init.py （需先启动MySQL服务）
"""

import os
import pymysql
import logging
from typing import List
from pymysql import Error as MySQLError
from pymysql.connections import Connection

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

class DBConfig:
    """从环境变量加载数据库配置"""
    def __init__(self):
        self.host = os.getenv('DB_HOST', '127.0.0.1')
        self.port = int(os.getenv('DB_PORT', 3306))
        self.user = os.getenv('DB_ROOT_USER', 'root')
        self.password = os.getenv('DB_ROOT_PASSWORD', '123456')
        self.database = 'iot_platform'  # 指定目标数据库

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
            logging.info("数据库连接成功")
            return conn
        except MySQLError as e:
            attempt += 1
            logging.error(f"连接失败，第{attempt}次重试... 错误: {e}")
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
                        logging.debug(f"执行成功: {command[:50]}...")
                    except MySQLError as e:
                        logging.error(f"执行失败: {command[:50]}...\n错误: {e}")
                        conn.rollback()
                        raise
            conn.commit()
            logging.info(f"文件 {os.path.basename(file_path)} 执行完成")
    except Exception as e:
        conn.rollback()
        logging.error(f"事务回滚，错误: {e}")
        raise

def main():
    config = DBConfig()
    sql_files = [
        '/Users/wangqiao/NutstoreFiles/code/ai/servo_ai_project/servo_ai/scripts/create_tables.sql',  # 建表文件
        '/Users/wangqiao/NutstoreFiles/code/ai/servo_ai_project/servo_ai/scripts/insert_data.sql'   # 数据文件
    ]
    
    try:
        conn = create_connection(config)
        with conn:
            for sql_file in sql_files:
                if not os.path.exists(sql_file):
                    raise FileNotFoundError(f"SQL文件不存在: {sql_file}")
                execute_sql_file(conn, sql_file)
    except Exception as e:
        logging.error(f"执行失败: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()