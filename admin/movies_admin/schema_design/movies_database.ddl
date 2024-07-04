CREATE SCHEMA IF NOT EXISTS content;

CREATE TABLE IF NOT EXISTS content.film_work (
    id uuid PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    creation_date DATE,
    rating FLOAT,
    type TEXT not null,
    created timestamp with time zone,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.genre (
    id uuid PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created timestamp with time zone,
    modified timestamp with time zone
);
CREATE UNIQUE INDEX name_idx ON content.genre (name);

CREATE TABLE IF NOT EXISTS content.genre_film_work (
    id uuid PRIMARY KEY,
    genre_id uuid NOT NULL,
    film_work_id uuid NOT NULL,
    created timestamp with time zone,
    
    CONSTRAINT FK_genre_film_work_genre FOREIGN KEY(genre_id)
    	REFERENCES content.genre(id),
    CONSTRAINT FK_genre_film_work_film_work FOREIGN KEY(film_work_id)
    	REFERENCES content.film_work(id),

    UNIQUE (film_work_id, genre_id)
);

CREATE TABLE IF NOT EXISTS content.person (
    id uuid PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    created timestamp with time zone,
    modified timestamp with time zone
);

CREATE TABLE IF NOT EXISTS content.person_film_work (
    id uuid PRIMARY KEY,
    person_id uuid NOT NULL,
    film_work_id uuid NOT NULL,
    role VARCHAR(255) NOT NULL,
    created timestamp with time zone,
    
    CONSTRAINT FK_person_film_work_person FOREIGN KEY(person_id)
    	REFERENCES content.person(id),
    CONSTRAINT FK_person_film_work_film_work FOREIGN KEY(film_work_id)
    	REFERENCES content.film_work(id),

    UNIQUE (film_work_id, person_id, role)
);
