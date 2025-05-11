#!/usr/bin/env sh
#
# 构建并运行示例Docker镜像
#
# 将本地项目目录挂载到容器中，模拟常见的开发工作流
#
# 使用示例:
#   ./run_docker.sh                                            # 启动开发服务器
#   ./run_docker.sh pytest                                     # 执行测试
#   ./run_docker.sh bash                                       # 进入容器shell
#   ./run.sh --dockerfile /abs/path/to/Dockerfile              # 指定绝对路径
#   ./run.sh --dockerfile ./Dockerfile                         # 指定相对路径
#   ./run.sh                                                   # 不指定Dockerfile路径，使用当前目录的Dockerfile
# 

#
# docker run命令参数说明:
#   --rm                  容器退出后自动删除
#   --volume .:/app       挂载当前目录到容器的/app目录，代码修改无需重建镜像
#   --volume ./.venv:/app/.venv  单独挂载虚拟环境，避免开发环境影响容器
#   --publish 8000:8000   将容器的8000端口暴露到宿主机
#   $INTERACTIVE          根据终端类型设置交互模式
#   $(docker build -q .)  构建镜像并获取镜像ID作为运行目标,使用静默模式(-q)构建直接获取镜像ID
#   $(docker build -q -f "$DOCKERFILE_PATH" .)  构建镜像并获取镜像ID作为运行目标,使用静默模式(-q) 构建直接获取镜像ID
#   支持通过 --dockerfile 参数指定 Dockerfile 路径, 未指定参数时默认使用当前目录的 Dockerfile
#   "$@"                  将所有参数传递给容器内的命令


# 解析Dockerfile路径参数
DOCKERFILE_PATH="Dockerfile_local"
while [[ "$#" -gt 0 ]]; do
    case "$1" in
        --dockerfile)
            DOCKERFILE_PATH="$2"
            shift 2
            ;;
        *)
            break
            ;;
    esac
done

# 检测终端是否支持交互模式
if [ -t 1 ]; then
    INTERACTIVE="-it"
else
    INTERACTIVE=""
fi

echo "正在构建Docker镜像..."
echo "使用的Dockerfile路径: $DOCKERFILE_PATH"
# 执行Docker容器
docker run \
    --rm \
    --volume .:/app \
    --volume ./.venv:/app/.venv \
    --publish 8000:8000 \
    $INTERACTIVE \
    $(docker build -q -f "$DOCKERFILE_PATH" .) \
    "$@"