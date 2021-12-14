# ===================================================================
# Build stage
# ===================================================================
FROM python:3.8 AS builder

COPY requirements.txt .

RUN pip3 install --upgrade pip

# install dependencies to the local user directory (eg. /root/.local)
RUN pip3 install --user -r requirements.txt

# ===================================================================
# App image
# ===================================================================
FROM python:3.8-slim

WORKDIR /usr/src/app

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local

# update PATH environment variable
ENV PATH=/root/.local:$PATH:/root/.local/bin

COPY ./src ./src

CMD ["python", "./src/handler.py"]
