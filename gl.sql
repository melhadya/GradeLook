create table if not exists classes(
    id integer primary key,
    name text not null unique,
    type text not null ---online/school/private/center + grade
);

create table if not exists students(
    id integer primary key,
    name text not null,
    class integer not null,
    phone text not null,
    email text not null,
    foreign key(class) references classes(id) on delete cascade
);

create table if not exists categories(
    id integer primary key,
    name text not null unique
);

create table if not exists instances(
    id integer primary key,
    title text not null,
    class integer not null,
    category integer not null,
    date text not null,
    foreign key(category) references categories(id) on delete cascade,
    foreign key(class) references classes(id) on delete cascade
);

/*
create table users(
    id integer primary key,
    username text unique not null,
    hash text not null,
    name text not null,
    title text not null,
    phone text not null,
    email text not null,
    quota integer default 100,
    consumption integer default 0
);

create table inst+<instances.id>(
    id integer primary key,
    student integer not null,
    score numeric default 0,
    total numeric not null,
    foreign key(student) references students(id) on delete cascade
);
*/