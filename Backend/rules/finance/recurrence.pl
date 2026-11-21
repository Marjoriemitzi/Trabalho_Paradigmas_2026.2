:- module(recurrence, [recurrence_due/5]).
:- encoding(utf8).

% recurrence_due(+Frequencia, +Dia, +Ano, +Mes, +DiaDoMes)
% Verdadeiro se a data é uma ocorrência da regra.
% weekly: Dia de 1 (segunda) a 7 (domingo). monthly: Dia de 1 a 31; em mês mais
% curto, vale o último dia do mês.
recurrence_due(weekly, DiaDaSemana, Ano, Mes, Dia) :-
    day_of_the_week(date(Ano, Mes, Dia), DiaDaSemana).
recurrence_due(monthly, DiaPedido, Ano, Mes, Dia) :-
    last_day(Ano, Mes, Ultimo),
    Dia =:= min(DiaPedido, Ultimo).

last_day(Ano, 2, 29) :- leap_year(Ano), !.
last_day(_, 2, 28) :- !.
last_day(_, Mes, 30) :- memberchk(Mes, [4, 6, 9, 11]), !.
last_day(_, _, 31).

leap_year(Ano) :- Ano mod 400 =:= 0, !.
leap_year(Ano) :- Ano mod 4 =:= 0, Ano mod 100 =\= 0.
