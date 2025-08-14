const express = require('express');
const router = express.Router();
const configStore = require('../utils/configStore');

// Return current configuration settings
router.get('/', async (req, res) => {
  res.json({ success: true, config: configStore.getSettings() });
});

// Update configuration settings
router.put('/', async (req, res) => {
  const updated = configStore.updateSettings(req.body || {});
  res.json({ success: true, config: updated });
});

module.exports = router;
