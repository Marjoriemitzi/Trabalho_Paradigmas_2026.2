valid_password(Senha) :-
    string_length(Senha, Tamanho), Tamanho >= 12,
    has_upper(Senha),
    has_lower(Senha),
    has_digit(Senha),
    has_symbol(Senha).

password_error(Senha, too_short) :-
    string_length(Senha, Tamanho), Tamanho < 12.
password_error(Senha, no_upper) :-
    \+ has_upper(Senha).
password_error(Senha, no_lower) :-
    \+ has_lower(Senha).
password_error(Senha, no_digit) :-
    \+ has_digit(Senha).
password_error(Senha, no_symbol) :-
    \+ has_symbol(Senha).

has_upper(Senha)  :- has_char(Senha, upper(_)).
has_lower(Senha)  :- has_char(Senha, lower(_)).
has_digit(Senha)  :- has_char(Senha, digit(_)).
has_symbol(Senha) :-
    string_chars(Senha, Letras), member(Letra, Letras), \+ char_type(Letra, alnum).

has_char(Senha, Tipo) :-
    string_chars(Senha, Letras), member(Letra, Letras), char_type(Letra, Tipo).
