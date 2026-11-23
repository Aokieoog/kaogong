# 公考日历订阅

这是一个可部署到 GitHub 的 `.ics` 日历订阅项目，覆盖国考、各省（区、市）公务员考试及事业单位招考的公告、报名、准考证打印、笔试、面试和成绩查询节点。

## 订阅方式

推送到 GitHub 后，订阅地址固定为：

`https://raw.githubusercontent.com/<用户名>/<仓库名>/main/docs/kaogong.ics`

在 Apple Calendar、Google Calendar、Outlook 或手机日历中选择“通过 URL 订阅”。GitHub Actions 每天 08:10（中国时间）抓取官网；日历客户端按自身刷新策略更新。

## 可靠性规则

项目只抓取政府、组织部门、人社部门或人事考试机构官网。新抓取结果写入 `data/pending_events.json`，不直接发布；核对公告原文后，将条目移入 `data/verified_events.json`，再自动生成订阅文件。这样可以避免网页导航文字或更正公告造成错误提醒。

## 使用

```bash
python3 scripts/update_calendar.py
python3 scripts/update_calendar.py --validate
```

`data/sources.json` 已提供全国和 31 个省（区、市）的官方入口；可按实际公告栏目继续细化 URL。发布前将 `verified_events.json` 中核实的事件保留或新增即可。
