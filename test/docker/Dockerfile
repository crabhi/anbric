FROM debian:11

RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y openssh-server --no-install-recommends \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y sudo python3 vim \
    && rm -r /var/lib/apt

RUN adduser --gecos "" user --disabled-password && adduser user sudo
ADD test_key.pub /home/user/.ssh/authorized_keys
RUN chmod u=rwX,go= /home/user/.ssh \
    && chown -R user:user /home/user/.ssh \
    && rm /etc/ssh/ssh_host_*key* \
    && echo '%sudo        ALL=(ALL:ALL) NOPASSWD:ALL' > /etc/sudoers.d/sudo_nopasswd

ADD host_key /etc/ssh/ssh_host_ed25519_key
RUN chmod 0600 /etc/ssh/ssh_host_ed25519_key

ENTRYPOINT ["bash", "-c", "service ssh start && while true; do sleep 10; done"]

EXPOSE 22
