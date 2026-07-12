# Сборка
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Пусто = тот же origin (запросы к /api через nginx). Инлайнится в бандл.
ARG NEXT_PUBLIC_API_URL=""
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Рантайм
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/next.config.mjs ./next.config.mjs
# public/ содержит self-hosted Monaco и Pyodide (их кладёт prebuild) —
# без него песочница и редактор кода не отдаются в проде.
COPY --from=build /app/public ./public
EXPOSE 3000
CMD ["npm", "run", "start"]
