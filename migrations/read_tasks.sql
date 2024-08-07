CREATE OR REPLACE FUNCTION read_tasks(p_user_id integer)
RETURNS TABLE(
    id integer,
    creator_id integer,
    name varchar(100),
    description text,
    finished boolean
) STABLE AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id, 
        t.creator_id, 
        t.name, 
        t.description, 
        t.finished 
    FROM 
        task t
    WHERE 
        t.creator_id = p_user_id
    UNION ALL
    SELECT 
        t.id, 
        t.creator_id, 
        t.name, 
        t.description, 
        t.finished 
    FROM 
        task t
    JOIN 
        permissions p ON t.id = p.task_id
    WHERE 
        p.user_id = p_user_id AND p.perm_type = 'read';
END;
$$ LANGUAGE plpgsql;
