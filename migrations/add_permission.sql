CREATE OR REPLACE FUNCTION add_permission(
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
        INSERT INTO permissions (user_id, task_id, perm_type)
        VALUES (p_recepient_id, p_task_id, p_perm_type)
        ON CONFLICT DO NOTHING;
        
        RETURN TRUE;
    ELSE 
        RETURN FALSE;
    END IF;
END;
$$ LANGUAGE plpgsql;
