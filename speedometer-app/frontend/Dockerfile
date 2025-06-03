FROM node:16-alpine

WORKDIR /app

# Install dependencies
COPY package.json ./
RUN npm install

# Copy app source
COPY . .

# Build the app
RUN npm run build

# Install serve and run the app
RUN npm install -g serve
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]