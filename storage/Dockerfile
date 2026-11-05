# @spec docs/BACKLOG.md#sls-010 | docs/PLATFORM.md#stockage
FROM golang:1-bookworm@sha256:b08bc99468058b6d8a0ada17fa54996b910d5e82a7e95bee0372e3bd98415258 AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY *.go ./
RUN CGO_ENABLED=0 go build -mod=readonly -trimpath -o /p2-quota .

FROM scratch
COPY --from=build /p2-quota /p2-quota
ENTRYPOINT ["/p2-quota"]
