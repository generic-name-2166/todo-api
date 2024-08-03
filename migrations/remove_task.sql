CREATE OR REPLACE FUNCTION remove_task(p_user_id integer, p_task_id integer)
RETURNS boolean AS $$
DECLARE
    is_authorized boolean;
BEGIN
    is_authorized := (SELECT EXISTS (
        SELECT 1
        FROM task AS t
        WHERE t.id = p_task_id AND t.creator_id = p_user_id
    ));

    IF is_authorized THEN
        DELETE FROM task
        WHERE id = p_task_id;

        DELETE FROM permissions
        WHERE task_id = p_task_id;

        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
