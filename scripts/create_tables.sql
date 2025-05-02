-- auto-generated definition
create table t_gec_file_ocr_record
(
    id              bigint unsigned auto_increment comment 'ID'
        primary key,
    status          tinyint                            not null comment '状态: 0:未处理 1:处理成功 2:处理失败',
    business_id     varchar(32)                        not null comment '业务id, (电站编号/项目公司id)',
    object_id       varchar(100)                       not null comment '文件存储ID',
    name            varchar(100)                       null comment '文件名字',
    content         text                               null comment '文件扫描内容',
    ai_task_id      varchar(200)                       null comment 'AI任务ID',
    ai_status       tinyint                            null comment 'AI状态 0:未处理 1:处理成功 -1:处理失败',
    ai_content      text                               null comment 'AI文件扫描内容',
    url             varchar(350)                       null comment '文件url',
    job_id          varchar(200)                       null comment '任务id',
    batch_no        varchar(50)                        null comment '批次号',
    ocr_type        int                                null comment 'ocr类型',
    doc_type        varchar(50)                        null comment '合同类型',
    version         int      default 1                 not null comment '版本号',
    record_capacity decimal(10, 3)                     null comment '备案容量',
    remark          varchar(1000)                      null comment '备注',
    is_delete       tinyint  default 0                 not null comment '是否删除,0:有效,1:删除',
    creator_id      bigint   default 0                 not null comment '创建人ID',
    creator         varchar(50)                        not null comment '创建人',
    create_time     datetime default CURRENT_TIMESTAMP not null comment '创建时间',
    create_by       bigint   default 0                 not null comment '更新人ID',
    update_by       varchar(50)                        not null comment '更新人',
    update_time     datetime default CURRENT_TIMESTAMP not null comment '更新时间'
)
    comment '文件ocr扫描记录表' row_format = DYNAMIC;



