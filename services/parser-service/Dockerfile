FROM golang:1.21-alpine AS builder

WORKDIR /app

COPY go.mod main.go ./
RUN go mod tidy
RUN go build -o parser-service main.go

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/parser-service .

EXPOSE 8001

CMD ["./parser-service"]
