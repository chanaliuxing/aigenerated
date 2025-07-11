const express = require('express');
const router = express.Router();

// Static workflow phase list
const phases = [
  { name: 'INFO_COLLECTION', displayName: 'Information Collection' },
  { name: 'CASE_ANALYSIS', displayName: 'Case Analysis' },
  { name: 'PRODUCT_RECOMMENDATION', displayName: 'Product Recommendation' },
  { name: 'SALES_CONVERSION', displayName: 'Sales Conversion' }
];

// Return available workflow phases
router.get('/phases', async (req, res) => {
  res.json({ success: true, phases });
});

module.exports = router;
