# Get iamge
FROM quay.io/jupyter/base-notebook

# setup working directory for container
WORKDIR /notebook/
COPY --chmod=0777 . .

# Install necessary packages
#USER root
#RUN  apt-get update && \
#    apt-get install -y \
#    git && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists

# Copy requirements.txt
#COPY ./requirements.txt /notebook/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -Ur /notebook/requirements.txt

# Clone repo
# RUN cd /notebook && git clone https://github.com/pendingintent/cdisc-json-validation.git
USER root

