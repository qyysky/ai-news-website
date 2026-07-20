# 襄阳招聘日报

一个无需后端的襄阳公开招聘信息网站。GitHub Actions 每天从公开可访问的招聘页面和公开资讯检索中抓取信息，生成静态数据文件；GitHub Pages 直接展示，因此可免费托管。

## 发布到 GitHub Pages

1. 将此目录推送到一个 GitHub 仓库。
2. 打开仓库的 **Settings → Pages**。
3. 在 **Build and deployment** 中选择 **Deploy from a branch**，分支选 `main`（或你的默认分支），目录选 `/(root)`，保存。
4. 在 **Actions** 页面运行一次 “Update daily Xiangyang jobs” 工作流，立即填充当天招聘信息。

之后工作流会在每天北京时间 08:00 自动更新并提交 `data/news.json`。如果仓库属于组织，请确认 Actions 具备读写权限：**Settings → Actions → General → Workflow permissions → Read and write permissions**。

## 数据范围与来源

- 襄阳人才综合服务平台：公开招聘公告与企业岗位。
- 公开资讯检索：用于补充可公开访问的本地招聘资讯。
- 不抓取需要登录、规避验证码的页面，也不采集简历、联系方式等个人信息。

## 自定义来源

编辑 `scripts/fetch_news.py` 中的来源地址或抓取函数即可增加或替换公开来源。页面只读取 `data/news.json`，无需修改前端代码。
