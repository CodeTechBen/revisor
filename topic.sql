SELECT
    DATE_TRUNC('month', ah.answer_time) AS month_start,
    t.topic_name,
    COUNT(*) FILTER (WHERE a.is_correct) AS correct_answers,
    --COUNT(*) FILTER (WHERE NOT a.is_correct) AS incorrect_answers,
    -- COUNT(*) AS total_answers,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE a.is_correct) / COUNT(*),
        2
    ) AS accuracy_percent
FROM answer_history ah
JOIN answer a 
    ON ah.answer_id = a.answer_id
JOIN question q 
    ON a.question_id = q.question_id
JOIN topic t 
    ON q.topic_id = t.topic_id
GROUP BY month_start, t.topic_name
ORDER BY topic_name ASC;