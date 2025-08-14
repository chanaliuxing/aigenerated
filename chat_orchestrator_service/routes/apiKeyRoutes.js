const express = require('express');
const router = express.Router();
const configStore = require('../utils/configStore');

// Get all stored API keys
router.get('/', async (req, res) => {
  res.json({ success: true, keys: configStore.getApiKeys() });
});

// Store a new API key
router.post('/', async (req, res) => {
  const key = {
    id: Date.now().toString(),
    value: req.body?.value || '',
    provider: req.body?.provider || 'unknown'
  };
  configStore.addApiKey(key);
  res.status(201).json({ success: true, key });
});

// Delete an API key by id
router.delete('/:id', async (req, res) => {
  configStore.deleteApiKey(req.params.id);
  res.json({ success: true });
});

module.exports = router;
