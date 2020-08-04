FROM python:3

# Install linux applications
RUN apt-get update && apt-get install --yes \
    fonts-powerline \
    curl \
    zsh \
    git \
    emacs

RUN apt-get install unzip
#RUN apt-get install x11vnc --yes

# Installing LSSS on Linux
#
#1. Unzip the LSSS installation zip file for linux.
#   The resulting directory is referred to as LSSS_INSTALL_SRC.
RUN mkdir /LSSS_INSTALL_SRC && \
    cd /LSSS_INSTALL_SRC && \
    wget https://www.marec.no/downloads/cd-lsss-2.8.0-20200204-1059/lsss-2.8.0-20200204-1059-linux.zip && \
    unzip lsss-2.8.0-20200204-1059-linux.zip && \
    rm lsss-2.8.0-20200204-1059-linux.zip

#2. Install dongle driver
#   1. Change directory:
#         cd LSSS_INSTALL_SRC/sntl_sud_*
#      or on Debian-based systems, such as Ubuntu:
#         cd LSSS_INSTALL_SRC/sntl_sud_*/Debian_support
#   2. Run:
#         sudo ./sud_install.sh
RUN cd /LSSS_INSTALL_SRC/lsss-2.8.0-20200204-1059/sntl_sud_7.5.6/Debian_support && \
    ./sud_install.sh

#3. Install LSSS
#   a. Unzip the LSSS zip-file in LSSS_INSTALL_SRC.
#      The resulting directory is referred to as LSSS_HOME.
RUN mkdir /LSSS_HOME && \
    unzip /LSSS_INSTALL_SRC/lsss-2.8.0-20200204-1059/lsss-2.8.0-linux.zip -d /LSSS_HOME && \
    rm -rf LSSS_INSTALL_SRC

#4. Start LSSS
#   a. Insert a valid dongle in an USB port.
#   b. Start LSSS by running LSSS_HOME/lsss/LSSS.sh.
#RUN /LSSS_HOME/lsss-2.8.0/lsss/LSSS.sh

#5. Optional
#   a. Create a shortcut to the startup script on the desktop using the icon LSSS_HOME/lsss/LSSS.png.
#   b. See optional post-install steps in ReleaseNotes.txt.
#   c. If necessary, install a different version of Java than what is included.
#      Set the environment variable JAVA_HOME or MAREC_JAVA_HOME to the Java installation directory.

CMD zsh
