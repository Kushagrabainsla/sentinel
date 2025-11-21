FROM public.ecr.aws/lambda/python:3.11

# Install dependencies to /opt/python
RUN pip install --target /opt/python google-generativeai

# The layer will be in /opt/python
CMD ["echo", "Dependencies installed"]
