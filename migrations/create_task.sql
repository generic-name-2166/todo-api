CREATE OR REPLACE FUNCTION create_task(p_user_id integer, p_name varchar(50), p_description text)
RETURNS void AS $$
BEGIN
    INSERT INTO "task" (creator_id, name, description)
    VALUES (p_user_id, p_name, p_description);
END;
$$ LANGUAGE plpgsql;
