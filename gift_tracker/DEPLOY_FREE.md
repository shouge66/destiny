# 免费固定域名部署指南（Render）

目标：把当前项目部署到可长期访问的免费域名（`*.onrender.com`），让他人可直接打开使用。

当前状态：
- 本地可用地址：`http://127.0.0.1:5500/`
- 公网固定域名需要你在 Render 完成一次实际部署后才会真正可用
- 因此我现在不能诚实地给你一个“已在线可访问”的公网网址，只能给出部署后将获得的固定域名格式

本项目已支持 Blueprint 部署，会自动创建两个服务：
- `fangzhi-backend`（Django API）
- `fangzhi-frontend`（静态前端）

## 1. 推送到 GitHub

把整个仓库推送到 GitHub（必须是 Render 可访问的仓库）。

## 2. 在 Render 创建 Blueprint

1. 登录 Render。
2. 点击 `New +` -> `Blueprint`。
3. 选择你的 GitHub 仓库。
4. Render 会自动读取 `gift_tracker/render.yaml`。
5. 点击 `Apply` 创建服务。

创建完成后会得到两个免费固定域名（服务名可读，域名长期不变）：
- 后端：`https://fangzhi-backend.onrender.com`
- 前端：`https://fangzhi-frontend.onrender.com`

说明：如果服务名已被占用，Render 会加后缀，请以控制台显示的最终域名为准。

部署后，其他人可以通过以下三种方式直接进入：
- 自己注册账号
- 点击“游客体验”直接进入 demo 账号
- 使用自动初始化的演示账号

## 3. 配置后端环境变量

进入后端服务 `fangzhi-backend` -> `Environment`，确认/设置：

- `DEBUG=False`
- `ALLOWED_HOSTS=*`
- `CORS_ALLOW_ALL_ORIGINS=True`
- `WENMO_TIANJI_API_URL=<你的文墨天机API地址，可选>`
- `WENMO_TIANJI_API_KEY=<你的文墨天机API密钥，可选>`
- `DEMO_USERNAME=demo`
- `DEMO_PASSWORD=<你自己设置一个密码，建议强密码>`
- `DEMO_EMAIL=demo@example.com`

说明：
- 命理接口未配置时，前端会自动回退到本地保底分析。
- 配置后会优先调用专业排盘接口。
- 服务启动时会自动执行 `python manage.py ensure_demo_user`，确保 demo 账号存在。

## 4. 配置前端调用后端地址（关键）

进入前端服务 `fangzhi-frontend` -> `Environment`，新增：

- `BACKEND_API_BASE=https://fangzhi-backend.onrender.com/api`

然后手动触发一次前端重部署（`Manual Deploy` -> `Deploy latest commit`）。

构建时会自动写入 `config.runtime.js`，无需再手改前端文件。

## 5. 对外可用链接

部署成功后，把前端域名发给别人即可直接使用：

- 前端入口：`https://fangzhi-frontend.onrender.com`

首次访问可用方式：
- 页面直接注册新账号
- 点击“游客体验”进入 demo 账号
- 如果你愿意公开 demo 密码，也可以直接把 `DEMO_USERNAME` / `DEMO_PASSWORD` 发给别人

可用于自检的后端接口：

- 健康检查：`https://fangzhi-backend.onrender.com/api/health/`
- API 根：`https://fangzhi-backend.onrender.com/api/`

## 6. 常见问题

1. 首次打开很慢：
   免费实例会休眠，首次访问冷启动约 30~90 秒。

2. 前端可打开但登录失败：
   先检查 `BACKEND_API_BASE` 是否是正确的后端 `https` 地址，确认前端已重新部署。

3. 看到 CORS 报错：
   检查后端 `CORS_ALLOW_ALL_ORIGINS=True` 是否生效并完成重启。
