CREATE OR REPLACE FUNCTION find_is_authorized(
    p_user_id integer, 
    p_task_id integer, 
    p_perm_type varchar(50)
)
RETURNS boolean AS $$
BEGIN
    RETURN (SELECT EXISTS (
        SELECT 1
        FROM task AS t
        LEFT JOIN permissions AS p
        ON t.id = p.task_id AND p.user_id = p_user_id AND p.perm_type = p_perm_type
        WHERE t.id = p_task_id AND (t.creator_id = p_user_id OR p.user_id IS NOT NULL)
    ));
END;
$$ LANGUAGE plpgsql;
