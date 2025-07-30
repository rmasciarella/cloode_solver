FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    gnupg \
    lsb-release \
    software-properties-common \
    sudo \
    vim \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - \
    && sudo apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.7.1
ENV POETRY_HOME=/opt/poetry
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && poetry --version

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Create a non-root user
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user (if it doesn't exist)
RUN if ! id -u $USERNAME > /dev/null 2>&1; then \
        groupadd --gid $USER_GID $USERNAME \
        && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME; \
    fi \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

# Set working directory
WORKDIR /workspace

# Configure Poetry to create virtualenvs in project
RUN poetry config virtualenvs.in-project true

# Ensure pip is up to date
RUN pip install --upgrade pip setuptools wheel

# Note: We don't install dependencies here because the workspace
# will be mounted later. Dependencies will be installed via post-create script.

# Switch to non-root user
USER $USERNAME

# Set environment variables
ENV PYTHONPATH=/workspace
ENV PATH="/workspace/.venv/bin:$PATH"