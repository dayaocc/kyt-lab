SELECT * FROM high_risk_snapshot 
WHERE total_risk_score >= 80 AND is_reported = FALSE;