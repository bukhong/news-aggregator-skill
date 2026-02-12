# 🗞️ News Aggregator 指令菜单

请回复 **序号** 执行任务。所有报告均自动保存到 `reports/YYYY-MM-DD/` 并以中文呈现。

---

### 🎯 核心新闻源

| # | 名称 | 命令 |
|---|---|---|
| 1 | 🦄 硅谷热点 (Hacker News) | `--source hackernews` |
| 2 | 🐙 开源趋势 (GitHub Trending) | `--source github` |
| 3 | 🚀 创投快讯 (36Kr) | `--source 36kr` |
| 4 | 🐱 产品猎人 (Product Hunt) | `--source producthunt` |
| 5 | 🤓 极客社区 (V2EX) | `--source v2ex` |
| 6 | 🐧 腾讯科技 (Tencent News) | `--source tencent` |
| 7 | 📈 华尔街见闻 (WallStreetCN) | `--source wallstreetcn` |
| 8 | 🔴 微博热搜 (Weibo) | `--source weibo` |
| 9 | 🤗 HF 每日论文 (Hugging Face) | `--source huggingface` |

---

### 📧 AI 行业内参

| # | 名称 | 命令 |
|---|---|---|
| 10 | ChinAI (Jeffrey Ding) | `--source chinai` |
| 11 | Memia (Ben Reid) | `--source memia` |
| 12 | Ben's Bites | `--source bensbites` |
| 13 | One Useful Thing (Ethan Mollick) | `--source oneusefulthing` |
| 14 | Interconnects (Nathan Lambert) | `--source interconnects` |
| 15 | AI to ROI | `--source aitoroi` |
| 16 | KDnuggets | `--source kdnuggets` |
| 17 | 🧠 全部 AI 内参聚合 | `--source ai_newsletters --limit 3` |

---

### ✍️ 深度思考 & 播客

| # | 名称 | 命令 |
|---|---|---|
| 18 | Paul Graham | `--source paulgraham` |
| 19 | Wait But Why | `--source waitbutwhy` |
| 20 | James Clear | `--source jamesclear` |
| 21 | Farnam Street | `--source farnamstreet` |
| 22 | Scott Young | `--source scottyoung` |
| 23 | Dan Koe | `--source dankoe` |
| 24 | 📚 全部文章聚合 | `--source essays --limit 3` |
| 25 | Lex Fridman Podcast | `--source lexfridman` |
| 26 | Latent Space (swyx) | `--source latentspace` |
| 27 | 80,000 Hours | `--source 80000hours` |
| 28 | 🎧 全部播客聚合 | `--source podcasts --limit 3` |

---

### ☕️ 每日早报 (Daily Briefings)

| # | 名称 | 命令 |
|---|---|---|
| 29 | 🌅 综合早报 (General) | `daily_briefing.py --profile general --no-save` |
| 30 | 💰 财经早报 (Finance) | `daily_briefing.py --profile finance --no-save` |
| 31 | 🤖 科技早报 (Tech) | `daily_briefing.py --profile tech --no-save` |
| 32 | 🍉 吃瓜早报 (Social) | `daily_briefing.py --profile social --no-save` |
| 33 | 🧠 AI 深度日报 (AI Daily) | `daily_briefing.py --profile ai_daily --no-save` |
| 34 | 📚 深度阅读清单 | `daily_briefing.py --profile reading_list --no-save` |

---

### 🔀 自由组合

直接指定多个源，用逗号分隔：

```
hackernews,github,wallstreetcn
```

例如：*"帮我看看 HN 和 GitHub 今天有什么热点"* → Agent 自动执行 `--source hackernews,github`

---

**✨ 请输入序号 (1-34) 或源名组合来执行**
