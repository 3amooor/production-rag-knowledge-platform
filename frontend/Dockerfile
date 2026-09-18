FROM node:24-alpine AS base
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .

FROM base AS development
CMD ["npm", "run", "dev"]

FROM base AS production
RUN npm run build
FROM nginx:1.27-alpine
COPY --from=production /app/dist /usr/share/nginx/html
