CREATE OR REPLACE FUNCTION get_current_user(p_username character varying)
RETURNS TABLE(id integer, username varchar(50), hashed_password text) AS $$
BEGIN
    RETURN QUERY 
    SELECT u.id, u.username, u.hashed_password
    FROM "user" AS u
    WHERE u.username = p_username;
END;
$$ LANGUAGE plpgsql;
