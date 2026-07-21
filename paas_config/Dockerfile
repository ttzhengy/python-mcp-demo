ARG BASE_IMAGE_PARA
# 构建基础镜像时使用python3.12
FROM $BASE_IMAGE_PARA
USER root

# 添加pip.conf文件，脱敏，仅示意
RUN echo "[global]" > /etc/pip.conf && \
    echo "index-url = 制品库url，这里隐去"

WORKDIR /home/python
# 复制软件包到workdir下，脱敏，仅示意
COPY $TARGET_PARA $DEPLOY_PARA

RUN pip3 install ...

EXPOSE 8000
USER python

CMD ["/opt/python/python-3.12.11/", "-m", "oboy_py"]