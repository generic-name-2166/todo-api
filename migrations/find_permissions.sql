CREATE OR REPLACE FUNCTION find_permissions(
    p_user_id integer,
    p_task_id integer
)
RETURNS TABLE(
    task_id integer,
    user_id integer,
    perm_type varchar(50)
) AS $$
BEGIN
    -- Caller is supposed to guarantee user has permission to do this
    RETURN QUERY
    SELECT p.task_id, p.user_id, p.perm_type
    FROM permissions AS p
    WHERE p.task_id = p_task_id;
END;
$$ LANGUAGE plpgsql;
