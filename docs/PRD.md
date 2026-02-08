# PurrView 产品需求文档

## 项目概述

PurrView 是一个猫咪喂食监控系统，通过现有的 RTMP 摄像头（俯视固定角度）实时监控 5 只猫的进食行为。系统使用 OpenCV 作为低成本运动检测门控，配合 Gemini 多模态 API 进行智能分析（猫咪识别 + 食物量估算），无需自定义 ML 训练。

**域名**: purrview.dev

## 核心功能

### 1. 实时流处理（Stream Worker）
- 通过 ffmpeg 从 RTMP 摄像头提取帧（每 5 秒 1 帧，缩放至 1280x720）
- OpenCV MOG2 背景减除算法检测食盆区域的运动
- 运动检测到后触发 Gemini API 分析
- 冷却机制：触发后 30 秒内不重复调用 API

### 2. AI 分析
- **猫咪识别**：基于预上传的参考照片，通过 few-shot 方式让 Gemini 识别是哪只猫
- **进食/饮水判断**：判断猫是在进食还是喝水（区分 Food vs Water 事件）
- **食物量/水量估算**：估算食盆/水盆中的存量
- **结构化输出**：使用 Pydantic schema 确保 JSON 响应格式一致，包含 `event_type` 字段

### 3. 进食事件追踪
- 状态机：空闲 → 活跃（检测到运动）→ 进食中（AI 确认）→ 空闲（2 分钟无运动）
- 将连续帧组合为单个进食事件
- 记录：首帧、过程中周期帧、末帧

### 4. Web 仪表板 (Modern Bento Box Design)
- **设计风格**：采用现代 "Bento Box" 布局，使用中性背景（Off-white）、大圆角卡片、柔和阴影和高对比度强调色（Emerald Green/Orange）。
- **总览页**：
    - 关键指标卡片：今日进食次数、活跃猫咪数、今日饮水量、最近进食时间。
    - 可视化：每日食物消耗趋势柱状图。
    - 最近活动：以列表形式展示最近的进食和饮水事件（带图标区分）。
- **猫咪管理**：网格视图展示猫咪卡片（状态：Fed/Hungry/Eating），支持添加/编辑。
- **进食时间线**：详细的时间轴列表，区分进食（g）和饮水（ml）事件。
- **统计报表**：每日/每周图表，每只猫的进食趋势。

## 用户场景

### 场景 1：日常监控
Lin 早上打开 PurrView 仪表板，查看昨晚到今早有哪些猫吃了东西，每只猫吃了多少。

### 场景 2：健康异常发现
系统发现猫 A 已经 24 小时没有进食记录，发送提醒通知。

### 场景 3：新猫注册
通过 Web 界面上传新猫的照片和描述，系统自动将其加入 AI 识别的参考库。

## 技术约束

- **成本控制**：Gemini 2.5 Flash 约 $0.0011/图片，预估每天 ~150 次调用 ≈ $0.17/天
- **延迟**：运动检测 < 10ms/帧，Gemini 分析 ~2-3 秒/帧（可接受，不是实时需求）
- **共享数据库**：所有表使用 `purrview_` 前缀，与 project-kalshi 共享 Supabase 项目

## 数据库表

| 表名 | 说明 |
|------|------|
| `purrview_cats` | 猫咪资料（名称、描述、参考照片 URL） |
| `purrview_feeding_events` | 进食/饮水事件（关联猫，记录类型 `event_type` [food/water]、量变化 `amount`、持续时间） |
| `purrview_frames` | 关键帧（关联进食事件，存储 Gemini 原始分析） |
| `purrview_food_bowls` | 食盆 ROI 配置（坐标、名称、激活状态） |

## 开发阶段

### Phase 1：项目基础搭建 ✅
- Monorepo 结构（apps/worker + apps/web）
- Supabase 数据库迁移（4 表 + 索引 + RLS）
- Worker 骨架：capture, detector, analyzer, tracker, storage, config, main
- Web 骨架：Next.js 15 + 页面路由
- 文档：CLAUDE.md, PRD.md, .env.example

### Phase 2：通知 + 数据采集基础 ✅
- Lark 飞书通知：实时喂食卡片 + 每日摘要（notifier.py, digest.py）
- 数据采集脚本（collect.py）：RTMP 抓帧 + 运动检测评分
- EC2 部署脚本（scripts/ec2-collect.sh）
- 修复：capture.py 分辨率适配（2560x1440 → 1280x720）
- 修复：config.py .env 路径解析
- Supabase Storage bucket 创建（purrview-frames）

### Phase 3：数据标注 + Gemini 调优 ⬅️ 当前
- [ ] 在 EC2 上采集 24h 数据（5 秒/帧，~2.6GB/天）
- [ ] 从采集帧中筛选有猫的帧，收集每只猫的参考照片（俯视角度）
- [ ] 人工标注：猫名、是否进食、食物量
- [ ] 标定食盆 ROI 坐标（写入 purrview_food_bowls 表）
- [ ] 用标注数据测试 Gemini prompt，调优识别准确率
- [ ] 校准运动检测阈值（区分噪声 vs 真实运动）

### Phase 4：端到端 Pipeline 打通
- [ ] 接入 Gemini 实时分析（analyzer.py 已有骨架）
- [ ] 事件存储到 Supabase（storage.py 已有骨架）
- [ ] 关键帧上传到 Supabase Storage
- [ ] Lark 通知接入真实事件
- [ ] EC2 上跑完整 worker（main.py）
- [ ] EC2 本地数据自动清理（cron）

### Phase 5：Web 仪表板
- [ ] 总览页：今日指标 + 趋势图
- [ ] 猫咪管理：资料卡片 + 参考照片上传
- [ ] 进食时间线：事件列表 + 帧缩略图
- [ ] 统计报表：每日/每周图表

### Phase 6：生产部署 + 监控
- [ ] Worker Docker 化部署到 EC2
- [ ] Web 部署到 Vercel
- [ ] 健康异常告警（猫 24h 未进食）
- [ ] 监控：Worker 心跳、Gemini 调用量/成本
