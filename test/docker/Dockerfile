FROM debian:11

RUN apt-get update && apt-get install -y openssh-server --no-install-recommends \
    && apt-get install -y sudo python3 \
    && rm -r /var/lib/apt

RUN adduser --gecos "" user --disabled-password && adduser user sudo
ADD test_key.pub /home/user/.ssh/authorized_keys
RUN chmod u=rwX,go= /home/user/.ssh \
    && chown -R user:user /home/user/.ssh \
    && rm /etc/ssh/ssh_host_*key* \
    && echo '%sudo        ALL=(ALL:ALL) NOPASSWD:ALL' > /etc/sudoers.d/sudo_nopasswd

ADD host_key /etc/ssh/ssh_host_ed25519_key

ENTRYPOINT ["bash", "-c", "service ssh start -d && while true; do sleep 10; done"]

EXPOSE 22
