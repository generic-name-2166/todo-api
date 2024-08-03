CREATE OR REPLACE FUNCTION find_is_creator(
    p_user_id integer, 
    p_task_id integer 
)
RETURNS boolean AS $$
BEGIN
    RETURN (SELECT EXISTS (
        SELECT 1
        FROM task AS t
        WHERE t.id = p_task_id AND t.creator_id = p_user_id
    ));
END;
$$ LANGUAGE plpgsql;
