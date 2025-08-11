// start-server.js
const path = require('path');
const { config } = require('dotenv');

// Load environment variables from .env.nocodb
config({ path: path.join(__dirname, '.env.nocodb') });

// Set environment variables
process.env.NC_DB = process.env.DATABASE_URL;
process.env.PORT = process.env.PORT || '8080';

console.log('Starting NocoDB...');
console.log(`URL: http://localhost:${process.env.PORT}`);
console.log('Press Ctrl+C to stop\n');

// Start NocoDB
require('nocodb');
