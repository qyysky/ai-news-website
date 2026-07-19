# AI Daily

一个无需后端的每日 AI 新闻网站。GitHub Actions 每天从公开 RSS 源抓取资讯，生成静态数据文件；GitHub Pages 直接展示，因此可免费托管。

## 发布到 GitHub Pages

1. 将此目录推送到一个 GitHub 仓库。
2. 打开仓库的 **Settings → Pages**。
3. 在 **Build and deployment** 中选择 **Deploy from a branch**，分支选 `main`（或你的默认分支），目录选 `/(root)`，保存。
4. 在 **Actions** 页面运行一次 “Update daily AI news” 工作流，立即填充当天新闻。

之后工作流会在每天北京时间 08:00 自动更新并提交 `data/news.json`。如果仓库属于组织，请确认 Actions 具备读写权限：**Settings → Actions → General → Workflow permissions → Read and write permissions**。

## 自定义新闻源

编辑 `scripts/fetch_news.py` 中的 `FEEDS` 列表即可增加或替换 RSS / Atom 地址。页面只读取 `data/news.json`，无需修改前端代码。
