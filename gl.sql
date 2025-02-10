/*create table users(
    id integer primary key,
    username text unique not null,
    hash text not null,
    name text not null,
    title text not null,
    phone text not null,
    email text,
    quota integer not null,
    consumption integer default 0
);
*/

create table students(
    id integer primary key,
    name text not null,
    birth number not null,
    grade text not null,
    email text not null,
    phone text not null
);

create table categories(
    catname text not null unique
);

create table instances(
    id integer primary key,
    name text not null,
    code text not null,
    grade text not null,
    category text not null,
    foreign key(category) references categories(catname)
);

/*
create table instX(
    id integer primary key,
    student integer not null,
    score numeric default 0,
    total numeric not null,
    foreign key(student) references students(id)
);
*/
