FROM node:18-alpine
WORKDIR /app

COPY package.json ./
COPY package-lock.json ./
COPY tsconfig.json ./
COPY src ./

RUN npm install
EXPOSE 5000
CMD ["npm", "start"]
