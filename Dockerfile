# Get iamge
FROM quay.io/jupyter/base-notebook

# setup working directory for container
WORKDIR /notebook/
COPY --chmod=0777 . .

# Install dependencies
RUN pip install --no-cache-dir -Ur /notebook/requirements.txt

# Clone repo
# RUN cd /notebook && git clone https://github.com/pendingintent/cdisc-json-validation.git
USER root

