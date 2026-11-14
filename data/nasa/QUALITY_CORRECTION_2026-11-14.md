# GLDAS Morocco data correction

The original v2 data commit included 32,544 `-9999` source-fill values in the combined GLDAS Morocco cube. They occupy 113 of its 400 grid cells in every month and are missing values, not soil-moisture readings.

This branch keeps the original v2 regional data commit and changes only the combined GLDAS Morocco cube, its validation report, and this correction note. The combined cube now stores those values as `NaN`. Valid coverage is 287/400 cells (71.75%) each month, across all 288 months. The 288 downloaded monthly source subsets remain byte-for-byte as originally committed for provenance.

Any derived statistics, charts or receipts made from the old cube must be regenerated before use. No application code or derived output is included in this data-only branch.
