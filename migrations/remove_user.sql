CREATE OR REPLACE FUNCTION remove_user(p_user_id integer)
RETURNS void AS $$
BEGIN
    DELETE FROM "user"
    WHERE id = p_user_id;

    DELETE FROM task
    WHERE creator_id = p_user_id;

    DELETE FROM permissions
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;
