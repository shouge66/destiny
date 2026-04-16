# 免费无卡部署指南（PythonAnywhere + GitHub Pages）

目标：在不绑定银行卡的情况下，把项目部署成“别人可直接访问”的公网网址；如果你持有自己的域名，还可以把 GitHub Pages 入口绑定成包含 `daodestiny` 的自定义域名。

方案：
- 后端（Django API）：PythonAnywhere 免费版
- 前端（静态 SPA）：GitHub Pages 免费版

## 0. 前置条件

1. 代码已推送到 GitHub 仓库：
   `https://github.com/shouge66/destiny`
2. 本地已经验证功能可用（登录/注册/游客体验）。

## 1. 部署后端到 PythonAnywhere（免费无卡）

1. 注册并登录 PythonAnywhere：
   `https://www.pythonanywhere.com/`
2. 打开 `Consoles` -> `Bash`。
3. 克隆仓库：

```bash
git clone https://github.com/shouge66/destiny.git
cd destiny/gift_tracker
python3.10 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py ensure_demo_user
```

4. 创建 Web App：
   `Web` -> `Add a new web app` -> `Manual configuration` -> `Python 3.10`。
5. 在 `Web` 页面配置：
   Python path:
   `/home/<你的用户名>/destiny/gift_tracker`
   WSGI file 使用项目的 `gift_tracker/wsgi.py`。
6. 在 `Web` -> `Environment variables` 增加：

- `DEBUG=False`
- `ALLOWED_HOSTS=<你的用户名>.pythonanywhere.com`
- `CORS_ALLOW_ALL_ORIGINS=True`
- `DEMO_USERNAME=demo`
- `DEMO_PASSWORD=<你自己设置的强密码>`
- `DEMO_EMAIL=demo@example.com`
- `WENMO_TIANJI_API_URL=<可选>`
- `WENMO_TIANJI_API_KEY=<可选>`

7. 点击 `Reload` 重载 Web App。

部署成功后后端地址通常是：
`https://<你的用户名>.pythonanywhere.com/api/`

可验证：
- `https://<你的用户名>.pythonanywhere.com/api/health/`

## 2. 部署前端到 GitHub Pages（免费无卡）

1. 打开仓库 Settings -> Pages。
2. Source 选择 `Deploy from a branch`。
3. Branch 选择 `main`，Folder 选择 `/(root)`。
4. 保存并等待发布。

发布后前端地址通常是：
`https://shouge66.github.io/destiny/`

## 2.1 GitHub Pages 自定义域名（关键词：daodestiny）

先说结论：
- GitHub Pages 不能直接免费送你一个 `daodestiny` 域名。
- 你必须先拥有一个自己的域名，然后才能绑定到 GitHub Pages。
- 推荐优先考虑这些名字：
   - `daodestiny.com`
   - `www.daodestiny.com`
   - `daodestiny.cn`
   - `daodestiny.life`
   - `daodestiny.app`

推荐绑定方式：
- 主域名：`daodestiny.com`
- 或更稳妥：`www.daodestiny.com`

GitHub Pages 里这样配置：
1. 打开仓库 `Settings` -> `Pages`。
2. 在 `Custom domain` 中填入你的域名，例如：
    `www.daodestiny.com`
3. 保存。
4. 勾选 `Enforce HTTPS`。

DNS 配置方式：

如果你绑定的是 `www.daodestiny.com`：
- 在域名服务商后台新增 1 条 `CNAME` 记录
- 主机记录：`www`
- 记录值：`shouge66.github.io`

如果你绑定的是根域名 `daodestiny.com`：
- 新增 4 条 `A` 记录，指向 GitHub Pages 官方 IP：
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
- 可选再加 1 条 `CNAME`：
   - 主机记录：`www`
   - 记录值：`shouge66.github.io`

建议：
- 如果你只是要一个更像正式产品的网址，优先用 `www.daodestiny.com`，配置最简单。
- 如果你还没买域名，可以先继续用：
   `https://shouge66.github.io/destiny/`
- 等你买好域名后，再把自定义域名绑定上去。

## 3. 绑定前端到后端 API

编辑文件 `gift_tracker/frontend-spa/config.runtime.js`，把非本地地址改为 PythonAnywhere：

```js
window.__GIFT_API_BASE__ = isLocal
  ? "http://127.0.0.1:8000/api"
  : "https://<你的用户名>.pythonanywhere.com/api";
```

修改后提交并推送到 GitHub，Pages 会自动更新。

## 4. 对外可用网址

- 前端入口：`https://shouge66.github.io/destiny/`
- 自定义域名入口（如果已绑定成功）：`https://www.daodestiny.com/` 或 `https://daodestiny.com/`
- 后端健康检查：`https://<你的用户名>.pythonanywhere.com/api/health/`

## 5. 用户进入方式

部署后别人可通过以下方式使用：
1. 注册新账号
2. 游客体验按钮
3. demo 账号（你可按需公开）

## 6. 常见问题

1. 前端打开但无法请求后端：
   检查 `config.runtime.js` 是否已经改成 PythonAnywhere 的 API 地址，并已推送生效。

2. CORS 报错：
   保持 `CORS_ALLOW_ALL_ORIGINS=True`，然后重载 PythonAnywhere Web App。

3. PythonAnywhere 免费限制：
   免费版有资源和出站网络限制，适合演示与轻量使用；正式生产建议升级付费或迁移到其他平台。

4. 为什么 GitHub Pages 里填了域名但打不开：
   大多数情况是 DNS 还没生效，或你还没有在域名服务商后台把记录指向 GitHub Pages。

5. 自定义域名想用 `daodestiny` 但还没买到：
   GitHub 不能代替域名注册商。你需要先在阿里云、腾讯云、Namecheap、Cloudflare Registrar 等平台注册一个包含 `daodestiny` 的域名，然后再回来绑定。
