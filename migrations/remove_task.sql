CREATE OR REPLACE FUNCTION remove_task(p_user_id integer, p_task_id integer)
RETURNS boolean AS $$
DECLARE
    is_creator boolean;
BEGIN
    is_creator := find_is_creator(p_user_id, p_task_id);

    IF is_creator THEN
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
