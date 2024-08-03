CREATE TABLE "user"
(
    id serial NOT NULL PRIMARY KEY,
    username character varying(50) NOT NULL UNIQUE,
    hashed_password text NOT NULL
);
