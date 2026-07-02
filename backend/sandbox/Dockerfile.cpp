FROM gcc:13
COPY run_cpp.sh /run.sh
RUN chmod +x /run.sh && useradd -m -u 1000 runner
USER runner
ENTRYPOINT ["/run.sh"]
