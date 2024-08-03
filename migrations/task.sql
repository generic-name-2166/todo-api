CREATE TABLE task
(
    id serial NOT NULL PRIMARY KEY,
    creator_id integer NOT NULL,
    name varchar(100) NOT NULL,
    description text,
    finished boolean NOT NULL DEFAULT FALSE
);
