CREATE OR REPLACE FUNCTION delete_user(p_user_id integer)
RETURNS void AS $$
BEGIN
    DELETE FROM "user"
    WHERE id = p_user_id;
END;
$$ LANGUAGE plpgsql;
