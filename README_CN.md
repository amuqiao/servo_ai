# uv-docker 示例项目

一个演示在 Docker 镜像中使用 uv 的示例项目，重点展示本地开发时挂载项目的最佳实践。

请参考 [uv Docker 集成指南](https://docs.astral.sh/uv/guides/integration/docker/) 获取更多背景信息。

## 快速开始

项目提供了 [`run.sh`](./run.sh) 工具脚本用于快速构建镜像和启动容器。该脚本演示了使用绑定挂载（bind mounts）实现项目目录和虚拟环境目录的开发最佳实践。

使用 `docker run` 运行容器化 Web 应用：

```console
$ ./run.sh
```

访问 [`http://localhost:8000`](http://localhost:8000) 查看网站。

项目也提供了 Docker compose 配置来演示使用 Docker compose 的开发最佳实践。Docker compose 比直接使用 `docker run` 更复杂，但能提供更强大的工作流支持。

使用 Docker compose 运行 Web 应用：

```
docker compose up --watch 
```

默认启动 Web 应用，同时提供命令行入口用于演示：

```console
$ ./run.sh hello
```

## 项目结构

### Dockerfile

[`Dockerfile`](./Dockerfile) 定义了基础镜像，包含：
- uv 的安装
- 分离安装项目依赖和项目代码以实现最佳镜像构建缓存
- 环境变量 PATH 配置
- Web 应用启动配置

[`multistage.Dockerfile`](./multistage.Dockerfile) 扩展基础 Dockerfile 实现多阶段构建，减小最终镜像体积。

[`standalone.Dockerfile`](./standalone.Dockerfile) 在多阶段构建中使用托管 Python 解释器替代基础镜像自带的系统解释器。

### Dockerignore 文件

[`.dockerignore`](./.dockerignore) 包含 .venv 目录排除规则，确保镜像构建时不包含虚拟环境。注意该规则不适用于容器运行时的卷挂载。

### 运行脚本

[`run.sh`](./run.sh) 演示了使用 `docker run` 进行本地开发的典型命令，通过挂载项目源码实现实时修改反馈。

### Docker compose 文件

[compose.yml](./compose.yml) 包含 Docker compose 配置，使用 [watch 指令](https://docs.docker.com/compose/file-watch/#compose-watch-versus-bind-mounts) 实现文件变更自动同步的最佳实践。

### 应用代码

Python 应用代码位于 [`src/uv_docker_example/__init__.py`](./src/uv_docker_example/__init__.py)，包含命令行入口和基于 FastAPI 的 "hello world" 示例。

### 项目配置

[`pyproject.toml`](./pyproject.toml) 包含 Ruff 开发依赖、FastAPI 运行时依赖，并定义了 `hello` 应用入口。

## 常用命令

验证环境一致性：

```console
$ ./run.sh uv sync --frozen
Audited 2 packages ...
```

进入容器 bash shell：

```console
$ ./run.sh /bin/bash
```

仅构建镜像：

```console
$ docker build .
```

构建多阶段镜像：

```console
$ docker build . --file multistage.Dockerfile
```