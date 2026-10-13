FROM node:22-alpine
WORKDIR /app
COPY package*.json ./
COPY pnpm-lock.yaml pnpm-workspace.yaml ./
RUN corepack enable && corepack prepare pnpm@11.19.0 --activate && pnpm install --frozen-lockfile
COPY . .
EXPOSE 5173
CMD ["pnpm", "dev"]
