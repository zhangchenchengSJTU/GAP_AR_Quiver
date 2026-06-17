FROM gapsystem/gap-docker
# 使用 python3 -m pip 来安装 pyvis 库
RUN python3 -m pip install pyvis
COPY --chown=1000:1000 . $HOME/GAP_Online
USER gap
WORKDIR $HOME/GAP_Online
EXPOSE 8000
CMD ["python3", "ARquiver/source/server.py", "8000"]
