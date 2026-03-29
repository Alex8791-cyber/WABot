FROM ghcr.io/cirruslabs/flutter:3.27.4 AS build

WORKDIR /app
COPY . .

ARG API_BASE_URL=http://localhost:8000
RUN flutter pub get && \
    flutter build web --release --dart-define=API_BASE_URL=$API_BASE_URL

FROM nginx:alpine
COPY --from=build /app/build/web /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
