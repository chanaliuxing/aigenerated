const fs = require('fs');
const path = require('path');

const dataDir = path.join(__dirname, '../data');
const configFile = path.join(dataDir, 'config.json');

function load() {
  try {
    if (fs.existsSync(configFile)) {
      return JSON.parse(fs.readFileSync(configFile, 'utf8'));
    }
  } catch (err) {
    console.error('Config load error:', err);
  }
  return { apiKeys: [], settings: {} };
}

function save(data) {
  fs.mkdirSync(dataDir, { recursive: true });
  fs.writeFileSync(configFile, JSON.stringify(data, null, 2));
}

function getSettings() {
  return load().settings;
}

function updateSettings(updates) {
  const data = load();
  data.settings = Object.assign({}, data.settings, updates);
  save(data);
  return data.settings;
}

function getApiKeys() {
  return load().apiKeys;
}

function addApiKey(key) {
  const data = load();
  data.apiKeys.push(key);
  save(data);
  return key;
}

function deleteApiKey(id) {
  const data = load();
  data.apiKeys = data.apiKeys.filter(k => k.id !== id);
  save(data);
}

module.exports = {
  getSettings,
  updateSettings,
  getApiKeys,
  addApiKey,
  deleteApiKey
};
