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
    is_authorized := (SELECT EXISTS (
        SELECT 1
        FROM task AS t
        LEFT JOIN permissions AS p
        ON t.id = p.task_id AND p.user_id = p_user_id AND p.perm_type = 'update'
        WHERE t.id = p_task_id AND (t.creator_id = p_user_id OR p.user_id IS NOT NULL)
    ));

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
