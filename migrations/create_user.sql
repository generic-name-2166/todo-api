CREATE OR REPLACE FUNCTION create_user(p_username varchar(50), p_hashed_password text)
RETURNS boolean AS $$
DECLARE
    user_count integer;
BEGIN
    user_count := (SELECT COUNT(*) FROM "user" WHERE username = p_username);

    IF user_count > 0 THEN
        -- username is not unique
        RETURN FALSE;
    ELSE
        INSERT INTO "user" (username, hashed_password)
        VALUES (p_username, p_hashed_password);
        RETURN TRUE;
    END IF;
END;
$$ LANGUAGE plpgsql;
