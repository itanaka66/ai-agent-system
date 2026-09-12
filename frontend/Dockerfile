# Frontend (Agent Console) container image: builds the static Vite bundle,
# then serves it with nginx, which also reverse-proxies /api and /metrics to
# the orchestrator container - so the browser only ever talks to one origin
# and there's nothing to configure (no VITE_API_BASE_URL needed).

FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
