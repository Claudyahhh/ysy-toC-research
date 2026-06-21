# YSY Research

杨三月的公开研究报告库。这里沉淀 AI、市场、商业战略与产品增长等主题的研究成果。

## 报告目录

报告发布后在此登记：

| 日期 | 报告 | 主题 | 在线阅读 | PDF |
|---|---|---|---|---|
| 2026-06-21 | 电商行业研究报告 | 电商、平台经济、AI | [阅读](reports/ecommerce-industry-research/) | [下载](reports/ecommerce-industry-research/report.pdf) |
| 2026-06-21 | 搜索引擎行业研究 | 搜索引擎、AI 搜索、平台经济 | [阅读](reports/search-engine-industry-research/) | [下载](reports/search-engine-industry-research/report.pdf) |

## 仓库结构

```text
ysy-toC-research/
├── README.md
├── reports/
│   └── report-slug/
│       ├── README.md
│       ├── report.pdf
│       └── assets/
└── templates/
    └── report-template.md
```

每篇报告使用一个独立目录：

- `README.md`：可搜索、可引用、可追踪修改的 Markdown 正文。
- `report.pdf`：保留正式排版，方便下载与传播。
- `assets/`：报告使用的图片、图表和流程图。

## 发布流程

1. 复制 [`templates/report-template.md`](templates/report-template.md) 到新的报告目录并重命名为 `README.md`。
2. 将图片放进该报告的 `assets/` 目录，正文使用相对路径引用。
3. 运行 `python3 scripts/render_report_pdf.py <报告README.md> <报告目录/report.pdf>` 生成 PDF。
4. 在本页“报告目录”登记报告。
5. 检查隐私、数据来源和第三方素材版权后再公开发布。

## 内容与引用说明

- 报告会区分事实、来源观点和作者判断。
- 数据尽量标注统计时间、口径与原始来源。
- 飞书原稿可在报告元数据中保留链接及同步日期。
- 除非报告页面另有说明，仓库内容版权归作者所有，不自动授予再分发或商业使用许可。

## 作者

杨三月（杨思嫣）
