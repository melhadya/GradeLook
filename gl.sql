/*create table users(
    id integer primary key,
    username text unique not null,
    hash text not null,
    name text not null,
    title text not null,
    phone text not null,
    email text,
    quota integer default 100,
    consumption integer default 0
);
*/

create table classes(
    id integer primary key,
    cname text not null unique,
    ctype text not null ---online/school/private/center + grade
);

create table students(
    id integer primary key,
    sname text not null,
    birth number not null,
    sclass text not null,
    email text not null,
    phone text not null,
    foreign key(class) references classes(cname) on delete cascade on update cascade
);

create table categories(
    id integer primary key,
    catname text not null unique
);

create table instances(
    id integer primary key,
    iname text not null,
    code text not null,
    class text not null,
    category text not null,
    idate text not null,
    foreign key(category) references categories(catname) on delete cascade on update cascade,
    foreign key(class) references classes(cname) on delete cascade on update cascade
);

/*
create table instX(
    id integer primary key,
    student integer not null,
    score numeric default 0,
    total numeric not null,
    foreign key(student) references students(id) on delete cascade on update cascade
);
*/
