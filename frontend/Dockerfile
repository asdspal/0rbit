FROM node:18-alpine AS base

WORKDIR /app

COPY package*.json ./
RUN npm install --silent

COPY . .
RUN mkdir -p public

RUN npm run build

FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=base /app/package*.json ./
COPY --from=base /app/.next ./.next
COPY --from=base /app/public ./public
COPY --from=base /app/next.config.mjs ./next.config.mjs
RUN npm install --omit=dev --silent

ENV NODE_ENV=production

EXPOSE 3000

CMD ["npm", "start"]
