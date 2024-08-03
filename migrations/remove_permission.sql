CREATE OR REPLACE FUNCTION remove_permission(
    p_user_id integer,
    p_task_id integer,
    p_recepient_id integer,
    p_perm_type varchar(50)
)
RETURNS boolean AS $$
DECLARE
    is_creator boolean;
BEGIN
    is_creator := find_is_creator(p_user_id, p_task_id);

    IF is_creator THEN
        DELETE FROM permissions 
        WHERE user_id = p_recepient_id AND task_id = p_task_id AND perm_type = p_perm_type;
        
        RETURN TRUE;
    ELSE 
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
