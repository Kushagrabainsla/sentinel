-- Example seed row; safe to run multiple times
INSERT INTO campaigns (name, template_id, segment_id, state)
SELECT 'Sample', 'tmpl_sample', 'seg_all', 'draft'
WHERE NOT EXISTS (SELECT 1 FROM campaigns WHERE name = 'Sample');
