# WARP Pool Controller

一个拥有现代化 Web 界面的、支持运行时动态管理的 WARP 实例代理池工具。

## ✨ 功能特性

- **图形化管理界面**: 通过 Vue.js 和 TailwindCSS 构建的现代化 Web UI，实时监控和管理所有 WARP 实例。
- **动态实例管理**: 在运行时通过 UI 直接添加、删除、修改 WARP 实例，无需重启服务或修改配置文件。
- **状态持久化**: 所有实例配置和状态都存储在 SQLite 数据库中，服务重启后数据不丢失。
- **统一代理入口**: 提供一个单一、稳定的 SOCKS5 代理地址 (`socks5://<your-host>:10800`)，自动将流量转发到健康的 WARP 实例，实现负载均衡和故障转移。
- **实时状态更新**: 使用 WebSocket 实时推送实例状态到前端，确保数据即时同步。
- **容器化部署**: 整个应用栈（后端、前端、数据库）通过 Docker Compose 进行管理，一键启动。

## 🚀 快速开始

### 先决条件

- [Docker](https://www.docker.com/get-started)
- [Docker Compose](https://docs.docker.com/compose/install/)

### 部署

1.  **克隆项目**
    ```bash
    git clone https://github.com/CrisRain/warppool.git
    cd warppool
    ```

2.  **启动服务**
    使用 Docker Compose 启动所有服务（后端 API、前端 UI、统一代理）。
    ```bash
    docker-compose up --build -d
    ```

3.  **访问 Web UI**
    在浏览器中打开 `http://localhost:5173` 即可访问管理界面。

    > **注意**: `5173` 是 Vite 开发服务器的端口。如果前端被构建并由 Nginx 服务（如生产 `Dockerfile` 中所示），端口可能会是 `80` 或其他。请根据 `docker-compose.yml` 中的端口映射进行调整。

4.  **添加 WARP 实例**
    - 在 Web UI 中，点击 "Add Instance" 按钮。
    - 输入一个唯一的实例名称（例如 `warp-01`）和一个未被占用的 SOCKS5 端口（例如 `11001`）。
    - 点击 "Add Instance" 提交。
    - 后端服务会自动拉取 `warp-instance` 镜像并根据你提供的配置启动一个新的 WARP 容器。

5.  **使用统一代理**
    将你的客户端或应用程序的 SOCKS5 代理设置为 `socks5://localhost:10800`。`controller-app` 会自动将你的请求路由到当前池中一个健康的 WARP 实例。

## 🛠️ 技术栈

- **后端**: FastAPI, SQLAlchemy, Alembic, Docker SDK
- **前端**: Vue.js, Vite, TailwindCSS, Axios
- **数据库**: SQLite
- **代理**: 自定义异步 SOCKS5 代理
- **部署**: Docker, Docker Compose

## 📂 项目结构

```
warppool/
├── docker-compose.yml
├── README.md
├── controller-app/
│   ├── Dockerfile
│   ├── alembic/
│   ├── app/
│   └── data/
├── frontend/
│   ├── Dockerfile
│   └── src/
└── warp-instance/
    └── Dockerfile
```

## 🤝 贡献

欢迎提交 Pull Requests。对于重大更改，请先开启一个 issue 来讨论您想要改变的内容。

## 📄 许可证

[MIT](LICENSE)