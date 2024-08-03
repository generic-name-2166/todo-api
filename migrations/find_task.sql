CREATE OR REPLACE FUNCTION find_task(p_user_id integer, p_task_id integer)
RETURNS TABLE(
    id integer,
    creator_id integer,
    name varchar(100),
    description text,
    finished boolean
) AS $$
BEGIN
    RETURN QUERY 
    SELECT t.id, t.creator_id, t.name, t.description, t.finished
    FROM task AS t
    LEFT JOIN permissions AS p
    ON t.id = p.task_id AND p.user_id = p_user_id AND p.perm_type = 'read'
    WHERE t.id = p_task_id AND (t.creator_id = p_user_id OR p.user_id IS NOT NULL);
END;
$$ LANGUAGE plpgsql;
