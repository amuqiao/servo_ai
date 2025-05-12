CREATE DATABASE IF NOT EXISTS iot_platform 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;


-- - DEFAULT CHARACTER SET utf8mb4

-- - 指定数据库默认使用utf8mb4字符集
-- - 支持完整的Unicode字符（包括emoji表情符号）
-- - 每个字符最多占用4字节（原utf8仅支持3字节）

-- - DEFAULT COLLATE utf8mb4_unicode_ci
-- - 定义字符串比较和排序的规则
-- - unicode_ci 支持多语言不区分大小写比较
-- - 相比 utf8mb4_general_ci 排序更准确