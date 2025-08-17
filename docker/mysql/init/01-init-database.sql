-- MySQL 8.0 初始化脚本
-- 设置时区为东八区
SET time_zone = '+08:00';

-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS `n8n_mobile_cards` 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE `n8n_mobile_cards`;



-- 刷新权限
FLUSH PRIVILEGES;

-- 创建手机卡最新数据表
CREATE TABLE IF NOT EXISTS `mobile_cards_latest` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据源',
  `card_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '卡片ID',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称',
  `yys` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '运营商',
  `monthly_rent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '月租费用',
  `general_flow` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通用流量',
  `call_times` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通话时长',
  `age_range` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '年龄范围',
  `ka_origin` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '卡片归属',
  `disable_area` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '禁发区域',
  `rebate_money` decimal(10,2) DEFAULT NULL COMMENT '返佣金额',
  `top_detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '详细描述',
  `point` int DEFAULT NULL COMMENT '分数',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '额外参数',
  `data_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_created_at` (`created_at`) USING BTREE,
  KEY `idx_source_card_id` (`source`,`card_id`,`data_time`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手机卡最新数据表';

-- 创建手机卡历史数据表
CREATE TABLE IF NOT EXISTS `mobile_cards_history` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `source` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数据源',
  `latest_id` int NOT NULL COMMENT '最新表ID',
  `card_id` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '卡片ID',
  `product_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称',
  `yys` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '运营商',
  `monthly_rent` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '月租费用',
  `general_flow` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通用流量',
  `call_times` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '通话时长',
  `age_range` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '年龄范围',
  `ka_origin` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '卡片归属',
  `disable_area` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '禁发区域',
  `rebate_money` decimal(10,2) DEFAULT NULL COMMENT '返佣金额',
  `top_detail` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '详细描述',
  `point` int DEFAULT NULL COMMENT '分数',
  `params` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT '额外参数',
  `data_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`) USING BTREE,
  KEY `idx_created_at` (`created_at`) USING BTREE,
  KEY `idx_source_card_id` (`source`,`card_id`,`data_time`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='手机卡历史数据表';

-- 显示创建的数据库
SHOW DATABASES;

-- 显示创建的表
SHOW TABLES;

-- 显示当前时区设置
SELECT @@global.time_zone, @@session.time_zone;

-- 显示表创建成功信息
SELECT 'Tables created successfully!' as status;
