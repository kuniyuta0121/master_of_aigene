FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY go.mod .
COPY main.go .
RUN go build -o search_service .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/search_service .
CMD ["./search_service"]
