FROM --platform=linux/arm64 python:3.10
WORKDIR /app
ADD . /app
RUN python3 -m pip install -r requirements.txt
ENV STATIC_ROOT=/static
COPY .env .env
CMD ["/app/entrypoint.sh"]
