const express = require('express');
const router = express.Router();

// Placeholder workflow routes
router.get('/phases', async (req, res) => {
  res.json({ success: true, phases: [] });
});

module.exports = router;
