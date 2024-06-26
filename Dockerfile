FROM tensorflow/tensorflow:latest-gpu

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get install -y sudo

RUN mkdir -p /persistent

COPY copy/provision.sh /provision.sh
COPY copy/sudoers /etc/sudoers

ENTRYPOINT ["bash", "-c", "/provision.sh"]
