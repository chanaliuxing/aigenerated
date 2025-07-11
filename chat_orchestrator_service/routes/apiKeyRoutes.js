const express = require('express');
const router = express.Router();

// Placeholder API key management routes
router.get('/', async (req, res) => {
  res.json({ success: true, keys: [] });
});

router.post('/', async (req, res) => {
  res.status(201).json({ success: true, message: 'API key stored (stub)' });
});

router.delete('/:id', async (req, res) => {
  res.json({ success: true, message: `Deleted key ${req.params.id} (stub)` });
});

module.exports = router;
