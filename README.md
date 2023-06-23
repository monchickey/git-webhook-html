# 接收 Git Webhooks 并生成 HTML 静态页面的工具

## 1. 支持的 Git Webhooks
- [x] GitHub
- [x] Gitee

## 2. 支持的页面生成工具
- [x] Hugo
- [x] mdBook

## 安装配置

### 1. 前提条件
1. Python 3.6+
2. Python 依赖：Flask 和 Gunicorn
3. Git 客户端
4. 根据生成页面的种类安装：hugo 或 mdbook 环境
5. Web 服务器，建议使用 nginx 提供访问

需要的 Python 依赖有：Flask 和 Gunicorn，可以使用 pip 工具安装：

```bash
pip install flask gunicorn
```

### 2. 运行程序
克隆当前仓库：

```bash
git clone https://github.com/monchickey/git-webhook-html.git
cd git-webhook-html
```

运行服务：

```bash
gunicorn -w 1 -b 127.0.0.1:5000 -e GIT_URL=<git-repo-url> -e TOOL_TYPE=<hugo or mdbook> -e SECRET_KET=<secret-key> main:app
```

其中：

`git-repo-url` 表示待渲染的 Git 仓库地址，如果是私有仓库则需要提前配置好 SSH 密钥。

`TOOL_TYPE` 指定工具类型，当前只支持 hugo 和 mdBook。

`secret-key` 表示 Git 服务器配置 WebHooks 时所指定的 key，要和后续仓库的配置保持一致，如果留空表示不进行验证，但是强烈建议配置。

运行后默认会克隆仓库到脚本当前的目录，同时会将静态页面生成到当前目录下的 `<repo-name>-output` 中，如果想设置单独的静态页面输出目录，需要设置 `OUTPUT` 环境变量指定输出目录，并且在运行程序前创建好它。

### 3. 配置 nginx 代理 Webhooks 请求和静态页面

假设工作目录为：`/opt/git-webhook-html`，仓库的输出目录为：`/opt/git-webhook-html/example-output`，nginx 的配置示例如下：

```
    server {
        listen       80;
        server_name  example.com;

        
        root /opt/git-webhook-html/example-output;
        index index.html index.htm;

        error_page  404              /404.html;

        # redirect server error pages to the static page /50x.html
        error_page   500 502 503 504  /50x.html;
        location = /50x.html {
            root   html;
        }

        location /api/docs {
            proxy_pass http://127.0.0.1:5000;
            proxy_redirect off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_intercept_errors on;
            error_page 500 502 503 504 /50x.html;
        }
    }
```

其中 `server_name` 需要替换为实际的域名，并做好解析。

### 4. 在仓库设置 WebHooks

对于 GitHub 仓库首先进入仓库首页，依次点击：“Settings - Webhooks - Add webhook”，配置内容如下：

1. Payload URL 中输入：`http://example.com/api/docs`，实际运行时请将 `example.com` 替换为实际的主机地址，建议开启 HTTPS 以保证安全。

2. Content type 选择：`application/json`

3. Secret 输入认证密钥，要和上面启动程序时指定的 `secret-key` 保持一致。

4. 事件类型选择默认的 "Just the `push` event. " 即只在 push 事件时触发 Webhooks。

5. 勾选 "Active" 表示激活 Webhooks。

6. 最后点击 Add webhook 完成添加，添加后默认会发送一条 `ping` 事件的消息。

之后当仓库有新的 `push` 事件时，就会自动触发 Webhooks 调用我们启动的服务来更新页面。

对于 Gitee 仓库的 Webhooks 配置方式类似，也是进入仓库首页，依次点击：“管理 - WebHooks - 添加 webHook”，配置内容如下：

1. URL 输入我们运行服务的实际地址，和上面一样。
2. WebHook 密码/签名密钥选择 “签名密钥”，然后输入认证的密钥，和上面的 `secret-key` 保持一致。
3. 事件选择 `Push`。
4. 勾选 “激活” 选项。
5. 点击 “添加” 按钮完成添加，添加后默认会发送一条 `push` 事件的测试消息。

之后当仓库有新的 `push` 事件时，就会触发 Webhooks 了。
