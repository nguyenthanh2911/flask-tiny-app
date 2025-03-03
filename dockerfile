# Use Alpine as the base image
FROM alpine:latest

# Install Python, pip, and other dependencies
RUN apk add --no-cache python3 py3-pip

# Set the working directory
WORKDIR /usr/src/app

# Copy requirements and install dependencies
RUN python3 -m venv venv
RUN . venv/bin/activate

# Cài đặt Flask trong môi trường ảo
RUN venv/bin/pip install flask flask_sqlalchemy flask_login werkzeug


# Copy application files
COPY app.py ./
COPY templates ./templates
COPY static ./css

# Chạy lệnh tạo database
RUN venv/bin/python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Expose the application's port
EXPOSE 5000

# Run the application
CMD ["venv/bin/python", "app.py"]