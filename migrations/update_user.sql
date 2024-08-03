CREATE OR REPLACE FUNCTION update_user(p_id integer, p_username varchar(50))
RETURNS boolean AS $$
DECLARE
    user_count integer;
BEGIN
    user_count := (SELECT COUNT(*) FROM "user" WHERE username = p_username);

    IF user_count > 0 THEN
        -- username is not unique
        RETURN FALSE;
    ELSE
        UPDATE "user" SET username = p_username
        WHERE p_id = id;
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql;
