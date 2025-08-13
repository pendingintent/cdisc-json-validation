# Get iamge
FROM ubuntu:latest

# setup working directory for container
WORKDIR /notebook/

# Install necessary packages
RUN apt-get update && \ 
    apt-get install -y \
    software-properties-common \ 
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists

# Create a virtual environment
RUN python3 -m venv /opt/venv


# Install dependencies
COPY requirements.txt /opt/requirements.txt
RUN /opt/venv/bin/pip install -Ur /opt/requirements.txt

# Activate virtual environment and install Jupyter
RUN /opt/venv/bin/pip install jupyter

COPY . .

CMD ["/opt/venv/bin/jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root"]
