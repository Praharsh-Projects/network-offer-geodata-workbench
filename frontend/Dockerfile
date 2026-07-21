FROM node:22-alpine AS build

WORKDIR /app
RUN npm install --global pnpm@10.28.1

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY frontend ./
RUN pnpm build

FROM node:22-alpine AS runtime

ENV HOST=0.0.0.0 \
    PORT=3000 \
    NODE_ENV=production

WORKDIR /app
COPY --from=build --chown=node:node /app/.output ./.output

USER node
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
