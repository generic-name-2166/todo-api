CREATE OR REPLACE FUNCTION update_task(
    p_user_id integer,
    p_task_id integer,
    p_name varchar(100),
    p_description text,
    p_finished boolean
)
RETURNS boolean AS $$
DECLARE
    is_authorized boolean;
BEGIN
    is_authorized := find_is_authorized(p_user_id, p_task_id, 'update');

    IF is_authorized THEN
        UPDATE task
        SET name = p_name, description = p_description
        WHERE id = p_task_id;

        IF p_finished IS NOT NULL THEN
            UPDATE task
            SET finished = p_finished
            WHERE id = p_task_id;
        END IF;

        RETURN TRUE;
    ELSE
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
